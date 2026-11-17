# ==============================================================================
# ⚠️ 【重要防呆提醒】本檔案是：stock_arsenal_v1.py (前端主畫面)
# 請確認 GitHub 網頁頂端的檔名是 stock_arsenal_v1.py 再貼上！切勿貼到 data_engine.py！
# ==============================================================================
import os, re, json, importlib
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import data_engine as de
importlib.reload(de)

st.set_page_config(page_title="個股衍生武器庫 & 短線當沖戰情室", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

DEFAULT_STATES = {
    "font_scale": 1.05, "theme_mode": "dark", "admin_unlocked": False, "active_nav_tab": 1,
    "unlocked_tab1": False, "unlocked_tab2": False, "unlocked_tab4": False,
    "target_stock_code": "2330", "w_buy_p": 1410.0, "w_sell_p": 1415.0, "w_lots": 1,
    "dynamic_stock_meta": {}, "close_popover_seq": 0,
    "tab1_master_items": [
        {"id": "🕯️", "name": "🕯️ 三週期共振雷達 & K線實戰圖 (日K / 60分K / 5分K)", "show": True},
        {"id": "📊", "name": "📊 法人與資券直方柱狀圖 (近20日視覺化)", "show": True},
        {"id": "📋", "name": "📋 五週期籌碼累計矩陣 & 逐日明細表", "show": True},
        {"id": "📰", "name": "📰 近期市場消息與催化劑雷達", "show": True},
        {"id": "📐", "name": "📐 下個交易日 AH / NH / NL / AL 支撐壓力區間", "show": True},
    ],
    "ai_chat_history": [{"role": "assistant", "content": "您好！我是戰情室 AI 助手 🤖。請直接問我**「為什麼 00877 這麼弱？」**、**「怎麼看 3167？」**或**「6214 能買嗎？」**，我會結合官方真實數據與新聞為您剖析原因與 AH/NH/NL/AL 價位！"}]
}
for k, v in DEFAULT_STATES.items(): st.session_state.setdefault(k, v)

def dec_font(): st.session_state.font_scale = max(0.90, round(st.session_state.font_scale - 0.10, 2))
def inc_font(): st.session_state.font_scale = min(1.40, round(st.session_state.font_scale + 0.10, 2))
def toggle_theme(): st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"
def switch_to_tab(tab_num): st.session_state.active_nav_tab = int(tab_num)

is_dark = (st.session_state.theme_mode == "dark")
BG_MAIN, BG_SIDEBAR, TEXT_MAIN, TEXT_SUB, TEXT_MUTED, CARD_BG, CARD_BG_ALT, CARD_BORDER, BANNER_BG, SCORE_BOX_BG, NEWS_BG, PLOT_BG, GRID_COLOR, BULL_COLOR, BEAR_COLOR, WARN_COLOR = (
    ("#0E1117", "#161B26", "#FFFFFF", "#CBD5E0", "#A0AEC0", "#1A1F2C", "#1E232F", "#2D3748", "linear-gradient(135deg, #16222A 0%, #3A6073 100%)", "rgba(0,0,0,0.38)", "#161B26", "#141824", "#2D3748", "#FF6B6B", "#2ECC71", "#F1C40F") if is_dark else
    ("#F8FAFC", "#F1F5F9", "#0F172A", "#334155", "#475569", "#FFFFFF", "#FFFFFF", "#CBD5E1", "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)", "rgba(255,255,255,0.85)", "#F1F5F9", "#FFFFFF", "#E2E8F0", "#DC2626", "#16A34A", "#D97706")
)
scale = st.session_state.font_scale
card_min_w = "245px" if scale >= 1.15 else "210px"

st.markdown(f"""<style>
.stApp {{ background-color: {BG_MAIN} !important; color: {TEXT_MAIN} !important; }}
.block-container {{ max-width: 1260px !important; padding: 3.4rem 2rem 5rem 2rem !important; }}
section[data-testid="stSidebar"] {{ background-color: {BG_SIDEBAR} !important; color: {TEXT_MAIN} !important; }}
h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, [data-testid="stCaptionContainer"] {{ color: {TEXT_MAIN} !important; }}
.stButton > button {{ background-color: {CARD_BG} !important; color: {TEXT_MAIN} !important; border: 1px solid {CARD_BORDER} !important; font-weight: bold !important; white-space: normal !important; line-height: 1.35 !important; padding: 0.45rem 0.7rem !important; min-height: 2.45rem !important; }}
.stButton > button:hover {{ border-color: #4A90E2 !important; color: #60A5FA !important; }}
.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: #FFFFFF !important; border: 1.5px solid #60A5FA !important; }}
div[data-testid="stPopover"] {{ position: fixed !important; bottom: 24px !important; right: 26px !important; z-index: 999999 !important; }}
div[data-testid="stPopover"] > div > button, div[data-testid="stPopover"] > button {{ background: linear-gradient(135deg, #00D26A 0%, #009E4F 100%) !important; color: #000 !important; border-radius: 50px !important; padding: 11px 20px !important; font-size: 15.5px !important; font-weight: 800 !important; border: 2px solid #FFF !important; box-shadow: 0 6px 20px rgba(0,210,106,0.55) !important; white-space: nowrap !important; }}
div[data-testid="stPopover"] > div > button *, div[data-testid="stPopover"] > button * {{ color: #000 !important; font-weight: 800 !important; }}
div[data-baseweb="popover"] > div, div[data-testid="stPopoverBody"] {{ background-color: {CARD_BG} !important; color: {TEXT_MAIN} !important; border: 1.5px solid #4A90E2 !important; border-radius: 14px !important; }}
div[data-testid="stPopoverBody"] * {{ color: {TEXT_MAIN} !important; }}
div[data-testid="stPopoverBody"] .stButton > button {{ background-color: {BG_MAIN} !important; border: 1px solid #4A90E2 !important; border-radius: 8px !important; }}
div[data-testid="stPopoverBody"] .stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: #FFF !important; }}
div[data-testid="stPopoverBody"] .stButton > button[kind="primary"] * {{ color: #FFF !important; }}
div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] {{ background-color: {CARD_BG_ALT} !important; border: 1px solid {CARD_BORDER} !important; border-radius: 8px !important; padding: 8px 10px !important; margin-bottom: 6px !important; }}
div[data-testid="stPopoverBody"] [data-testid="stChatInput"] > div {{ background-color: {BG_MAIN} !important; border: 1px solid {CARD_BORDER} !important; }}
@media (max-width: 768px) {{ .block-container {{ padding: 2.2rem 0.65rem 5.5rem 0.65rem !important; }} div[data-testid="stPopover"] {{ bottom: 68px !important; right: 12px !important; }} }}
.app-main-title {{ font-size: {round(21.5 * scale, 1)}px; font-weight: 800; color: {TEXT_MAIN}; margin: 0; }}
.score-banner {{ background: {BANNER_BG}; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; border: 1px solid #4A90E2; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }}
.pillar-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax({card_min_w}, 1fr)); gap: 12px; margin-bottom: 16px; }}
.pillar-card {{ background-color: {CARD_BG}; border-radius: 12px; padding: 14px 15px; border: 1px solid {CARD_BORDER}; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
.pillar-title {{ font-size: {round(13.5 * scale, 1)}px; color: {TEXT_MUTED}; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; font-weight: 600; }}
.pillar-main {{ font-size: {round(18.5 * scale, 1)}px; font-weight: bold; margin-bottom: 8px; color: {TEXT_MAIN}; }}
.bar-bg {{ background-color: {CARD_BORDER}; border-radius: 6px; height: 7px; width: 100%; margin-bottom: 10px; overflow: hidden; }}
.pillar-sub {{ font-size: {round(13.5 * scale, 1)}px; color: {TEXT_SUB}; line-height: 1.65; }}
.tag-bull {{ background-color: rgba(231,76,60,0.15); color: {BULL_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {BULL_COLOR}; }}
.tag-bear {{ background-color: rgba(46,204,113,0.15); color: {BEAR_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {BEAR_COLOR}; }}
.tag-neutral {{ background-color: rgba(241,196,15,0.15); color: {WARN_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {WARN_COLOR}; }}
.metric-card {{ background-color: {CARD_BG_ALT}; border-radius: 10px; padding: 16px; margin-bottom: 12px; border: 1px solid {CARD_BORDER}; border-left: 5px solid #00D26A; font-size: {round(15 * scale, 1)}px; line-height: 1.65; }}
.news-card {{ background-color: {NEWS_BG}; border-radius: 8px; padding: 11px 14px; margin-bottom: 8px; border-left: 3px solid #4A90E2; font-size: {round(14.5 * scale, 1)}px; }}
.cta-box {{ background: {BANNER_BG}; border-radius: 12px; padding: 18px; text-align: center; margin-top: 20px; border: 1px solid #4A90E2; }}
.disclaimer {{ font-size: {round(12.5 * scale, 1)}px; color: {TEXT_MUTED}; margin-top: 25px; line-height: 1.6; }}
</style>""", unsafe_allow_html=True)

components.html(f"""<script>
(function() {{
    const parentDoc = window.parent.document;
    const closeSeq = {int(st.session_state.get("close_popover_seq", 0))};
    if (closeSeq > 0 && window.parent._lastClosePopoverSeq !== closeSeq) {{
        window.parent._lastClosePopoverSeq = closeSeq;
        setTimeout(() => {{
            const popBtn = parentDoc.querySelector('div[data-testid="stPopover"] button[aria-expanded="true"]');
            if (popBtn) popBtn.click();
            window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}, 60);
    }}
}})();
</script>""", height=0, width=0)

top_c1, top_c2 = st.columns([6.8, 3.2])
top_c1.markdown('<div class="app-main-title">⚡ 個股衍生武器庫 & 短線當沖戰情室</div>', unsafe_allow_html=True)
with top_c2.expander("⚙️ 顯示設定（切換深淺色 ／ 字體大小）"):
    b1, b2, b3 = st.columns(3)
    b1.button("☀️淺色" if is_dark else "🌙深色", use_container_width=True, on_click=toggle_theme)
    b2.button("➖縮小", use_container_width=True, on_click=dec_font)
    b3.button(f"➕放大({int(round(scale*100))}%)", use_container_width=True, on_click=inc_font)

def style_signed_numbers(val):
    try:
        v = float(val)
        if v > 0: return f"color: {BULL_COLOR}; font-weight: bold; background-color: rgba(255,75,75,0.12);"
        elif v < 0: return f"color: {BEAR_COLOR}; font-weight: bold; background-color: rgba(46,204,113,0.12);"
    except Exception: pass
    return f"color: {TEXT_SUB};"

def fmt_colored_num(val, unit="張", is_float=False):
    c = BULL_COLOR if val > 0 else (BEAR_COLOR if val < 0 else TEXT_SUB)
    return f"<span style='color:{c}; font-weight:bold;'>{(f'{val:+,.2f}' if is_float else f'{int(val):+,}')} {unit}</span>"

def render_cta_box(title_txt, btn_txt, line_url):
    st.markdown(f"""<div class="cta-box"><p style="font-size:{round(16*scale,1)}px; margin-bottom:12px; font-weight:bold;">{title_txt}</p>
    <a href="{line_url}" target="_blank" style="background-color:#00D26A; color:#000; padding:10px 20px; border-radius:8px; font-weight:bold; font-size:{round(15*scale,1)}px; text-decoration:none; display:inline-block;">{btn_txt}</a></div>""", unsafe_allow_html=True)

def plot_universal_kline_chart(kline_records, scale_factor=1.05, show_bb=True, show_td=True, show_cdp=True, cdp_vals=None, show_volume=False):
    df_k = pd.DataFrame(kline_records)
    x_col = "ShortDate" if "ShortDate" in df_k.columns else "DateStr"
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.74, 0.26]) if (show_volume and "Volume" in df_k.columns) else make_subplots(rows=1, cols=1)
    fig.add_trace(go.Candlestick(x=df_k[x_col], open=df_k["Open"], high=df_k["High"], low=df_k["Low"], close=df_k["Close"], increasing_line_color="#FF4B4B", increasing_fillcolor="#FF4B4B", decreasing_line_color="#00D26A", decreasing_fillcolor="#00D26A", name="K線"), row=1, col=1)
    for col, name, clr, w, dsh in [("MA5", "5MA", "#3498DB", 1.4, None), ("MA20", "20MA", "#F59E0B", 2.2, None), ("MA60", "60MA", "#9B59B6", 1.5, "dot")]:
        if col in df_k.columns: fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k[col], mode="lines", name=name, line=dict(color=clr, width=w, dash=dsh), hovertemplate="%{y:,.2f}"), row=1, col=1)
    if show_bb and "BB_Upper" in df_k.columns:
        fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k["BB_Upper"], mode="lines", name="布林上軌", line=dict(color="rgba(52,152,219,0.65)", width=1.3, dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k["BB_Lower"], mode="lines", name="布林下軌", line=dict(color="rgba(46,204,113,0.75)", width=1.5, dash="dash"), fill="tonexty", fillcolor="rgba(52,152,219,0.05)"), row=1, col=1)
    b_col, s_col = ("TD_Buy_Disp" if "TD_Buy_Disp" in df_k.columns else "TD_Buy"), ("TD_Sell_Disp" if "TD_Sell_Disp" in df_k.columns else "TD_Sell")
    if show_td and b_col in df_k.columns:
        for _, r in df_k.iterrows():
            bv, sv = int(r.get(b_col, 0)), int(r.get(s_col, 0))
            if bv == 9: fig.add_annotation(x=r[x_col], y=float(r["Low"]), text="<b>▲低9</b>", showarrow=False, yshift=-15, font=dict(color="#00D26A", size=int(11*scale_factor)), bgcolor="rgba(0,210,106,0.16)", bordercolor="#00D26A", row=1, col=1)
            elif 1 <= bv <= 8: fig.add_annotation(x=r[x_col], y=float(r["Low"]), text=f"<b>{bv}</b>", showarrow=False, yshift=-11, font=dict(color="#00D26A", size=int(9.5*scale_factor)), row=1, col=1)
            if sv == 9: fig.add_annotation(x=r[x_col], y=float(r["High"]), text="<b>▼高9</b>", showarrow=False, yshift=15, font=dict(color="#FF4B4B", size=int(11*scale_factor)), bgcolor="rgba(255,75,75,0.16)", bordercolor="#FF4B4B", row=1, col=1)
            elif 1 <= sv <= 8: fig.add_annotation(x=r[x_col], y=float(r["High"]), text=f"<b>{sv}</b>", showarrow=False, yshift=11, font=dict(color="#FF4B4B", size=int(9.5*scale_factor)), row=1, col=1)
    if len(df_k) >= 20:
        dr, sc = df_k.iloc[-20], ("#F1C40F" if is_dark else "#D97706")
        dp = round(float(dr["Close"]), 2)
        fig.add_trace(go.Scatter(x=[dr[x_col]], y=[dp], mode="markers+text", name="20根扣抵", marker=dict(color=sc, size=13, symbol="star"), text=[f"⭐{dp}"], textposition="top center", textfont=dict(color=sc, size=int(10.5*scale_factor))), row=1, col=1)
        fig.add_hline(y=dp, line_width=1.1, line_dash="dash", line_color=sc, annotation_text=f"扣抵 {dp}", annotation_position="bottom left", row=1, col=1)
    if show_cdp and cdp_vals:
        for k, lbl, clr, pos in [("AH", "AH極端突破", "#EF4444", "top left"), ("NH", "NH常態壓力", "#F97316", "top right"), ("NL", "NL常態支撐", "#38BDF8", "bottom right"), ("AL", "AL極端破底", "#10B981", "bottom left")]:
            fig.add_hline(y=cdp_vals[k], line_width=1.1, line_dash="dot", line_color=clr, annotation_text=f"{lbl} {cdp_vals[k]}", annotation_position=pos, annotation_font=dict(color=clr, size=int(9.5*scale_factor)), row=1, col=1)
    if show_volume and "Volume" in df_k.columns:
        fig.add_trace(go.Bar(x=df_k[x_col], y=df_k["Volume"], name="量(張)", marker_color=["#FF4B4B" if c >= o else "#00D26A" for c, o in zip(df_k["Close"], df_k["Open"])]), row=2, col=1)
    y_min, y_max = float(df_k["Low"].min()), float(df_k["High"].max())
    if show_cdp and cdp_vals: y_min, y_max = min(y_min, cdp_vals["NL"]), max(y_max, cdp_vals["NH"])
    pad = max(0.5, (y_max - y_min) * 0.08)
    fig.update_layout(hovermode="x unified", yaxis=dict(range=[y_min - pad, y_max + pad], gridcolor=GRID_COLOR), xaxis=dict(type="category", rangeslider=dict(visible=False), tickangle=-35, nticks=10), legend=dict(orientation="h", y=1.02, x=0), height=int((440 if show_volume else 400)*max(1.0, scale_factor*0.92)), margin=dict(l=8, r=12, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN))
    return fig

