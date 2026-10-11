import streamlit as st

def apply_styles(language='English'):
    direction = 'rtl' if language == 'اردو' else 'ltr'
    align = 'right' if language == 'اردو' else 'left'
    st.markdown(f"""
    <style>
    :root {{ --bg:#E8ECF1; --surface:#E8ECF1; --ink:#303746; --muted:#687386; --accent:#E84D55; --good:#18794E; --warn:#8A5A00; --bad:#B42318; }}
    .stApp {{ background:var(--bg); color:var(--ink); direction:{direction}; }}
    [data-testid="stSidebar"] {{ background:var(--bg); border-right:1px solid #d7dce3; }}
    [data-testid="stSidebar"] > div {{ padding-top:1.2rem; }}
    .brand-lockup {{ display:flex; align-items:center; gap:12px; padding:12px 8px; }}
    .brand-mark {{ width:42px;height:42px;display:grid;place-items:center;border-radius:13px;background:var(--bg);box-shadow:4px 4px 9px #c7ccd3,-4px -4px 9px #fff;color:var(--accent);font-size:22px;font-weight:800; }}
    .brand-name {{font-size:19px;font-weight:800;letter-spacing:-.5px;color:var(--ink)}} .brand-name span {{color:var(--accent)}}
    .brand-sub {{font-size:9px;letter-spacing:1.5px;color:var(--muted);margin-top:2px}}
    h1,h2,h3 {{color:var(--ink)!important;letter-spacing:-.35px}} p, label, [data-testid="stCaptionContainer"] {{color:var(--muted)}}
    .topline {{display:flex;justify-content:space-between;align-items:center;gap:18px;margin:8px 0 24px}}
    .eyebrow {{font-size:10px;letter-spacing:1.7px;text-transform:uppercase;color:var(--accent);font-weight:800}}
    .subhead {{margin-top:-10px;color:var(--muted);font-size:14px}}
    .status-pill {{border-radius:30px;padding:9px 13px;background:var(--bg);box-shadow:inset 2px 2px 5px #c7ccd3,inset -2px -2px 5px #fff;font-size:12px;color:var(--muted);white-space:nowrap}}
    .status-dot {{display:inline-block;width:7px;height:7px;border-radius:50%;background:#26956b;margin-right:7px}}
    .welcome-panel,.soft-panel {{background:var(--surface);border-radius:20px;padding:22px 24px;margin:8px 0 22px;box-shadow:6px 6px 14px #c7ccd3,-6px -6px 14px #fff;border:1px solid rgba(255,255,255,.55)}}
    .welcome-panel {{display:flex;justify-content:space-between;align-items:center;gap:20px;min-height:150px}} .welcome-panel h2 {{margin:.35rem 0;font-size:27px}} .welcome-panel p {{max-width:680px;margin-bottom:0;line-height:1.6}}
    .welcome-icon {{font-size:32px;color:var(--accent);border-radius:18px;padding:15px 19px;box-shadow:inset 3px 3px 7px #c7ccd3,inset -3px -3px 7px #fff}}
    .metric-card {{min-height:130px;padding:17px 18px;border-radius:18px;background:var(--surface);box-shadow:5px 5px 12px #c7ccd3,-5px -5px 12px #fff;border:1px solid rgba(255,255,255,.45);margin-bottom:12px}}
    .metric-top {{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px;font-weight:650;gap:8px}} .metric-icon {{color:var(--accent);font-size:17px}}
    .metric-value {{font-size:clamp(20px,2vw,29px);font-weight:800;letter-spacing:-.7px;margin:14px 0 5px;overflow-wrap:anywhere;color:var(--ink)}} .metric-caption {{font-size:11px;color:var(--muted);line-height:1.4}}
    .section-heading {{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:22px 0 12px}} .section-heading h3 {{font-size:17px;margin:0}} .section-heading span {{font-size:11px;color:var(--muted)}}
    .soft-tile {{padding:17px;border-radius:16px;box-shadow:4px 4px 9px #c7ccd3,-4px -4px 9px #fff;min-height:115px}} .tile-icon {{color:var(--accent);font-size:20px}} .tile-title {{font-weight:750;margin:6px 0;color:var(--ink)}} .tile-copy {{font-size:12px;color:var(--muted)}}
    .table-wrap {{direction:ltr;overflow-x:auto;border-radius:14px;box-shadow:inset 2px 2px 5px #c7ccd3,inset -2px -2px 5px #fff;padding:4px;margin:8px 0 16px}}
    .ss-table {{direction:ltr;width:100%;border-collapse:collapse;font-size:13px;background:transparent;}} .ss-table th {{text-align:{align};color:var(--muted);font-size:11px;font-weight:750;padding:12px 14px;border-bottom:1px solid #cfd5dd;white-space:nowrap}} .ss-table td {{padding:11px 14px;border-bottom:1px solid rgba(190,198,208,.55);color:var(--ink);white-space:nowrap}} .ss-table tr:last-child td {{border-bottom:0}} .ss-table tbody tr:hover {{background:rgba(255,255,255,.35)}}
    div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea,div[data-testid="stDateInput"] input,div[data-testid="stSelectbox"] div[data-baseweb="select"] {{border-radius:12px!important;background:var(--bg)!important;box-shadow:inset 3px 3px 6px #c7ccd3,inset -3px -3px 6px #fff!important}}
    .stButton > button,.stDownloadButton > button {{border:0;border-radius:12px;background:var(--bg);color:var(--ink);font-weight:700;box-shadow:4px 4px 8px #c7ccd3,-4px -4px 8px #fff;transition:transform .15s,box-shadow .15s;min-height:42px}}
    .stButton > button:hover,.stDownloadButton > button:hover {{color:var(--accent);transform:translateY(-1px);box-shadow:3px 3px 6px #c7ccd3,-3px -3px 6px #fff}}
    .stButton > button:focus-visible,.stDownloadButton > button:focus-visible {{outline:3px solid var(--accent);outline-offset:2px}}
    button[kind="primary"] {{background:var(--accent)!important;color:white!important;box-shadow:3px 3px 8px #c7ccd3,-3px -3px 8px #fff!important}}
    [data-testid="stAlert"] {{border-radius:12px}} .footer {{border-top:1px solid #d4dae2;margin-top:38px;padding:16px 0;color:var(--muted);font-size:11px;text-align:center}}
    [data-testid="stFileUploader"] section {{border-radius:14px!important;background:var(--bg)!important;box-shadow:inset 3px 3px 6px #c7ccd3,inset -3px -3px 6px #fff!important}}
    @media(max-width:760px) {{ .topline,.welcome-panel {{align-items:flex-start;flex-direction:column}} .welcome-panel h2 {{font-size:22px}} .metric-card {{min-height:115px;padding:14px}} .metric-value {{font-size:22px}} }}
    </style>
    """, unsafe_allow_html=True)
