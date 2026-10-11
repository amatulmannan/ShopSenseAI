from io import BytesIO
from services.data_loader import load_sales, load_products

def test_load_sales_csv():
    content=b'sale_id,date,product_id,quantity_sold,unit_price,unit_cost\nS1,2026-01-01,P1,2,10.00,6.00\n'
    r=load_sales(BytesIO(content))
    assert r['ok'] and r['records'][0]['quantity_sold']==2

def test_duplicate_sale_ids_reported():
    content=b'sale_id,date,product_id,quantity_sold,unit_price,unit_cost\nS1,2026-01-01,P1,2,10.00,6.00\nS1,2026-01-02,P1,1,10.00,6.00\n'
    r=load_sales(BytesIO(content))
    assert r['ok'] and len(r['records']) == 1 and r['audit']['rows_rejected'] == 1 and any('duplicate' in e.lower() for e in r['errors'])

def test_missing_required_column():
    r=load_sales(BytesIO(b'sale_id,date,product_id\nS1,2026-01-01,P1\n'))
    assert not r['ok'] and any('missing required' in e.lower() for e in r['errors'])

def test_products_csv():
    r=load_products(BytesIO(b'product_id,name,quantity,reorder_level\nP1,Pen,3,5\n'))
    assert r['ok'] and r['records'][0]['quantity']==3

def test_duplicate_headers_and_malformed_csv_rejected():
    duplicate=load_sales(BytesIO(b'sale_id,date,product_id,quantity_sold,unit_price,unit_price\nS1,2026-01-01,P1,1,2,3\n'))
    assert not duplicate['ok'] and 'duplicate column' in duplicate['errors'][0].lower()
    malformed=load_sales(BytesIO(b'sale_id,date,product_id,quantity_sold,unit_price\nS1,"2026-01-01,P1,1,2\n'))
    assert not malformed['ok'] and malformed['errors']
