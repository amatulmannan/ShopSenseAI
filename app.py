from __future__ import annotations
import io, html
from decimal import Decimal
import pandas as pd
import plotly.express as px
import streamlit as st
from config import APP_NAME, MAX_UPLOAD_MB, MAX_ROWS, LLM_MODEL
from services.data_loader import load_sales, load_products, sample_data
from services.validation import validate_upload
from services.analytics import sales_summary, inventory_summary, data_quality_report
from services.business_questions import answer_question, SUGGESTED_QUESTIONS
from llm_provider import provider_status, test_connection, explain_with_llm, ProviderError
from i18n import t, LANGUAGES
from ui.styles import apply_styles
from ui.components import metric_card, show_messages, html_table

st.set_page_config(page_title=APP_NAME, page_icon="S", layout="wide", initial_sidebar_state="expanded")
if "language" not in st.session_state: st.session_state.language = "English"
if "data_mode" not in st.session_state: st.session_state.data_mode = "demo"
if "sales_records" not in st.session_state or "products" not in st.session_state:
    _s, _p = sample_data(); st.session_state.sales_records = _s; st.session_state.products = _p
if "sales_audit" not in st.session_state: st.session_state.sales_audit = {"rows_seen":len(st.session_state.sales_records),"rows_loaded":len(st.session_state.sales_records),"rows_rejected":0}
if "products_audit" not in st.session_state: st.session_state.products_audit = {"rows_seen":len(st.session_state.products),"rows_loaded":len(st.session_state.products),"rows_rejected":0}
if "question_history" not in st.session_state: st.session_state.question_history = []
if "provider_test" not in st.session_state: st.session_state.provider_test = None
lang = st.sidebar.selectbox("Language / زبان", list(LANGUAGES), index=list(LANGUAGES).index(st.session_state.language), key="language_picker")
st.session_state.language = lang
apply_styles(lang)
st.sidebar.markdown("<div class='brand-lockup'><div class='brand-mark'>S</div><div><div class='brand-name'>ShopSense <span>AI</span></div><div class='brand-sub'>LOCAL-FIRST BUSINESS ANALYTICS</div></div></div>", unsafe_allow_html=True)
st.sidebar.caption(t(lang,"tagline"))
page_keys=["dashboard","upload","ask","sales","inventory","quality","settings"]
page_labels=[t(lang,k) for k in page_keys]
page = st.sidebar.radio(t(lang,"navigation"), page_labels, label_visibility="collapsed")
active=page_keys[page_labels.index(page)]
sales=st.session_state.sales_records; products=st.session_state.products
source_text=t(lang,"source_demo") if st.session_state.data_mode=="demo" else t(lang,"source_upload")
st.sidebar.markdown(f"**{t(lang,'source_label')}**")
st.sidebar.caption(source_text)
if st.sidebar.button(t(lang,"reset_session"), use_container_width=True):
    _s,_p=sample_data(); st.session_state.sales_records=_s; st.session_state.products=_p; st.session_state.data_mode="demo"
    st.session_state.sales_audit={"rows_seen":len(_s),"rows_loaded":len(_s),"rows_rejected":0}; st.session_state.products_audit={"rows_seen":len(_p),"rows_loaded":len(_p),"rows_rejected":0}
    st.session_state.question_history=[]; st.session_state.pop('latest_answer',None); st.rerun()

# Reporting period applies to dashboards and Sales Insights; no data is modified.
with st.sidebar.expander(t(lang,"date_filter"), expanded=False):
    start_date=st.date_input(t(lang,"start_date"), value=None, key="report_start")
    end_date=st.date_input(t(lang,"end_date"), value=None, key="report_end")
    if start_date and end_date and start_date > end_date: st.warning("Start date must not be after end date.")
