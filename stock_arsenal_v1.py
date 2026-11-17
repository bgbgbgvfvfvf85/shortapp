# 檔案名稱：stock_arsenal_v1.py (v12.1 完美跳轉版：點擊切換按鈕自動收合小助手 + 強制跨分頁跳轉分頁1 + 100%保留對話紀錄)
import os, re, json, requests, importlib
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
    "ai_chat_history": [{"role": "assistant", "content": "您好！我是戰情室 AI 助手 🤖。請點選上方快捷按鈕，或直接輸入任何**個股代號（如 3167、6214）**、**ETF 代號（如 0050、00878、00937B）**或**大盤問題**，我會立即調出官方真實數據為您統整實戰結論與 AH/NH/NL/AL 四價位！"}]
}
for k, v in DEFAULT_STATES.items():
    st.session_state.setdefault(k, v)

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
card_min_width = "245px" if scale >= 1.15 else "210px"

st.markdown(f"""<style>
.stApp {{ background-color: {BG_MAIN} !important; color: {TEXT_MAIN} !important; }}
.block-container {{ max-width: 1260px !important; padding: 3.4rem 2rem 5rem 2rem !important; }}
section[data-testid="stSidebar"] {{ background-color: {BG_SIDEBAR} !important; color: {TEXT_MAIN} !important; }}
h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, [data-testid="stCaptionContainer"] {{ color: {TEXT_MAIN} !important; }}
.stButton > button {{ background-color: {CARD_BG} !important; color: {TEXT_MAIN} !important; border: 1px solid {CARD_BORDER} !important; font-weight: bold !important; white-space: normal !important; word-break: break-word !important; line-height: 1.35 !important; padding: 0.45rem 0.7rem !important; min-height: 2.45rem !important; }}
.stButton > button:hover {{ border-color: #4A90E2 !important; color: #60A5FA !important; }}
.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: #FFFFFF !important; border: 1.5px solid #60A5FA !important; }}
div[data-testid="stPopover"] {{ position: fixed !important; bottom: 24px !important; right: 26px !important; z-index: 999999 !important; width: auto !important; }}
div[data-testid="stPopover"] > div > button, div[data-testid="stPopover"] > button {{ background: linear-gradient(135deg, #00D26A 0%, #009E4F 100%) !important; color: #000000 !important; border-radius: 50px !important; padding: 11px 20px !important; font-size: 15.5px !important; font-weight: 800 !important; border: 2px solid #FFFFFF !important; box-shadow: 0 6px 20px rgba(0, 210, 106, 0.55) !important; white-space: nowrap !important; }}
div[data-testid="stPopover"] > div > button *, div[data-testid="stPopover"] > button * {{ color: #000000 !important; font-weight: 800 !important; }}
div[data-baseweb="popover"] > div, div[data-testid="stPopoverBody"] {{ background-color: {CARD_BG} !important; color: {TEXT_MAIN} !important; border: 1.5px solid #4A90E2 !important; border-radius: 14px !important; }}
div[data-testid="stPopoverBody"] h1, div[data-testid="stPopoverBody"] h2, div[data-testid="stPopoverBody"] h3, div[data-testid="stPopoverBody"] h4, div[data-testid="stPopoverBody"] p, div[data-testid="stPopoverBody"] span, div[data-testid="stPopoverBody"] li, div[data-testid="stPopoverBody"] strong, div[data-testid="stPopoverBody"] b, div[data-testid="stPopoverBody"] div[data-testid="stCaptionContainer"] {{ color: {TEXT_MAIN} !important; }}
div[data-testid="stPopoverBody"] code, .stMarkdown code {{ background-color: rgba(59, 130, 246, 0.18) !important; color: #38BDF8 !important; padding: 2px 6px !important; border-radius: 4px !important; font-weight: bold !important; }}
div[data-testid="stPopoverBody"] .stButton > button {{ background-color: {BG_MAIN} !important; color: {TEXT_MAIN} !important; border: 1px solid #4A90E2 !important; border-radius: 8px !important; }}
div[data-testid="stPopoverBody"] .stButton > button * {{ color: {TEXT_MAIN} !important; }}
div[data-testid="stPopoverBody"] .stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: #FFFFFF !important; border: 1.5px solid #60A5FA !important; }}
div[data-testid="stPopoverBody"] .stButton > button[kind="primary"] * {{ color: #FFFFFF !important; }}
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlockBorderWrapper"] {{ background-color: {BG_MAIN} !important; border-color: {CARD_BORDER} !important; }}
div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] {{ background-color: {CARD_BG_ALT} !important; border: 1px solid {CARD_BORDER} !important; border-radius: 8px !important; padding: 8px 10px !important; margin-bottom: 6px !important; }}
div[data-testid="stPopoverBody"] [data-testid="stChatInput"] > div {{ background-color: {BG_MAIN} !important; border: 1px solid {CARD_BORDER} !important; }}
div[data-testid="stPopoverBody"] textarea {{ color: {TEXT_MAIN} !important; -webkit-text-fill-color: {TEXT_MAIN} !important; caret-color: {TEXT_MAIN} !important; }}
@media (max-width: 768px) {{
    .block-container {{ padding: 2.2rem 0.65rem 5.5rem 0.65rem !important; }}
    div[data-testid="stPopover"] {{ bottom: 68px !important; right: 12px !important; }}
    div[data-testid="stPopover"] > div > button, div[data-testid="stPopover"] > button {{ padding: 8px 14px !important; font-size: 13.5px !important; }}
}}
div[data-baseweb="tab-list"] {{ display: flex !important; flex-wrap: wrap !important; gap: 6px !important; }}
button[data-baseweb="tab"] {{ white-space: nowrap !important; padding: 0 12px !important; }}
button[data-baseweb="tab"] p {{ color: {TEXT_MAIN} !important; font-weight: bold !important; font-size: {round(14 * scale, 1)}px !important; white-space: nowrap !important; }}
.app-main-title {{ font-size: {round(21.5 * scale, 1)}px; font-weight: 800; color: {TEXT_MAIN}; line-height: 1.4; padding: 4px 0; margin: 0; }}
.score-banner {{ background: {BANNER_BG}; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; border: 1px solid #4A90E2; color: {TEXT_MAIN}; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; box-sizing: border-box; }}
.pillar-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax({card_min_width}, 1fr)); gap: 12px; margin-bottom: 16px; }}
.pillar-card {{ background-color: {CARD_BG}; border-radius: 12px; padding: 14px 15px; border: 1px solid {CARD_BORDER}; color: {TEXT_MAIN}; box-sizing: border-box; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
.pillar-title {{ font-size: {round(13.5 * scale, 1)}px; color: {TEXT_MUTED}; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; font-weight: 600; }}
.pillar-main {{ font-size: {round(18.5 * scale, 1)}px; font-weight: bold; margin-bottom: 8px; color: {TEXT_MAIN}; word-break: break-word; }}
.bar-bg {{ background-color: {CARD_BORDER}; border-radius: 6px; height: 7px; width: 100%; margin-bottom: 10px; overflow: hidden; }}
.pillar-sub {{ font-size: {round(13.5 * scale, 1)}px; color: {TEXT_SUB}; line-height: 1.65; }}
.tag-bull {{ background-color: rgba(231, 76, 60, 0.15); color: {BULL_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {BULL_COLOR}; white-space: nowrap; }}
.tag-bear {{ background-color: rgba(46, 204, 113, 0.15); color: {BEAR_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {BEAR_COLOR}; white-space: nowrap; }}
.tag-neutral {{ background-color: rgba(241, 196, 15, 0.15); color: {WARN_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {WARN_COLOR}; white-space: nowrap; }}
.metric-card {{ background-color: {CARD_BG_ALT}; border-radius: 10px; padding: 16px; margin-bottom: 12px; border: 1px solid {CARD_BORDER}; border-left: 5px solid #00D26A; color: {TEXT_MAIN}; font-size: {round(15 * scale, 1)}px; line-height: 1.65; }}
.news-card {{ background-color: {NEWS_BG}; border-radius: 8px; padding: 11px 14px; margin-bottom: 8px; border-left: 3px solid #4A90E2; font-size: {round(14.5 * scale, 1)}px; line-height: 1.5; color: {TEXT_MAIN}; }}
.cta-box {{ background: {BANNER_BG}; border-radius: 12px; padding: 18px; text-align: center; margin-top: 20px; border: 1px solid #4A90E2; color: {TEXT_MAIN}; }}
.disclaimer {{ font-size: {round(12.5 * scale, 1)}px; color: {TEXT_MUTED}; margin-top: 25px; line-height: 1.6; }}
</style>""", unsafe_allow_html=True)

components.html(f"""<script>
(function() {{
    const parentDoc = window.parent.document;
    function injectCSS(doc) {{
        if (!doc || doc.getElementById('plotly-hover-offset-v91')) return;
        const s = doc.createElement('style'); s.id = 'plotly-hover-offset-v91';
        s.innerHTML = `g.hoverlayer g.hovertext > path, g.hoverlayer g.hovertext > rect, g.hoverlayer g.hovertext > text {{ transform: translate(68px, -10px) !important; }} g.hoverlayer g.hovertext {{ opacity: 0.90 !important; pointer-events: none !important; }}`;
        doc.head.appendChild(s);
    }}
    injectCSS(parentDoc);
    setInterval(() => {{ injectCSS(parentDoc); parentDoc.querySelectorAll('iframe').forEach(ifr => {{ try {{ if (ifr.contentDocument) injectCSS(ifr.contentDocument); }} catch (e) {{}} }}); }}, 800);

    // 【v12.1 關鍵機制】當觸發跨頁跳轉時 (close_popover_seq 遞增)，自動收合展開中的小助手 Popover 並捲回頂部！
    const closeSeq = {int(st.session_state.get("close_popover_seq", 0))};
    if (closeSeq > 0 && window.parent._lastClosePopoverSeq !== closeSeq) {{
        window.parent._lastClosePopoverSeq = closeSeq;
        setTimeout(() => {{
            const popBtn = parentDoc.querySelector('div[data-testid="stPopover"] button[aria-expanded="true"]');
            if (popBtn) {{ popBtn.click(); }}
            else {{
                parentDoc.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true }}));
            }}
            window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}, 60);
    }}
}})();
</script>""", height=0, width=0)

top_c1, top_c2 = st.columns([6.8, 3.2])
with top_c1:
    st.markdown('<div class="app-main-title">⚡ 個股衍生武器庫 & 短線當沖戰情室</div>', unsafe_allow_html=True)
with top_c2:
    with st.expander("⚙️ 顯示設定（切換深淺色 ／ 字體大小）"):
        btn_t, btn_c1, btn_c2 = st.columns(3)
        btn_t.button("☀️淺色" if is_dark else "🌙深色", use_container_width=True, on_click=toggle_theme)
        btn_c1.button("➖縮小字", use_container_width=True, on_click=dec_font)
        btn_c2.button(f"➕放大({int(round(scale*100))}%)", use_container_width=True, on_click=inc_font)

# ==========================================
# 2. 視覺化圖表引擎 (支援 AH / NH / NL / AL 四價位疊加)
# ==========================================
def style_signed_numbers(val):
    try:
        v = float(val)
        if v > 0: return f"color: {BULL_COLOR}; font-weight: bold; background-color: rgba(255, 75, 75, 0.12);"
        elif v < 0: return f"color: {BEAR_COLOR}; font-weight: bold; background-color: rgba(46, 204, 113, 0.12);"
    except Exception: pass
    return f"color: {TEXT_SUB};"

def fmt_colored_num(val, unit="張", is_float=False):
    color = BULL_COLOR if val > 0 else (BEAR_COLOR if val < 0 else TEXT_SUB)
    return f"<span style='color:{color}; font-weight:bold;'>{(f'{val:+,.2f}' if is_float else f'{int(val):+,}')} {unit}</span>"

def render_cta_box(title_txt, btn_txt, line_url):
    st.markdown(f"""<div class="cta-box"><p style="font-size:{round(16 * scale, 1)}px; margin-bottom:12px; font-weight:bold; color:{TEXT_MAIN};">{title_txt}</p>
    <a href="{line_url}" target="_blank" style="background-color:#00D26A; color:#000000; padding:10px 20px; border-radius:8px; font-weight:bold; font-size:{round(15 * scale, 1)}px; text-decoration:none; display:inline-block;">{btn_txt}</a></div>""", unsafe_allow_html=True)

