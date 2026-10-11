"""security.py - shared input/security checks for ShopSense AI (Member 4).

Public contract (do not rename):
    validate_question(question) -> str          (raises ValidationError if invalid)
    validate_records(records)   -> {"ok", "records", "errors"}
    authorize_tool(tool_name, permissions) -> bool   (default deny)
Extra helpers: validate_upload(), redact_secrets(), flag_suspicious_text().

Everything uploaded is untrusted DATA. Nothing here (or anywhere) may eval/exec it.
"""
import math
import re
from datetime import date

# ---------------------------------------------------------------- limits
LIMITS = {
    "max_question_chars": 500,
    "max_file_bytes": 1_000_000,          # 1 MB
    "max_rows": 5_000,
    "max_string_chars": 100,
    "allowed_extensions": {".csv"},
    "allowed_content_types": {"text/csv", "application/csv", "application/vnd.ms-excel"},
    "max_quantity": 1_000_000,
    "max_money": 10_000_000.0,            # unit cost / price
    "min_date": date(2000, 1, 1),
    "max_date": date(2100, 12, 31),
}

# ---------------------------------------------------------------- tools
# Explicit allowlist: tool -> permission required. Everything else is DENIED.
ALLOWED_TOOLS = {
    "load_sales": "read_data",
    "sales_summary": "read_data",
    "get_reorder_candidates": "read_data",
}

PRODUCT_FIELDS = {"product_id", "name", "quantity", "unit_cost", "selling_price", "reorder_level"}
SALES_FIELDS = {"sale_id", "date", "product_id", "quantity_sold", "unit_price", "unit_cost"}
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ValidationError(ValueError):
    """Raised by validate_question / validate_upload with a user-safe message."""


# ---------------------------------------------------------------- question
def validate_question(question):
    """Return the cleaned question string, or raise ValidationError."""
    if not isinstance(question, str):
        raise ValidationError("Question must be text.")
    q = _CTRL_RE.sub("", question).strip()
    if not q:
        raise ValidationError("Question is empty.")
    if len(q) > LIMITS["max_question_chars"]:
        raise ValidationError(f"Question too long (max {LIMITS['max_question_chars']} characters).")
    return q


_INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)",
    r"disregard .{0,30}(instructions|rules)",
    r"system prompt", r"you are now", r"reveal .{0,30}(key|secret|password|prompt)",
    r"(delete|drop|erase) .{0,20}(records|inventory|data|table)",
    r"(place|make|send) .{0,20}(order|purchase|payment|message|email)",
]


def flag_suspicious_text(text):
    """Heuristic WARNING only. Never the sole defence: the real defences are the
    tool allowlist, read-only tools and treating text as data."""
    t = str(text).lower()
    return [p for p in _INJECTION_PATTERNS if re.search(p, t)]


# ---------------------------------------------------------------- upload
def validate_upload(filename, size_bytes, content_type=None):
    """Check file metadata BEFORE reading it. Returns safe basename or raises."""
    if not isinstance(filename, str) or not filename.strip():
        raise ValidationError("Missing file name.")
    if "\x00" in filename or "/" in filename or "\\" in filename or ".." in filename:
        raise ValidationError("Unsafe file name (path characters are not allowed).")
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in LIMITS["allowed_extensions"]:
        raise ValidationError("Only .csv files are allowed.")
    if content_type and content_type.split(";")[0].strip().lower() not in LIMITS["allowed_content_types"]:
        raise ValidationError("Unexpected content type; expected CSV.")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
        raise ValidationError("Invalid file size.")
    if size_bytes > LIMITS["max_file_bytes"]:
        raise ValidationError(f"File too large (max {LIMITS['max_file_bytes']} bytes).")
    return filename


# ---------------------------------------------------------------- records
def _num(value, field, lo, hi, integer, errs, prefix):
    if isinstance(value, bool):
        errs.append(f"{prefix}{field}: must be a number"); return None
    try:
        x = float(value) if isinstance(value, (int, float, str)) else None
        if isinstance(value, str) and not value.strip():
            x = None
    except ValueError:
        x = None
    if x is None or math.isnan(x) or math.isinf(x):
        errs.append(f"{prefix}{field}: not a valid number"); return None
    if integer and x != int(x):
        errs.append(f"{prefix}{field}: must be a whole number"); return None
    if not lo <= x <= hi:
        errs.append(f"{prefix}{field}: out of range ({lo}..{hi})"); return None
    return int(x) if integer else x