def plot_20d_chip_bar_chart(daily_table, scale_factor=1.1):
    df_c = pd.DataFrame(daily_table).sort_values("交易日期", ascending=True)
    df_c["ShortDate"] = df_c["交易日期"].str.slice(5)
    fig = go.Figure()
    for col, name, clr in [("外資買賣超(張)", "外資", "#3498DB"), ("投信買賣超(張)", "投信", "#FF6B6B"), ("自營商買賣超(張)", "自營", "#F59E0B")]:
        fig.add_trace(go.Bar(x=df_c["ShortDate"], y=df_c[col], name=name, marker_color=clr))
    fig.add_trace(go.Scatter(x=df_c["ShortDate"], y=df_c["三大法人合計(張)"], mode="lines+markers", name="法人合計", line=dict(color=TEXT_MAIN, width=2, dash="dot")))
    fig.update_layout(barmode="group", hovermode="x unified", xaxis=dict(type="category", tickangle=-35), yaxis=dict(gridcolor=GRID_COLOR), legend=dict(orientation="h", y=1.02), height=330, margin=dict(l=8, r=12, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN))
    return fig

def plot_20d_margin_bar_chart(daily_table, scale_factor=1.1):
    df_m = pd.DataFrame(daily_table).sort_values("交易日期", ascending=True)
    df_m["ShortDate"] = df_m["交易日期"].str.slice(5)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_m["ShortDate"], y=df_m["融資增減(張)"], name="融資增減", marker_color="#FF6B6B"))
    fig.add_trace(go.Bar(x=df_m["ShortDate"], y=df_m["融券增減(張)"], name="融券增減", marker_color="#2ECC71"))
    fig.add_trace(go.Scatter(x=df_m["ShortDate"], y=df_m["券資比(%)"], mode="lines+markers", name="券資比(%)", yaxis="y2", line=dict(color="#F59E0B", width=2, dash="dot")))
    fig.update_layout(barmode="group", hovermode="x unified", xaxis=dict(type="category", tickangle=-35), yaxis=dict(gridcolor=GRID_COLOR), yaxis2=dict(overlaying="y", side="right", showgrid=False), legend=dict(orientation="h", y=1.02), height=330, margin=dict(l=8, r=12, t=35, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN))
    return fig

