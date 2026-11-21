# ==============================================================================
# ⚠️ 【重要防呆提醒】本檔案是：ui_charts.py (視覺化圖表與 CSS 樣式引擎 v13.0)
# 請在 GitHub 點選 Add file -> Create new file，檔名填 ui_charts.py 並貼上！
# ==============================================================================
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_theme_palette(is_dark=True):
    if is_dark:
        return {
            "BG_MAIN": "#0E1117", "BG_SIDEBAR": "#161B26", "TEXT_MAIN": "#FFFFFF",
            "TEXT_SUB": "#CBD5E0", "TEXT_MUTED": "#A0AEC0", "CARD_BG": "#1A1F2C",
            "CARD_BG_ALT": "#1E232F", "CARD_BORDER": "#2D3748",
            "BANNER_BG": "linear-gradient(135deg, #16222A 0%, #3A6073 100%)",
            "SCORE_BOX_BG": "rgba(0,0,0,0.38)", "NEWS_BG": "#161B26",
            "PLOT_BG": "#141824", "GRID_COLOR": "#2D3748",
            "BULL_COLOR": "#FF6B6B", "BEAR_COLOR": "#2ECC71", "WARN_COLOR": "#F1C40F"
        }
    return {
        "BG_MAIN": "#F8FAFC", "BG_SIDEBAR": "#F1F5F9", "TEXT_MAIN": "#0F172A",
        "TEXT_SUB": "#334155", "TEXT_MUTED": "#475569", "CARD_BG": "#FFFFFF",
        "CARD_BG_ALT": "#FFFFFF", "CARD_BORDER": "#CBD5E1",
        "BANNER_BG": "linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%)",
        "SCORE_BOX_BG": "rgba(255,255,255,0.85)", "NEWS_BG": "#F1F5F9",
        "PLOT_BG": "#FFFFFF", "GRID_COLOR": "#E2E8F0",
        "BULL_COLOR": "#DC2626", "BEAR_COLOR": "#16A34A", "WARN_COLOR": "#D97706"
    }

