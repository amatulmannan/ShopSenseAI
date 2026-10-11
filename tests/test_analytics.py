from decimal import Decimal
from services.analytics import sales_summary, inventory_summary, get_reorder_candidates

def test_sales_math_exact():
    rows=[{'sale_id':'S1','date':'2026-01-01','product_id':'P1','quantity_sold':2,'unit_price':Decimal('10.00'),'unit_cost':Decimal('6.00')},{'sale_id':'S2','date':'2026-01-02','product_id':'P2','quantity_sold':1,'unit_price':Decimal('5.00'),'unit_cost':Decimal('2.00')}]
    s=sales_summary(rows)
    assert s['revenue']==Decimal('25.00')
    assert s['cost_of_goods_sold']==Decimal('14.00')
    assert s['gross_profit']==Decimal('11.00')
    assert s['units_sold']==3

def test_missing_cost_disables_complete_profit():
    rows=[{'sale_id':'S1','date':'2026-01-01','product_id':'P1','quantity_sold':1,'unit_price':Decimal('10.00'),'unit_cost':None}]
    s=sales_summary(rows)
    assert s['gross_profit'] is None
    assert s['warnings']

def test_date_filter_inclusive():
    rows=[{'date':'2026-01-01','quantity_sold':1,'unit_price':Decimal('2'),'unit_cost':Decimal('1'),'product_id':'P1'},{'date':'2026-01-02','quantity_sold':1,'unit_price':Decimal('3'),'unit_cost':Decimal('1'),'product_id':'P1'}]
    assert sales_summary(rows,'2026-01-02','2026-01-02')['revenue']==Decimal('3')

def test_inventory_flags():
    result=inventory_summary([{'product_id':'P1','name':'A','quantity':0,'reorder_level':2},{'product_id':'P2','name':'B','quantity':2,'reorder_level':2}])
    assert result['out_of_stock_count']==1 and result['low_stock_count']==1

def test_reorder_alert_does_not_forecast():
    rows=[{'product_id':'P1','name':'A','quantity':1,'reorder_level':2}]
    assert get_reorder_candidates(rows)[0]['basis']=='reorder_level'