def check_tab_password_gate(tab_num, tab_key, is_locked, correct_pwd, gate_title, gate_desc, line_url):
    if not is_locked or st.session_state.get(tab_key, False): return True
    st.markdown(f"#### 🔒 【{gate_title}】專屬授權解鎖")
    st.info(f"💡 {gate_desc}")
    with st.form(f"form_{tab_key}"):
        c1, c2 = st.columns([7.5, 2.5])
        pwd_in = c1.text_input("密碼：", type="password", label_visibility="collapsed", placeholder="請輸入專屬解鎖密碼...")
        if c2.form_submit_button("🔓 確認解鎖", use_container_width=True, type="primary"):
            if pwd_in.strip() == str(correct_pwd).strip(): st.session_state[tab_key], st.session_state.active_nav_tab = True, int(tab_num); st.rerun()
            else: st.error("❌ 密碼不正確。")
    render_cta_box(f"🔑 還沒有【{gate_title}】通行碼嗎？", f"💬 點此私訊營業員：索取【{gate_title}】密碼", line_url)
    return False

@st.fragment
def render_fast_profit_calculator(line_url, is_public_promo=False):
    for i in range(1, 6): st.session_state.setdefault(f"bp_{i}", 0.0); st.session_state.setdefault(f"bl_{i}", 0)
    st.subheader("🧮 現股當沖 ／ 隔日沖「獲利價位 & 近五檔損益」試算室")
    with st.container(border=True):
        c1, c2 = st.columns([3.5, 6.5])
        excel_fold = c1.number_input("🏷️ 手續費折數 (低消 20 元)：", 0.10, 10.00, 2.80, 0.05, format="%.2f")
        tax_opt = c2.radio("🏛️ 交易稅率模式：", ["⚡ 現股當沖 (稅 0.15%)", "📅 隔日沖/現股 (稅 0.30%)", "🏦 ETF (稅 0.10%)"], horizontal=True)
        tax_rate = 0.0015 if "0.15%" in tax_opt else (0.0030 if "0.30%" in tax_opt else 0.0010)
    l_col, r_col = st.columns([4.6, 5.4], gap="medium")
    with l_col:
        with st.container(border=True):
            st.markdown("#### 🎯 1. 單筆買賣「獲利價位 & 損益試算」")
            b1, b2, b3 = st.columns(3)
            buy_p = b1.number_input("💵 買進價", 0.01, 30000.0, step=float(de.get_tw_tick_size(st.session_state.w_buy_p)), format="%.2f", key="w_buy_p")
            sell_p = b2.number_input("💴 賣出價", 0.01, 30000.0, step=float(de.get_tw_tick_size(st.session_state.w_sell_p)), format="%.2f", key="w_sell_p")
            lots = b3.number_input("📦 張數", 1, 10000, step=1, key="w_lots")
            res = de.calc_trade_row_min20(buy_p, sell_p, lots, excel_fold, tax_rate)
            p_clr = BULL_COLOR if res["net_pnl"] > 0 else (BEAR_COLOR if res["net_pnl"] < 0 else TEXT_MAIN)
            st.markdown(f"""<div class="pillar-card" style="border-left:5px solid {p_clr}; margin-top:6px;">
            <div class="pillar-title"><span>📊 買 {buy_p:g} ➔ 賣 {sell_p:g} ({lots} 張)</span><span class="{'tag-bull' if res['net_pnl']>0 else 'tag-bear'}">ROI {res['roi_pct']:+.2f}%</span></div>
            <div style="font-size:{round(14*scale,1)}px; line-height:1.75;">
            • <b>總成本：</b>手續費 {res['total_fee']:,} ＋ 稅 {res['tax']:,} ＝ <b>{res['total_cost']:,} 元</b><br>
            • 📈 <b>做多獲利價：</b><b style="color:#F59E0B;">{res['long_be_price']:.2f} 元</b> (+{res['long_win_ticks']}檔至 {res['long_win_price']:g} 元即賺)<br>
            • 📉 <b>放空獲利價：</b><b style="color:#3498DB;">{res['short_be_price']:.2f} 元</b> (-{res['short_win_ticks']}檔至 {res['short_win_price']:g} 元即賺)<br>
            • 💰 <b>實拿淨損益：</b><b style="color:{p_clr}; font-size:{round(20*scale,1)}px;">{res['net_pnl']:+,} 元</b></div></div>""", unsafe_allow_html=True)
        with st.expander("🧮 2. 分批進場平均成本試算器（最多 5 批）"):
            s_lots, s_val = 0, 0.0
            for idx in range(1, 6):
                bc1, bc2 = st.columns(2)
                pv = bc1.number_input(f"第 {idx} 批成交價", 0.0, 30000.0, step=0.5, format="%.2f", key=f"bp_{idx}")
                lv = bc2.number_input(f"第 {idx} 批張數", 0, 10000, step=1, key=f"bl_{idx}")
                if pv > 0 and lv > 0: s_lots += int(lv); s_val += (pv * lv)
            avg_p = round(s_val / s_lots, 2) if s_lots > 0 else 0.0
            st.markdown(f"📌 總張數：**{s_lots} 張** ｜ ⚖️ 加權均價：**{avg_p:.2f} 元**")
            if s_lots > 0:
                st.button(f"📈 帶入做多 ({avg_p:.2f}元 × {s_lots}張)", use_container_width=True, on_click=lambda a=avg_p, l=s_lots: st.session_state.update({"w_buy_p": float(a), "w_sell_p": float(de.step_tw_ticks(a, 2)), "w_lots": int(l)}))
    with r_col:
        with st.container(border=True):
            st.markdown("#### 📊 3. 做多 ／ 放空「近五檔價位損益速查表」")
            t_l, t_s = st.tabs([f"📈 做多五檔 (買 {buy_p:g}元)", f"📉 放空五檔 (賣 {sell_p:g}元)"])
            for t_obj, is_l in [(t_l, True), (t_s, False)]:
                with t_obj:
                    steps, p_c = ([5, 4, 3, 2, 1, 0, -1, -2, -3], "賣價") if is_l else ([-5, -4, -3, -2, -1, 0, 1, 2, 3], "補價")
                    r5 = []
                    for s_i in steps:
                        tp = de.step_tw_ticks(buy_p if is_l else sell_p, s_i)
                        rc = de.calc_trade_row_min20(buy_p if is_l else tp, tp if is_l else sell_p, lots, excel_fold, tax_rate)
                        r5.append({"檔位": f"{s_i:+}檔", p_c: tp, "實拿損益": rc["net_pnl"], "報酬率": rc["roi_pct"], "總成本": rc["total_cost"]})
                    st.dataframe(pd.DataFrame(r5).style.map(style_signed_numbers, subset=["實拿損益", "報酬率"]).format({p_c: "{:g}", "實拿損益": "{:+,.0f}", "報酬率": "{:+.2f}%", "總成本": "{:,.0f}"}), use_container_width=True, hide_index=True, height=350)
    render_cta_box("🔥 想申請更優惠的【VIP 手續費折數】嗎？" if is_public_promo else "⚡ 想索取今日盤後【當沖主力分點明細】嗎？", "💬 點此私訊專屬營業員諮詢", line_url)

