"""Conservative validation and explicit server-side tool authorization."""
from services.validation import validate_question, validate_records, ValidationError
ALLOWED_TOOLS={'sales_summary','inventory_summary','get_reorder_candidates'}

def authorize_tool(tool_name, permissions):
    return bool(isinstance(tool_name,str) and tool_name in ALLOWED_TOOLS and isinstance(permissions,(set,list,tuple)) and tool_name in permissions)
