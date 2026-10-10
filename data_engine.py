
"""ShopSense AI: trusted data and analytics engine.

This module performs read-only analysis on fictional or authorized CSV data.
It does not make purchases or modify inventory.
"""

import csv
import math
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


SALES_COLUMNS = (
    "sale_id",
    "date",
    "product_id",
    "quantity_sold",
    "unit_price",
    "unit_cost",
)

PRODUCT_COLUMNS = (
    "product_id",
    "name",
    "quantity",
    "unit_cost",
    "selling_price",
    "reorder_level",
)


def _parse_decimal(value, field, row_number, errors, *, allow_zero=True):
    """Parse a finite, non-negative decimal value."""
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        errors.append({
            "row": row_number,
            "field": field,
            "message": f"{field} must be a valid number.",
        })
        return None

    if not number.is_finite():
        errors.append({
            "row": row_number,
            "field": field,
            "message": f"{field} must be finite.",
        })
        return None

    if number < 0 or (not allow_zero and number == 0):
        errors.append({
            "row": row_number,
            "field": field,
            "message": (
                f"{field} must be "
                + ("greater than zero." if not allow_zero else "non-negative.")
            ),
        })
        return None

    return number


def _parse_date(value, row_number, errors):
    try:
        parsed = date.fromisoformat(str(value).strip())
        if parsed.isoformat() != str(value).strip():
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        errors.append({
            "row": row_number,
            "field": "date",
            "message": "date must use YYYY-MM-DD format.",
        })
        return None


def _read_csv(file_or_path, required_columns):
    """Read a CSV and report file-level or header errors."""
    result = {
        "ok": False,
        "rows": [],
        "errors": [],
        "warnings": [],
    }

    path = Path(file_or_path)

    if path.suffix.lower() != ".csv":
        result["errors"].append({
            "row": None,
            "field": None,
            "message": "Unsupported format. Only .csv files are supported.",
        })
        return result

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                result["errors"].append({
                    "row": 1,
                    "field": None,
                    "message": "CSV is empty or has no header.",
                })
                return result

            headers = [header.strip() for header in reader.fieldnames]

            if len(headers) != len(set(headers)):
                result["errors"].append({
                    "row": 1,
                    "field": None,
                    "message": "Duplicate column names are not allowed.",
                })
                return result

            missing = [
                column for column in required_columns
                if column not in headers
            ]

            if missing:
                result["errors"].append({
                    "row": 1,
                    "field": None,
                    "message": f"Missing required columns: {missing}",
                })
                return result

            reader.fieldnames = headers

            for row in reader:
                row_number = reader.line_num
                if None in row:
                    result["errors"].append({
                        "row": row_number,
                        "field": None,
                        "message": "Row contains more values than the header.",
                    })
                    continue
                result["rows"].append((row_number, row))

    except (OSError, UnicodeError, csv.Error) as exc:
        result["errors"].append({
            "row": None,
            "field": None,
            "message": f"Could not read CSV: {exc}",
        })
        return result

    result["ok"] = True
    return result


def load_sales(file_or_path) -> dict:
    """Load sales CSV, validating each row without silently dropping errors."""
    raw = _read_csv(file_or_path, SALES_COLUMNS)

    result = {
        "ok": False,
        "records": [],
        "errors": list(raw["errors"]),
        "warnings": list(raw["warnings"]),
    }

    if not raw["ok"]:
        return result

    seen_ids = set()

    for row_number, row in raw["rows"]:
        row_errors = []

        sale_id = (row.get("sale_id") or "").strip()
        product_id = (row.get("product_id") or "").strip()

        if not sale_id:
            row_errors.append({
                "row": row_number,
                "field": "sale_id",
                "message": "sale_id is required.",
            })

        if not product_id:
            row_errors.append({
                "row": row_number,
                "field": "product_id",
                "message": "product_id is required.",
            })

        parsed_date = _parse_date(row.get("date"), row_number, row_errors)

        quantity = _parse_decimal(
            row.get("quantity_sold"), "quantity_sold",
            row_number, row_errors, allow_zero=False,
        )

        unit_price = _parse_decimal(
            row.get("unit_price"), "unit_price", row_number, row_errors,
        )

        raw_cost = (row.get("unit_cost") or "").strip()
        unit_cost = None

        if not raw_cost:
            row_errors.append({
                "row": row_number,
                "field": "unit_cost",
                "message": "unit_cost is missing; COGS cannot be calculated.",
            })
        else:
            unit_cost = _parse_decimal(
                raw_cost, "unit_cost", row_number, row_errors,
            )

        if quantity is not None and quantity != quantity.to_integral_value():
            row_errors.append({
                "row": row_number,
                "field": "quantity_sold",
                "message": "quantity_sold must be a whole number.",
            })

        if sale_id and sale_id in seen_ids:
            row_errors.append({
                "row": row_number,
                "field": "sale_id",
                "message": f"Duplicate sale_id: {sale_id}.",
            })

        if sale_id:
            seen_ids.add(sale_id)

        if row_errors:
            result["errors"].extend(row_errors)
            continue

        result["records"].append({
            "sale_id": sale_id,
            "date": parsed_date.isoformat(),
            "product_id": product_id,
            "quantity_sold": int(quantity),
            "unit_price": unit_price,
            "unit_cost": unit_cost,
        })

    result["ok"] = len(result["errors"]) == 0

    if result["errors"]:
        result["warnings"].append(
            "Only valid rows are included in records; review all errors."
        )

    return result