de.init_sample_csvs()
cfg = de.load_config()
sector_map_all = de.load_sector_map()
df_quotes, df_futures, df_cb = de.read_csv_safely(de.QUOTES_FILE), de.read_csv_safely(de.FUTURES_FILE), de.read_csv_safely(de.CB_FILE)
margins_global_map = dict(zip(df_futures["代號"].astype(str), df_futures["保證金比例"]))
master_stock_dict = de.get_master_stock_dictionary()
if len(df_quotes) < len(master_stock_dict): df_quotes = pd.DataFrame(list(master_stock_dict.values())).sort_values("代號")

if not df_quotes.empty:
    df_quotes = df_quotes[df_quotes["代號"].str.match(r"^(00\d{2,4}[A-Za-z]?|\d{4})$", na=False)].copy()
    fut_codes = set(df_futures["代號"].astype(str))
    df_quotes["has_fut_sort"] = df_quotes["代號"].astype(str).apply(lambda x: 0 if x in fut_codes else 1)
    stock_options = [f"{r['代號']} {r['名稱']}" + (" ⚡[有期貨]" if str(r['代號']) in fut_codes else "") for _, r in df_quotes.sort_values(["has_fut_sort", "代號"]).iterrows()]
else: stock_options = ["2330 台積電 ⚡[有期貨]"]

code_to_name_map = dict(zip(df_quotes["代號"].astype(str), df_quotes["名稱"].astype(str)))
name_to_code_map = dict(zip(df_quotes["名稱"].astype(str), df_quotes["代號"].astype(str)))
code_to_mkt_map = dict(zip(df_quotes["代號"].astype(str), df_quotes.get("市場", pd.Series(["TWSE"]*len(df_quotes)))))
for d_c, d_m in st.session_state.get("dynamic_stock_meta", {}).items():
    code_to_name_map.setdefault(d_c, d_m["name"]); name_to_code_map.setdefault(d_m["name"], d_c); code_to_mkt_map.setdefault(d_c, d_m["mkt"])

with st.sidebar:
    st.caption("🔐 專供營業員維護使用")
    if not st.session_state.admin_unlocked:
        with st.form("admin_login_form"):
            adm_in = st.text_input("🔑 營業員管理登入：", type="password")
            if st.form_submit_button("🔓 登入後台", use_container_width=True):
                if adm_in == de.ADMIN_SECRET_CODE: st.session_state.admin_unlocked = True; st.rerun()
                else: st.error("❌ 密碼錯誤")
    else:
        c_a1, c_a2 = st.columns([7, 3])
        c_a1.success("✅ 管理員已解鎖")
        if c_a2.button("登出", use_container_width=True): st.session_state.admin_unlocked = False; st.rerun()
        new_line = st.text_input("💬 LINE 連結：", value=cfg["broker_line_url"]).strip()
        new_promo = st.checkbox("🌐 對外開發公版模式", value=bool(cfg.get("public_promo_mode", False)))
        new_g_key = st.text_input("🤖 Gemini API Key (標準為 AIzaSy 開頭)：", type="password", value=str(cfg.get("gemini_api_key", ""))).strip()
        new_fm = st.text_input("🔑 FinMind Token：", type="password", value=str(cfg.get("finmind_token", ""))).strip()
        l_t1, p_t1 = st.checkbox("鎖定分頁 1", value=bool(cfg.get("lock_tab1", False))), st.text_input("分頁 1 密碼：", value=str(cfg.get("pwd_tab1", "VIP888"))).strip()
        l_t2, p_t2 = st.checkbox("鎖定分頁 2", value=bool(cfg.get("lock_tab2", False))), st.text_input("分頁 2 密碼：", value=str(cfg.get("pwd_tab2", "TICK888"))).strip()
        l_t4, p_t4 = st.checkbox("鎖定分頁 3", value=bool(cfg.get("lock_tab4", False))), st.text_input("分頁 3 密碼：", value=str(cfg.get("pwd_tab4", "VIP888"))).strip()
        n_vals = {"lock_tab1": l_t1, "pwd_tab1": p_t1, "lock_tab2": l_t2, "pwd_tab2": p_t2, "lock_tab4": l_t4, "pwd_tab4": p_t4, "public_promo_mode": new_promo, "gemini_api_key": new_g_key, "finmind_token": new_fm, "broker_line_url": new_line or cfg["broker_line_url"]}
        if any(cfg.get(k) != v for k, v in n_vals.items()): cfg.update(n_vals); de.save_config(cfg); st.toast("✅ 設定已自動儲存！")
        st.divider()
        if st.button("🏛️ 同步大盤法人、外資期貨與資券", use_container_width=True, type="primary"):
            m_res = de.sync_market_institutional_online(new_fm)
            if m_res: cfg.update(m_res); de.save_config(cfg); st.success("✅ 同步完成！"); st.rerun()

is_public_promo, fm_token_str = bool(cfg.get("public_promo_mode", False)), str(cfg.get("finmind_token", "")).strip()
cur_tab = st.session_state.active_nav_tab if st.session_state.active_nav_tab in [1, 2, 3] else 1
for col_n, (t_idx, l_k, u_k, ico, lbl) in zip(st.columns(3), [(1, "lock_tab1", "unlocked_tab1", "🔍", "1. 個股三週期共振雷達"), (2, "lock_tab2", "unlocked_tab2", "🧮", "2. 現沖/隔日沖獲利試算"), (3, "lock_tab4", "unlocked_tab4", "🚦", "3. 大盤籌碼 & 動態主流族群")]):
    col_n.button(f"{'🔒' if (cfg.get(l_k, False) and not st.session_state[u_k]) else ico} {lbl}", use_container_width=True, type="primary" if cur_tab == t_idx else "secondary", on_click=switch_to_tab, args=(t_idx,))

st.markdown("<hr style='margin-top:4px; margin-bottom:16px; border-color:#2D3748;'>", unsafe_allow_html=True)
current_active_code = st.session_state.target_stock_code
current_active_name = code_to_name_map.get(current_active_code, "台積電")

def jump_to_tab2_with_price(close_p):
    st.session_state.w_buy_p, st.session_state.w_sell_p, st.session_state.active_nav_tab = float(close_p), float(de.step_tw_ticks(close_p, 2)), 2

def jump_to_tab1_with_stock(code_str, name_str="", mkt_str="TWSE"):
    c_clean, n_clean = str(code_str).strip().upper(), str(name_str).replace("🔥", "").strip()
    if n_clean: st.session_state.dynamic_stock_meta[c_clean] = {"name": n_clean, "mkt": mkt_str}
    st.session_state.target_stock_code, st.session_state.active_nav_tab = c_clean, 1
    st.session_state.close_popover_seq = int(st.session_state.get("close_popover_seq", 0)) + 1