period_start=start_date.isoformat() if start_date else None
period_end=end_date.isoformat() if end_date else None
summary=sales_summary(sales,period_start,period_end)
inv=inventory_summary(products)
page_title=t(lang,active)
st.markdown(f"<div class='topline'><div><div class='eyebrow'>{html.escape(t(lang,'workspace'))}</div><h1>{html.escape(page_title)}</h1><p class='subhead'>{html.escape(t(lang,active+'_subtitle'))}</p></div><div class='status-pill'><span class='status-dot'></span>{html.escape(source_text)}</div></div>",unsafe_allow_html=True)
if st.session_state.data_mode=="demo": st.info(t(lang,"demo_notice"))
if not sales and not products and active not in ("upload","settings"):
    st.warning(t(lang,"no_source"))

if active=="dashboard":
    st.markdown(f"<div class='welcome-panel'><div><div class='eyebrow'>{html.escape(t(lang,'welcome_eyebrow'))}</div><h2>{html.escape(t(lang,'welcome_title'))}</h2><p>{html.escape(t(lang,'welcome_body'))}</p></div><div class='welcome-icon'>↗</div></div>",unsafe_allow_html=True)
    cols=st.columns(4)
    metric_card(cols[0],t(lang,"revenue"),summary.get("revenue_text","Unavailable"),t(lang,"selected_data"),"↗")
    metric_card(cols[1],t(lang,"gross_profit"),summary.get("gross_profit_text","Unavailable"),t(lang,"not_net_profit"),"◈")
    metric_card(cols[2],t(lang,"units_sold"),f"{summary.get('units_sold',0):,}",t(lang,"valid_sales_rows",n=summary.get('transaction_count',0)),"▤")
    metric_card(cols[3],t(lang,"stock_alerts"),str(inv["low_stock_count"]+inv["out_of_stock_count"]),t(lang,"items_need_attention"),"⚑")
    if summary.get("error"): st.error(summary["error"])
    left,right=st.columns([1.5,1])
    with left:
        st.markdown(f"<div class='section-heading'><h3>{html.escape(t(lang,'sales_trend'))}</h3><span>{html.escape(t(lang,'sales_trend_detail'))}</span></div>",unsafe_allow_html=True)
        trend=summary.get("daily_trend",[])
        if trend:
            fig=px.line(pd.DataFrame([{'Date':x['date'],'Revenue':float(x['revenue_value'])} for x in trend]),x='Date',y='Revenue',markers=True)
            fig.update_layout(paper_bgcolor='#E8ECF1',plot_bgcolor='#E8ECF1',font_color='#303746',margin=dict(l=10,r=10,t=20,b=10),height=300)
            fig.update_traces(line_color='#E84D55',marker_color='#E84D55')
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
        else: st.info(t(lang,"no_sales"))
    with right:
        st.markdown(f"<div class='section-heading'><h3>{html.escape(t(lang,'top_products'))}</h3><span>{html.escape(t(lang,'by_units'))}</span></div>",unsafe_allow_html=True)
        html_table(summary.get("top_products",[])[:5], columns=['product_id','units_sold','revenue'])
    st.markdown(f"<div class='section-heading'><h3>{html.escape(t(lang,'quick_actions'))}</h3></div>",unsafe_allow_html=True)
    qcols=st.columns(3)
    for col,key in zip(qcols,["q_revenue","q_top","q_stock"]):
        with col: st.markdown(f"<div class='soft-tile'><div class='tile-icon'>⌕</div><div class='tile-title'>{html.escape(t(lang,key))}</div><div class='tile-copy'>{html.escape(t(lang,'quick_action_copy'))}</div></div>",unsafe_allow_html=True)
    if summary.get('warnings'): show_messages(summary['warnings'])
