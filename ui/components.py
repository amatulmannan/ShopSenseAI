from __future__ import annotations
import html
import streamlit as st

def metric_card(col,label,value,caption,icon=''):
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-top'><span>{html.escape(str(label))}</span><span class='metric-icon'>{html.escape(str(icon))}</span></div><div class='metric-value'>{html.escape(str(value))}</div><div class='metric-caption'>{html.escape(str(caption))}</div></div>",unsafe_allow_html=True)

def show_messages(messages,kind='warning'):
    for msg in messages:
        if kind=='error': st.error(str(msg))
        elif kind=='warning': st.warning(str(msg))
        else: st.info(str(msg))

def html_table(records, columns=None, max_rows=100):
    """Escaped HTML table: avoids Streamlit's Arrow-backed dataframe renderer."""
    if records is None or len(records)==0:
        st.caption('No rows to display.')
        return
    rows=[dict(r) for r in records[:max_rows]]
    cols=columns or list(rows[0].keys())
    head=''.join(f'<th>{html.escape(str(c))}</th>' for c in cols)
    body=[]
    for row in rows:
        body.append('<tr>'+''.join(f'<td>{html.escape(str(row.get(c,"")))}</td>' for c in cols)+'</tr>')
    st.markdown("<div class='table-wrap'><table class='ss-table'><thead><tr>"+head+"</tr></thead><tbody>"+''.join(body)+"</tbody></table></div>",unsafe_allow_html=True)
    if len(records)>max_rows: st.caption(f"Showing {max_rows} of {len(records)} rows.")