if cur_tab == 1:
    if check_tab_password_gate(1, "unlocked_tab1", cfg.get("lock_tab1", False), cfg.get("pwd_tab1", "VIP888"), "個股三週期技術與籌碼雷達", "請輸入 VIP 通行碼解鎖。", cfg["broker_line_url"]):
        def _move_mod(idx, d):
            items = st.session_state.tab1_master_items
            if 0 <= idx + d < len(items): items[idx], items[idx + d] = items[idx + d], items[idx]
        def _toggle_mod(idx): st.session_state.tab1_master_items[idx]["show"] = not st.session_state.tab1_master_items[idx]["show"]
        def _reset_mod(): st.session_state.tab1_master_items = [dict(x) for x in DEFAULT_STATES["tab1_master_items"]]

        target_c = str(st.session_state.target_stock_code).strip().upper()
        if not any(opt.startswith(target_c + " ") for opt in stock_options):
            dyn_m = st.session_state.get("dynamic_stock_meta", {}).get(target_c, {})
            s_n, s_m = dyn_m.get("name", code_to_name_map.get(target_c, target_c)), dyn_m.get("mkt", "TPEX" if target_c.endswith("B") else "TWSE")
            code_to_name_map[target_c], code_to_mkt_map[target_c] = s_n, s_m
            stock_options.insert(0, f"{target_c} {s_n}")
        default_idx = next((i for i, opt in enumerate(stock_options) if opt.startswith(target_c + " ")), 0)
        sel_box_key = f"tab1_sel_{target_c}"
        def _on_chg():
            v = st.session_state.get(sel_box_key, "")
            if v: st.session_state.target_stock_code = v.split(" ")[0].strip().upper()
        sel_c1, sel_c2 = st.columns([6.8, 3.2])
        sel_opt = sel_c1.selectbox(f"📌 請輸入個股或 ETF 代號/名稱搜尋（共收錄 {len(stock_options):,} 檔標的）：", options=stock_options, index=default_idx, key=sel_box_key, on_change=_on_chg)
        selected_code = sel_opt.split(" ")[0].strip().upper()
        st.session_state.target_stock_code = selected_code
        stock_name = code_to_name_map.get(selected_code, selected_code)
        market_hint = code_to_mkt_map.get(selected_code, "TPEX" if selected_code.endswith("B") else "TWSE")
        current_active_code, current_active_name = selected_code, stock_name

        with st.spinner(f"正在對帳【{selected_code} {stock_name}】官方真實日K、三週期共振與籌碼..."):
            tech = de.fetch_technical_indicators(selected_code, market_hint)
            tech_60m = de.fetch_intraday_kline_full(selected_code, market_hint, "60m")
            tech_5m = de.fetch_intraday_kline_full(selected_code, market_hint, "5m")
            chip = de.fetch_chip_data_20d(selected_code, fm_token_str)
            margin_info = de.fetch_margin_short_20d(selected_code, fm_token_str)
            fund_info = de.fetch_fundamental_revenue_and_shareholding(selected_code, fm_token_str)
            taiex_quick = de.fetch_taiex_market_data()
            news_data = de.fetch_stock_news(selected_code, stock_name)

        if not tech["ok"]: st.error(f"無法取得 {selected_code} 資料。"); st.stop()
        close_price, ma20_price, ma60_price, deduct_price, trade_date = tech["close"], tech["ma20"], tech["ma60"], tech["deduct"], tech["date"]
        k_val, d_val, rsi_val, vol_ratio, td_b_cnt, td_s_cnt = tech["K"], tech["D"], tech["rsi"], tech["vol_ratio"], tech["td_buy"], tech["td_sell"]
        cdp_vals = de.calculate_cdp(tech["high"], tech["low"], close_price)
        sel_c2.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
        sel_c2.button(f"🧮 帶入【{stock_name} {close_price}元】算當沖損益 ➔", use_container_width=True, on_click=jump_to_tab2_with_price, args=(close_price,))

        with st.expander("🎛️ 點此展開【自訂版面模組順序 & 顯示開關】（可點 ⬆️ / ⬇️ 自由上下移動板塊）"):
            for i, m_item in enumerate(st.session_state.tab1_master_items):
                mc1, mc2, mc3, mc4 = st.columns([0.8, 6.8, 1.2, 1.2])
                mc1.checkbox("顯示", value=m_item["show"], key=f"mod_chk_{m_item['id']}", label_visibility="collapsed", on_change=_toggle_mod, args=(i,))
                mc2.markdown(f"<div style='padding-top:6px; font-weight:bold; color:{TEXT_MAIN if m_item['show'] else TEXT_MUTED};'>第 {i+1} 順位：{m_item['name']}</div>", unsafe_allow_html=True)
                mc3.button("⬆️ 上移", key=f"mod_up_{m_item['id']}", disabled=(i == 0), use_container_width=True, on_click=_move_mod, args=(i, -1))
                mc4.button("⬇️ 下移", key=f"mod_dn_{m_item['id']}", disabled=(i == len(st.session_state.tab1_master_items) - 1), use_container_width=True, on_click=_move_mod, args=(i, 1))
            st.button("🔄 恢復預設順序與全部顯示", use_container_width=True, on_click=_reset_mod)

        eval_res = de.evaluate_three_pillars(tech, chip, BULL_COLOR, BEAR_COLOR, WARN_COLOR, tech_60m=tech_60m, tech_5m=tech_5m, margin_info=margin_info, fund_info=fund_info, taiex_info=taiex_quick, code_str=selected_code)
        st.subheader(f"📊 【{selected_code} {stock_name}】機構級四維度共振體檢 & 實戰總結論")
        st.markdown(f"<p style='font-size:{round(14*scale,1)}px; color:{TEXT_MUTED}; margin-top:-10px;'>📅 <b>最新有效交易日：{trade_date}</b> ｜ 最新價：<b>{close_price} 元</b>（單日 <b>{tech['chg_1d_pct']:+.2f}%</b> ／ Alpha <b>{eval_res['alpha_1d']:+.2f}%</b>） ｜ 市場：<b>{'上市' if market_hint=='TWSE' else '上櫃'}</b></p>", unsafe_allow_html=True)
        st.markdown(f"""<div class="score-banner"><div style="flex:1; min-width:240px;">
        <div style="font-size:{round(19*scale,1)}px; font-weight:bold; color:{eval_res['v_color']}; margin-bottom:8px;">{eval_res['verdict']}</div>
        <div style="font-size:{round(14.2*scale,1)}px; line-height:1.7; background:{SCORE_BOX_BG}; padding:10px 14px; border-radius:8px; border-left:4px solid {eval_res['v_color']};">{eval_res['v_desc_html']}</div></div>
        <div style="text-align:center; padding:12px 18px; background:{SCORE_BOX_BG}; border-radius:10px; border:1px solid {CARD_BORDER};">
        <div style="font-size:{round(12.5*scale,1)}px; color:{TEXT_MUTED};">機構量化總分</div>
        <div style="font-size:{round(32*scale,1)}px; font-weight:bold; color:{eval_res['v_color']};">{eval_res['total']}<span style="font-size:{round(14*scale,1)}px; color:{TEXT_SUB};"> / 100</span></div></div></div>""", unsafe_allow_html=True)

        with st.expander(f"🧮 查看【{stock_name} {eval_res['total']} / 100 分】4 大維度計分明細"):
            st.dataframe(pd.DataFrame(eval_res["breakdown"], columns=["評估維度", "本項得分", "客觀數據動態計分依據"]), use_container_width=True, hide_index=True)

        t_pct, m_pct, c_pct, f_pct = int((eval_res["t_score"]/25.0)*100), int((eval_res["m_score"]/25.0)*100), int((eval_res["c_score"]/30.0)*100), int((eval_res["f_score"]/20.0)*100)
        p_chip = chip["periods"]
        td_str = f"▲低九第 {td_b_cnt} 天" if td_b_cnt > 0 else (f"▼高九第 {td_s_cnt} 天" if td_s_cnt > 0 else "⚪ 無九轉")
        if fund_info.get("has_rev") and not selected_code.startswith("00"):
            rev_main = f"YoY {fund_info['yoy_latest']:+.1f}%"
            rev_sub = f"- <b>{fund_info['rev_month']} 加速度：</b><b>{fund_info['yoy_accel']:+.1f}%</b><br>- <b>外資持股：</b>{fund_info['foreign_hold_pct']}%"
        else:
            bias_etf = round(((close_price - ma20_price) / ma20_price) * 100.0, 2) if ma20_price > 0 else 0.0
            rev_main = f"融資 {margin_info['margin_bal']:,} 張" if margin_info["eligible"] else "🏦 ETF 模式"
            rev_sub = f"- <b>月線乖離：</b><b>{bias_etf:+.2f}%</b><br>- <b>融資單日：</b>{fmt_colored_num(margin_info['margin_chg'])}"

        st.markdown(f"""<div class="pillar-grid">
        <div class="pillar-card"><div class="pillar-title"><span>🛡️ 1. Alpha & 均線</span><span class="{'tag-bull' if eval_res['alpha_1d']>=0 else 'tag-bear'}">Alpha {eval_res['alpha_1d']:+.1f}%</span></div><div class="pillar-main">月線 {ma20_price} 元</div><div class="bar-bg"><div style="width:{t_pct}%; height:100%; background:{BULL_COLOR if t_pct>=60 else BEAR_COLOR};"></div></div><div class="pillar-sub">- <b>5日Alpha：</b>{eval_res['alpha_5d']:+.2f}%<br>- <b>20日扣抵：</b>{deduct_price} 元｜5MA {tech['ma5']}</div></div>
        <div class="pillar-card"><div class="pillar-title"><span>⚡ 2. 三週期動能</span><span class="{'tag-bull' if k_val>=d_val else 'tag-bear'}">{'KD金叉' if k_val>=d_val else 'KD死叉'}</span></div><div class="pillar-main">K：{k_val}｜D：{d_val}</div><div class="bar-bg"><div style="width:{m_pct}%; height:100%; background:{BULL_COLOR if m_pct>=60 else BEAR_COLOR};"></div></div><div class="pillar-sub">- <b>60/5分 20MA：</b>{tech_60m.get('ma20','-')}／{tech_5m.get('ma20','-')}<br>- <b>九轉：</b>{td_str}｜量比 {vol_ratio}倍</div></div>
        <div class="pillar-card"><div class="pillar-title"><span>💰 3. 法人 & 資券</span><span class="{'tag-bull' if eval_res['inst_vol_ratio']>0 else 'tag-bear'}">佔量 {eval_res['inst_vol_ratio']:+.1f}%</span></div><div class="pillar-main">5日 {fmt_colored_num(p_chip[5]['tot'])}</div><div class="bar-bg"><div style="width:{c_pct}%; height:100%; background:{BULL_COLOR if c_pct>=60 else BEAR_COLOR};"></div></div><div class="pillar-sub">- <b>1日/3日：</b>{fmt_colored_num(p_chip[1]['tot'])}／{fmt_colored_num(p_chip[3]['tot'])}<br>- <b>5日資增減：</b>{fmt_colored_num(margin_info['periods'][5]['m_chg'])}</div></div>
        <div class="pillar-card"><div class="pillar-title"><span>🚀 4. 營收 / 位階</span><span class="tag-neutral">基本面</span></div><div class="pillar-main">{rev_main}</div><div class="bar-bg"><div style="width:{f_pct}%; height:100%; background:#3498DB;"></div></div><div class="pillar-sub">{rev_sub}<br>- <b>10/20日法人：</b>{fmt_colored_num(p_chip[10]['tot'])}／{fmt_colored_num(p_chip[20]['tot'])}</div></div></div>""", unsafe_allow_html=True)

        for sec_item in [x["id"] for x in st.session_state.tab1_master_items if x["show"]]:
            if sec_item == "🕯️":
                mtf_res = de.evaluate_mtf_resonance(tech, tech_60m, tech_5m, cdp_vals, BULL_COLOR, BEAR_COLOR, WARN_COLOR)
                st.markdown(f"##### 🎯 【{selected_code} {stock_name}】日 K × 60 分 K × 5 分 K「三週期多空共振雷達」")
                st.markdown(f"""<div class="metric-card" style="border-left:5px solid {mtf_res['color']};"><div style="font-weight:bold; color:{mtf_res['color']};">{mtf_res['title']}</div><div>{mtf_res['desc']}</div></div>""", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(mtf_res["table"]), use_container_width=True, hide_index=True)
                c_k1, c_k2, c_k3 = st.columns(3)
                s_bb, s_td, s_cdp = c_k1.checkbox("🟣 布林通道", True, key="s_bb"), c_k2.checkbox("🔢 神奇九轉", True, key="s_td"), c_k3.checkbox("📐 AH/NH/NL/AL 四價位線", True, key="s_cdp")
                kt1, kt2, kt3 = st.tabs(["📅 1. 日 K 實戰圖", "⏱️ 2. 60 分 K 波段圖", "⚡ 3. 5 分 K 當沖圖"])
                with kt1: st.plotly_chart(plot_universal_kline_chart(tech["kline_60"], scale, s_bb, s_td, s_cdp, cdp_vals, False), use_container_width=True, theme=None)
                with kt2:
                    if tech_60m["ok"]: st.plotly_chart(plot_universal_kline_chart(tech_60m["records"], scale, s_bb, s_td, s_cdp, cdp_vals, True), use_container_width=True, theme=None)
                with kt3:
                    if tech_5m["ok"]: st.plotly_chart(plot_universal_kline_chart(tech_5m["records"], scale, s_bb, s_td, s_cdp, cdp_vals, True), use_container_width=True, theme=None)
            elif sec_item == "📊":
                bt1, bt2 = st.tabs(["📊 三大法人買賣超直方圖", "📊 融資融券增減 & 券資比"])
                with bt1:
                    if chip["ok"] and chip["daily_table"]: st.plotly_chart(plot_20d_chip_bar_chart(chip["daily_table"], scale), use_container_width=True, theme=None)
                with bt2:
                    if margin_info["ok"] and margin_info["daily_table"]: st.plotly_chart(plot_20d_margin_bar_chart(margin_info["daily_table"], scale), use_container_width=True, theme=None)
            elif sec_item == "📋":
                tbl1, tbl2, tbl3 = st.tabs(["🎯 1. 五週期累計矩陣", "📋 2. 法人逐日明細", "📋 3. 資券逐日明細"])
                with tbl1:
                    p_mg = margin_info["periods"]
                    m_rows = [{"籌碼主體": lbl, **{f"近 {w} 日": p_chip[w][k] for w in [1, 3, 5, 10, 20]}} for lbl, k in [("🌍 外資 (張)", "f"), ("🏦 投信 (張)", "t"), ("🏢 自營商 (張)", "d"), ("💰 法人合計 (張)", "tot")]]
                    if margin_info["ok"] and margin_info["eligible"]:
                        m_rows.extend([{"籌碼主體": "📈 融資增減 (張)", **{f"近 {w} 日": p_mg[w]["m_chg"] for w in [1, 3, 5, 10, 20]}}, {"籌碼主體": "📉 融券增減 (張)", **{f"近 {w} 日": p_mg[w]["s_chg"] for w in [1, 3, 5, 10, 20]}}])
                    p_cols = ["近 1 日", "近 3 日", "近 5 日", "近 10 日", "近 20 日"]
                    st.dataframe(pd.DataFrame(m_rows).style.map(style_signed_numbers, subset=p_cols).format({c: "{:+,}" for c in p_cols}), use_container_width=True, hide_index=True)
                with tbl2:
                    if chip["ok"] and chip["daily_table"]:
                        nc = ["外資買賣超(張)", "投信買賣超(張)", "自營商買賣超(張)", "三大法人合計(張)"]
                        st.dataframe(pd.DataFrame(chip["daily_table"]).style.map(style_signed_numbers, subset=nc).format({c: "{:+,}" for c in nc}), use_container_width=True, hide_index=True)
                with tbl3:
                    if margin_info["ok"] and margin_info["daily_table"]:
                        st.dataframe(pd.DataFrame(margin_info["daily_table"]).style.map(style_signed_numbers, subset=["融資增減(張)", "融券增減(張)"]), use_container_width=True, hide_index=True)
            elif sec_item == "📰":
                with st.container(border=True):
                    st.markdown("📰 **近期市場消息與催化劑雷達：**")
                    if news_data["news"]:
                        for n in news_data["news"]:
                            st.markdown(f"""<div class="news-card"><span style="background:#2D3748; color:#63B3ED; padding:2px 6px; border-radius:4px; font-size:12px; margin-right:6px;">{n['tag']}</span><span style="color:{TEXT_MUTED}; font-size:12px; margin-right:8px;">🕒 {n['ago']}</span><a href="{n['link']}" target="_blank" style="color:{TEXT_MAIN}; text-decoration:none;">{n['title']}</a></div>""", unsafe_allow_html=True)
                    else: st.caption("近期無重大個股新聞。")
            elif sec_item == "📐":
                st.markdown(f"""<div class="metric-card"><h4>📐 下個交易日【{stock_name} AH / NH / NL / AL 當沖支撐壓力四價位】</h4>
                - 🔥 <b>壓力區間：</b>常態反彈壓力 <b>NH {cdp_vals['NH']} 元</b> ｜ 極端突破壓力 <b>AH {cdp_vals['AH']} 元</b><br>
                - 🛡️ <b>支撐區間：</b>常態回檔支撐 <b>NL {cdp_vals['NL']} 元</b> ｜ 極端破底支撐 <b>AL {cdp_vals['AL']} 元</b></div>""", unsafe_allow_html=True)

        render_cta_box(f"💬 想索取【{selected_code} {stock_name}】主力分點籌碼或討論策略嗎？", "💬 點此私訊專屬營業員諮詢", cfg["broker_line_url"])

