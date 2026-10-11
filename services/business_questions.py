from __future__ import annotations
from services.validation import validate_question, ValidationError
from services.analytics import sales_summary, inventory_summary
from security import authorize_tool, ALLOWED_TOOLS

SUGGESTED_QUESTIONS={
'English':['What were my total sales?','Which products sold the most?','Which products have low stock?','Which products are out of stock?','How many units were sold?','What was my gross profit?'],
'اردو':['میری کل فروخت کتنی تھی؟','سب سے زیادہ کون سی مصنوعات فروخت ہوئیں؟','کن مصنوعات کا اسٹاک کم ہے؟','کون سی مصنوعات کا اسٹاک ختم ہے؟','کتنے یونٹ فروخت ہوئے؟','مجموعی منافع کتنا تھا؟'],
'Roman Urdu':['Meri total sales kitni thin?','Sab se zyada kaun si products bikin?','Kin products ka stock kam hai?','Kin products ka stock khatam hai?','Kitne units sell huay?','Gross profit kitna tha?']}

def _intent(q):
    s=q.casefold()
    patterns={
    'revenue':['total sales','sales total','revenue','کل فروخت','فروخت کتنی','total sale','meri total sales','kul farokht','total bikri'],
    'top':['sold the most','best selling','top products','زیادہ کون سی','زیادہ فروخت','sab se zyada','zyada products','best seller'],
    'low_stock':['low stock','stock kam','اسٹاک کم','کم اسٹاک','kam stock'],
    'out_of_stock':['out of stock','stock khatam','اسٹاک ختم','ختم ہے','stock khatam'],
    'units':['units sold','how many units','کتنے یونٹ','units sell','kitne units','kitne unit'],
    'profit':['gross profit','profit','منافع','munafa','gross munafa']}
    for intent,terms in patterns.items():
        if any(term in s for term in terms): return intent
    return None

def answer_question(question, sales_records, products, language='English'):
    try: q=validate_question(question)
    except ValidationError as e: return {'answer':str(e),'tool_used':None,'evidence':[],'warnings':[]}
    intent=_intent(q)
    if not intent:
        messages={'English':'I cannot answer that reliably from the currently supported analytics. Try total revenue, units sold, gross profit, best-selling products, low stock, or out-of-stock products.','اردو':'موجودہ تجزیے سے اس سوال کا قابلِ اعتماد جواب نہیں دیا جا سکتا۔ کل آمدنی، فروخت شدہ یونٹس، مجموعی منافع یا اسٹاک کے بارے میں پوچھیں۔','Roman Urdu':'Maujooda analytics se is sawal ka bharosemand jawab nahi mil sakta. Total revenue, units sold, gross profit ya stock ke bare mein poochain.'}
        return {'answer':messages.get(language,messages['English']),'tool_used':None,'evidence':[],'warnings':['Unsupported question; no analytics were run.']}
    evidence=[]; warnings=[]
    tool_name='inventory_summary' if intent in ('low_stock','out_of_stock') else 'sales_summary'
    if not authorize_tool(tool_name, ALLOWED_TOOLS):
        return {'answer':'This analytics action is not allowed.','tool_used':None,'evidence':[],'warnings':['The requested tool is not on the server-side allowlist.']}
    if intent in ('low_stock','out_of_stock'):
        inv=inventory_summary(products); warnings.extend(inv['warnings'])
        if intent=='low_stock':
            items=[x for x in inv['items'] if x['quantity']>0 and x['quantity']<=x['reorder_level']]
            answer='Low-stock products: '+(', '.join(f"{x['name']} ({x['quantity']} left; reorder level {x['reorder_level']})" for x in items) if items else 'No low-stock products were found using the configured reorder levels.')
            evidence=[f"{x['name']}: quantity {x['quantity']} ≤ reorder level {x['reorder_level']}" for x in items]
        else:
            items=[x for x in inv['items'] if x['quantity']==0]
            answer='Out-of-stock products: '+(', '.join(x['name'] for x in items) if items else 'No out-of-stock products were found.')
            evidence=[f"{x['name']}: quantity 0" for x in items]
    else:
        s=sales_summary(sales_records); warnings.extend(s.get('warnings',[]))
        if intent=='revenue': answer=f"Total recorded revenue is {s['revenue_text']}. Currency is not confirmed, so no currency symbol is shown."; evidence=[f"Sales records: {s['transaction_count']}",f"Included dates: {s['start_date']} to {s['end_date']}",f"Revenue = sum(quantity_sold × unit_price) = {s['revenue_text']}"]
        elif intent=='top':
            top=s['top_products'][:5]; answer='Top products by units sold: '+(', '.join(f"{x['product_id']} ({x['units_sold']} units)" for x in top) if top else 'No valid sales records are available.'); evidence=[f"{x['product_id']}: {x['units_sold']} units; revenue {x['revenue']}" for x in top]
        elif intent=='units': answer=f"A total of {s['units_sold']:,} units were recorded as sold."; evidence=[f"Summed quantity_sold across {s['transaction_count']} sales records."]
        else:
            if s['gross_profit'] is None: answer='Gross profit cannot be calculated completely because one or more included sales records are missing a valid unit_cost.'; warnings.append('Missing unit_cost prevents a complete gross profit calculation.')
            else: answer=f"Gross profit is {s['gross_profit_text']} before operating expenses. This is not net profit."; evidence=[f"Revenue {s['revenue_text']} minus COGS {s['cogs_text']} = gross profit {s['gross_profit_text']}.",f"Gross margin: {s['gross_margin_text']}"]
    return {'answer':answer,'tool_used':intent,'evidence':evidence,'warnings':list(dict.fromkeys(warnings))}
