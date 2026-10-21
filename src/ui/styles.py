"""사용자가 제공한 파란색 SPOT CHECK 시안의 레이아웃."""

import streamlit as st


def apply_styles():
    st.html("""<style>
    .stApp{background:radial-gradient(ellipse at 85% 5%,#e7f0ff 0%,#f8faff 48%,#fff 100%)}
    .stMainBlockContainer{max-width:none;width:100%;padding:1.5rem clamp(18px,3vw,64px) 2rem;min-height:100dvh}
    [data-testid="stHeader"]{background:transparent}
    h1,h2,h3{color:#0c1837;letter-spacing:-.055em!important;font-weight:800!important}
    p{line-height:1.75}button{transition:all .15s ease!important}button:hover{transform:translateY(-1px)}
    .brand{display:flex;gap:11px;align-items:center;margin:4px 0 10px}.brand strong{font-size:23px;letter-spacing:-1px;font-weight:900;color:#0d1937}
    .brand small{display:block;color:#607497;font-size:8px;letter-spacing:1.2px;margin-top:-3px}
    .brand-pin{width:34px;height:40px}.eyebrow{font-size:12px;font-weight:700;color:#0866ff;letter-spacing:.12em;margin-bottom:16px}
    .page-title{text-align:center;padding:30px 0 26px}.page-title h1{font-size:30px!important;margin:0 0 8px}.page-title p{color:#72819c;margin:0;font-size:14px}
    .stepper{display:flex;align-items:center;justify-content:flex-end;gap:12px;padding:13px 0 8px;color:#8c99ad;font-size:12px}
    .step{display:flex;gap:7px;align-items:center;white-space:nowrap}.step b{border-radius:50%;width:24px;height:24px;display:grid;place-items:center;background:#d6deeb;color:white}
    .step.active{color:#0866ff;font-weight:700}.step.active b,.step.done b{background:#0866ff}.step.done{color:#5074ac}.step-line{height:1px;background:#c9d8ee;width:28px}
    .st-key-hero{padding:clamp(28px,5vw,80px)!important;min-height:calc(100dvh - 160px);border-radius:20px;background:linear-gradient(135deg,#fff 20%,#eef4ff 100%);overflow:hidden;border:1px solid #e4ecf8;justify-content:center}
    .st-key-hero h1{font-size:58px!important;line-height:1.1;margin-bottom:4px}.st-key-hero h2{font-size:30px!important;line-height:1.35;max-width:610px;margin-bottom:12px}
    .hero-copy{font-size:15px;color:#344760;max-width:510px;margin-bottom:24px}.st-key-hero [data-testid="stMetric"]{background:#fffffff0;box-shadow:0 5px 18px #10244812;border-radius:12px;padding:16px 22px;border:1px solid #e4ecf7}
    [data-testid="stMetricValue"]{font-size:27px;font-weight:800}.st-key-hero [data-testid="stMetricLabel"]{color:#61718b}
    .st-key-region-panel,.st-key-location-panel,.st-key-chat-context{background:#ffffffd9;border:1px solid #dfe8f6;border-radius:16px;padding:22px;box-shadow:0 5px 24px #25395906}
    div[class*="st-key-spot-card-"] button{min-height:92px;text-align:left;border-color:#dbe5f4;background:#fff;white-space:pre-line}
    div[class*="st-key-spot-card-"] button p{font-size:15px;line-height:1.55}
    div[class*="st-key-spot-card-"] button[kind="primary"]{background:#0866ff;border-color:#0866ff;color:#fff}
    .brand-marker{display:block;flex-shrink:0;width:29px;height:29px;background:#0866ff;border-radius:50% 50% 50% 0;transform:rotate(-45deg);position:relative;margin:0 6px 10px 2px}
    .brand-marker:after{content:"";position:absolute;width:13px;height:13px;background:white;border-radius:50%;left:8px;top:8px}
    .selection-card{padding:16px;background:#eff5ff;border:1px solid #d8e7ff;border-radius:10px;margin:12px 0;color:#183252;font-size:14px}
    .selection-card small{display:block;font-size:12px;color:#7587a3;margin-top:6px}.label{font-size:12px;color:#7a89a3;margin:14px 0 10px}
    .st-key-chat-context{min-height:650px}.st-key-chat-context h3{font-size:16px!important}.st-key-chat-context p{font-size:13px}
    [data-testid="stChatMessage"]{border:1px solid #e7edf7;border-radius:16px;background:#fff;padding:16px;margin-bottom:14px}
    [data-testid="stChatInput"]{border-radius:12px;background:white;border:1px solid #dbe5f4}
    .feature{background:white;border:1px solid #e1e9f5;border-radius:14px;padding:22px;min-height:130px}.feature span{color:#0866ff;font-size:12px;font-weight:800;letter-spacing:.1em}.feature h3{font-size:18px!important;margin:9px 0}.feature p{color:#75839b;font-size:13px;margin:0}
    .footer{font-size:11px;color:#8996aa;display:flex;justify-content:space-between;padding:26px 0 6px;border-top:1px solid #e5ecf7;margin-top:28px}
    .spotcheck-map-status{font-size:11px;color:#788aa5;padding-top:6px}
    .st-key-chat-feed{height:calc(100dvh - 250px)!important;min-height:360px}
    @media(max-width:900px){[data-testid="stHorizontalBlock"]{flex-wrap:wrap}[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{min-width:min(100%,320px);flex:1 1 320px}.stepper{justify-content:flex-start}.st-key-chat-context{min-height:0}}
    @media(max-width:600px){.stMainBlockContainer{padding:1rem}.st-key-hero{padding:28px 20px!important;min-height:calc(100dvh - 180px)}.st-key-hero h1{font-size:38px!important}.st-key-hero h2{font-size:24px!important}.stepper{gap:6px}.page-title{padding:20px 0}.page-title h1{font-size:24px!important}.footer{flex-direction:column;gap:8px}.st-key-chat-feed{height:65dvh!important}.brand strong{font-size:20px}}
    </style>""")


def brand():
    st.html('''<div class="brand"><span class="brand-marker" aria-hidden="true"></span><div><strong>SPOT CHECK</strong><small>AI LOCATION INTELLIGENCE</small></div></div>''')


def stepper(active):
    labels = ["지역 선택", "위치 설정", "분석 시작"]
    parts = []
    for index, label in enumerate(labels, 1):
        style = "active" if index == active else "done" if index < active else ""
        parts.append(f'<div class="step {style}"><b>{"✓" if index < active else index}</b>{label}</div>')
    st.html('<div class="stepper">' + '<span class="step-line"></span>'.join(parts) + '</div>')


def page_title(title, subtitle):
    from html import escape
    st.html(f'<div class="page-title"><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>')