elif cur_tab == 2:
    if check_tab_password_gate(2, "unlocked_tab2", cfg.get("lock_tab2", False), cfg.get("pwd_tab2", "TICK888"), "現沖與隔日沖獲利價位試算室", "請輸入通行碼解鎖。", cfg["broker_line_url"]):
        render_fast_profit_calculator(cfg["broker_line_url"], is_public_promo)

elif cur_tab == 3:
    if check_tab_password_gate(3, "unlocked_tab4", cfg.get("lock_tab4", False), cfg.get("pwd_tab4", "VIP888"), "大盤期現貨風向與主流族群雷達", "請輸入 VIP 通行碼解鎖。", cfg["broker_line_url"]):
        tb4_c1, tb4_c2 = st.columns([7.5, 2.5])
        tb4_c1.subheader("🚦 台股大盤資金風向球 & 實戰總結論")
        if tb4_c2.button("🔄 重新掃描族群與大盤", use_container_width=True):
            for fn in (de.fetch_taiex_market_data, de._fetch_twse_official_taiex_kline, de.auto_sync_market_chips_cached, de.fetch_full_market_snapshot_and_breadth, de.fetch_all_stock_industry_map, de.scan_sector_performance):
                try: fn.clear()
                except Exception: pass
            st.rerun()

        cfg = de.auto_sync_market_chips_cached(fm_token_str)
        taiex = de.fetch_taiex_market_data()
        breadth_fg = de.fetch_full_market_snapshot_and_breadth(cfg.get("cnn_fear_greed", 34))
        if taiex["ok"]:
            mkt_eval = de.evaluate_taiex_market_score(taiex, cfg, breadth_fg, taiex.get("macro"), BULL_COLOR, BEAR_COLOR, WARN_COLOR)
            macro, mkt_cdp = mkt_eval["macro"], de.calculate_cdp(taiex["high"], taiex["low"], taiex["close"])
            st.markdown(f"<p style='font-size:{round(14*scale,1)}px; color:{TEXT_MUTED};'>📅 <b>交易日：{taiex['date']}</b> ｜ 加權指數：<b>{taiex['close']:,} 點</b>（<b>{taiex['chg']:+} 點</b>） ｜ 💵 台幣：<b>{macro['fx_rate']}</b> ｜ 🌎 費半：<b>{macro['sox_chg_1d_pct']:+.2f}%</b>（<b>r={macro['sox_corr_20d']}</b>）</p>", unsafe_allow_html=True)
            st.markdown(f"""<div class="score-banner"><div style="flex:1; min-width:240px;">
            <div style="font-size:{round(19*scale,1)}px; font-weight:bold; color:{mkt_eval['color']}; margin-bottom:8px;">{mkt_eval['light']}</div>
            <div style="font-size:{round(14.2*scale,1)}px; line-height:1.7; background:{SCORE_BOX_BG}; padding:10px 14px; border-radius:8px; border-left:4px solid {mkt_eval['color']};">{mkt_eval['summary_action_html']}</div></div>
            <div style="text-align:center; padding:12px 18px; background:{SCORE_BOX_BG}; border-radius:10px; border:1px solid {CARD_BORDER};">
            <div style="font-size:{round(12.5*scale,1)}px; color:{TEXT_MUTED};">大盤風向分</div>
            <div style="font-size:{round(32*scale,1)}px; font-weight:bold; color:{mkt_eval['color']};">{mkt_eval['total']}<span style="font-size:{round(14*scale,1)}px; color:{TEXT_SUB};"> / 100</span></div></div></div>""", unsafe_allow_html=True)
            st.plotly_chart(plot_universal_kline_chart(taiex["kline_60"], scale, True, True, True, mkt_cdp, False), use_container_width=True, theme=None)

            sector_rank = de.scan_sector_performance(json.dumps(sector_map_all, ensure_ascii=False), margins_global_map)
            if sector_rank:
                st.markdown(f"#### 🔥 台股主流族群「證交所 28 大細分產業動態活水」強弱總覽（共 {len(sector_rank)} 大族群）")
                df_sec_ov = pd.DataFrame([{"主流族群分類": s["族群名稱"], "成分股數": s.get("成分股數", ""), "近1日平均漲跌(%)": s["近1日平均漲跌(%)"], "近5日平均漲跌(%)": s["近5日平均漲跌(%)"], "領漲指標股 (🔥動態入榜)": s.get("近5日領漲指標股", "")} for s in sector_rank])
                st.dataframe(df_sec_ov.style.map(style_signed_numbers, subset=["近1日平均漲跌(%)", "近5日平均漲跌(%)"]).format({"近1日平均漲跌(%)": "{:+.2f}%", "近5日平均漲跌(%)": "{:+.2f}%"}), use_container_width=True, hide_index=True, height=390)
                sec_opts = [f"👉 {s['族群名稱']} （近1日 {s['近1日平均漲跌(%)']:+.2f}% ｜ 近5日 {s['近5日平均漲跌(%)']:+.2f}%）" for s in sector_rank]
                chosen_sec = sector_rank[sec_opts.index(st.selectbox("🔎 選擇展開查看成分股之主流族群：", sec_opts))]
                df_stk = pd.DataFrame([{k: v for k, v in it.items() if not str(k).startswith("_")} for it in chosen_sec["stocks"]])
                st.dataframe(df_stk.style.map(style_signed_numbers, subset=["近1日漲跌(%)", "近5日漲跌(%)"]).format({"最新收盤(元)": "{:.2f}", "月線(20MA)": "{:.2f}", "近1日漲跌(%)": "{:+.2f}%", "近5日漲跌(%)": "{:+.2f}%"}), use_container_width=True, hide_index=True)
                stk_list = chosen_sec["stocks"]
                b_cols = st.columns(min(4, max(1, len(stk_list))))
                for idx_s, s_it in enumerate(stk_list):
                    b_cols[idx_s % len(b_cols)].button(f"🔍 {s_it['代號']} {s_it['名稱']} ({s_it['近1日漲跌(%)']:+.1f}%)", key=f"sb_{chosen_sec['族群名稱']}_{s_it['代號']}", use_container_width=True, on_click=jump_to_tab1_with_stock, args=(s_it["代號"], s_it["名稱"], s_it.get("_mkt", "TWSE")))
            render_cta_box(mkt_eval["cta_title"], mkt_eval["cta_btn"], cfg["broker_line_url"])