def plot_universal_kline_chart(kline_records, scale_factor=1.05, show_bb=True, show_td=True, show_cdp=True, cdp_vals=None, show_volume=False):
    df_k = pd.DataFrame(kline_records)
    x_col = "ShortDate" if "ShortDate" in df_k.columns else ("TimeStr" if "TimeStr" in df_k.columns else "DateStr")
    if x_col not in df_k.columns:
        df_k["ShortDate"] = df_k["DateStr"].astype(str).str.slice(5)
        x_col = "ShortDate"

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.74, 0.26]) if (show_volume and "Volume" in df_k.columns) else make_subplots(rows=1, cols=1)
    fig.add_trace(go.Candlestick(x=df_k[x_col], open=df_k["Open"], high=df_k["High"], low=df_k["Low"], close=df_k["Close"], increasing_line_color="#FF4B4B", increasing_fillcolor="#FF4B4B", decreasing_line_color="#00D26A", decreasing_fillcolor="#00D26A", name="K線"), row=1, col=1)

    for col, name, clr, w, dsh in [("MA5", "5MA", "#3498DB", 1.4, None), ("MA20", "20MA", "#F59E0B", 2.2, None), ("MA60", "60MA", "#9B59B6", 1.5, "dot")]:
        if col in df_k.columns:
            fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k[col], mode="lines", name=name, line=dict(color=clr, width=w, dash=dsh), hovertemplate="%{y:,.2f}"), row=1, col=1)

    if show_bb and "BB_Upper" in df_k.columns and "BB_Lower" in df_k.columns:
        fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k["BB_Upper"], mode="lines", name="布林上軌", line=dict(color="rgba(52, 152, 219, 0.65)", width=1.3, dash="dash"), hovertemplate="%{y:,.2f}"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k["BB_Lower"], mode="lines", name="布林下軌", line=dict(color="rgba(46, 204, 113, 0.75)", width=1.5, dash="dash"), fill="tonexty", fillcolor="rgba(52, 152, 219, 0.05)", hovertemplate="%{y:,.2f}"), row=1, col=1)

    b_col, s_col = ("TD_Buy_Disp" if "TD_Buy_Disp" in df_k.columns else "TD_Buy"), ("TD_Sell_Disp" if "TD_Sell_Disp" in df_k.columns else "TD_Sell")
    if show_td and b_col in df_k.columns and s_col in df_k.columns:
        for _, r_row in df_k.iterrows():
            b_val, s_val = int(r_row.get(b_col, 0)), int(r_row.get(s_col, 0))
            if b_val == 9: fig.add_annotation(x=r_row[x_col], y=float(r_row["Low"]), text="<b>▲低9</b>", showarrow=False, yshift=-15, font=dict(color="#00D26A", size=int(11 * scale_factor)), bgcolor="rgba(0, 210, 106, 0.16)", bordercolor="#00D26A", borderwidth=1, borderpad=2, row=1, col=1)
            elif 1 <= b_val <= 8: fig.add_annotation(x=r_row[x_col], y=float(r_row["Low"]), text=f"<b>{b_val}</b>", showarrow=False, yshift=-11, font=dict(color="#00D26A", size=int(9.5 * scale_factor)), row=1, col=1)
            if s_val == 9: fig.add_annotation(x=r_row[x_col], y=float(r_row["High"]), text="<b>▼高9</b>", showarrow=False, yshift=15, font=dict(color="#FF4B4B", size=int(11 * scale_factor)), bgcolor="rgba(255, 75, 75, 0.16)", bordercolor="#FF4B4B", borderwidth=1, borderpad=2, row=1, col=1)
            elif 1 <= s_val <= 8: fig.add_annotation(x=r_row[x_col], y=float(r_row["High"]), text=f"<b>{s_val}</b>", showarrow=False, yshift=11, font=dict(color="#FF4B4B", size=int(9.5 * scale_factor)), row=1, col=1)

    if len(df_k) >= 20:
        ded_row, star_color = df_k.iloc[-20], ("#F1C40F" if is_dark else "#D97706")
        ded_price = round(float(ded_row["Close"]), 2)
        fig.add_trace(go.Scatter(x=[ded_row[x_col]], y=[ded_price], mode="markers+text", name="20根扣抵", marker=dict(color=star_color, size=13, symbol="star", line=dict(color="#000000", width=1)), text=[f"⭐{ded_price}"], textposition="top center", textfont=dict(color=star_color, size=int(10.5 * scale_factor), weight="bold"), hoverinfo="skip"), row=1, col=1)
        fig.add_hline(y=ded_price, line_width=1.1, line_dash="dash", line_color=star_color, annotation_text=f"扣抵 {ded_price}", annotation_position="bottom left", annotation_font=dict(color=star_color, size=int(9.5 * scale_factor)), row=1, col=1)

    if show_cdp and cdp_vals:
        for lv_key, lv_lbl, lv_clr, lv_pos in [("AH", "AH極端突破", "#EF4444", "top left"), ("NH", "NH常態壓力", "#F97316", "top right"), ("NL", "NL常態支撐", "#38BDF8", "bottom right"), ("AL", "AL極端破底", "#10B981", "bottom left")]:
            fig.add_hline(y=cdp_vals[lv_key], line_width=1.1, line_dash="dot", line_color=lv_clr, annotation_text=f"{lv_lbl} {cdp_vals[lv_key]}", annotation_position=lv_pos, annotation_font=dict(color=lv_clr, size=int(9.5 * scale_factor)), row=1, col=1)

    if show_volume and "Volume" in df_k.columns:
        bar_colors = ["#FF4B4B" if c >= o else "#00D26A" for c, o in zip(df_k["Close"], df_k["Open"])]
        fig.add_trace(go.Bar(x=df_k[x_col], y=df_k["Volume"], name="量(張)", marker_color=bar_colors, hovertemplate="%{y:,.0f} 張"), row=2, col=1)

    y_min_val = min(float(df_k["Low"].min()), float(df_k["BB_Lower"].dropna().min())) if (show_bb and "BB_Lower" in df_k.columns and not df_k["BB_Lower"].dropna().empty) else float(df_k["Low"].min())
    y_max_val = max(float(df_k["High"].max()), float(df_k["BB_Upper"].dropna().max())) if (show_bb and "BB_Upper" in df_k.columns and not df_k["BB_Upper"].dropna().empty) else float(df_k["High"].max())
    if show_cdp and cdp_vals:
        y_min_val, y_max_val = min(y_min_val, cdp_vals["NL"]), max(y_max_val, cdp_vals["NH"])
    pad_y = max(0.5, (y_max_val - y_min_val) * 0.08)

    layout_cfg = dict(
        hovermode="x unified", hoverlabel=dict(bgcolor=CARD_BG, font_size=int(11.5 * scale_factor), font_color=TEXT_MAIN, bordercolor="#4A90E2"), spikedistance=-1,
        yaxis=dict(range=[y_min_val - pad_y, y_max_val + pad_y], tickfont=dict(size=int(11 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True, showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="#A0AEC0", spikethickness=1.0, spikedash="dot"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=int(10 * scale_factor), color=TEXT_MAIN)),
        height=int((450 if show_volume else 410) * max(1.0, scale_factor * 0.92)), margin=dict(l=8, r=12, t=42, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN)
    )
    if show_volume and "Volume" in df_k.columns:
        layout_cfg["xaxis"] = dict(type="category", rangeslider=dict(visible=False), showticklabels=False)
        layout_cfg["xaxis2"] = dict(type="category", tickangle=-35, nticks=10, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True)
        layout_cfg["yaxis2"] = dict(tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True)
    else:
        layout_cfg["xaxis"] = dict(type="category", rangeslider=dict(visible=False), tickangle=-35, nticks=10, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True, showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="#A0AEC0", spikethickness=1.2, spikedash="dot")

    fig.update_layout(**layout_cfg)
    return fig

def plot_20d_chip_bar_chart(daily_table, stock_title, scale_factor=1.1):
    df_c = pd.DataFrame(daily_table).sort_values("交易日期", ascending=True)
    df_c["ShortDate"] = df_c["交易日期"].str.slice(5)
    fig = go.Figure()
    for col, name, clr in [("外資買賣超(張)", "外資", "#3498DB"), ("投信買賣超(張)", "投信", "#FF6B6B"), ("自營商買賣超(張)", "自營", "#F59E0B")]:
        fig.add_trace(go.Bar(x=df_c["ShortDate"], y=df_c[col], name=name, marker_color=clr))
    fig.add_trace(go.Scatter(x=df_c["ShortDate"], y=df_c["三大法人合計(張)"], mode="lines+markers", name="法人合計", line=dict(color=TEXT_MAIN, width=2.2, dash="dot"), marker=dict(size=6, color="#00D26A")))
    fig.add_hline(y=0, line_width=1, line_color=TEXT_MUTED)
    fig.update_layout(barmode="group", hovermode="x unified", xaxis=dict(type="category", tickangle=-35, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True), yaxis=dict(tickfont=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN)), height=int(340 * max(1.0, scale_factor * 0.92)), margin=dict(l=8, r=12, t=38, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN))
    return fig

def plot_20d_margin_bar_chart(daily_table, stock_title, scale_factor=1.1):
    df_m = pd.DataFrame(daily_table).sort_values("交易日期", ascending=True)
    df_m["ShortDate"] = df_m["交易日期"].str.slice(5)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_m["ShortDate"], y=df_m["融資增減(張)"], name="融資增減", marker_color="#FF6B6B"))
    fig.add_trace(go.Bar(x=df_m["ShortDate"], y=df_m["融券增減(張)"], name="融券增減", marker_color="#2ECC71"))
    fig.add_trace(go.Scatter(x=df_m["ShortDate"], y=df_m["券資比(%)"], mode="lines+markers", name="券資比(%)", yaxis="y2", line=dict(color="#F59E0B", width=2.2, dash="dot"), marker=dict(size=6, color="#F59E0B")))
    fig.add_hline(y=0, line_width=1, line_color=TEXT_MUTED)
    fig.update_layout(barmode="group", hovermode="x unified", xaxis=dict(type="category", tickangle=-35, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True), yaxis=dict(tickfont=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True), yaxis2=dict(tickfont=dict(size=int(10 * scale_factor), color="#F59E0B"), overlaying="y", side="right", showgrid=False, automargin=True), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN)), height=int(340 * max(1.0, scale_factor * 0.92)), margin=dict(l=8, r=12, t=38, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN))
    return fig

def check_tab_password_gate(tab_num, tab_key, is_locked, correct_pwd, gate_title, gate_desc, line_url):
    if not is_locked or st.session_state.get(tab_key, False): return True
    st.markdown(f"#### 🔒 【{gate_title}】專屬授權解鎖")
    st.info(f"💡 {gate_desc}")
    with st.form(f"form_{tab_key}"):
        c1, c2 = st.columns([7.5, 2.5])
        pwd_in = c1.text_input("請輸入此專區通行密碼：", type="password", label_visibility="collapsed", placeholder="請輸入本專區專屬解鎖密碼...")
        if c2.form_submit_button("🔓 確認解鎖本頁", use_container_width=True, type="primary"):
            if pwd_in.strip() == str(correct_pwd).strip():
                st.session_state[tab_key], st.session_state.active_nav_tab = True, int(tab_num)
                st.rerun()
            else: st.error("❌ 密碼不正確，請重新輸入或私訊您的專屬營業員索取。")
    render_cta_box(f"🔑 還沒有【{gate_title}】的專屬通行碼嗎？", f"💬 點此私訊專屬營業員：索取【{gate_title}】解鎖密碼", line_url)
    return False

