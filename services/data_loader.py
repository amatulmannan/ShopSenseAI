from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import date
import re
from services.validation import safe_csv_reader, validate_csv_columns, ValidationError
from schemas import SALES_REQUIRED, PRODUCTS_REQUIRED

_NUM = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d{1,4})?$")
def _decimal(value, field, row, optional=False):
    if value is None or str(value).strip()=="":
        if optional: return None
        raise ValueError(f"Row {row}: {field} is required.")
    text=str(value).strip()
    if not _NUM.fullmatch(text): raise ValueError(f"Row {row}: {field} must be a non-negative number (up to 4 decimal places).")
    try: return Decimal(text)
    except InvalidOperation: raise ValueError(f"Row {row}: invalid {field}.")

def _read(file_or_path):
    if isinstance(file_or_path, str):
        with open(file_or_path,'rb') as f: return safe_csv_reader(f)
    return safe_csv_reader(file_or_path)

def load_sales(file_or_path):
    errors=[]; warnings=[]; records=[]; raw_rows=[]
    try:
        fields,rows=_read(file_or_path); errors.extend(validate_csv_columns(fields, SALES_REQUIRED))
        if errors: return {'ok':False,'records':[],'errors':errors,'warnings':warnings,'audit':{'rows_seen':len(rows),'rows_loaded':0,'rows_rejected':len(rows)}}
        seen=set(); exact_seen=set()
        for idx,r in enumerate(rows,start=2):
            raw_rows.append(r); row_errors=[]
            sid=str(r.get('sale_id','')).strip(); pid=str(r.get('product_id','')).strip()
            if not sid: row_errors.append(f"Row {idx}: sale_id is required.")
            elif sid in seen: row_errors.append(f"Row {idx}: duplicate sale_id {sid!r}; row rejected.")
            try:
                ds=str(r.get('date','')).strip(); d=date.fromisoformat(ds)
                if d.isoformat()!=ds: raise ValueError
            except Exception: row_errors.append(f"Row {idx}: date must be a valid YYYY-MM-DD date.")
            qtxt=str(r.get('quantity_sold','')).strip()
            if not re.fullmatch(r"[1-9]\d*",qtxt): row_errors.append(f"Row {idx}: quantity_sold must be a positive integer.")
            try: price=_decimal(r.get('unit_price'),'unit_price',idx)
            except ValueError as e: row_errors.append(str(e)); price=None
            try: cost=_decimal(r.get('unit_cost'),'unit_cost',idx,optional=True)
            except ValueError as e: row_errors.append(str(e)); cost=None
            if not pid: row_errors.append(f"Row {idx}: product_id is required.")
            if row_errors:
                errors.extend(row_errors); continue
            seen.add(sid)
            rec={'sale_id':sid,'date':d.isoformat(),'product_id':pid,'quantity_sold':int(qtxt),'unit_price':price,'unit_cost':cost}
            key=tuple((k,str(v)) for k,v in sorted(rec.items()))
            if key in exact_seen: warnings.append(f"Row {idx}: exact duplicate row detected; retained because sale_id uniqueness is the primary rule.")
            exact_seen.add(key); records.append(rec)
            if cost is None: warnings.append(f"Row {idx}: unit_cost is missing; complete gross profit cannot be calculated.")
        audit={'rows_seen':len(rows),'rows_loaded':len(records),'rows_rejected':len(rows)-len(records),'errors':len(errors),'warnings':len(warnings)}
        return {'ok':bool(records) and not errors or bool(records),'records':records,'errors':errors,'warnings':list(dict.fromkeys(warnings)),'audit':audit}
    except (OSError,ValidationError,UnicodeError) as e: return {'ok':False,'records':[],'errors':[str(e)],'warnings':warnings,'audit':{'rows_seen':0,'rows_loaded':0,'rows_rejected':0}}

