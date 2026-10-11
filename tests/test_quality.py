from decimal import Decimal
from services.analytics import data_quality_report, sales_summary, inventory_summary
from services.data_loader import load_sales
from io import BytesIO

def test_partial_sales_load_audits_rejected_rows():
    raw=b'sale_id,date,product_id,quantity_sold,unit_price,unit_cost\nS1,2026-01-01,P1,2,10,6\nS1,2026-01-02,P1,1,10,6\nS3,bad,P2,1,2,1\n'
    result=load_sales(BytesIO(raw))
    assert result['ok'] and len(result['records'])==1
    assert result['audit']['rows_seen']==3 and result['audit']['rows_rejected']==2
    assert len(result['errors'])>=2

def test_gross_margin_and_daily_trend():
    rows=[{'sale_id':'1','date':'2026-01-01','product_id':'P','quantity_sold':2,'unit_price':Decimal('10'),'unit_cost':Decimal('4')}]
    result=sales_summary(rows)
    assert result['gross_margin_text']=='60.00%'
    assert result['daily_trend'][0]['date']=='2026-01-01'

def test_invalid_date_filter_is_reported_not_ignored():
    assert sales_summary([], '2026-02-31')['ok'] is False

def test_quality_counts_missing_values_and_exact_duplicates():
    row={'sale_id':'1','date':'2026-01-01','product_id':'P','quantity_sold':1,'unit_price':Decimal('2'),'unit_cost':None}
    q=data_quality_report([row,row],[])
    assert q['duplicate_sales_rows']==1
    assert q['sales_missing_values']['unit_cost']==2

def test_negative_stock_excluded_with_warning():
    inv=inventory_summary([{'product_id':'P','name':'Pen','quantity':-1,'reorder_level':2}])
    assert inv['total_products']==0 and inv['warnings']