elif active=="upload":
    st.markdown(f"<div class='soft-panel'><h3>{html.escape(t(lang,'upload_sales'))}</h3><p>{html.escape(t(lang,'sales_schema'))}</p><p>Required: sale_id, date (YYYY-MM-DD), product_id, quantity_sold (positive integer), unit_price (non-negative). Optional: unit_cost. Maximum {MAX_UPLOAD_MB} MB and {MAX_ROWS:,} rows.</p></div>",unsafe_allow_html=True)
    sf=st.file_uploader(t(lang,"sales_csv"),type=["csv"],key="sales_file",help=f"CSV only; maximum {MAX_UPLOAD_MB} MB.")
    if sf is not None:
        st.caption(f"{sf.name} · {sf.size:,} bytes")
        st.markdown(f"**{t(lang,'preview_sales')}**")
        try: st.code(sf.getvalue()[:2500].decode('utf-8-sig',errors='replace'),language='csv')
        except Exception: pass
    st.markdown(f"<div class='soft-panel'><h3>{html.escape(t(lang,'upload_products'))}</h3><p>{html.escape(t(lang,'products_schema'))}</p><p>Required: product_id, name, quantity (non-negative integer), reorder_level. Optional: unit_cost, selling_price.</p></div>",unsafe_allow_html=True)
    pf=st.file_uploader(t(lang,"products_csv"),type=["csv"],key="products_file",help=f"CSV only; maximum {MAX_UPLOAD_MB} MB.")
    if pf is not None:
        st.caption(f"{pf.name} · {pf.size:,} bytes")
        st.markdown(f"**{t(lang,'preview_products')}**")
        st.code(pf.getvalue()[:2500].decode('utf-8-sig',errors='replace'),language='csv')
    if st.button(t(lang,"validate_load"),type="primary"):
        if sf is None and pf is None: st.warning(t(lang,"choose_file"))
        else:
            errs=[]; warnings=[]; ns=[]; np=[]; sa={"rows_seen":0,"rows_loaded":0,"rows_rejected":0}; pa={"rows_seen":0,"rows_loaded":0,"rows_rejected":0}
            if sf is not None:
                ok,msg=validate_upload(sf.name,sf.size,sf.getvalue(),MAX_UPLOAD_MB)
                if not ok: errs.extend(msg)
                else:
                    result=load_sales(io.BytesIO(sf.getvalue())); errs.extend(result['errors']); warnings.extend(result['warnings']); sa=result.get('audit',{})
                    if result['ok']: ns=result['records']
            if pf is not None:
                ok,msg=validate_upload(pf.name,pf.size,pf.getvalue(),MAX_UPLOAD_MB)
                if not ok: errs.extend(msg)
                else:
                    result=load_products(io.BytesIO(pf.getvalue())); errs.extend(result['errors']); warnings.extend(result['warnings']); pa=result.get('audit',{})
                    if result['ok']: np=result['records']
            valid_selected=(sf is None or bool(ns)) and (pf is None or bool(np))
            if not valid_selected or not (ns or np): show_messages(errs or ['No valid rows were found.'],kind='error')
            else:
                st.session_state.sales_records=ns; st.session_state.products=np; st.session_state.data_mode='uploaded'
                st.session_state.sales_audit=sa; st.session_state.products_audit=pa; st.session_state.question_history=[]; st.session_state.pop('latest_answer',None)
                if errs: st.session_state.last_upload_errors=errs
                if warnings: st.session_state.last_upload_warnings=warnings
                st.success(t(lang,"upload_success"))
                if errs: st.warning(t(lang,"upload_partial")); show_messages(errs,kind='warning')
                if warnings: show_messages(warnings,kind='warning')
                st.rerun()
    c1,c2=st.columns(2)
    with c1: st.download_button(t(lang,"download_sales_sample"),pd.DataFrame(sample_data()[0]).assign(**{}).to_csv(index=False).encode('utf-8'),"sample_sales.csv","text/csv")
    with c2: st.download_button(t(lang,"download_products_sample"),pd.DataFrame(sample_data()[1]).to_csv(index=False).encode('utf-8'),"sample_products.csv","text/csv")
    st.caption(t(lang,"rejected_rows_notice"))
    if st.session_state.get('last_upload_errors'): show_messages(st.session_state.last_upload_errors,kind='warning')
    if st.session_state.get('last_upload_warnings'): show_messages(st.session_state.last_upload_warnings,kind='warning')