def _text(value, field, errs, prefix, id_like=False):
    if not isinstance(value, str) or not value.strip():
        errs.append(f"{prefix}{field}: required text"); return None
    v = value.strip()
    if len(v) > LIMITS["max_string_chars"]:
        errs.append(f"{prefix}{field}: too long (max {LIMITS['max_string_chars']})"); return None
    if _CTRL_RE.search(v) or v.startswith(_FORMULA_PREFIXES):
        errs.append(f"{prefix}{field}: formula-like or control characters not allowed"); return None
    if id_like and not _ID_RE.match(v):
        errs.append(f"{prefix}{field}: only letters, digits, - and _ allowed"); return None
    return v


def _check_product(r, prefix, errs):
    n0 = len(errs)
    out = {
        "product_id": _text(r.get("product_id"), "product_id", errs, prefix, True),
        "name": _text(r.get("name"), "name", errs, prefix),
        "quantity": _num(r.get("quantity"), "quantity", 0, LIMITS["max_quantity"], True, errs, prefix),
        "unit_cost": _num(r.get("unit_cost"), "unit_cost", 0, LIMITS["max_money"], False, errs, prefix),
        "selling_price": _num(r.get("selling_price"), "selling_price", 0, LIMITS["max_money"], False, errs, prefix),
        "reorder_level": _num(r.get("reorder_level"), "reorder_level", 0, LIMITS["max_quantity"], True, errs, prefix),
    }
    return out if len(errs) == n0 else None


def _check_sale(r, prefix, errs):
    n0 = len(errs)
    d = _text(r.get("date"), "date", errs, prefix)
    if d is not None:
        try:
            parsed = date.fromisoformat(d)
            if not LIMITS["min_date"] <= parsed <= LIMITS["max_date"]:
                errs.append(f"{prefix}date: out of range")
        except ValueError:
            errs.append(f"{prefix}date: must be YYYY-MM-DD")
    out = {
        "sale_id": _text(r.get("sale_id"), "sale_id", errs, prefix, True),
        "date": d,
        "product_id": _text(r.get("product_id"), "product_id", errs, prefix, True),
        "quantity_sold": _num(r.get("quantity_sold"), "quantity_sold", 1, LIMITS["max_quantity"], True, errs, prefix),
        "unit_price": _num(r.get("unit_price"), "unit_price", 0, LIMITS["max_money"], False, errs, prefix),
        "unit_cost": _num(r.get("unit_cost"), "unit_cost", 0, LIMITS["max_money"], False, errs, prefix),
    }
    return out if len(errs) == n0 else None


def validate_records(records):
    """Validate product OR sales records. Returns {"ok", "records", "errors"}.
    Invalid rows are reported (never silently dropped); ok is False if any error."""
    errors = []
    if not isinstance(records, (list, tuple)):
        return {"ok": False, "records": [], "errors": ["records must be a list of dicts"]}
    if len(records) > LIMITS["max_rows"]:
        return {"ok": False, "records": [],
                "errors": [f"Too many rows ({len(records)}); max {LIMITS['max_rows']}"]}
    clean = []
    for i, r in enumerate(records, start=1):
        prefix = f"row {i}: "
        if not isinstance(r, dict):
            errors.append(prefix + "not a record"); continue
        keys = set(r.keys())
        if keys == PRODUCT_FIELDS:
            rec = _check_product(r, prefix, errors)
        elif keys == SALES_FIELDS:
            rec = _check_sale(r, prefix, errors)
        else:
            errors.append(prefix + "unknown or missing fields: "
                          + ", ".join(sorted(keys ^ (PRODUCT_FIELDS if keys & {"name", "quantity"} else SALES_FIELDS))))
            continue
        if rec is not None:
            clean.append(rec)
    return {"ok": not errors, "records": clean, "errors": errors}


# ---------------------------------------------------------------- tools
def authorize_tool(tool_name, permissions):
    """True only if tool is allowlisted AND its required permission is granted."""
    if not isinstance(tool_name, str) or tool_name not in ALLOWED_TOOLS:
        return False
    try:
        return ALLOWED_TOOLS[tool_name] in set(permissions or ())
    except TypeError:
        return False


# ---------------------------------------------------------------- secrets
_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{8,}|AIza[0-9A-Za-z_\-]{10,}|gsk_[A-Za-z0-9]{8,}|"
    r"(?i:api[_-]?key|secret|token|password)\s*[=:]\s*\S+)")


def redact_secrets(text):
    """Mask anything key-like before showing text to users or writing logs."""
    return _SECRET_RE.sub("[REDACTED]", str(text))