def load_products(file_or_path) -> dict:
    """Load and validate the shared product CSV structure."""
    raw = _read_csv(file_or_path, PRODUCT_COLUMNS)

    result = {
        "ok": False,
        "records": [],
        "errors": list(raw["errors"]),
        "warnings": list(raw["warnings"]),
    }

    if not raw["ok"]:
        return result

    seen_ids = set()

    for row_number, row in raw["rows"]:
        row_errors = []
        product_id = (row.get("product_id") or "").strip()
        name = (row.get("name") or "").strip()

        if not product_id:
            row_errors.append({
                "row": row_number,
                "field": "product_id",
                "message": "product_id is required.",
            })
        elif product_id in seen_ids:
            row_errors.append({
                "row": row_number,
                "field": "product_id",
                "message": f"Duplicate product_id: {product_id}.",
            })

        if product_id:
            seen_ids.add(product_id)

        if not name:
            row_errors.append({
                "row": row_number,
                "field": "name",
                "message": "name is required.",
            })

        quantity = _parse_decimal(
            row.get("quantity"), "quantity", row_number, row_errors,
        )
        cost = _parse_decimal(
            row.get("unit_cost"), "unit_cost", row_number, row_errors,
        )
        price = _parse_decimal(
            row.get("selling_price"), "selling_price", row_number, row_errors,
        )
        reorder_level = _parse_decimal(
            row.get("reorder_level"), "reorder_level", row_number, row_errors,
        )

        for field, value in (
            ("quantity", quantity),
            ("reorder_level", reorder_level),
        ):
            if value is not None and value != value.to_integral_value():
                row_errors.append({
                    "row": row_number,
                    "field": field,
                    "message": f"{field} must be a whole number.",
                })

        if row_errors:
            result["errors"].extend(row_errors)
            continue

        result["records"].append({
            "product_id": product_id,
            "name": name,
            "quantity": int(quantity),
            "unit_cost": cost,
            "selling_price": price,
            "reorder_level": int(reorder_level),
        })

    result["ok"] = len(result["errors"]) == 0

    if result["errors"]:
        result["warnings"].append(
            "Only valid product rows are included in records."
        )

    return result


def validate_product_references(records, products):
    """Report sales referring to product IDs absent from product data."""
    product_ids = {p["product_id"] for p in products}
    errors = []
    for record in records:
        if record["product_id"] not in product_ids:
            errors.append({
                "sale_id": record["sale_id"],
                "product_id": record["product_id"],
                "message": "Sale references an unknown product_id.",
            })
    return {"ok": not errors, "errors": errors}


def sales_summary(records, start_date, end_date) -> dict:
    """Calculate revenue, COGS, gross profit, units and top products.

    Date range is inclusive and uses local calendar dates (YYYY-MM-DD).
    If any included record lacks a usable unit_cost, COGS and gross profit
    are returned as None rather than being misleadingly understated.
    """
    result = {
        "ok": False,
        "revenue": 0.0,
        "cost_of_goods_sold": 0.0,
        "gross_profit": 0.0,
        "units_sold": 0,
        "top_products": [],
        "warnings": [],
    }

    try:
        start = date.fromisoformat(str(start_date))
        end = date.fromisoformat(str(end_date))
    except (ValueError, TypeError):
        result["warnings"].append("Dates must use YYYY-MM-DD format.")
        return result

    if start.isoformat() != str(start_date) or end.isoformat() != str(end_date):
        result["warnings"].append("Dates must use YYYY-MM-DD format.")
        return result

    if start > end:
        result["warnings"].append("start_date must not be after end_date.")
        return result

    revenue = Decimal("0")
    cogs = Decimal("0")
    units = 0
    missing_cost = False
    product_totals = defaultdict(lambda: {
        "units_sold": 0,
        "revenue": Decimal("0"),
    })

    for record in records:
        try:
            sale_date = date.fromisoformat(str(record["date"]))
            if not start <= sale_date <= end:
                continue

            quantity = int(record["quantity_sold"])
            price = Decimal(str(record["unit_price"]))
            cost_value = record.get("unit_cost")
            cost = None if cost_value is None else Decimal(str(cost_value))

            if (
                quantity <= 0
                or not price.is_finite()
                or price < 0
                or (cost is not None and (not cost.is_finite() or cost < 0))
            ):
                raise ValueError

        except (KeyError, ValueError, TypeError, InvalidOperation):
            result["warnings"].append(
                "An invalid record was excluded from the summary."
            )
            continue

        line_revenue = quantity * price
        revenue += line_revenue
        units += quantity

        product_id = str(record.get("product_id", "UNKNOWN"))
        product_totals[product_id]["units_sold"] += quantity
        product_totals[product_id]["revenue"] += line_revenue

        if cost is None:
            missing_cost = True
        else:
            cogs += quantity * cost

    result["revenue"] = float(revenue)
    result["units_sold"] = units
    result["top_products"] = [
        {
            "product_id": product_id,
            "units_sold": values["units_sold"],
            "revenue": float(values["revenue"]),
        }
        for product_id, values in sorted(
            product_totals.items(),
            key=lambda item: (
                -item[1]["units_sold"], item[0]
            ),
        )
    ]

    if missing_cost:
        result["cost_of_goods_sold"] = None
        result["gross_profit"] = None
        result["warnings"].append(
            "At least one included sale has missing unit_cost; "
            "COGS and gross profit are incomplete and not reported."
        )
    else:
        result["cost_of_goods_sold"] = float(cogs)
        result["gross_profit"] = float(revenue - cogs)

    result["warnings"].append(
        "Gross profit excludes rent, wages, tax, delivery, returns, "
        "and other unrecorded expenses."
    )
    result["ok"] = True
    return result


