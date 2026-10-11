from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from datetime import date
from typing import Any

def D(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))
def money(value: Any) -> str:
    return f"{D(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"

def sales_summary(records, start_date=None, end_date=None):
    warnings=[]; valid=[]
    try: start = date.fromisoformat(str(start_date)) if start_date else None
    except ValueError: return {"ok":False,"error":"Invalid start date; use YYYY-MM-DD.","warnings":[]}
    try: end = date.fromisoformat(str(end_date)) if end_date else None
    except ValueError: return {"ok":False,"error":"Invalid end date; use YYYY-MM-DD.","warnings":[]}
    if start and end and start > end: return {"ok":False,"error":"Start date must not be after end date.","warnings":[]}
    seen_before_filter=set()
    for r in records:
        try:
            sale_id=str(r.get('sale_id',''))
            if sale_id and sale_id in seen_before_filter:
                warnings.append("Duplicate sale_id found in in-memory records; duplicate row excluded.")
                continue
            d=date.fromisoformat(str(r['date']))
            if start and d < start: continue
            if end and d > end: continue
            q=int(r['quantity_sold']); price=D(r['unit_price'])
            if q <= 0 or price < 0: raise ValueError("invalid quantity or price")
            valid.append((r,d,q,price))
            if sale_id: seen_before_filter.add(sale_id)
        except (ValueError, TypeError, KeyError, ArithmeticError): warnings.append("A malformed sale record was excluded from analytics.")
    revenue=Decimal('0'); cogs=Decimal('0'); cogs_complete=bool(valid); units=0
    product_units=defaultdict(int); product_revenue=defaultdict(Decimal); daily=defaultdict(Decimal); seen_sale_ids=set()
    for r,d,q,price in valid:
        sale_id=str(r.get('sale_id',''))
        if sale_id: seen_sale_ids.add(sale_id)
        line_revenue=q*price; revenue+=line_revenue; units+=q
        pid=str(r.get('product_id','Unknown')); product_units[pid]+=q; product_revenue[pid]+=line_revenue; daily[d]+=line_revenue
        cost=r.get('unit_cost')
        if cost is None or str(cost).strip()=="": cogs_complete=False
        else:
            try:
                unit_cost=D(cost)
                if unit_cost < 0: cogs_complete=False
                else: cogs += q*unit_cost
            except Exception: cogs_complete=False
    if not cogs_complete: warnings.append("COGS, gross profit, and gross margin are unavailable because at least one included sale lacks a valid unit_cost.")
    products=[{'product_id':pid,'units_sold':u,'revenue':money(product_revenue[pid])} for pid,u in sorted(product_units.items(),key=lambda x:(-x[1],x[0])) if u > 0]
    product_performance=[{'product_id':pid,'units_sold':u,'revenue':money(product_revenue[pid]),'revenue_value':product_revenue[pid]} for pid,u in sorted(product_units.items(),key=lambda x:(-product_revenue[x[0]],x[0])) if u > 0]
    gross_profit=revenue-cogs if cogs_complete else None
    margin=(gross_profit/revenue*Decimal('100')) if cogs_complete and revenue > 0 else (Decimal('0') if cogs_complete and revenue == 0 else None)
    dates=[d for _,d,_,_ in valid]
    return {'ok':True,'revenue':revenue,'revenue_text':money(revenue),'cost_of_goods_sold':cogs if cogs_complete else None,'cogs_text':money(cogs) if cogs_complete else 'Unavailable','gross_profit':gross_profit,'gross_profit_text':money(gross_profit) if gross_profit is not None else 'Unavailable','gross_margin':margin,'gross_margin_text':f"{margin.quantize(Decimal('0.01'))}%" if margin is not None else 'Unavailable','units_sold':units,'transaction_count':len(seen_sale_ids) if seen_sale_ids else len(valid),'average_transaction_value':(revenue/len(valid) if valid else Decimal('0')),'average_transaction_value_text':money(revenue/len(valid) if valid else 0),'top_products':products,'product_performance':product_performance,'daily_trend':[{'date':d.isoformat(),'revenue':money(v),'revenue_value':v} for d,v in sorted(daily.items())],'warnings':list(dict.fromkeys(warnings)),'start_date':min(dates).isoformat() if dates else None,'end_date':max(dates).isoformat() if dates else None,'rows_in_period':len(valid),'currency_confirmed':False}

def inventory_summary(products):
    items=[]; low=out=0; seen=set(); warnings=[]
    for p in products:
        pid=str(p.get('product_id',''))
        if pid in seen:
            warnings.append(f"Duplicate product_id {pid!r}; first inventory record used."); continue
        seen.add(pid)
        try: q=int(p['quantity']); threshold=int(p.get('reorder_level',0))
        except (ValueError,TypeError,KeyError): warnings.append(f"Invalid stock values for product {pid!r}; record excluded."); continue
        if q < 0 or threshold < 0: warnings.append(f"Negative stock/reorder values for product {pid!r}; record excluded."); continue
        status='Out of stock' if q==0 else ('Low stock' if q<=threshold else 'In stock')
        if q==0: out+=1
        elif q<=threshold: low+=1
        items.append({'product_id':pid,'name':str(p.get('name','')),'quantity':q,'reorder_level':threshold,'status':status,'unit_cost':money(p['unit_cost']) if p.get('unit_cost') is not None else 'Unavailable','selling_price':money(p['selling_price']) if p.get('selling_price') is not None else 'Unavailable'})
    return {'items':items,'total_products':len(items),'low_stock_count':low,'out_of_stock_count':out,'warnings':warnings}

def data_quality_report(sales_records, products, sales_audit=None, products_audit=None):
    def missing(records, keys):
        return {k:sum(1 for r in records if r.get(k) is None or str(r.get(k)).strip()=="") for k in keys}
    sales_keys=('sale_id','date','product_id','quantity_sold','unit_price','unit_cost')
    product_keys=('product_id','name','quantity','reorder_level','unit_cost','selling_price')
    def duplicate_rows(records):
        seen=set(); count=0
        for row in records:
            key=tuple((k,str(v)) for k,v in sorted(row.items()))
            if key in seen: count+=1
            seen.add(key)
        return count
    return {'sales_rows_loaded':len(sales_records),'product_rows_loaded':len(products),'sales_missing_values':missing(sales_records,sales_keys),'products_missing_values':missing(products,product_keys),'duplicate_sales_rows':duplicate_rows(sales_records),'duplicate_product_rows':duplicate_rows(products),'sales_audit':sales_audit or {},'products_audit':products_audit or {}}

def get_reorder_candidates(products, average_daily_sales=None, lead_time_days=7, safety_days=3):
    return [{'product_id':p['product_id'],'name':p['name'],'quantity':int(p['quantity']),'reorder_level':int(p.get('reorder_level',0)),'reason':'Out of stock' if int(p['quantity'])==0 else 'At or below configured reorder level','basis':'reorder_level'} for p in products if int(p['quantity'])<=int(p.get('reorder_level',0))]