def load_products(file_or_path):
    errors=[]; warnings=[]; records=[]
    try:
        fields,rows=_read(file_or_path); errors.extend(validate_csv_columns(fields, PRODUCTS_REQUIRED))
        if errors: return {'ok':False,'records':[],'errors':errors,'warnings':warnings,'audit':{'rows_seen':len(rows),'rows_loaded':0,'rows_rejected':len(rows)}}
        seen=set()
        for idx,r in enumerate(rows,start=2):
            row_errors=[]; pid=str(r.get('product_id','')).strip(); name=str(r.get('name','')).strip()
            if not pid: row_errors.append(f"Row {idx}: product_id is required.")
            elif pid in seen: row_errors.append(f"Row {idx}: duplicate product_id {pid!r}; row rejected.")
            if not name: row_errors.append(f"Row {idx}: name is required.")
            qtxt=str(r.get('quantity','')).strip(); rtxt=str(r.get('reorder_level','')).strip()
            if not re.fullmatch(r"\d+",qtxt): row_errors.append(f"Row {idx}: quantity must be a non-negative integer.")
            if not re.fullmatch(r"\d+",rtxt): row_errors.append(f"Row {idx}: reorder_level must be a non-negative integer.")
            try: cost=_decimal(r.get('unit_cost'),'unit_cost',idx,optional=True)
            except ValueError as e: row_errors.append(str(e)); cost=None
            try: price=_decimal(r.get('selling_price'),'selling_price',idx,optional=True)
            except ValueError as e: row_errors.append(str(e)); price=None
            if row_errors: errors.extend(row_errors); continue
            seen.add(pid); records.append({'product_id':pid,'name':name,'quantity':int(qtxt),'unit_cost':cost,'selling_price':price,'reorder_level':int(rtxt)})
        audit={'rows_seen':len(rows),'rows_loaded':len(records),'rows_rejected':len(rows)-len(records),'errors':len(errors),'warnings':len(warnings)}
        return {'ok':bool(records),'records':records,'errors':errors,'warnings':warnings,'audit':audit}
    except (OSError,ValidationError,UnicodeError) as e: return {'ok':False,'records':[],'errors':[str(e)],'warnings':warnings,'audit':{'rows_seen':0,'rows_loaded':0,'rows_rejected':0}}

def sample_data():
    from datetime import timedelta
    products=[{'product_id':'P001','name':'Notebook','quantity':12,'unit_cost':Decimal('80.00'),'selling_price':Decimal('110.00'),'reorder_level':5},{'product_id':'P002','name':'Blue Pen','quantity':4,'unit_cost':Decimal('15.00'),'selling_price':Decimal('25.00'),'reorder_level':8},{'product_id':'P003','name':'Sketchbook','quantity':0,'unit_cost':Decimal('140.00'),'selling_price':Decimal('200.00'),'reorder_level':3},{'product_id':'P004','name':'Gift Bag','quantity':30,'unit_cost':Decimal('20.00'),'selling_price':Decimal('40.00'),'reorder_level':10},{'product_id':'P005','name':'Marker Set','quantity':7,'unit_cost':Decimal('95.00'),'selling_price':Decimal('150.00'),'reorder_level':6}]
    sales=[]; base=date(2026,9,1)
    pattern=[('P001',2,Decimal('110.00'),Decimal('80.00')),('P002',5,Decimal('25.00'),Decimal('15.00')),('P004',3,Decimal('40.00'),Decimal('20.00')),('P003',1,Decimal('200.00'),Decimal('140.00')),('P001',4,Decimal('110.00'),Decimal('80.00')),('P005',2,Decimal('150.00'),Decimal('95.00'))]
    for i in range(36):
        pid,q,price,cost=pattern[i%len(pattern)]; d=base+timedelta(days=i*2)
        sales.append({'sale_id':f'S{i+1:03d}','date':d.isoformat(),'product_id':pid,'quantity_sold':q,'unit_price':price,'unit_cost':cost})
    return sales,products