# ==========================================
# 3. 分頁 2 專用「獲利價位 & 近五檔損益」試算室 (@st.fragment)
# ==========================================
@st.fragment
def render_fast_profit_calculator(line_url, is_public_promo=False):
    for idx_b in range(1, 6):
        st.session_state.setdefault(f"bp_{idx_b}", 0.0)
        st.session_state.setdefault(f"bl_{idx_b}", 0)

    st.subheader("🧮 現股當沖 ／ 隔日沖「獲利價位 & 近五檔損益」試算室")
    with st.container(border=True):
        top_p1, top_p2 = st.columns([3.5, 6.5])
        excel_fold = top_p1.number_input("🏷️ 手續費折數 (如 2.8 折，低消 20 元)：", min_value=0.10, max_value=10.00, value=2.80, step=0.05, format="%.2f")
        tax_mode_opt = top_p2.radio("🏛️ 交易稅率模式（一鍵切換，全表同步更新）：", options=["⚡ 現股當沖 (稅 0.15%)", "📅 隔日沖/一般現股 (稅 0.30%)", "🏦 ETF 交易 (稅 0.10%)"], index=0, horizontal=True)
        excel_tax_rate = 0.0015 if "0.15%" in tax_mode_opt else (0.0030 if "0.30%" in tax_mode_opt else 0.0010)

    left_col, right_col = st.columns([4.6, 5.4], gap="medium")
    with left_col:
        with st.container(border=True):
            st.markdown("#### 🎯 1. 單筆買賣「獲利價位 & 損益試算」")
            st.caption(f"目前設定：手續費 **{excel_fold:.2f} 折 (低消20元)** ｜ 交易稅率 **{excel_tax_rate*100:.2f}%**")
            in_b1, in_b2, in_b3 = st.columns(3)
            buy_p_in = in_b1.number_input("💵 買進股價 (元)", min_value=0.01, max_value=30000.0, step=float(de.get_tw_tick_size(st.session_state.w_buy_p)), format="%.2f", key="w_buy_p")
            sell_p_in = in_b2.number_input("💴 賣出股價 (元)", min_value=0.01, max_value=30000.0, step=float(de.get_tw_tick_size(st.session_state.w_sell_p)), format="%.2f", key="w_sell_p")
            lots_in = in_b3.number_input("📦 交易張數 (張)", min_value=1, max_value=10000, step=1, key="w_lots")

            main_res = de.calc_trade_row_min20(buy_p_in, sell_p_in, lots_in, excel_fold, excel_tax_rate)
            pnl_color = BULL_COLOR if main_res["net_pnl"] > 0 else (BEAR_COLOR if main_res["net_pnl"] < 0 else TEXT_MAIN)
            st.markdown(f"""<div class="pillar-card" style="border-left: 5px solid {pnl_color}; margin-top: 6px;">
            <div class="pillar-title"><span>📊 買 {buy_p_in:g} 元 ➔ 賣 {sell_p_in:g} 元 ({lots_in} 張)</span><span class="{'tag-bull' if main_res['net_pnl']>0 else 'tag-bear'}">報酬率 {main_res['roi_pct']:+.2f}%</span></div>
            <div style="background:{SCORE_BOX_BG}; padding:10px 12px; border-radius:8px; margin-bottom:10px; font-size:{round(13.5*scale,1)}px; line-height:1.65;">
            • <b>手續費明細：</b>買 {main_res['fee_buy']:,} ＋ 賣 {main_res['fee_sell']:,} ＝ <b>{main_res['total_fee']:,} 元</b> ｜ <b>稅與總成本：</b>稅 {main_res['tax']:,} ／ 總成本 <b>{main_res['total_cost']:,} 元</b></div>
            <div style="font-size:{round(14.5*scale,1)}px; line-height:1.75;">
            - 📈 <b>做多獲利價：</b><span style="color:#F59E0B; font-weight:bold; font-size:{round(16*scale,1)}px;">{main_res['long_be_price']:.2f} 元</span> <span style="font-size:12.5px; color:#00D26A; font-weight:bold;">(⚡+{main_res['long_win_ticks']}檔至 {main_res['long_win_price']:g} 元即賺)</span><br>
            - 📉 <b>放空獲利價：</b><span style="color:#3498DB; font-weight:bold; font-size:{round(16*scale,1)}px;">{main_res['short_be_price']:.2f} 元</span> <span style="font-size:12.5px; color:#3498DB; font-weight:bold;">(⚡-{main_res['short_win_ticks']}檔至 {main_res['short_win_price']:g} 元即賺)</span><br>
            - 💰 <b>實拿淨損益：</b><span style="color:{pnl_color}; font-weight:bold; font-size:{round(21*scale,1)}px;">{main_res['net_pnl']:+,} 元</span></div></div>""", unsafe_allow_html=True)

        with st.expander("🧮 2. 點此展開【分批進場平均成本試算器】（最多 5 批攤平試算）"):
            def load_batch_demo():
                for i_d, (dp, dl) in enumerate([(106.0, 3), (106.5, 5), (105.0, 5), (0.0, 0), (0.0, 0)], 1):
                    st.session_state[f"bp_{i_d}"], st.session_state[f"bl_{i_d}"] = float(dp), int(dl)
            def clear_batch_all():
                for i_d in range(1, 6): st.session_state[f"bp_{i_d}"], st.session_state[f"bl_{i_d}"] = 0.0, 0

            bt_c1, bt_c2 = st.columns(2)
            bt_c1.button("✨ 帶入範例", key="btn_b_demo", use_container_width=True, on_click=load_batch_demo)
            bt_c2.button("🗑️ 清空歸零", key="btn_b_clr", use_container_width=True, on_click=clear_batch_all)

            sum_lots, sum_raw_val = 0, 0.0
            for idx in range(1, 6):
                bc1, bc2 = st.columns(2)
                p_val = bc1.number_input(f"第 {idx} 批成交價 (元)", min_value=0.0, max_value=30000.0, step=0.5, format="%.2f", key=f"bp_{idx}")
                l_val = bc2.number_input(f"第 {idx} 批張數 (張)", min_value=0, max_value=10000, step=1, key=f"bl_{idx}")
                if p_val > 0 and l_val > 0:
                    sum_lots += int(l_val); sum_raw_val += (p_val * l_val)

            sum_ntd_val, avg_stock_p = int(round(sum_raw_val * 1000)), (round(sum_raw_val / sum_lots, 2) if sum_lots > 0 else 0.0)
            st.markdown(f"""<div style="background:{CARD_BG}; border:1px solid {CARD_BORDER}; border-radius:10px; padding:12px 14px; margin-top:6px; margin-bottom:10px;">
            <div>📌 <b>總張數：</b><b>{sum_lots:,} 張</b> ｜ 💵 <b>總金額：</b><b>{sum_ntd_val:,} 元</b></div>
            <div style="font-size:{round(17.5*scale,1)}px; font-weight:bold; color:#00D26A; margin-top:4px;">⚖️ 加權平均股價：{avg_stock_p:.2f} 元</div></div>""", unsafe_allow_html=True)

            if sum_lots > 0:
                st.button(f"📈 做多帶入：買進設為 {avg_stock_p:.2f} 元 × {sum_lots} 張", use_container_width=True, on_click=lambda a=avg_stock_p, l=sum_lots: st.session_state.update({"w_buy_p": float(a), "w_sell_p": float(de.step_tw_ticks(a, 2)), "w_lots": int(l)}))
                st.button(f"📉 放空帶入：賣出設為 {avg_stock_p:.2f} 元 × {sum_lots} 張", use_container_width=True, on_click=lambda a=avg_stock_p, l=sum_lots: st.session_state.update({"w_sell_p": float(a), "w_buy_p": float(de.step_tw_ticks(a, -2)), "w_lots": int(l)}))

    with right_col:
        with st.container(border=True):
            st.markdown("#### 📊 3. 做多 ／ 放空「近五檔價位損益速查表」")
            tab_long_5, tab_short_5 = st.tabs([f"📈 做多五檔 (買 {buy_p_in:g}元 × {lots_in}張)", f"📉 放空五檔 (賣 {sell_p_in:g}元 × {lots_in}張)"])
            for tab_obj, is_long in [(tab_long_5, True), (tab_short_5, False)]:
                with tab_obj:
                    if is_long:
                        st.caption(f"⚡ 買進 **{buy_p_in:g}元** 往上 **+{main_res['long_win_ticks']} 檔 ({main_res['long_win_price']:g}元)** 即開始獲利！")
                        steps, p_col = [5, 4, 3, 2, 1, 0, -1, -2, -3], "賣價"
                    else:
                        st.caption(f"⚡ 先賣 **{sell_p_in:g}元** 往下 **-{main_res['short_win_ticks']} 檔 ({main_res['short_win_price']:g}元)** 回補即開始獲利！")
                        steps, p_col = [-5, -4, -3, -2, -1, 0, 1, 2, 3], "補價"

                    rows_5 = []
                    for s_i in steps:
                        t_p = de.step_tw_ticks(buy_p_in if is_long else sell_p_in, s_i)
                        r_c = de.calc_trade_row_min20(buy_p_in if is_long else t_p, t_p if is_long else sell_p_in, lots_in, excel_fold, excel_tax_rate)
                        lbl = (f"🔥+{s_i}檔" if s_i > 0 else ("⚪平盤" if s_i == 0 else f"❄️{s_i}檔")) if is_long else (f"🔥{s_i}檔" if s_i < 0 else ("⚪平盤" if s_i == 0 else f"❄️+{s_i}檔"))
                        rows_5.append({"檔位": lbl, p_col: t_p, "實拿損益": r_c["net_pnl"], "報酬率": r_c["roi_pct"], "總成本(稅+費)": r_c["total_cost"]})

                    st.dataframe(pd.DataFrame(rows_5).style.map(style_signed_numbers, subset=["實拿損益", "報酬率"]).format({p_col: "{:g}", "實拿損益": "{:+,.0f}", "報酬率": "{:+.2f}%", "總成本(稅+費)": "{:,.0f}"}), use_container_width=True, hide_index=True, height=365)

    render_cta_box(
        "🔥 常做短線現沖或隔日沖，想申請更優惠的【VIP 專屬手續費折數】讓獲利價位門檻更低嗎？" if is_public_promo else "⚡ 想索取今日盤後【當沖主力分點進出明細】、或調整您的單日電子交易與資券額度嗎？",
        "💬 點此私訊專屬營業員：評估交易量與申請【VIP 手續費優惠專案】" if is_public_promo else "💬 點此私訊您的專屬營業員：索取主力分點籌碼與額度調整服務",
        line_url
    )

# ==========================================
# 4. 營業員永久記憶加密後台與全市場 2,300+ 檔常駐名冊載入
# ==========================================
de.init_sample_csvs()
cfg = de.load_config()
sector_map_all = de.load_sector_map()
df_quotes, df_futures, df_cb = de.read_csv_safely(de.QUOTES_FILE), de.read_csv_safely(de.FUTURES_FILE), de.read_csv_safely(de.CB_FILE)
margins_global_map = dict(zip(df_futures["代號"].astype(str), df_futures["保證金比例"]))

master_stock_dict = de.get_master_stock_dictionary()
if len(df_quotes) < len(master_stock_dict):
    df_quotes = pd.DataFrame(list(master_stock_dict.values())).sort_values("代號")

if not df_quotes.empty:
    df_quotes = df_quotes[df_quotes["代號"].str.match(r"^(00\d{2,4}[A-Za-z]?|\d{4})$", na=False)].copy()
    fut_codes = set(df_futures["代號"].astype(str))
    df_quotes["has_fut_sort"] = df_quotes["代號"].astype(str).apply(lambda x: 0 if x in fut_codes else 1)
    stock_options = [f"{r['代號']} {r['名稱']}" + (" ⚡[有期貨]" if str(r['代號']) in fut_codes else "") for _, r in df_quotes.sort_values(["has_fut_sort", "代號"]).iterrows()]
else: stock_options = ["2330 台積電 ⚡[有期貨]"]

code_to_name_map = dict(zip(df_quotes["代號"].astype(str), df_quotes["名稱"].astype(str)))
name_to_code_map = dict(zip(df_quotes["名稱"].astype(str), df_quotes["代號"].astype(str)))
code_to_mkt_map = dict(zip(df_quotes["代號"].astype(str), df_quotes.get("市場", pd.Series(["TWSE"]*len(df_quotes)))))

for d_code, d_meta in st.session_state.get("dynamic_stock_meta", {}).items():
    code_to_name_map.setdefault(d_code, d_meta["name"])
    name_to_code_map.setdefault(d_meta["name"], d_code)
    code_to_mkt_map.setdefault(d_code, d_meta["mkt"])

