from __future__ import annotations
import csv, io, re
from config import MAX_QUESTION_CHARS, MAX_ROWS
from schemas import SALES_REQUIRED, PRODUCTS_REQUIRED

class ValidationError(ValueError): pass

def validate_question(question: str) -> str:
    if not isinstance(question, str): raise ValidationError("Question must be text.")
    q=question.strip()
    if not q: raise ValidationError("Please enter a business question.")
    if len(q)>MAX_QUESTION_CHARS: raise ValidationError(f"Question is too long (maximum {MAX_QUESTION_CHARS} characters).")
    return q

def validate_records(records):
    errors=[]; clean=[]
    if not isinstance(records,list): return {"ok":False,"records":[],"errors":["Records must be a list."]}
    if len(records)>MAX_ROWS: return {"ok":False,"records":[],"errors":[f"Too many rows; maximum is {MAX_ROWS}."]}
    for i,row in enumerate(records, start=2):
        if not isinstance(row,dict): errors.append(f"Row {i}: expected a record."); continue
        if not str(row.get("product_id","")).strip(): errors.append(f"Row {i}: product_id is required."); continue
        clean.append(dict(row))
    return {"ok":not errors,"records":clean,"errors":errors}

def validate_upload(filename, size, content, max_mb=5):
    errors=[]
    if not isinstance(filename,str) or not filename.lower().endswith('.csv'): errors.append("Only .csv files are supported.")
    if filename and (filename.startswith(('/', '\\')) or '..' in filename.replace('\\','/').split('/')): errors.append("Unsafe filename.")
    if not isinstance(content,(bytes,bytearray)) or size<=0 or not content: errors.append("The uploaded file is empty or invalid.")
    elif len(content) != size: errors.append("Uploaded size does not match the supplied content length.")
    if isinstance(size,int) and size>max_mb*1024*1024: errors.append(f"File exceeds the {max_mb} MB limit.")
    if content and b'\x00' in content[:4096]: errors.append("The file does not look like a text CSV.")
    return not errors, errors

def validate_csv_columns(fieldnames, required):
    if not fieldnames: return ["CSV has no header row."]
    normalized={str(x).strip() for x in fieldnames if x is not None}
    missing=[x for x in required if x not in normalized]
    return ["Missing required columns: "+", ".join(missing)] if missing else []

def safe_csv_reader(file_obj):
    raw=file_obj.read() if hasattr(file_obj,'read') else file_obj
    if isinstance(raw,str): text=raw
    else:
        text=None
        for enc in ('utf-8-sig','utf-8','cp1252'):
            try: text=bytes(raw).decode(enc); break
            except UnicodeDecodeError: continue
        if text is None: raise ValidationError("Could not decode CSV. Save it as UTF-8 and try again.")
    if not text.strip(): raise ValidationError("The CSV file is empty.")
    try:
        reader=csv.reader(io.StringIO(text, newline=''), strict=True)
        try: raw_headers=next(reader)
        except StopIteration: raise ValidationError("CSV has no header row.")
        headers=[str(h).strip() for h in raw_headers]
        if not headers or not any(headers): raise ValidationError("CSV has no header row.")
        if len(headers)>100: raise ValidationError("CSV has too many columns.")
        normalized=[h.casefold() for h in headers]
        if any(not h for h in headers): raise ValidationError("CSV contains a blank column name.")
        if len(set(normalized)) != len(normalized): raise ValidationError("CSV contains duplicate column names; rename them so each column is unique.")
        rows=[]
        for n,values in enumerate(reader,start=2):
            if n>MAX_ROWS+1: raise ValidationError(f"CSV exceeds the {MAX_ROWS} row limit.")
            if len(values)>len(headers): raise ValidationError(f"Row {n}: more values than columns.")
            if len(values)<len(headers): values=values+['']*(len(headers)-len(values))
            rows.append({headers[i]: (values[i].strip() if isinstance(values[i],str) else values[i]) for i in range(len(headers))})
        return headers, rows
    except csv.Error as e: raise ValidationError("Malformed CSV quoting or delimiters. Re-save as a standard comma-separated CSV.") from e