def get_reorder_candidates(
    products, average_daily_sales=None, lead_time_days=7, safety_days=3
) -> list:
    """Estimate reorder quantities using demand during lead time plus safety.

    average_daily_sales may be a dict mapping product_id to daily demand,
    or a product record containing average_daily_sales. Missing demand
    yields a candidate with an explicit warning, not a guessed quantity.
    """
    if lead_time_days < 0 or safety_days < 0:
        raise ValueError("lead_time_days and safety_days must be non-negative.")

    recommendations = []

    for product in products:
        product_id = product.get("product_id")
        stock = product.get("quantity")
        reorder_level = product.get("reorder_level")
        warnings = []

        if isinstance(average_daily_sales, dict):
            demand = average_daily_sales.get(product_id)
        else:
            demand = product.get("average_daily_sales")

        if demand is None:
            warnings.append("Average daily sales are missing.")
        else:
            try:
                demand = Decimal(str(demand))
                if not demand.is_finite() or demand < 0:
                    raise ValueError
            except (InvalidOperation, ValueError, TypeError):
                warnings.append("Average daily sales are invalid.")
                demand = None

        try:
            stock = int(stock)
            if stock < 0 or str(product.get("quantity")).strip() != str(stock):
                raise ValueError
        except (TypeError, ValueError):
            stock = None
            warnings.append("Current stock is missing or invalid.")

        try:
            reorder_level = int(reorder_level)
            if reorder_level < 0:
                raise ValueError
        except (TypeError, ValueError):
            reorder_level = None
            warnings.append("Reorder level is missing or invalid.")

        if demand is None or stock is None:
            suggested = None
            target = None
        else:
            target = int(
                (demand * (lead_time_days + safety_days)).to_integral_value(
                    rounding="ROUND_CEILING"
                )
            )
            suggested = max(0, target - stock)

        should_review = (
            suggested is None
            or (suggested > 0)
            or (
                reorder_level is not None
                and stock is not None
                and stock <= reorder_level
            )
        )

        if should_review:
            recommendations.append({
                "product_id": product_id,
                "name": product.get("name"),
                "current_stock": stock,
                "reorder_level": reorder_level,
                "average_daily_sales": (
                    float(demand) if demand is not None else None
                ),
                "lead_time_days": lead_time_days,
                "safety_days": safety_days,
                "target_stock": target,
                "suggested_reorder_quantity": suggested,
                "is_estimate": True,
                "warnings": warnings,
            })

    return recommendations


def anomaly_summary(records, products=None):
    """Report possible data anomalies, never assert fraud."""
    anomalies = []
    seen = set()

    for record in records:
        sale_id = record.get("sale_id")
        if sale_id in seen:
            anomalies.append({
                "type": "duplicate_sale_id",
                "sale_id": sale_id,
                "message": "Possible duplicate sale ID; review the source data.",
            })
        seen.add(sale_id)

        for field in ("quantity_sold", "unit_price", "unit_cost"):
            value = record.get(field)
            if value is not None:
                try:
                    if Decimal(str(value)) < 0:
                        anomalies.append({
                            "type": "negative_value",
                            "sale_id": sale_id,
                            "field": field,
                            "message": "Possible negative-value anomaly.",
                        })
                except InvalidOperation:
                    anomalies.append({
                        "type": "invalid_value",
                        "sale_id": sale_id,
                        "field": field,
                        "message": "Possible invalid numeric value.",
                    })

    if products is not None:
        for product in products:
            try:
                if int(product["quantity"]) < 0:
                    anomalies.append({
                        "type": "negative_stock",
                        "product_id": product.get("product_id"),
                        "message": "Possible negative-stock anomaly.",
                    })
            except (KeyError, ValueError, TypeError):
                anomalies.append({
                    "type": "invalid_stock",
                    "product_id": product.get("product_id"),
                    "message": "Stock quantity is missing or invalid.",
                })

    return {"ok": True, "anomalies": anomalies}