with st.sidebar:
    st.caption("🔐 專供營業員維護使用")
    if not st.session_state.admin_unlocked:
        with st.form("admin_login_form"):
            admin_input = st.text_input("🔑 營業員管理登入：", type="password", placeholder="請輸入管理員密碼")
            if st.form_submit_button("🔓 登入管理後台", use_container_width=True):
                if admin_input == de.ADMIN_SECRET_CODE: st.session_state.admin_unlocked = True; st.rerun()
                else: st.error("❌ 管理員密碼錯誤")
    else:
        col_adm1, col_adm2 = st.columns([7, 3])
        col_adm1.success("✅ 管理員已解鎖")
        if col_adm2.button("登出", use_container_width=True): st.session_state.admin_unlocked = False; st.rerun()

        st.subheader("🔐 獨立密碼鎖 & LINE / API 設定")
        new_line_url = st.text_input("💬 營業員 LINE 連結 (按Enter自動存檔)：", value=cfg["broker_line_url"]).strip()
        if new_line_url and not new_line_url.startswith("http"): new_line_url = "https://" + new_line_url
        new_promo_mode = st.checkbox("🌐 切換為「對外開發公版模式（顯示手續費優惠）」", value=bool(cfg.get("public_promo_mode", False)))
        new_gemini_key = st.text_input("🤖 Gemini API Key (選填)：", type="password", value=str(cfg.get("gemini_api_key", ""))).strip()
        new_fm_token = st.text_input("🔑 FinMind Token (選填)：", type="password", value=str(cfg.get("finmind_token", ""))).strip()

        l_t1, p_t1 = st.checkbox("鎖定【分頁 1：個股三週期共振雷達】", value=bool(cfg.get("lock_tab1", False))), st.text_input("分頁 1 密碼：", value=str(cfg.get("pwd_tab1", "VIP888"))).strip()
        l_t2, p_t2 = st.checkbox("鎖定【分頁 2：獲利價位與近五檔試算室】", value=bool(cfg.get("lock_tab2", False))), st.text_input("分頁 2 密碼：", value=str(cfg.get("pwd_tab2", "TICK888"))).strip()
        l_t4, p_t4 = st.checkbox("鎖定【分頁 3：大盤籌碼 & 動態主流族群】", value=bool(cfg.get("lock_tab4", False))), st.text_input("分頁 3 密碼：", value=str(cfg.get("pwd_tab4", "VIP888"))).strip()

        new_vals = {"lock_tab1": bool(l_t1), "pwd_tab1": p_t1, "lock_tab2": bool(l_t2), "pwd_tab2": p_t2, "lock_tab4": bool(l_t4), "pwd_tab4": p_t4, "public_promo_mode": bool(new_promo_mode), "gemini_api_key": new_gemini_key, "finmind_token": new_fm_token, "broker_line_url": new_line_url or cfg["broker_line_url"]}
        if any(cfg.get(k) != v for k, v in new_vals.items()):
            cfg.update(new_vals); de.save_config(cfg); st.toast("✅ 設定已自動儲存！")

        st.divider(); st.subheader("🗂️ 自訂熱門族群管理 (支援截圖辨識)")
        custom_sec_name = st.text_input("1️⃣ 輸入要新增/擴充的族群名稱：", placeholder="例如：17. 機器人與智慧製造")
        img_up = st.file_uploader("📸 (選填) 上傳看盤截圖自動辨識代號：", type=["png", "jpg", "jpeg"])
        if img_up and st.button("🔍 點此從截圖 AI 辨識股票代號", use_container_width=True):
            if not cfg.get("gemini_api_key"): st.warning("⚠️ 請先填入 Gemini API Key！")
            else:
                with st.spinner("🤖 正在辨識台股代號..."):
                    ext_txt = de.extract_stocks_from_image_via_gemini(img_up.getvalue(), img_up.type, cfg["gemini_api_key"])
                    if ext_txt: st.session_state.ocr_extracted_codes = ext_txt; st.success(f"✅ 辨識成功：{ext_txt}"); st.rerun()

        custom_codes_raw = st.text_area("2️⃣ 輸入成分股代號或名稱：", value=st.session_state.get("ocr_extracted_codes", ""), placeholder="例如：2359, 2049, 4576")
        if st.button("➕ 儲存並加入此族群", use_container_width=True, type="primary") and custom_sec_name.strip() and custom_codes_raw.strip():
            parsed_stocks = []
            for tk in [t.strip() for t in re.split(r"[,\s、，；;]+", custom_codes_raw) if t.strip()]:
                if tk in code_to_name_map: parsed_stocks.append([tk, code_to_name_map[tk], code_to_mkt_map.get(tk, "TWSE")])
                elif tk in name_to_code_map: parsed_stocks.append([name_to_code_map[tk], tk, code_to_mkt_map.get(name_to_code_map[tk], "TWSE")])
                elif re.match(r"^\d{4}$", tk): parsed_stocks.append([tk, tk, "TWSE"])
            if parsed_stocks:
                sector_map_all[custom_sec_name.strip()] = parsed_stocks; de.save_sector_map(sector_map_all); de.scan_sector_performance.clear(); st.success(f"🎉 已寫入【{custom_sec_name}】！"); st.rerun()

        if os.path.exists(de.CUSTOM_SECTORS_FILE) and st.button("🔄 還原預設 16 大族群", use_container_width=True):
            os.remove(de.CUSTOM_SECTORS_FILE); de.scan_sector_performance.clear(); st.rerun()

        st.divider(); st.subheader("🚀 官方名冊與大盤籌碼同步")
        if st.button("📈 1. 更新上市櫃 2,300+ 檔股票與 ETF 名冊", use_container_width=True):
            with st.spinner("正在更新上市櫃股票與全品項 ETF..."):
                ok, msg = de.sync_stock_code_list_online()
                if ok: st.success(msg); st.rerun()
        if st.button("🔄 2. 同步期交所 250+ 檔個股期", use_container_width=True):
            with st.spinner("正在同步個股期與保證金..."):
                ok, msg = de.sync_taifex_futures_online()
                if ok: st.success(msg); st.rerun()
        if st.button("🏛️ 3. 自動同步大盤法人、外資期貨與資券", use_container_width=True, type="primary"):
            with st.spinner("正在連線證交所與期交所抓取最新數據..."):
                mkt_res = de.sync_market_institutional_online(str(cfg.get("finmind_token", "")).strip())
                if mkt_res: cfg.update(mkt_res); de.save_config(cfg); st.success("✅ 同步完成！"); st.rerun()

        st.divider(); st.subheader("🚦 大盤籌碼手動微調校準")
        with st.form("manual_mkt_calibrate_form"):
            new_foi = st.number_input("外資台指期未平倉淨額(口)", value=int(cfg["mkt_foreign_oi"]), step=500)
            new_foi_chg = st.number_input("外資期貨未平倉單日增減(口)", value=int(cfg.get("mkt_foreign_oi_chg", -1420)), step=100)
            new_sp_f = st.number_input("外資上市現貨買賣超(億)", value=float(cfg.get("mkt_spot_foreign", 159.22)), step=10.0)
            new_sp_t = st.number_input("投信上市現貨買賣超(億)", value=float(cfg.get("mkt_spot_trust", 118.07)), step=5.0)
            new_sp_d = st.number_input("自營商上市現貨買賣超(億)", value=float(cfg.get("mkt_spot_dealer", 21.65)), step=5.0)
            new_mbal = st.number_input("大盤融資餘額(億元)", value=float(cfg.get("mkt_margin_bal", 6233.87)), step=10.0)
            new_mchg = st.number_input("大盤融資單日增減(億元)", value=float(cfg.get("mkt_margin_chg", -104.93)), step=2.0)
            new_mchg3 = st.number_input("大盤融資近3日累計增減(億元)", value=float(cfg.get("mkt_margin_chg_3d", -147.13)), step=5.0)
            new_sbal = st.number_input("大盤融券餘額(張)", value=int(cfg.get("mkt_short_bal", 217708)), step=1000)
            new_schg = st.number_input("大盤融券單日增減(張)", value=int(cfg.get("mkt_short_chg", 1169)), step=500)
            new_cnn_fg = st.number_input("CNN 恐懼貪婪備用值 (0~100)", min_value=0, max_value=100, value=int(cfg.get("cnn_fear_greed", 34)), step=1)
            if st.form_submit_button("💾 儲存手動微調數據", use_container_width=True):
                cfg.update({"mkt_foreign_oi": int(new_foi), "mkt_foreign_oi_chg": int(new_foi_chg), "mkt_spot_foreign": float(new_sp_f), "mkt_spot_trust": float(new_sp_t), "mkt_spot_dealer": float(new_sp_d), "mkt_margin_bal": float(new_mbal), "mkt_margin_chg": float(new_mchg), "mkt_margin_chg_3d": float(new_mchg3), "mkt_short_bal": int(new_sbal), "mkt_short_chg": int(new_schg), "cnn_fear_greed": int(new_cnn_fg)})
                de.save_config(cfg); st.success("✅ 已儲存！"); st.rerun()

        st.divider(); st.subheader("💾 雲端設定檔備份與還原")
        st.download_button("📤 一鍵下載設定檔備份 (.json)", data=json.dumps({"config": cfg, "custom_sectors": sector_map_all}, ensure_ascii=False, indent=2), file_name=f"arsenal_backup_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json", use_container_width=True)
        up_backup = st.file_uploader("📥 上傳備份檔還原：", type=["json"])
        if up_backup is not None:
            try:
                b_data = json.loads(up_backup.getvalue().decode("utf-8"))
                if "config" in b_data: de.save_config(b_data["config"])
                if "custom_sectors" in b_data: de.save_sector_map(b_data["custom_sectors"])
                st.success("🎉 備份還原成功！"); st.rerun()
            except Exception as e: st.error(f"還原失敗：{e}")

is_public_promo, fm_token_str = bool(cfg.get("public_promo_mode", False)), str(cfg.get("finmind_token", "")).strip()

# ==========================================
# 5. 頂部「黃金 3 大分頁膠囊導航列」與跨頁跳轉器
# ==========================================
if st.session_state.active_nav_tab not in [1, 2, 3]:
    st.session_state.active_nav_tab = 1
cur_tab = st.session_state.active_nav_tab
nav_cols = st.columns(3)
nav_specs = [
    (1, "lock_tab1", "unlocked_tab1", "🔍", "1. 個股三週期共振雷達"),
    (2, "lock_tab2", "unlocked_tab2", "🧮", "2. 現沖/隔日沖獲利試算"),
    (3, "lock_tab4", "unlocked_tab4", "🚦", "3. 大盤籌碼 & 動態主流族群")
]
for col_n, (t_idx, l_key, u_key, ico, lbl) in zip(nav_cols, nav_specs):
    icon_d = "🔒" if (cfg.get(l_key, False) and not st.session_state[u_key]) else ico
    col_n.button(f"{icon_d} {lbl}", use_container_width=True, type="primary" if cur_tab == t_idx else "secondary", on_click=switch_to_tab, args=(t_idx,))

st.markdown("<hr style='margin-top:4px; margin-bottom:16px; border-color:#2D3748;'>", unsafe_allow_html=True)
current_active_code = st.session_state.target_stock_code
current_active_name = code_to_name_map.get(current_active_code, "台積電")

def jump_to_tab2_with_price(close_p):
    st.session_state.w_buy_p, st.session_state.w_sell_p, st.session_state.active_nav_tab = float(close_p), float(de.step_tw_ticks(close_p, 2)), 2

def jump_to_tab1_with_stock(code_str, name_str="", mkt_str="TWSE"):
    c_clean = str(code_str).strip().upper()
    n_clean = str(name_str).replace("🔥", "").strip()
    if n_clean:
        st.session_state.dynamic_stock_meta[c_clean] = {"name": n_clean, "mkt": mkt_str}
    st.session_state.target_stock_code = c_clean
    st.session_state.active_nav_tab = 1
    st.session_state.close_popover_seq = int(st.session_state.get("close_popover_seq", 0)) + 1
    if "tab1_stock_sel_widget" in st.session_state:
        del st.session_state["tab1_stock_sel_widget"]