def inject_Wait_and_CSS(pal, scale=1.05, close_seq=0):
    BG_MAIN, BG_SIDEBAR, TEXT_MAIN, TEXT_SUB, TEXT_MUTED = pal["BG_MAIN"], pal["BG_SIDEBAR"], pal["TEXT_MAIN"], pal["TEXT_SUB"], pal["TEXT_MUTED"]
    CARD_BG, CARD_BG_ALT, CARD_BORDER, BANNER_BG = pal["CARD_BG"], pal["CARD_BG_ALT"], pal["CARD_BORDER"], pal["BANNER_BG"]
    NEWS_BG, BULL_COLOR, BEAR_COLOR, WARN_COLOR = pal["NEWS_BG"], pal["BULL_COLOR"], pal["BEAR_COLOR"], pal["WARN_COLOR"]
    card_min_w = "245px" if scale >= 1.15 else "210px"

    st.markdown(f"""<style>
.stApp {{ background-color: {BG_MAIN} !important; color: {TEXT_MAIN} !important; }}
.block-container {{ max-width: 1260px !important; padding: 3.4rem 2rem 5rem 2rem !important; }}
section[data-testid="stSidebar"] {{ background-color: {BG_SIDEBAR} !important; color: {TEXT_MAIN} !important; }}
h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, [data-testid="stCaptionContainer"] {{ color: {TEXT_MAIN} !important; }}
.stButton > button {{ background-color: {CARD_BG} !important; color: {TEXT_MAIN} !important; border: 1px solid {CARD_BORDER} !important; font-weight: bold !important; white-space: normal !important; line-height: 1.35 !important; padding: 0.45rem 0.7rem !important; min-height: 2.45rem !important; }}
.stButton > button:hover {{ border-color: #4A90E2 !important; color: #60A5FA !important; }}
.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: #FFFFFF !important; border: 1.5px solid #60A5FA !important; }}
div[data-testid="stPopover"] {{ position: fixed !important; bottom: 24px !important; right: 24px !important; left: auto !important; width: auto !important; max-width: 220px !important; z-index: 999999 !important; }}
div[data-testid="stPopover"] > div, div[data-testid="stPopover"] > div > button, div[data-testid="stPopover"] > button {{ width: auto !important; background: linear-gradient(135deg, #00D26A 0%, #009E4F 100%) !important; color: #000000 !important; border-radius: 50px !important; padding: 10px 18px !important; font-size: 15px !important; font-weight: 800 !important; border: 2px solid #FFFFFF !important; box-shadow: 0 6px 20px rgba(0,210,106,0.55) !important; white-space: nowrap !important; }}
div[data-testid="stPopover"] > div > button *, div[data-testid="stPopover"] > button * {{ color: #000000 !important; font-weight: 800 !important; }}
div[data-baseweb="popover"] > div, div[data-testid="stPopoverBody"] {{ background-color: {CARD_BG} !important; color: {TEXT_MAIN} !important; border: 1.5px solid #4A90E2 !important; border-radius: 14px !important; max-width: 92vw !important; }}
div[data-testid="stPopoverBody"] h1, div[data-testid="stPopoverBody"] h2, div[data-testid="stPopoverBody"] h3, div[data-testid="stPopoverBody"] h4 {{ font-size: 16px !important; line-height: 1.4 !important; margin: 6px 0 !important; color: {TEXT_MAIN} !important; }}
div[data-testid="stPopoverBody"] p, div[data-testid="stPopoverBody"] span, div[data-testid="stPopoverBody"] li, div[data-testid="stPopoverBody"] strong, div[data-testid="stPopoverBody"] b, div[data-testid="stPopoverBody"] div[data-testid="stCaptionContainer"] {{ color: {TEXT_MAIN} !important; font-size: 14.5px !important; line-height: 1.6 !important; }}
div[data-testid="stPopoverBody"] .stButton > button {{ background-color: {BG_MAIN} !important; color: {TEXT_MAIN} !important; border: 1px solid #4A90E2 !important; border-radius: 8px !important; }}
div[data-testid="stPopoverBody"] .stButton > button * {{ color: {TEXT_MAIN} !important; }}
div[data-testid="stPopoverBody"] .stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important; color: #FFFFFF !important; border: 1.5px solid #60A5FA !important; }}
div[data-testid="stPopoverBody"] .stButton > button[kind="primary"] * {{ color: #FFFFFF !important; }}
div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] {{ background-color: {CARD_BG_ALT} !important; border: 1px solid {CARD_BORDER} !important; border-radius: 8px !important; padding: 8px 10px !important; margin-bottom: 6px !important; }}
div[data-testid="stPopoverBody"] [data-testid="stChatInput"] > div {{ background-color: {BG_MAIN} !important; border: 1px solid {CARD_BORDER} !important; }}
div[data-testid="stPopoverBody"] textarea {{ color: {TEXT_MAIN} !important; -webkit-text-fill-color: {TEXT_MAIN} !important; caret-color: {TEXT_MAIN} !important; }}
@media (max-width: 768px) {{
    .block-container {{ padding: 2.2rem 0.65rem 5.5rem 0.65rem !important; }}
    div[data-testid="stPopover"] {{ bottom: 68px !important; right: 14px !important; left: auto !important; width: auto !important; max-width: 185px !important; }}
    div[data-testid="stPopover"] > div > button, div[data-testid="stPopover"] > button {{ padding: 8px 14px !important; font-size: 13.5px !important; }}
}}
div[data-baseweb="tab-list"] {{ display: flex !important; flex-wrap: wrap !important; gap: 6px !important; }}
button[data-baseweb="tab"] {{ white-space: nowrap !important; padding: 0 12px !important; }}
button[data-baseweb="tab"] p {{ color: {TEXT_MAIN} !important; font-weight: bold !important; font-size: {round(14 * scale, 1)}px !important; white-space: nowrap !important; }}
.app-main-title {{ font-size: {round(21.5 * scale, 1)}px; font-weight: 800; color: {TEXT_MAIN}; margin: 0; }}
.score-banner {{ background: {BANNER_BG}; border-radius: 14px; padding: 16px 18px; margin-bottom: 14px; border: 1px solid #4A90E2; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }}
.pillar-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax({card_min_w}, 1fr)); gap: 12px; margin-bottom: 16px; }}
.pillar-card {{ background-color: {CARD_BG}; border-radius: 12px; padding: 14px 15px; border: 1px solid {CARD_BORDER}; box-shadow: 0 2px 6px rgba(0,0,0,0.08); box-sizing: border-box; overflow: hidden; }}
.pillar-title {{ font-size: {round(13.5 * scale, 1)}px; color: {TEXT_MUTED}; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; font-weight: 600; }}
.pillar-main {{ font-size: {round(18.5 * scale, 1)}px; font-weight: bold; margin-bottom: 8px; color: {TEXT_MAIN}; word-break: break-word; }}
.bar-bg {{ background-color: {CARD_BORDER}; border-radius: 6px; height: 7px; width: 100%; margin-bottom: 10px; overflow: hidden; }}
.pillar-sub {{ font-size: {round(13.5 * scale, 1)}px; color: {TEXT_SUB}; line-height: 1.65; }}
.tag-bull {{ background-color: rgba(231,76,60,0.15); color: {BULL_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {BULL_COLOR}; white-space: nowrap; }}
.tag-bear {{ background-color: rgba(46,204,113,0.15); color: {BEAR_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {BEAR_COLOR}; white-space: nowrap; }}
.tag-neutral {{ background-color: rgba(241,196,15,0.15); color: {WARN_COLOR}; padding: 2px 8px; border-radius: 4px; font-size: {round(11.5 * scale, 1)}px; font-weight: bold; border: 1px solid {WARN_COLOR}; white-space: nowrap; }}
.metric-card {{ background-color: {CARD_BG_ALT}; border-radius: 10px; padding: 16px; margin-bottom: 12px; border: 1px solid {CARD_BORDER}; border-left: 5px solid #00D26A; font-size: {round(15 * scale, 1)}px; line-height: 1.65; color: {TEXT_MAIN}; }}
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
        s.innerHTML = `g.hoverlayer g.hovertext > path, g.hoverlayer g.hovertext > rect, g.hoverlayer g.hovertext > text {{ transform: translate(68px, -10px) !important; }} g.hoverlayer g.hovertext {{ opacity: 0.92 !important; pointer-events: none !important; }}`;
        doc.head.appendChild(s);
    }}
    injectCSS(parentDoc);
    setInterval(() => {{ injectCSS(parentDoc); parentDoc.querySelectorAll('iframe').forEach(ifr => {{ try {{ if (ifr.contentDocument) injectCSS(ifr.contentDocument); }} catch (e) {{}} }}); }}, 800);

    const closeSeq = {int(close_seq)};
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

def render_cta_box(title_txt, btn_txt, line_url, scale=1.05, text_main="#FFFFFF"):
    st.markdown(f"""<div class="cta-box"><p style="font-size:{round(16*scale,1)}px; margin-bottom:12px; font-weight:bold; color:{text_main};">{title_txt}</p>
    <a href="{line_url}" target="_blank" style="background-color:#00D26A; color:#000000; padding:10px 20px; border-radius:8px; font-weight:bold; font-size:{round(15*scale,1)}px; text-decoration:none; display:inline-block;">{btn_txt}</a></div>""", unsafe_allow_html=True)

def check_tab_password_gate(tab_num, tab_key, is_locked, correct_pwd, gate_title, gate_desc, line_url, scale=1.05, text_main="#FFFFFF"):
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
    render_cta_box(f"🔑 還沒有【{gate_title}】的專屬通行碼嗎？", f"💬 點此私訊專屬營業員：索取【{gate_title}】解鎖密碼", line_url, scale, text_main)
    return False

def plot_universal_kline_chart(kline_records, scale_factor=1.05, show_bb=True, show_td=True, show_cdp=True, cdp_vals=None, show_volume=False, pal=None, is_dark=True):
    if pal is None: pal = get_theme_palette(is_dark)
    CARD_BG, TEXT_MAIN, GRID_COLOR, PLOT_BG = pal["CARD_BG"], pal["TEXT_MAIN"], pal["GRID_COLOR"], pal["PLOT_BG"]
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
        fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k["BB_Upper"], mode="lines", name="布林上軌", line=dict(color="rgba(52,152,219,0.65)", width=1.3, dash="dash"), hovertemplate="%{y:,.2f}"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_k[x_col], y=df_k["BB_Lower"], mode="lines", name="布林下軌", line=dict(color="rgba(46,204,113,0.75)", width=1.5, dash="dash"), fill="tonexty", fillcolor="rgba(52,152,219,0.05)", hovertemplate="%{y:,.2f}"), row=1, col=1)

    b_col, s_col = ("TD_Buy_Disp" if "TD_Buy_Disp" in df_k.columns else "TD_Buy"), ("TD_Sell_Disp" if "TD_Sell_Disp" in df_k.columns else "TD_Sell")
    if show_td and b_col in df_k.columns and s_col in df_k.columns:
        for _, r in df_k.iterrows():
            bv, sv = int(r.get(b_col, 0)), int(r.get(s_col, 0))
            if bv == 9: fig.add_annotation(x=r[x_col], y=float(r["Low"]), text="<b>▲低9</b>", showarrow=False, yshift=-15, font=dict(color="#00D26A", size=int(11*scale_factor)), bgcolor="rgba(0,210,106,0.16)", bordercolor="#00D26A", borderwidth=1, borderpad=2, row=1, col=1)
            elif 1 <= bv <= 8: fig.add_annotation(x=r[x_col], y=float(r["Low"]), text=f"<b>{bv}</b>", showarrow=False, yshift=-11, font=dict(color="#00D26A", size=int(9.5*scale_factor)), row=1, col=1)
            if sv == 9: fig.add_annotation(x=r[x_col], y=float(r["High"]), text="<b>▼高9</b>", showarrow=False, yshift=15, font=dict(color="#FF4B4B", size=int(11*scale_factor)), bgcolor="rgba(255,75,75,0.16)", bordercolor="#FF4B4B", borderwidth=1, borderpad=2, row=1, col=1)
            elif 1 <= sv <= 8: fig.add_annotation(x=r[x_col], y=float(r["High"]), text=f"<b>{sv}</b>", showarrow=False, yshift=11, font=dict(color="#FF4B4B", size=int(9.5*scale_factor)), row=1, col=1)

    if len(df_k) >= 20:
        dr, sc = df_k.iloc[-20], ("#F1C40F" if is_dark else "#D97706")
        dp = round(float(dr["Close"]), 2)
        fig.add_trace(go.Scatter(x=[dr[x_col]], y=[dp], mode="markers+text", name="20根扣抵", marker=dict(color=sc, size=13, symbol="star", line=dict(color="#000", width=1)), text=[f"⭐{dp}"], textposition="top center", textfont=dict(color=sc, size=int(10.5*scale_factor), weight="bold"), hoverinfo="skip"), row=1, col=1)
        fig.add_hline(y=dp, line_width=1.1, line_dash="dash", line_color=sc, annotation_text=f"扣抵 {dp}", annotation_position="bottom left", annotation_font=dict(color=sc, size=int(9.5*scale_factor)), row=1, col=1)

    if show_cdp and cdp_vals:
        for k, lbl, clr, pos in [("AH", "AH極端突破", "#EF4444", "top left"), ("NH", "NH常態壓力", "#F97316", "top right"), ("NL", "NL常態支撐", "#38BDF8", "bottom right"), ("AL", "AL極端破底", "#10B981", "bottom left")]:
            fig.add_hline(y=cdp_vals[k], line_width=1.1, line_dash="dot", line_color=clr, annotation_text=f"{lbl} {cdp_vals[k]}", annotation_position=pos, annotation_font=dict(color=clr, size=int(9.5*scale_factor)), row=1, col=1)

    if show_volume and "Volume" in df_k.columns:
        fig.add_trace(go.Bar(x=df_k[x_col], y=df_k["Volume"], name="量(張)", marker_color=["#FF4B4B" if c >= o else "#00D26A" for c, o in zip(df_k["Close"], df_k["Open"])], hovertemplate="%{y:,.0f} 張"), row=2, col=1)

    y_min = min(float(df_k["Low"].min()), float(df_k["BB_Lower"].dropna().min())) if (show_bb and "BB_Lower" in df_k.columns and not df_k["BB_Lower"].dropna().empty) else float(df_k["Low"].min())
    y_max = max(float(df_k["High"].max()), float(df_k["BB_Upper"].dropna().max())) if (show_bb and "BB_Upper" in df_k.columns and not df_k["BB_Upper"].dropna().empty) else float(df_k["High"].max())
    if show_cdp and cdp_vals:
        y_min, y_max = min(y_min, cdp_vals["NL"]), max(y_max, cdp_vals["NH"])
    pad = max(0.5, (y_max - y_min) * 0.08)

    layout_cfg = dict(
        hovermode="x unified",
        hoverlabel=dict(bgcolor=CARD_BG, font_size=int(11.5 * scale_factor), font_color=TEXT_MAIN, bordercolor="#4A90E2"),
        spikedistance=-1,
        yaxis=dict(range=[y_min - pad, y_max + pad], tickfont=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True, showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="#A0AEC0", spikethickness=1.0, spikedash="dot"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=int(10 * scale_factor), color=TEXT_MAIN)),
        height=int((450 if show_volume else 410) * max(1.0, scale_factor * 0.92)),
        margin=dict(l=12, r=12, t=42, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN)
    )
    if show_volume and "Volume" in df_k.columns:
        layout_cfg["xaxis"] = dict(type="category", rangeslider=dict(visible=False), showticklabels=False)
        layout_cfg["xaxis2"] = dict(type="category", tickangle=-35, nticks=10, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True)
        layout_cfg["yaxis2"] = dict(tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True)
    else:
        layout_cfg["xaxis"] = dict(type="category", rangeslider=dict(visible=False), tickangle=-35, nticks=10, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True, showspikes=True, spikemode="across", spikesnap="cursor", spikecolor="#A0AEC0", spikethickness=1.2, spikedash="dot")
    fig.update_layout(**layout_cfg)
    return fig

def plot_20d_chip_bar_chart(daily_table, scale_factor=1.1, pal=None):
    if pal is None: pal = get_theme_palette(True)
    CARD_BG, TEXT_MAIN, TEXT_MUTED, GRID_COLOR, PLOT_BG = pal["CARD_BG"], pal["TEXT_MAIN"], pal["TEXT_MUTED"], pal["GRID_COLOR"], pal["PLOT_BG"]
    df_c = pd.DataFrame(daily_table).sort_values("交易日期", ascending=True)
    df_c["ShortDate"] = df_c["交易日期"].str.slice(5)
    fig = go.Figure()
    for col, name, clr in [("外資買賣超(張)", "外資", "#3498DB"), ("投信買賣超(張)", "投信", "#FF6B6B"), ("自營商買賣超(張)", "自營", "#F59E0B")]:
        fig.add_trace(go.Bar(x=df_c["ShortDate"], y=df_c[col], name=name, marker_color=clr, hovertemplate="%{y:+,} 張"))
    fig.add_trace(go.Scatter(x=df_c["ShortDate"], y=df_c["三大法人合計(張)"], mode="lines+markers", name="法人合計", line=dict(color=TEXT_MAIN, width=2.2, dash="dot"), marker=dict(size=6, color="#00D26A"), hovertemplate="%{y:+,} 張"))
    fig.add_hline(y=0, line_width=1, line_color=TEXT_MUTED)
    fig.update_layout(
        barmode="group", hovermode="x unified",
        hoverlabel=dict(bgcolor=CARD_BG, font_size=int(11.5 * scale_factor), font_color=TEXT_MAIN, bordercolor="#4A90E2"),
        xaxis=dict(type="category", tickangle=-35, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True),
        yaxis=dict(tickfont=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN)),
        height=int(340 * max(1.0, scale_factor * 0.92)), margin=dict(l=12, r=12, t=38, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN)
    )
    return fig

def plot_20d_margin_bar_chart(daily_table, scale_factor=1.1, pal=None):
    if pal is None: pal = get_theme_palette(True)
    CARD_BG, TEXT_MAIN, TEXT_MUTED, GRID_COLOR, PLOT_BG = pal["CARD_BG"], pal["TEXT_MAIN"], pal["TEXT_MUTED"], pal["GRID_COLOR"], pal["PLOT_BG"]
    df_m = pd.DataFrame(daily_table).sort_values("交易日期", ascending=True)
    df_m["ShortDate"] = df_m["交易日期"].str.slice(5)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_m["ShortDate"], y=df_m["融資增減(張)"], name="融資增減", marker_color="#FF6B6B", hovertemplate="%{y:+,} 張"))
    fig.add_trace(go.Bar(x=df_m["ShortDate"], y=df_m["融券增減(張)"], name="融券增減", marker_color="#2ECC71", hovertemplate="%{y:+,} 張"))
    fig.add_trace(go.Scatter(x=df_m["ShortDate"], y=df_m["券資比(%)"], mode="lines+markers", name="券資比(%)", yaxis="y2", line=dict(color="#F59E0B", width=2.2, dash="dot"), marker=dict(size=6, color="#F59E0B"), hovertemplate="%{y:.2f}%"))
    fig.add_hline(y=0, line_width=1, line_color=TEXT_MUTED)
    fig.update_layout(
        barmode="group", hovermode="x unified",
        hoverlabel=dict(bgcolor=CARD_BG, font_size=int(11.5 * scale_factor), font_color=TEXT_MAIN, bordercolor="#4A90E2"),
        xaxis=dict(type="category", tickangle=-35, tickfont=dict(size=int(10 * scale_factor), color=TEXT_MAIN), automargin=True),
        yaxis=dict(tickfont=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True),
        yaxis2=dict(tickfont=dict(size=int(10 * scale_factor), color="#F59E0B"), overlaying="y", side="right", showgrid=False, automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=int(10.5 * scale_factor), color=TEXT_MAIN)),
        height=int(340 * max(1.0, scale_factor * 0.92)), margin=dict(l=12, r=12, t=38, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN)
    )
    return fig

def plot_horizontal_cdp_bar(cdp_vals, close_price, scale=1.05, pal=None):
    if pal is None: pal = get_theme_palette(True)
    TEXT_MAIN, GRID_COLOR, PLOT_BG = pal["TEXT_MAIN"], pal["GRID_COLOR"], pal["PLOT_BG"]
    levels = [("AL 極端破底支撐", cdp_vals["AL"], "#2ECC71"), ("NL 常態回檔支撐", cdp_vals["NL"], "#3498DB"), ("NH 常態反彈壓力", cdp_vals["NH"], "#E67E22"), ("AH 極端突破壓力", cdp_vals["AH"], "#E74C3C")]
    fig_cdp = go.Figure(go.Bar(y=[x[0] for x in levels], x=[x[1] for x in levels], orientation='h', text=[f"{x[1]} 元" for x in levels], textposition='outside', textfont=dict(size=int(12 * scale), color=TEXT_MAIN), marker_color=[x[2] for x in levels]))
    fig_cdp.add_vline(x=close_price, line_width=2, line_dash="dash", line_color=TEXT_MAIN)
    fig_cdp.update_layout(
        xaxis=dict(range=[min(cdp_vals["AL"], close_price) * 0.95, max(cdp_vals["AH"], close_price) * 1.08], tickfont=dict(size=int(11 * scale), color=TEXT_MAIN), gridcolor=GRID_COLOR, automargin=True),
        yaxis=dict(tickfont=dict(size=int(12 * scale), color=TEXT_MAIN), automargin=True),
        height=int(270 * max(1.0, scale * 0.95)), margin=dict(l=12, r=40, t=25, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PLOT_BG, font=dict(color=TEXT_MAIN)
    )
    return fig_cdp
