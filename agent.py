"""Compatibility wrapper for the shared Member 1 contract; deterministic by default."""
from services.business_questions import answer_question as _answer

def answer_question(question, context):
    sales=context.get('sales_records',context.get('sales',[]))
    products=context.get('products',[])
    lang=context.get('language','English')
    return _answer(question,sales,products,lang)