# ------------------------------------------------------------------
# 【分頁 1：🔍 個股/ETF 三週期共振雷達 (含實戰綜合總結論 & AH/NH/NL/AL 四價位)】
# ------------------------------------------------------------------
if cur_tab == 1:
    if check_tab_password_gate(1, "unlocked_tab1", cfg.get("lock_tab1", False), cfg.get("pwd_tab1", "VIP888"), "個股三週期技術與籌碼雷達", "輸入本季基礎 VIP 通行碼即可解鎖「日K/60分K/5分K三週期共振雷達與機構級評分」。", cfg["broker_line_url"]):
        def _move_mod(idx, d):
            items = st.session_state.tab1_master_items
            if 0 <= idx + d < len(items): items[idx], items[idx + d] = items[idx + d], items[idx]
        def _toggle_mod(idx): st.session_state.tab1_master_items[idx]["show"] = not st.session_state.tab1_master_items[idx]["show"]
        def _reset_mod(): st.session_state.tab1_master_items = [dict(x) for x in DEFAULT_STATES["tab1_master_items"]]

        target_c = str(st.session_state.target_stock_code).strip().upper()
        if not any(opt.startswith(target_c + " ") for opt in stock_options):
            sec_lookup = {item[0]: (item[1].replace("🔥", ""), item[2]) for s_list in sector_map_all.values() for item in s_list}
            dyn_meta = st.session_state.get("dynamic_stock_meta", {}).get(target_c, {})
            s_name_fb, s_mkt_fb = sec_lookup.get(target_c, (dyn_meta.get("name", code_to_name_map.get(target_c, target_c)), dyn_meta.get("mkt", "TPEX" if target_c.endswith("B") else "TWSE")))
            code_to_name_map[target_c], code_to_mkt_map[target_c] = s_name_fb, s_mkt_fb
            has_f_tag = " ⚡[有期貨]" if target_c in set(df_futures["代號"].astype(str)) else ""
            stock_options.insert(0, f"{target_c} {s_name_fb}{has_f_tag}")

        default_idx = next((i for i, opt in enumerate(stock_options) if opt.startswith(target_c + " ")), 0)
        sel_c1, sel_c2 = st.columns([6.8, 3.2])
        selected_option = sel_c1.selectbox(f"📌 請直接輸入個股或 ETF 代號/名稱搜尋（目前共收錄 {len(stock_options):,} 檔上市櫃標的）：", options=stock_options, index=default_idx, key="tab1_stock_sel_widget")
        selected_code = selected_option.split(" ")[0].strip().upper()
        st.session_state.target_stock_code = selected_code

        match_rows = df_quotes[df_quotes["代號"] == selected_code]
        stock_name = str(match_rows.iloc[0]["名稱"]) if not match_rows.empty else code_to_name_map.get(selected_code, selected_code)
        market_hint = str(match_rows.iloc[0].get("市場", "TWSE")) if not match_rows.empty else code_to_mkt_map.get(selected_code, "TPEX" if selected_code.endswith("B") else "TWSE")
        current_active_code, current_active_name = selected_code, stock_name

        with st.spinner(f"正在對帳【{selected_code} {stock_name}】官方真實日K、三週期共振、對抗大盤 Alpha、外本比/投本比與月營收..."):
            tech = de.fetch_technical_indicators(selected_code, market_hint)
            tech_60m = de.fetch_intraday_kline_full(selected_code, market_hint, interval="60m")
            tech_5m = de.fetch_intraday_kline_full(selected_code, market_hint, interval="5m")
            chip = de.fetch_chip_data_20d(selected_code, fm_token_str)
            margin_info = de.fetch_margin_short_20d(selected_code, fm_token_str)
            fund_info = de.fetch_fundamental_revenue_and_shareholding(selected_code, fm_token_str)
            taiex_quick = de.fetch_taiex_market_data()
            news_data = de.fetch_stock_news(selected_code, stock_name)

        if not tech["ok"]: st.error(f"無法取得 {selected_code} 的即時 K 線資料。底層原因：{tech.get('err_msg', '網路被阻擋')}"); st.stop()

        close_price, high_price, low_price, ma20_price, ma60_price, deduct_price, trade_date = tech["close"], tech["high"], tech["low"], tech["ma20"], tech["ma60"], tech["deduct"], tech["date"]
        k_val, d_val, macd_osc, rsi_val, vol_ratio, td_b_cnt, td_s_cnt = tech["K"], tech["D"], tech["macd_osc"], tech["rsi"], tech["vol_ratio"], tech["td_buy"], tech["td_sell"]
        cdp_vals = de.calculate_cdp(high_price, low_price, close_price)

        with sel_c2:
            st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
            st.button(f"🧮 帶入【{stock_name} {close_price}元】去算當沖損益 ➔", use_container_width=True, on_click=jump_to_tab2_with_price, args=(close_price,))

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
        st.markdown(f"<p style='font-size:{round(14*scale, 1)}px; color:{TEXT_MUTED}; margin-top:-10px;'>📅 <b>最新有效交易日：{trade_date}</b> ｜ 最新價格：<b>{close_price} 元</b>（單日 <b>{tech['chg_1d_pct']:+.2f}%</b> ／ 對抗大盤 Alpha <b>{eval_res['alpha_1d']:+.2f}%</b>） ｜ 市場：<b>{'上市' if market_hint=='TWSE' else '上櫃'}</b></p>", unsafe_allow_html=True)

        st.markdown(f"""<div class="score-banner"><div style="flex: 1; min-width: 240px;">
        <div style="font-size: {round(13.5 * scale, 1)}px; color: {TEXT_MUTED}; margin-bottom: 4px;">🎯 系統機構級實戰總結論（綜合 Alpha、三週期分K、投本比/外本比與 AH/NH/NL/AL 價位）</div>
        <div style="font-size: {round(19 * scale, 1)}px; font-weight: bold; color: {eval_res['v_color']}; margin-bottom: 8px;">{eval_res['verdict']}</div>
        <div style="font-size: {round(14.2 * scale, 1)}px; color: {TEXT_MAIN}; line-height: 1.7; background: {SCORE_BOX_BG}; padding: 10px 14px; border-radius: 8px; border-left: 4px solid {eval_res['v_color']};">{eval_res['v_desc_html']}</div></div>
        <div style="text-align: center; padding: 12px 18px; background: {SCORE_BOX_BG}; border-radius: 10px; border: 1px solid {CARD_BORDER};">
        <div style="font-size: {round(12.5 * scale, 1)}px; color: {TEXT_MUTED};">機構量化總分</div>
        <div style="font-size: {round(32 * scale, 1)}px; font-weight: bold; color: {eval_res['v_color']};">{eval_res['total']}<span style="font-size:{round(14 * scale, 1)}px; color:{TEXT_SUB};"> / 100</span></div></div></div>""", unsafe_allow_html=True)

        with st.expander(f"🧮 點此查看【{stock_name} {eval_res['total']} / 100 分】之 4 大維度動態給分明細表（Alpha與趨勢 {eval_res['t_score']}/25 ＋ 三週期動能 {eval_res['m_score']}/25 ＋ 外本比與資券 {eval_res['c_score']}/30 ＋ 營收/位階 {eval_res['f_score']}/20）"):
            st.dataframe(pd.DataFrame(eval_res["breakdown"], columns=["評估維度", "本項得分", "客觀數據動態計分依據"]), use_container_width=True, hide_index=True)

        t_pct, m_pct, c_pct, f_pct = int((eval_res["t_score"] / 25.0) * 100), int((eval_res["m_score"] / 25.0) * 100), int((eval_res["c_score"] / 30.0) * 100), int((eval_res["f_score"] / 20.0) * 100)
        t_tag = f'<span class="{"tag-bull" if eval_res["alpha_1d"] >= 0 else "tag-bear"}">單日Alpha {eval_res["alpha_1d"]:+.1f}%</span>'
        m_tag = '<span class="tag-bull">KD金叉</span>' if k_val >= d_val else '<span class="tag-bear">KD死叉</span>'
        c_tag = f'<span class="{"tag-bull" if eval_res["inst_vol_ratio"] > 0 else "tag-bear"}">控盤度 {eval_res["inst_vol_ratio"]:+.1f}%</span>'
        td_str = (f"▲低九第 {td_b_cnt} 天" + (" (🔥滿9轉折)" if td_b_cnt == 9 else "")) if td_b_cnt > 0 else ((f"▼高九第 {td_s_cnt} 天" + (" (⚠️滿9衰竭)" if td_s_cnt == 9 else "")) if td_s_cnt > 0 else "⚪ 無連續九轉")
        p_chip = chip["periods"]

        if fund_info.get("has_rev") and not selected_code.startswith("00"):
            rev_yoy, rev_acc = fund_info["yoy_latest"], fund_info["yoy_accel"]
            rev_tag = f'<span class="{"tag-bull" if (rev_yoy > 0 and rev_acc >= 0) else ("tag-bear" if rev_yoy < 0 else "tag-neutral")}">{"加速成長" if rev_acc >= 0 else "高檔降速"}</span>'
            rev_main = f"YoY {rev_yoy:+.1f}%"
            rev_sub = f"- <b>{fund_info['rev_month']} 營收加速度：</b>較近3月均 <b>{rev_acc:+.1f}%</b><br>- <b>月增率(MoM)：</b>{fund_info['mom_latest']:+.1f}% ｜ <b>外資持股：</b>{fund_info['foreign_hold_pct']}%"
        else:
            bias_etf = round(((close_price - ma20_price) / ma20_price) * 100.0, 2) if ma20_price > 0 else 0.0
            rev_tag = f'<span class="{"tag-bull" if bias_etf >= 0 else "tag-bear"}">月線乖離 {bias_etf:+.1f}%</span>'
            rev_main = f"融資 {margin_info['margin_bal']:,} 張" if margin_info["eligible"] else "🏦 ETF 專區模式"
            rev_sub = f"- <b>融資單日：</b>{fmt_colored_num(margin_info['margin_chg'])} (使用率 {margin_info['margin_util']}%)<br>- <b>融券單日：</b>{fmt_colored_num(margin_info['short_chg'])}" if margin_info["eligible"] else f"- <b>ETF 乖離位階：</b>月線乖離 <b>{bias_etf:+.2f}%</b> (留意外資與散戶融資動向)"

        st.markdown(f"""<div class="pillar-grid">
        <div class="pillar-card"><div class="pillar-title"><span>🛡️ 1. 相對強弱(Alpha) & 均線</span>{t_tag}</div><div class="pillar-main">月線 {ma20_price} 元</div><div class="bar-bg"><div style="width:{t_pct}%; height:100%; background:{BULL_COLOR if t_pct>=60 else BEAR_COLOR};"></div></div><div class="pillar-sub">- <b>5日對抗大盤 Alpha：</b><b>{eval_res['alpha_5d']:+.2f}%</b><br>- <b>20日扣抵：</b>{deduct_price} 元 ({'助漲' if close_price >= deduct_price else '反壓'})<br>- <b>五日/季線：</b>5MA {tech['ma5']} ／ 60MA {ma60_price} 元</div></div>
        <div class="pillar-card"><div class="pillar-title"><span>⚡ 2. 三週期動能 & 九轉</span>{m_tag}</div><div class="pillar-main">K：{k_val} ｜ D：{d_val}</div><div class="bar-bg"><div style="width:{m_pct}%; height:100%; background:{BULL_COLOR if m_pct>=60 else BEAR_COLOR};"></div></div><div class="pillar-sub">- <b>60分/5分K 20MA：</b>{tech_60m.get('ma20','-')} ／ {tech_5m.get('ma20','-')} 元<br>- <b>神奇九轉：</b><b>{td_str}</b><br>- <b>量能比：</b>5日均量 <b>{vol_ratio} 倍</b> ｜ RSI {rsi_val}</div></div>
        <div class="pillar-card"><div class="pillar-title"><span>💰 3. 外本比/投本比 & 資券</span>{c_tag}</div><div class="pillar-main">5日 {fmt_colored_num(p_chip[5]['tot'])}</div><div class="bar-bg"><div style="width:{c_pct}%; height:100%; background:{BULL_COLOR if c_pct>=60 else BEAR_COLOR};"></div></div><div class="pillar-sub">- <b>近1日：</b>{fmt_colored_num(p_chip[1]['tot'])} ｜ <b>3日：</b>{fmt_colored_num(p_chip[3]['tot'])}<br>- <b>外資5日持股比增減：</b><b>{fund_info['foreign_hold_chg_5d']:+.2f}%</b><br>- <b>5日資增減：</b>{fmt_colored_num(margin_info['periods'][5]['m_chg'])} (券資比 {margin_info['short_margin_ratio']}%)</div></div>
        <div class="pillar-card"><div class="pillar-title"><span>🚀 4. 營收加速度 / ETF位階</span>{rev_tag}</div><div class="pillar-main">{rev_main}</div><div class="bar-bg"><div style="width:{f_pct}%; height:100%; background:#3498DB;"></div></div><div class="pillar-sub">{rev_sub}<br>- <b>10日/20日法人：</b>{fmt_colored_num(p_chip[10]['tot'])} ／ {fmt_colored_num(p_chip[20]['tot'])}</div></div></div>""", unsafe_allow_html=True)

        for sec_item in [x["id"] for x in st.session_state.tab1_master_items if x["show"]]:
            if sec_item == "🕯️":
                mtf_res = de.evaluate_mtf_resonance(tech, tech_60m, tech_5m, cdp_vals, BULL_COLOR, BEAR_COLOR, WARN_COLOR)
                st.markdown(f"##### 🎯 【{selected_code} {stock_name}】日 K × 60 分 K × 5 分 K「三週期多空共振雷達」")
                st.markdown(f"""<div class="metric-card" style="border-left: 5px solid {mtf_res['color']}; margin-bottom: 10px;">
                <div style="font-size:{round(16.5*scale,1)}px; font-weight:bold; color:{mtf_res['color']}; margin-bottom:6px;">{mtf_res['title']}</div>
                <div style="font-size:{round(14*scale,1)}px; color:{TEXT_SUB}; line-height:1.6;">{mtf_res['desc']}</div></div>""", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(mtf_res["table"]), use_container_width=True, hide_index=True)

                chk_c1, chk_c2, chk_c3 = st.columns(3)
                show_bb_s = chk_c1.checkbox("🟣 顯示布林通道 (±2σ)", value=True, key="s_bb_chk")
                show_td_s = chk_c2.checkbox("🔢 顯示神奇九轉 (TD9)", value=True, key="s_td_chk")
                show_cdp_s = chk_c3.checkbox("📐 疊加 AH / NH / NL / AL 支撐壓力線", value=True, key="s_cdp_chk")

                k_tab_daily, k_tab_60m, k_tab_5m = st.tabs([
                    "📅 1. 日 K 實戰圖 (100%官方對帳近60日 + 扣抵⭐ + 布林 + 九轉)",
                    "⏱️ 2. 60 分 K 波段轉折圖 (小時線 + 布林 + 九轉 + 扣抵⭐ + 四價位)",
                    "⚡ 3. 5 分 K 當沖狙擊圖 (五分線 + 布林 + 九轉 + 扣抵⭐ + 四價位)"
                ])
                with k_tab_daily:
                    st.plotly_chart(plot_universal_kline_chart(tech["kline_60"], scale, show_bb=show_bb_s, show_td=show_td_s, show_cdp=show_cdp_s, cdp_vals=cdp_vals, show_volume=False), use_container_width=True, theme=None)
                with k_tab_60m:
                    if tech_60m["ok"] and tech_60m["records"]:
                        st.plotly_chart(plot_universal_kline_chart(tech_60m["records"], scale, show_bb=show_bb_s, show_td=show_td_s, show_cdp=show_cdp_s, cdp_vals=cdp_vals, show_volume=True), use_container_width=True, theme=None)
                    else: st.info("目前暫無該標的之 60 分 K 資料。")
                with k_tab_5m:
                    if tech_5m["ok"] and tech_5m["records"]:
                        st.plotly_chart(plot_universal_kline_chart(tech_5m["records"], scale, show_bb=show_bb_s, show_td=show_td_s, show_cdp=show_cdp_s, cdp_vals=cdp_vals, show_volume=True), use_container_width=True, theme=None)
                    else: st.info("目前暫無該標的之 5 分 K 資料。")

            elif sec_item == "📊":
                st.markdown(f"##### 📊 【{selected_code} {stock_name}】近 20 日「法人買賣超 & 資券增減」直方圖")
                bar_tab1, bar_tab2 = st.tabs(["📊 1. 三大法人買賣超直方圖", "📊 2. 融資融券增減 & 券資比"])
                with bar_tab1:
                    if chip["ok"] and chip["daily_table"]: st.plotly_chart(plot_20d_chip_bar_chart(chip["daily_table"], f"{selected_code} {stock_name}", scale), use_container_width=True, theme=None)
                    else: st.caption("暫無法人買賣超資料。")
                with bar_tab2:
                    if margin_info["ok"] and margin_info["daily_table"]: st.plotly_chart(plot_20d_margin_bar_chart(margin_info["daily_table"], f"{selected_code} {stock_name}", scale), use_container_width=True, theme=None)
                    else: st.info("本標的無融資融券交易資料。")

            elif sec_item == "📋":
                st.markdown(f"##### 🎯 【{selected_code} {stock_name}】五週期籌碼累計總表與逐日明細")
                tbl_tab1, tbl_tab2, tbl_tab3 = st.tabs(["🎯 1. 五週期累計矩陣", "📋 2. 法人逐日明細", "📋 3. 資券逐日明細"])
                with tbl_tab1:
                    p_mg = margin_info["periods"]
                    matrix_rows = [{"籌碼主體": label, **{f"近 {w} 日": p_chip[w][k] for w in [1, 3, 5, 10, 20]}} for label, k in [("🌍 外資買賣超 (張)", "f"), ("🏦 投信買賣超 (張)", "t"), ("🏢 自營商買賣超 (張)", "d"), ("💰 三大法人合計 (張)", "tot")]]
                    if margin_info["ok"] and margin_info["eligible"]:
                        matrix_rows.extend([{"籌碼主體": "📈 融資累計增減 (張)", **{f"近 {w} 日": p_mg[w]["m_chg"] for w in [1, 3, 5, 10, 20]}}, {"籌碼主體": "📉 融券累計增減 (張)", **{f"近 {w} 日": p_mg[w]["s_chg"] for w in [1, 3, 5, 10, 20]}}])
                    period_cols = ["近 1 日", "近 3 日", "近 5 日", "近 10 日", "近 20 日"]
                    st.dataframe(pd.DataFrame(matrix_rows).style.map(style_signed_numbers, subset=period_cols).format({c: "{:+,}" for c in period_cols}), use_container_width=True, hide_index=True)
                with tbl_tab2:
                    if chip["ok"] and chip["daily_table"]:
                        num_cols = ["外資買賣超(張)", "投信買賣超(張)", "自營商買賣超(張)", "三大法人合計(張)"]
                        st.dataframe(pd.DataFrame(chip["daily_table"]).style.map(style_signed_numbers, subset=num_cols).format({c: "{:+,}" for c in num_cols}), use_container_width=True, hide_index=True)
                with tbl_tab3:
                    if margin_info["ok"] and margin_info["daily_table"]:
                        st.dataframe(pd.DataFrame(margin_info["daily_table"]).style.map(style_signed_numbers, subset=["融資增減(張)", "融券增減(張)"]).format({"融資餘額(張)": "{:,}", "融資增減(張)": "{:+,}", "融資使用率(%)": "{:.2f}%", "融券餘額(張)": "{:,}", "融券增減(張)": "{:+,}", "券資比(%)": "{:.2f}%"}), use_container_width=True, hide_index=True)

            elif sec_item == "📰":
                with st.container(border=True):
                    st.markdown(f"<div style='font-size:{round(16*scale, 1)}px; font-weight:bold; color:{TEXT_MAIN}; margin-bottom:10px;'>📰 近期市場消息與催化劑雷達：</div>", unsafe_allow_html=True)
                    if news_data["news"]:
                        for n in news_data["news"]:
                            st.markdown(f"""<div class="news-card"><span style="background:#2D3748; color:#63B3ED; padding:2px 6px; border-radius:4px; font-size:{round(12*scale, 1)}px; margin-right:6px;">{n['tag']}</span><span style="color:{TEXT_MUTED}; font-size:{round(12.5*scale, 1)}px; margin-right:8px;">🕒 {n['ago']}</span><a href="{n['link']}" target="_blank" style="color:{TEXT_MAIN}; text-decoration:none; font-weight:500;">{n['title']}</a></div>""", unsafe_allow_html=True)
                    else: st.caption("近期無重大個股新聞。")

            elif sec_item == "📐":
                st.subheader("📐 下個交易日 AH / NH / NL / AL 當沖支撐壓力四價位")
                levels = [("AL 極端破底支撐", cdp_vals["AL"], "#2ECC71"), ("NL 常態回檔支撐", cdp_vals["NL"], "#3498DB"), ("NH 常態反彈壓力", cdp_vals["NH"], "#E67E22"), ("AH 極端突破壓力", cdp_vals["AH"], "#E74C3C")]
                fig_cdp = go.Figure(go.Bar(y=[x[0] for x in levels], x=[x[1] for x in levels], orientation='h', text=[f"{x[1]} 元" for x in levels], textposition='outside', textfont=dict(size=int(12 * scale), color=TEXT_MAIN), marker_color=[x[2] for x in levels]))
                fig_cdp.add_vline(x=close_price, line_width=2, line_dash="dash", line_color=TEXT_MAIN)
                fig_cdp.update_layout(xaxis=dict(range=[min(cdp_vals["AL"], close_price) * 0.95, max(cdp_vals["AH"], close_price) * 1.08], tickfont=dict(size=int(11 * scale), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True), yaxis=dict(tickfont=dict(size=int(12 * scale), color=TEXT_MAIN), automargin=True), height=int(270 * max(1.0, scale * 0.95)), margin=dict(l=10, r=40, t=25, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN))
                st.plotly_chart(fig_cdp, use_container_width=True, theme=None)

        render_cta_box(
            f"💬 想針對【{selected_code} {stock_name}】討論三週期共振買賣點、外本比/投本比籌碼或申請專屬手續費優惠嗎？" if is_public_promo else f"💬 想索取【{selected_code} {stock_name}】今日盤後「關鍵主力分點買賣明細 / 法人研究報告」或討論操作策略嗎？",
            "💬 點此私訊專屬營業員：一對一諮詢與申請專屬手續費折數" if is_public_promo else f"💬 點此私訊您的專屬營業員：索取【{stock_name}】主力分點籌碼與部位健檢",
            cfg["broker_line_url"]
        )

# ------------------------------------------------------------------
# 【分頁 2：🧮 呼叫零延遲局部刷新區塊 (@st.fragment)】
# ------------------------------------------------------------------
elif cur_tab == 2:
    if check_tab_password_gate(2, "unlocked_tab2", cfg.get("lock_tab2", False), cfg.get("pwd_tab2", "TICK888"), "現沖與隔日沖獲利價位試算室", "請輸入通行碼解鎖。", cfg["broker_line_url"]):
        render_fast_profit_calculator(cfg["broker_line_url"], is_public_promo)

# ------------------------------------------------------------------
# 【分頁 3：🚦 大盤 5 維度動態評分 & 全市場活水主流族群快篩】
# ------------------------------------------------------------------
elif cur_tab == 3:
    if check_tab_password_gate(3, "unlocked_tab4", cfg.get("lock_tab4", False), cfg.get("pwd_tab4", "VIP888"), "大盤期現貨風向與主流族群雷達", "輸入本季基礎 VIP 通行碼即可解鎖「大盤資金風向球」與「全市場動態主流族群」。", cfg["broker_line_url"]):
        tb4_c1, tb4_c2 = st.columns([7.5, 2.5])
        tb4_c1.subheader("🚦 台股大盤資金風向球 & 實戰總結論")
        if tb4_c2.button("🔄 重新掃描族群與大盤", use_container_width=True):
            for fn in (de.fetch_taiex_market_data, de._fetch_twse_official_taiex_kline, de.auto_sync_market_chips_cached, de.fetch_full_market_snapshot_and_breadth, de.scan_sector_performance):
                try: fn.clear()
                except Exception: pass
            st.rerun()

        with st.spinner("⚡ 正在載入證交所官方大盤真實日K、新台幣匯率、費半連動與三大法人期現貨..."):
            cfg = de.auto_sync_market_chips_cached(fm_token_str)
            taiex = de.fetch_taiex_market_data()
            breadth_fg = de.fetch_full_market_snapshot_and_breadth(cfg.get("cnn_fear_greed", 34))

        if not taiex["ok"]: st.error(f"無法連線取得加權指數資料。底層原因：{taiex.get('err_msg', '網路限制')}")
        else:
            t_close, t_ma20, t_deduct = taiex["close"], taiex["ma20"], taiex["deduct"]
            foi, foi_chg = int(cfg["mkt_foreign_oi"]), int(cfg.get("mkt_foreign_oi_chg", -1420))
            sp_f, sp_t, sp_d = float(cfg.get("mkt_spot_foreign", 159.22)), float(cfg.get("mkt_spot_trust", 118.07)), float(cfg.get("mkt_spot_dealer", 21.65))
            sp_tot = round(sp_f + sp_t + sp_d, 2)
            m_bal, m_chg, m_chg3 = float(cfg.get("mkt_margin_bal", 6233.87)), float(cfg.get("mkt_margin_chg", -104.93)), float(cfg.get("mkt_margin_chg_3d", -147.13))
            s_bal, s_chg = int(cfg.get("mkt_short_bal", 217708)), int(cfg.get("mkt_short_chg", 1169))
            m_prev, s_prev = m_bal - m_chg, s_bal - s_chg
            m_chg_pct, s_chg_pct = (round((m_chg / m_prev) * 100, 2) if m_prev > 0 else 0.0), (round((s_chg / s_prev) * 100, 2) if s_prev > 0 else 0.0)

            mkt_eval = de.evaluate_taiex_market_score(taiex, cfg, breadth_fg, taiex.get("macro"), BULL_COLOR, BEAR_COLOR, WARN_COLOR)
            mkt_total, m_light, m_color, m_cta_title, m_cta_btn = mkt_eval["total"], mkt_eval["light"], mkt_eval["color"], mkt_eval["cta_title"], mkt_eval["cta_btn"]
            macro = mkt_eval["macro"]

            st.markdown(f"<p style='font-size:{round(14*scale, 1)}px; color:{TEXT_MUTED};'>📅 <b>最新有效交易日：{taiex['date']}</b> ｜ 加權指數：<b>{t_close:,} 點</b>（漲跌 <b>{taiex['chg']:+} 點</b>） ｜ 💵 新台幣匯率：<b>{macro['fx_rate']}</b>（近5日 {macro['fx_chg_5d']:+.2f}） ｜ 🌎 費半：<b>{macro['sox_chg_1d_pct']:+.2f}%</b>（20日相關係數 <b>r={macro['sox_corr_20d']}</b>）</p>", unsafe_allow_html=True)

            st.markdown(f"""<div class="score-banner"><div style="flex: 1; min-width: 240px;">
            <div style="font-size: {round(13.5 * scale, 1)}px; color: {TEXT_MUTED}; margin-bottom: 4px;">🚦 今日台股大盤多空風向燈號 & 實戰總結論</div>
            <div style="font-size: {round(19 * scale, 1)}px; font-weight: bold; color: {m_color}; margin-bottom: 8px;">{m_light}</div>
            <div style="font-size: {round(14.2 * scale, 1)}px; color: {TEXT_MAIN}; line-height: 1.7; background: {SCORE_BOX_BG}; padding: 10px 14px; border-radius: 8px; border-left: 4px solid {m_color}; margin-bottom: 8px;">{mkt_eval['summary_action_html']}</div></div>
            <div style="text-align: center; padding: 12px 18px; background: {SCORE_BOX_BG}; border-radius: 10px; border: 1px solid {CARD_BORDER};">
            <div style="font-size: {round(12.5 * scale, 1)}px; color: {TEXT_MUTED};">大盤動態風向分</div>
            <div style="font-size: {round(32 * scale, 1)}px; font-weight: bold; color: {m_color};">{mkt_total}<span style="font-size:{round(14 * scale, 1)}px; color:{TEXT_SUB};"> / 100</span></div></div></div>""", unsafe_allow_html=True)

            with st.expander(f"🧮 點此查看今日大盤【{mkt_total} / 100 分】之 5 大維度動態給分明細表（含匯率活水與費半相關係數權重）"):
                st.dataframe(pd.DataFrame(mkt_eval["breakdown"], columns=["評估維度", "本項得分", "客觀數據動態計分依據"]), use_container_width=True, hide_index=True)

            st.markdown(f"""<div class="pillar-grid">
            <div class="pillar-card"><div class="pillar-title"><span>🌍 1. 外資期現貨</span>{'<span class="tag-bull">現貨買超</span>' if sp_f > 0 else '<span class="tag-bear">現貨調節</span>'}</div><div class="pillar-main">現貨 {fmt_colored_num(sp_f, '億', True)}</div><div class="pillar-sub">- <b>台指期未平倉淨額：</b><b>{foi:,} 口</b><br>- <b>期貨單日增減：</b>{fmt_colored_num(foi_chg, '口')}</div></div>
            <div class="pillar-card"><div class="pillar-title"><span>🏦 2. 投信與匯率活水</span>{'<span class="tag-bull">台幣升值</span>' if macro['fx_chg_5d'] <= 0 else '<span class="tag-bear">台幣貶值</span>'}</div><div class="pillar-main">投信 {fmt_colored_num(sp_t, '億', True)}</div><div class="pillar-sub">- <b>三大法人現貨合計：</b>{fmt_colored_num(sp_tot, '億', True)}<br>- <b>台幣匯率(TWD=X)：</b><b>{macro['fx_rate']}</b> (5日{macro['fx_chg_5d']:+.2f})</div></div>
            <div class="pillar-card"><div class="pillar-title"><span>📈 3. 大盤融資餘額</span>{'<span class="tag-bull">融資增加</span>' if m_chg > 0 else '<span class="tag-bear">融資減肥</span>'}</div><div class="pillar-main">{m_bal:,} 億元</div><div class="pillar-sub">- <b>單日增減金額：</b>{fmt_colored_num(m_chg, '億元', True)} ({m_chg_pct:+}%)<br>- <b>近3日累計增減：</b>{fmt_colored_num(m_chg3, '億元', True)}</div></div>
            <div class="pillar-card"><div class="pillar-title"><span>📉 4. 大盤融券餘額</span>{'<span class="tag-bull">融券增加</span>' if s_chg > 0 else '<span class="tag-bear">融券回補</span>'}</div><div class="pillar-main">{s_bal:,} 張</div><div class="pillar-sub">- <b>單日增減張數：</b>{fmt_colored_num(s_chg, '張')} ({s_chg_pct:+}%)<br>- <b>前一日融券餘額：</b>{s_prev:,} 張</div></div></div>""", unsafe_allow_html=True)

            st.markdown("#### 🛡️ 大盤技術轉折 ＆ 市場廣度情緒指標")
            mkt_td_str = f"▲ 下跌低九第 {taiex['td_buy']} 天" if taiex["td_buy"] > 0 else (f"▼ 上漲高九第 {taiex['td_sell']} 天" if taiex["td_sell"] > 0 else "⚪ 無連續九轉")
            fg_val = breadth_fg["fg_score"]
            fg_tag = '<span class="tag-bull">🔥極度恐慌(&lt;20)</span>' if fg_val <= 20 else ('<span class="tag-neutral">⚠️恐慌(&lt;30)</span>' if fg_val <= 30 else ('<span class="tag-bear">🚨貪婪(&gt;75)</span>' if fg_val >= 75 else '<span class="tag-neutral">情緒中性</span>'))
            kd_tag = '<span class="tag-bull">🔥超賣(&lt;20)</span>' if taiex["K"] < 20 else ('<span class="tag-bull">KD金叉</span>' if taiex["K"] >= taiex["D"] else '<span class="tag-bear">KD死叉</span>')
            bb_tag = '<span class="tag-bull">✅站回下軌</span>' if taiex["reclaimed_bb_low"] else ('<span class="tag-bear">🚨破下軌</span>' if t_close < taiex["bb_lower"] else '<span class="tag-neutral">軌內運行</span>')
            breadth_main_str = f"上漲 {breadth_fg['up_cnt']} ／ 下跌 {breadth_fg['down_cnt']} 家" if breadth_fg["breadth_ok"] else f"CNN 恐懼貪婪：{fg_val}"

            st.markdown(f"""<div class="pillar-grid">
            <div class="pillar-card"><div class="pillar-title"><span>📉 1. KD / RSI / 月線乖離</span>{kd_tag}</div><div class="pillar-main">K：{taiex['K']} ｜ RSI：{taiex['rsi']}</div><div class="pillar-sub">- <b>KD 狀態：</b>K({taiex['K']}) / D({taiex['D']})<br>- <b>月線乖離率(BIAS)：</b><b>{taiex['bias20']:+.2f}%</b></div></div>
            <div class="pillar-card"><div class="pillar-title"><span>🟣 2. 布林通道 & K棒型態</span>{bb_tag}</div><div class="pillar-main">下軌 {taiex['bb_lower']:,} 點</div><div class="pillar-sub">- <b>布林位階：</b>{taiex['bb_status']}<br>- <b>今日K棒：</b>{taiex['k_pattern_str']}</div></div>
            <div class="pillar-card"><div class="pillar-title"><span>🔢 3. 神奇九轉 & 費半相關</span>{'<span class="tag-bull">高連動</span>' if macro['sox_corr_20d'] >= 0.5 else '<span class="tag-neutral">低連動</span>'}</div><div class="pillar-main">{'▲低' + str(taiex['td_buy']) if taiex['td_buy']>0 else ('▼高' + str(taiex['td_sell']) if taiex['td_sell']>0 else '九轉中性')}</div><div class="pillar-sub">- <b>神奇九轉：</b><b>{mkt_td_str}</b><br>- <b>費半指數：</b>{macro['sox_close']:,} ({macro['sox_chg_1d_pct']:+.2f}% / r={macro['sox_corr_20d']})</div></div>
            <div class="pillar-card"><div class="pillar-title"><span>🌡️ 4. 市場廣度(騰落) & 情緒</span>{fg_tag}</div><div class="pillar-main">{breadth_main_str}</div><div class="pillar-sub">- <b>上市櫃上漲佔比：</b><b>{breadth_fg['up_ratio']}%</b> (淨差 {breadth_fg['adl_diff']:+,}家)<br>- <b>CNN 恐懼貪婪：</b><b>{fg_val}</b> / 100</div></div></div>""", unsafe_allow_html=True)

            mkt_cdp = de.calculate_cdp(taiex["high"], taiex["low"], t_close)
            m_chk1, m_chk2, m_chk3 = st.columns(3)
            show_mkt_bb = m_chk1.checkbox("🟣 顯示大盤布林通道", value=True, key="mkt_bb_chk")
            show_mkt_td = m_chk2.checkbox("🔢 顯示大盤神奇九轉 (TD9)", value=True, key="mkt_td_chk")
            show_mkt_cdp = m_chk3.checkbox("📐 疊加明日大盤 AH/NH/NL/AL 四價位線", value=True, key="mkt_cdp_chk")
            st.plotly_chart(plot_universal_kline_chart(taiex["kline_60"], scale, show_bb=show_mkt_bb, show_td=show_mkt_td, show_cdp=show_mkt_cdp, cdp_vals=mkt_cdp, show_volume=False), use_container_width=True, theme=None)

            st.markdown(f"""<div class="metric-card" style="margin-top:8px;"><h4>📐 下個交易日【加權指數 AH / NH / NL / AL 關鍵四價位】</h4>
            - 🔥 <b>壓力區間：</b>常態反彈壓力 <b>NH {mkt_cdp['NH']:,} 點</b> ｜ 極端突破壓力 <b>AH {mkt_cdp['AH']:,} 點</b><br>
            - 🛡️ <b>支撐區間：</b>常態回檔支撐 <b>NL {mkt_cdp['NL']:,} 點</b> ｜ 極端破底支撐 <b>AL {mkt_cdp['AL']:,} 點</b></div>""", unsafe_allow_html=True)

            with st.spinner("🔥 正在掃描全市場 2,100 檔動態活水並更新主流族群強弱排行..."):
                sector_rank = de.scan_sector_performance(json.dumps(sector_map_all, ensure_ascii=False), margins_global_map)

            if sector_rank:
                top3_sectors_str = "、".join([f"{s['族群名稱']}(近1日{s['近1日平均漲跌(%)']:+}% / 5日{s['近5日平均漲跌(%)']:+}%)" for s in sector_rank[:3]])
                st.markdown(f"#### 🔥 台股主流族群「全市場 2,100 檔動態活水注入」強弱總覽（共 {len(sector_rank)} 大族群）")
                st.caption(f"💡 **動態活水機制說明：** 系統自動從全市場 2,100 檔中抓取今日帶量轉強的新飆股，依官方產業歸入對應族群（標示 **🔥**），若有新興強勢產業則自動浮現為 **🌟 [動態主流]**！目前領漲前三強：**{top3_sectors_str}**")
                df_sec_overview = pd.DataFrame([{"主流族群分類 (含動態浮現產業)": s["族群名稱"], "成分股數": s.get("成分股數", ""), "近1日平均漲跌(%)": s["近1日平均漲跌(%)"], "近5日(一週)平均漲跌(%)": s["近5日平均漲跌(%)"], "領漲指標股 (🔥代表今日全市場動態入榜)": s.get("近5日領漲指標股", "")} for s in sector_rank])
                st.dataframe(df_sec_overview.style.map(style_signed_numbers, subset=["近1日平均漲跌(%)", "近5日(一週)平均漲跌(%)"]).format({"近1日平均漲跌(%)": "{:+.2f}%", "近5日(一週)平均漲跌(%)": "{:+.2f}%"}), use_container_width=True, hide_index=True, height=410)

                sec_options = [f"👉 {s['族群名稱']} （{s.get('成分股數','')}｜近1日 {s['近1日平均漲跌(%)']:+.2f}% ｜ 近5日 {s['近5日平均漲跌(%)']:+.2f}%）" for s in sector_rank]
                chosen_sec_label = st.selectbox("🔎 請選擇想展開查看成分股之主流族群：", options=sec_options, index=0)
                chosen_sec_data = sector_rank[sec_options.index(chosen_sec_label)]

                st.markdown(f"##### 📋 【{chosen_sec_data['族群名稱']}】成分股報價與位階清單（標示 🔥 為今日全市場爆量強勢自動歸入該族群之新星）")
                df_sec_stocks = pd.DataFrame([{k: v for k, v in item.items() if not str(k).startswith("_")} for item in chosen_sec_data["stocks"]])
                st.dataframe(df_sec_stocks.style.map(style_signed_numbers, subset=["近1日漲跌(%)", "近5日漲跌(%)"]).format({"最新收盤(元)": "{:.2f}", "月線(20MA)": "{:.2f}", "近1日漲跌(%)": "{:+.2f}%", "近5日漲跌(%)": "{:+.2f}%"}), use_container_width=True, hide_index=True)

                st.markdown("###### 👆 點擊下方任一成分股按鈕，立即跳轉【分頁 1】查看三週期共振與 4 維度機構評分：")
                stk_list = chosen_sec_data["stocks"]
                btn_cols = st.columns(min(4, max(1, len(stk_list))))
                for idx_s, s_item in enumerate(stk_list):
                    with btn_cols[idx_s % len(btn_cols)]:
                        st.button(f"🔍 {s_item['代號']} {s_item['名稱']} ({s_item['近1日漲跌(%)']:+.1f}%)", key=f"sec_btn_{chosen_sec_data['族群名稱']}_{s_item['代號']}", use_container_width=True, on_click=jump_to_tab1_with_stock, args=(s_item["代號"], s_item["名稱"], s_item.get("_mkt", "TWSE")))

            render_cta_box(m_cta_title, m_cta_btn, cfg["broker_line_url"])

# ==========================================
# 6. 右下角懸浮「🤖 AI 戰情助手」Popover (點擊切換按鈕自動收合小助手 + 強制全頁跳轉分頁1 + 保留對話)
# ==========================================
@st.fragment
def render_floating_ai_assistant(active_code, active_name, cfg_obj, quotes_df):
    with st.popover("🤖 AI 戰情助手"):
        hd_c1, hd_c2 = st.columns([7.2, 2.8])
        hd_c1.markdown("#### 🤖 隨身 AI 短線戰情助手")
        if hd_c2.button("🗑️清空", key="btn_clr_ai_chat", use_container_width=True):
            st.session_state.ai_chat_history = [dict(DEFAULT_STATES["ai_chat_history"][0])]
            st.rerun()

        st.caption(f"目前背景主畫面：**{active_code} {active_name}**（可直接輸入任何個股如 3167 或 ETF 如 0050、00937B 獨立提問）")
        q_col1, q_col2 = st.columns(2)
        quick_q = None
        if q_col1.button(f"📊 診斷 {active_code} {active_name}", use_container_width=True): quick_q = f"請幫我診斷 {active_code} {active_name}"
        if q_col2.button("🛡️ 大盤匯率費半與總結", use_container_width=True): quick_q = "請告訴我今日大盤5維度評分、匯率費半連動與實戰操作總結論"

        with st.container(height=310, border=True):
            for idx_m, msg in enumerate(st.session_state.ai_chat_history[-8:]):
                with st.chat_message(msg["role"]):
                    st.markdown(str(msg["content"]).replace("`", "**"))
                    btn_c, btn_n, btn_m = msg.get("stock_code"), msg.get("stock_name", ""), msg.get("stock_mkt", "TWSE")
                    if btn_c:
                        is_already_on_tab1 = (int(st.session_state.active_nav_tab) == 1) and (str(btn_c) == str(st.session_state.target_stock_code))
                        btn_label = f"✅ 目前分頁1已顯示【{btn_c} {btn_n}】(點此收合小助手看圖)" if is_already_on_tab1 else f"🚀 點此收合小助手並跳轉【分頁1：{btn_c} {btn_n}】K線圖 ➔"
                        if st.button(btn_label, key=f"ai_jmp_btn_{idx_m}_{btn_c}", use_container_width=True, type="primary" if not is_already_on_tab1 else "secondary"):
                            jump_to_tab1_with_stock(btn_c, btn_n, btn_m)
                            st.rerun(scope="app")

        user_in = st.chat_input("輸入個股(如 3167)、ETF(如 0050)或大盤問題...")
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
                    if len(s_name) >= 2 and s_name in final_q:
                        target_c, target_n = name_to_code_map[s_name], s_name
                        break

            if not m_code and any(k in final_q for k in ["大盤", "加權", "台指", "止跌", "匯率", "費半"]):
                tx, bfg = de.fetch_taiex_market_data(), de.fetch_full_market_snapshot_and_breadth(cfg_obj.get("cnn_fear_greed", 34))
                if tx["ok"]:
                    m_ev = de.evaluate_taiex_market_score(tx, cfg_obj, bfg, tx.get("macro"), BULL_COLOR, BEAR_COLOR, WARN_COLOR)
                    mc, m_cdp = m_ev["macro"], de.calculate_cdp(tx["high"], tx["low"], tx["close"])
                    reply_txt = (
                        f"🛡️ **【台股大盤 5 維度實戰快篩（{tx['date']}｜總分 {m_ev['total']}/100）】**\n"
                        f"- **燈號診斷**：**{m_ev['light']}**\n"
                        f"- **加權指數**：**{tx['close']:,} 點**（單日 **{tx['chg']:+} 點**，月線乖離 **{tx['bias20']:+.2f}%**）\n"
                        f"- **匯率與費半**：台幣 **{mc['fx_rate']}**（5日 **{mc['fx_chg_5d']:+.2f}**）｜費半 **{mc['sox_chg_1d_pct']:+.2f}%**（20日相關係數 **r={mc['sox_corr_20d']}**）\n"
                        f"- **市場廣度**：上市櫃上漲 **{bfg['up_cnt']} 家** / 下跌 **{bfg['down_cnt']} 家**（上漲比 **{bfg['up_ratio']}%**）\n"
                        f"- **明日大盤四價位**：壓力 **NH {m_cdp['NH']:,} ／ AH {m_cdp['AH']:,}** ｜ 支撐 **NL {m_cdp['NL']:,} ／ AL {m_cdp['AL']:,}**\n\n"
                        f"{m_ev['summary_action']}"
                    )
                else: reply_txt = "目前暫時無法取得大盤資料，請稍後再試。"
                st.session_state.ai_chat_history.append({"role": "assistant", "content": reply_txt})
            else:
                t_mkt = code_to_mkt_map.get(target_c, master_stock_dict.get(target_c, {}).get("市場", "TPEX" if target_c.endswith("B") else "TWSE"))
                t_d = de.fetch_technical_indicators(target_c, t_mkt)
                t_60 = de.fetch_intraday_kline_full(target_c, t_mkt, "60m")
                t_5 = de.fetch_intraday_kline_full(target_c, t_mkt, "5m")
                c_d = de.fetch_chip_data_20d(target_c, str(cfg_obj.get("finmind_token", "")).strip())
                m_d = de.fetch_margin_short_20d(target_c, str(cfg_obj.get("finmind_token", "")).strip())
                f_d = de.fetch_fundamental_revenue_and_shareholding(target_c, str(cfg_obj.get("finmind_token", "")).strip())
                tx_q = de.fetch_taiex_market_data()
                if t_d["ok"]:
                    if target_n == target_c:
                        snap_m = de.fetch_full_market_snapshot_and_breadth().get("market_snap", {})
                        if target_c in snap_m: target_n = snap_m[target_c]["name"]
                    ev = de.evaluate_three_pillars(t_d, c_d, BULL_COLOR, BEAR_COLOR, WARN_COLOR, tech_60m=t_60, tech_5m=t_5, margin_info=m_d, fund_info=f_d, taiex_info=tx_q, code_str=target_c)
                    cdp_v, p_c = de.calculate_cdp(t_d["high"], t_d["low"], t_d["close"]), c_d["periods"]
                    mtf_r = de.evaluate_mtf_resonance(t_d, t_60, t_5, cdp_v, BULL_COLOR, BEAR_COLOR, WARN_COLOR)
                    is_etf_q = str(target_c).startswith("00")
                    rev_str = f"{f_d['rev_month']} 營收 YoY **{f_d['yoy_latest']:+.1f}%** (加速度 **{f_d['yoy_accel']:+.1f}%**)" if (f_d.get("has_rev") and not is_etf_q) else f"ETF 均線乖離率 **{round(((t_d['close']-t_d['ma20'])/t_d['ma20'])*100, 2):+.2f}%** (留意低九與散戶融資)"
                    api_k, reply_txt = str(cfg_obj.get("gemini_api_key", "")).strip(), ""
                    if api_k and not quick_q:
                        try:
                            sys_ctx = f"你是專業台股短線戰情AI助手。用戶正在詢問【{target_c} {target_n}】（必須針對 {target_c} {target_n} 回答，嚴禁回答其他股票！）。最新官方對帳數據：現價{t_d['close']}元（日期{t_d['date']}，單日{t_d['chg_1d_pct']:+.2f}%），機構總分{ev['total']}/100分，單日Alpha {ev['alpha_1d']:+.2f}%，5日法人控盤度{ev['inst_vol_ratio']:+.1f}%，三週期共振：{mtf_r['title']}，基本面/位階：{rev_str}。明日當沖四價位：極端突破AH={cdp_v['AH']}、常態壓力NH={cdp_v['NH']}、常態支撐NL={cdp_v['NL']}、極端破底AL={cdp_v['AL']}（請勿提CDP中軸）。實戰診斷：{ev['v_desc']}。請針對用戶問題「{final_q}」直接給出重點結論、操作觀察重點與四價位支撐壓力（嚴禁使用反引號 ` 包覆文字，改用粗體 ** 標示重點）。"
                            g_resp = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_k}", json={"contents": [{"parts": [{"text": sys_ctx}]}]}, timeout=12, verify=False)
                            if g_resp.status_code == 200: reply_txt = g_resp.json()["candidates"][0]["content"]["parts"][0]["text"].replace("`", "**")
                        except Exception: reply_txt = ""
                    if not reply_txt:
                        reply_txt = (
                            f"🔍 **【{target_c} {target_n} 機構四維度快篩（{t_d['date']} 現價 {t_d['close']} 元｜單日 {t_d['chg_1d_pct']:+.2f}%）】**\n"
                            f"- **機構總分**：**{ev['total']} / 100 分**（單日Alpha **{ev['alpha_1d']:+.2f}%** ｜ 5日法人佔量 **{ev['inst_vol_ratio']:+.1f}%**）\n"
                            f"- **三週期共振**：**{mtf_r['title']}**\n"
                            f"- **{'ETF 位階觀察' if is_etf_q else '基本面動能'}**：{rev_str}\n"
                            f"- **三大法人合計**：1日 **{p_c[1]['tot']:+,}張** ｜ 3日 **{p_c[3]['tot']:+,}張** ｜ 5日 **{p_c[5]['tot']:+,}張**\n"
                            f"- **明日當沖四價位**：\n"
                            f"  • 🔥 壓力：**NH {cdp_v['NH']} 元** ／ **AH {cdp_v['AH']} 元**\n"
                            f"  • 🛡️ 支撐：**NL {cdp_v['NL']} 元** ／ **AL {cdp_v['AL']} 元**\n\n"
                            f"{ev['v_desc']}"
                        )
                    st.session_state.ai_chat_history.append({"role": "assistant", "content": reply_txt, "stock_code": target_c, "stock_name": target_n, "stock_mkt": t_mkt})
                else:
                    st.session_state.ai_chat_history.append({"role": "assistant", "content": f"查無 {target_c} 的即時資料，請確認代號是否正確。"})
            st.rerun()

render_floating_ai_assistant(current_active_code, current_active_name, cfg, df_quotes)

st.markdown("""<div class="disclaimer"><b>⚠️ 合規與免責聲明：</b><br>
1. 本頁面所有資訊皆由公開歷史交易數據，經固定數學公式（如 AH/NH/NL/AL 四價位系統、移動平均線、布林通道、TD神奇九轉計數、皮爾森相關係數、KD/MACD/RSI 公式）與公開新聞 RSS 自動產出。<br>
2. 本工具僅供客觀統計數據檢索與交易成本試算參考，<b>絕不構成任何形式之有價證券或期貨買賣建議、推薦或目標價預測</b>。投資人交易前應獨立判斷並自負風險。</div>""", unsafe_allow_html=True)