elif active=="ask":
    st.markdown(f"<div class='soft-panel'><h3>{html.escape(t(lang,'ask_heading'))}</h3><p>{html.escape(t(lang,'ask_body'))}</p></div>",unsafe_allow_html=True)
    questions=SUGGESTED_QUESTIONS.get(lang,SUGGESTED_QUESTIONS['English'])
    choice=st.selectbox(t(lang,"suggested_questions"),[t(lang,"choose_suggestion")]+questions)
    question=st.text_area(t(lang,"your_question"),value=choice if choice!=t(lang,"choose_suggestion") else "",height=100,placeholder=t(lang,"question_placeholder"),key="business_question")
    ai_consent=st.checkbox(t(lang,"ask_ai_optin"),value=False)
    if st.button(t(lang,"get_answer"),type="primary"):
        result=answer_question(question,sales,products,lang)
        st.session_state.latest_answer={'question':question,'result':result,'ai':None}
        if result.get('tool_used') and ai_consent:
            evidence={'tool':result['tool_used'],'answer':result['answer'],'evidence':result.get('evidence',[]),'warnings':result.get('warnings',[]),'period':{'start':summary.get('start_date'),'end':summary.get('end_date')},'currency_confirmed':False}
            try: st.session_state.latest_answer['ai']=explain_with_llm(question,evidence)
            except ProviderError as e: st.session_state.latest_answer['ai_error']=str(e)
        elif result.get('tool_used') and not ai_consent:
            st.session_state.latest_answer['ai_note']=t(lang,'ai_consent_required')
    if st.session_state.get('latest_answer'):
        item=st.session_state.latest_answer
        with st.container(border=True):
            st.markdown(f"**{html.escape(item['question'])}**")
            st.write(item['result']['answer'])
            st.caption(t(lang,'answer_source')+': '+t(lang,'deterministic'))
            if item['result'].get('evidence'): st.caption(t(lang,'evidence')+': '+' · '.join(item['result']['evidence']))
            if item['result'].get('warnings'): show_messages(item['result']['warnings'],kind='warning')
            if item.get('ai'): st.markdown('**'+t(lang,'ai_explanation')+'**'); st.write(item['ai']); st.caption(t(lang,'answer_source')+': '+t(lang,'llm'))
            if item.get('ai_error'): st.warning(item['ai_error'])
            if item.get('ai_note'): st.caption(item['ai_note'])
elif active=="sales":
    st.markdown(f"<div class='soft-panel'><h3>{html.escape(t(lang,'sales_overview'))}</h3><p>{html.escape(t(lang,'sales_overview_body'))}</p></div>",unsafe_allow_html=True)
    c=st.columns(4)
    for col,label,val in zip(c,[t(lang,"revenue"),t(lang,"cogs"),t(lang,"gross_profit"),t(lang,"units_sold")],[summary.get("revenue_text","Unavailable"),summary.get("cogs_text","Unavailable"),summary.get("gross_profit_text","Unavailable"),f"{summary.get('units_sold',0):,}"]): metric_card(col,label,val,t(lang,"calculated_from_valid_rows"),"◈")
    c=st.columns(3)
    metric_card(c[0],t(lang,'gross_margin'),summary.get('gross_margin_text','Unavailable'),t(lang,'not_net_profit'),'％')
    metric_card(c[1],t(lang,'avg_transaction'),summary.get('average_transaction_value_text','Unavailable'),t(lang,'transactions'),'↔')
    metric_card(c[2],t(lang,'transactions'),summary.get('transaction_count',0),t(lang,'data_coverage'),'▤')
    st.caption(t(lang,"profit_disclaimer")); st.caption(t(lang,"currency_notice"))
    st.markdown(f"### {t(lang,'product_performance')}")
    html_table(summary.get('product_performance',[]),columns=['product_id','units_sold','revenue'])
    if summary.get("warnings"): show_messages(summary["warnings"],kind="warning")
elif active=="inventory":
    st.markdown(f"<div class='soft-panel'><h3>{html.escape(t(lang,'inventory_status'))}</h3><p>{html.escape(t(lang,'inventory_body'))}</p></div>",unsafe_allow_html=True)
    c=st.columns(3)
    metric_card(c[0],t(lang,"total_products"),str(inv["total_products"]),t(lang,"loaded_products"),"▦")
    metric_card(c[1],t(lang,"low_stock"),str(inv["low_stock_count"]),t(lang,"at_or_below_reorder"),"⚑")
    metric_card(c[2],t(lang,"out_of_stock"),str(inv["out_of_stock_count"]),t(lang,"quantity_zero"),"○")
    html_table(inv['items'],columns=['product_id','name','quantity','reorder_level','status','unit_cost','selling_price'])
    if inv.get('warnings'): show_messages(inv['warnings'])
    st.caption(t(lang,"reorder_note"))