@st.fragment
def render_floating_ai_assistant(active_code, active_name, cfg_obj, quotes_df):
    with st.popover("🤖 AI 戰情助手"):
        hd_c1, hd_c2 = st.columns([7.2, 2.8])
        hd_c1.markdown("#### 🤖 隨身 AI 短線戰情助手")
        if hd_c2.button("🗑️清空", key="btn_clr_ai_chat", use_container_width=True):
            st.session_state.ai_chat_history = [dict(DEFAULT_STATES["ai_chat_history"][0])]; st.rerun()

        api_k = str(cfg_obj.get("gemini_api_key", "")).strip()
        k_status = f"🟢 已載入 Gemini 金鑰 (**{api_k[:5]}...**)" if api_k else "⚪ 未設定金鑰 (使用內建歸因引擎)"
        st.caption(f"主畫面：**{active_code} {active_name}** ｜ 狀態：{k_status}")

        q_col1, q_col2 = st.columns(2)
        quick_q = None
        if q_col1.button(f"📊 診斷 {active_code} {active_name}", use_container_width=True): quick_q = f"請幫我深度分析 {active_code} {active_name} 近期強弱原因、籌碼結構與明日當沖四價位策略"
        if q_col2.button("🛡️ 大盤匯率費半與總結", use_container_width=True): quick_q = "請告訴我今日大盤5維度評分、匯率費半連動與實戰操作總結論"

        with st.container(height=310, border=True):
            for idx_m, msg in enumerate(st.session_state.ai_chat_history[-8:]):
                with st.chat_message(msg["role"]):
                    st.markdown(str(msg["content"]).replace("`", "**"))
                    btn_c, btn_n, btn_m = msg.get("stock_code"), msg.get("stock_name", ""), msg.get("stock_mkt", "TWSE")
                    if btn_c:
                        on_t1 = (int(st.session_state.active_nav_tab) == 1) and (str(btn_c) == str(st.session_state.target_stock_code))
                        lbl = f"✅ 分頁1已顯示【{btn_c} {btn_n}】(點此收合看圖)" if on_t1 else f"🚀 點此收合小助手並跳轉【分頁1：{btn_c} {btn_n}】K線圖 ➔"
                        if st.button(lbl, key=f"ai_jmp_{idx_m}_{btn_c}", use_container_width=True, type="primary" if not on_t1 else "secondary"):
                            jump_to_tab1_with_stock(btn_c, btn_n, btn_m); st.rerun(scope="app")

        user_in = st.chat_input("問問題(如：為什麼00877這麼弱？怎麼看3167？)...")
        final_q = quick_q or user_in
        if final_q:
            st.session_state.ai_chat_history.append({"role": "user", "content": final_q})
            target_c, target_n = active_code, active_name
            m_code = re.search(r"(?<![0-9A-Za-z])(00\d{2,4}[A-Za-z]?|\d{4})(?![0-9A-Za-z])", final_q.upper())
            if m_code:
                target_c = m_code.group(1).upper()
                target_n = code_to_name_map.get(target_c, master_stock_dict.get(target_c, {}).get("名稱", target_c))
            else:
                for s_name in sorted(name_to_code_map.keys(), key=len, reverse=True):
                    if len(s_name) >= 2 and s_name in final_q: target_c, target_n = name_to_code_map[s_name], s_name; break

            if not m_code and any(k in final_q for k in ["大盤", "加權", "台指", "止跌", "匯率", "費半"]):
                tx, bfg = de.fetch_taiex_market_data(), de.fetch_full_market_snapshot_and_breadth(cfg_obj.get("cnn_fear_greed", 34))
                if tx["ok"]:
                    m_ev = de.evaluate_taiex_market_score(tx, cfg_obj, bfg, tx.get("macro"), BULL_COLOR, BEAR_COLOR, WARN_COLOR)
                    mc, m_cdp = m_ev["macro"], de.calculate_cdp(tx["high"], tx["low"], tx["close"])
                    reply_txt = f"🛡️ **【台股大盤 5 維度快篩（{tx['date']}｜總分 {m_ev['total']}/100）】**\n- **燈號**：**{m_ev['light']}**\n- **指數**：**{tx['close']:,} 點**（單日 **{tx['chg']:+}**）｜台幣 **{mc['fx_rate']}**｜費半 **{mc['sox_chg_1d_pct']:+.2f}%**\n- **明日四價位**：壓力 **NH {m_cdp['NH']:,} ／ AH {m_cdp['AH']:,}** ｜ 支撐 **NL {m_cdp['NL']:,} ／ AL {m_cdp['AL']:,}**\n\n{m_ev['summary_action']}"
                else: reply_txt = "暫時無法取得大盤資料。"
                st.session_state.ai_chat_history.append({"role": "assistant", "content": reply_txt})
            else:
                t_mkt = code_to_mkt_map.get(target_c, master_stock_dict.get(target_c, {}).get("市場", "TPEX" if target_c.endswith("B") else "TWSE"))
                t_d = de.fetch_technical_indicators(target_c, t_mkt)
                t_60, t_5 = de.fetch_intraday_kline_full(target_c, t_mkt, "60m"), de.fetch_intraday_kline_full(target_c, t_mkt, "5m")
                c_d = de.fetch_chip_data_20d(target_c, fm_token_str)
                m_d = de.fetch_margin_short_20d(target_c, fm_token_str)
                f_d = de.fetch_fundamental_revenue_and_shareholding(target_c, fm_token_str)
                tx_q = de.fetch_taiex_market_data()
                if t_d["ok"]:
                    if target_n == target_c:
                        snap_m = de.fetch_full_market_snapshot_and_breadth().get("market_snap", {})
                        if target_c in snap_m: target_n = snap_m[target_c]["name"]
                    n_d = de.fetch_stock_news(target_c, target_n).get("news", [])
                    ev = de.evaluate_three_pillars(t_d, c_d, BULL_COLOR, BEAR_COLOR, WARN_COLOR, tech_60m=t_60, tech_5m=t_5, margin_info=m_d, fund_info=f_d, taiex_info=tx_q, code_str=target_c)
                    cdp_v, p_c = de.calculate_cdp(t_d["high"], t_d["low"], t_d["close"]), c_d["periods"]
                    mtf_r = de.evaluate_mtf_resonance(t_d, t_60, t_5, cdp_v, BULL_COLOR, BEAR_COLOR, WARN_COLOR)
                    smart_reasons_txt = de.build_smart_diagnostic_reasons(target_c, target_n, t_d, c_d, m_d, f_d, ev, n_d)

                    reply_txt, g_err = "", ""
                    if api_k:
                        news_titles = "；".join([x["title"] for x in n_d]) if n_d else "近期無特定重大新聞"
                        sys_ctx = (
                            f"你是專業台股實戰分析師AI助手。用戶提問：「{final_q}」（鎖定標的：【{target_c} {target_n}】）。\n"
                            f"請根據以下真實數據直接回答用戶問題（分析走弱或走強原因、主力與散戶融資動向、明日觀察點）：\n"
                            f"- 日期：{t_d['date']}，現價：{t_d['close']}元（單日 {t_d['chg_1d_pct']:+.2f}%，5日 {t_d['chg_5d_pct']:+.2f}%），5MA={t_d['ma5']}、20MA={t_d['ma20']}、20日扣抵={t_d['deduct']}\n"
                            f"- 評分：{ev['total']}/100（單日Alpha {ev['alpha_1d']:+.2f}%，5日法人佔量 {ev['inst_vol_ratio']:+.1f}%），三大法人1日 {p_c[1]['tot']:+,}張、5日 {p_c[5]['tot']:+,}張；5日融資增減 {m_d['periods'][5]['m_chg']:+,}張\n"
                            f"- 三週期：{mtf_r['title']}｜系統歸因：{smart_reasons_txt}｜近期新聞：{news_titles}\n"
                            f"- 明日四價位：極端突破AH={cdp_v['AH']}、常態壓力NH={cdp_v['NH']}、常態支撐NL={cdp_v['NL']}、極端破底AL={cdp_v['AL']}（勿提CDP中軸）。\n"
                            f"請用犀利白話直接給結論、原因剖析與四價位操作應對（嚴禁使用反引號 `，改用粗體 **）。"
                        )
                        g_txt, g_err = de.call_gemini_generate_content(sys_ctx, api_k)
                        if g_txt: reply_txt = f"✨ **【Gemini 2.5 Flash 深度實戰分析：{target_c} {target_n}】**\n\n" + g_txt

                    if not reply_txt:
                        err_note = f"\n\n⚠️ *(Gemini API 呼叫未通過：{g_err}；標準 Gemini 金鑰應為 AIzaSy 開頭，目前已自動由內建智慧歸因引擎為您解答)*" if (api_k and g_err) else ""
                        reply_txt = (
                            f"🔍 **【{target_c} {target_n} 機構四維度快篩（{t_d['date']} 現價 {t_d['close']} 元｜單日 {t_d['chg_1d_pct']:+.2f}% ／ 5日 {t_d['chg_5d_pct']:+.2f}%）】**\n"
                            f"- **機構總分**：**{ev['total']} / 100 分**｜**三週期**：**{mtf_r['title']}**\n\n"
                            f"{smart_reasons_txt}\n\n"
                            f"📐 **【明日當沖四價位與操作應對】**：\n"
                            f"- 🔥 **壓力**：**NH {cdp_v['NH']} 元** ／ **AH {cdp_v['AH']} 元** ｜ 🛡️ **支撐**：**NL {cdp_v['NL']} 元** ／ **AL {cdp_v['AL']} 元**\n\n"
                            f"{ev['v_desc']}{err_note}"
                        )
                    st.session_state.ai_chat_history.append({"role": "assistant", "content": reply_txt, "stock_code": target_c, "stock_name": target_n, "stock_mkt": t_mkt})
                else:
                    st.session_state.ai_chat_history.append({"role": "assistant", "content": f"查無 {target_c} 的即時資料。"})
            st.rerun()

render_floating_ai_assistant(current_active_code, current_active_name, cfg, df_quotes)
st.markdown("""<div class="disclaimer"><b>⚠️ 合規與免責聲明：</b>本頁面資訊皆由公開歷史數據經固定數學公式（AH/NH/NL/AL 四價位、均線、布林、TD九轉、KD/MACD/RSI）自動產出，僅供統計檢索與成本試算參考，絕不構成買賣建議。</div>""", unsafe_allow_html=True)