elif active=="quality":
    st.markdown(f"<div class='soft-panel'><h3>{html.escape(t(lang,'quality_heading'))}</h3><p>{html.escape(t(lang,'quality_body'))}</p></div>",unsafe_allow_html=True)
    st.write(f"**{t(lang,'data_source')}:** {source_text}")
    quality=data_quality_report(sales,products,st.session_state.sales_audit,st.session_state.products_audit)
    qcols=st.columns(4)
    metric_card(qcols[0],t(lang,'sales_rows'),quality['sales_rows_loaded'],t(lang,'rows_loaded'),'▤')
    metric_card(qcols[1],t(lang,'product_rows'),quality['product_rows_loaded'],t(lang,'rows_loaded'),'▦')
    metric_card(qcols[2],t(lang,'rows_rejected'),quality['sales_audit'].get('rows_rejected',0)+quality['products_audit'].get('rows_rejected',0),t(lang,'quality_audit'),'!')
    metric_card(qcols[3],t(lang,'duplicate_rows'),quality['duplicate_sales_rows']+quality['duplicate_product_rows'],t(lang,'quality_audit'),'↻')
    st.markdown(f"### {t(lang,'quality_audit')}")
    audit_rows=[]
    for name,audit in [('Sales',quality['sales_audit']),('Products / inventory',quality['products_audit'])]:
        audit_rows.append({'dataset':name,'rows_seen':audit.get('rows_seen',0),'rows_loaded':audit.get('rows_loaded',0),'rows_rejected':audit.get('rows_rejected',0)})
    html_table(audit_rows)
    st.markdown(f"### {t(lang,'missing_values')}")
    miss=[{'dataset':'Sales','column':k,'missing':v} for k,v in quality['sales_missing_values'].items()]+[{'dataset':'Products','column':k,'missing':v} for k,v in quality['products_missing_values'].items()]
    html_table(miss)
    if st.session_state.get('last_upload_errors'): st.markdown(f"### {t(lang,'quality_warnings')}"); show_messages(st.session_state.last_upload_errors,kind='warning')
    st.markdown(f"### {t(lang,'methodology')}")
    st.write(t(lang,'methodology_text')); st.caption(t(lang,'currency_notice'))
    st.markdown(f"### {t(lang,'schemas')}")
    st.code("Sales: sale_id, date (YYYY-MM-DD), product_id, quantity_sold, unit_price, unit_cost (optional)\nProducts: product_id, name, quantity, reorder_level, unit_cost (optional), selling_price (optional)")
else:
    st.markdown(f"<div class='soft-panel'><h3>{html.escape(t(lang,'settings_heading'))}</h3><p>{html.escape(t(lang,'settings_body'))}</p></div>",unsafe_allow_html=True)
    status=provider_status(); checked=st.session_state.provider_test
    st.markdown(f"### {t(lang,'llm_mode')}")
    st.write(f"**{t(lang,'settings_model')}:** {status.model or 'Not configured'}")
    if status.state=='missing': st.warning(status.message)
    elif checked and checked.state=='connected': st.success(checked.message)
    elif checked and checked.state=='error': st.error(checked.message)
    else: st.info(status.message)
    if st.button(t(lang,'test_connection'),type='primary'):
        with st.spinner('Checking provider configuration and model access…'):
            st.session_state.provider_test=test_connection()
        st.rerun()
    st.caption(t(lang,'api_setup'))
    st.markdown(f"### {t(lang,'privacy_heading')}")
    st.write(t(lang,'data_privacy')); st.write(t(lang,'privacy_note'))
    st.caption('The connection test checks API/model access only. It does not send uploaded sales or inventory data.')

st.markdown("<div class='footer'>ShopSense AI · Local-first analytics · Numbers come from deterministic calculations</div>",unsafe_allow_html=True)
