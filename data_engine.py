# 檔案名稱：data_engine.py (v10.1 自動滿血載入 2100+ 檔上市櫃股票與全品項ETF + 三週期共振引擎)
import os, re, io, csv, json, math, time, base64, urllib.parse, urllib3, requests
from requests.adapters import HTTPAdapter
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import streamlit as st

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 0. 全域 TCP 連線池 (省去 93 檔成分股重複 SSL 握手時間)
# ==========================================
GLOBAL_HTTP_SESSION = requests.Session()
_adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=1)
GLOBAL_HTTP_SESSION.mount("https://", _adapter)
GLOBAL_HTTP_SESSION.mount("http://", _adapter)
GLOBAL_HTTP_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache", "Pragma": "no-cache"
})

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arsenal_data")
QUOTES_FILE, FUTURES_FILE, CB_FILE = [os.path.join(DATA_DIR, f) for f in ("daily_quotes.csv", "futures_list.csv", "cb_list.csv")]
CONFIG_FILE, CUSTOM_SECTORS_FILE = [os.path.join(DATA_DIR, f) for f in ("config.json", "custom_sectors.json")]
ADMIN_SECRET_CODE = "admin888"

DEFAULT_SECTOR_STOCKS_MAP = {
    "1. 晶圓代工與先進製程": [["2330", "台積電", "TWSE"], ["2303", "聯電", "TWSE"], ["5347", "世界", "TPEX"], ["6770", "力積電", "TWSE"]],
    "2. CoWoS與先進封裝設備": [["3131", "弘塑", "TPEX"], ["6187", "萬潤", "TPEX"], ["3583", "辛耘", "TWSE"], ["6640", "均華", "TPEX"], ["3680", "家登", "TPEX"], ["2467", "志聖", "TWSE"], ["3711", "日月光投控", "TWSE"]],
    "3. 無塵室與廠務工程": [["2404", "漢唐", "TWSE"], ["6139", "亞翔", "TWSE"], ["5536", "聖暉*", "TPEX"], ["6196", "帆宣", "TWSE"], ["6691", "洋基工程", "TWSE"]],
    "4. CPO矽光子與光通訊": [["3450", "聯鈞", "TWSE"], ["3363", "上詮", "TPEX"], ["4979", "華星光", "TPEX"], ["3163", "波若威", "TPEX"], ["6442", "光聖", "TWSE"], ["4977", "眾達-KY", "TWSE"], ["3081", "聯亞", "TPEX"]],
    "5. AI散熱與水冷模組": [["3017", "奇鋐", "TWSE"], ["3324", "雙鴻", "TPEX"], ["3653", "健策", "TWSE"], ["2421", "建準", "TWSE"], ["8996", "高力", "TWSE"], ["3483", "力致", "TPEX"]],
    "6. 高階銅箔基板(CCL)與銅箔": [["2383", "台光電", "TWSE"], ["6274", "台燿", "TPEX"], ["6213", "聯茂", "TWSE"], ["8358", "金居", "TPEX"], ["4989", "榮科", "TWSE"]],
    "7. PCB硬板與伺服器板": [["2368", "金像電", "TWSE"], ["3044", "健鼎", "TWSE"], ["2313", "華通", "TWSE"], ["8155", "博智", "TPEX"], ["5439", "高技", "TPEX"]],
    "8. ABF與IC載板": [["3037", "欣興", "TWSE"], ["3189", "景碩", "TWSE"], ["8046", "南電", "TWSE"], ["4958", "臻鼎-KY", "TWSE"]],
    "9. AI伺服器與組裝代工": [["2317", "鴻海", "TWSE"], ["2382", "廣達", "TWSE"], ["3231", "緯創", "TWSE"], ["6669", "緯穎", "TWSE"], ["2356", "英業達", "TWSE"], ["2376", "技嘉", "TWSE"], ["2357", "華碩", "TWSE"]],
    "10. ASIC矽智財與IC設計": [["3661", "世芯-KY", "TWSE"], ["3443", "創意", "TWSE"], ["2454", "聯發科", "TWSE"], ["3529", "力旺", "TPEX"], ["6643", "M31", "TPEX"], ["5274", "信驊", "TPEX"], ["3035", "智原", "TWSE"]],
    "11. 800VDC電源與BBU備援電池": [["2308", "台達電", "TWSE"], ["2301", "光寶科", "TWSE"], ["6781", "AES-KY", "TWSE"], ["3211", "順達", "TPEX"], ["4931", "新盛力", "TPEX"], ["6558", "興能高", "TWSE"]],
    "12. TLVR電感與被動元件": [["2327", "國巨", "TWSE"], ["2492", "華新科", "TWSE"], ["3357", "臺慶科", "TPEX"], ["2375", "凱美", "TWSE"], ["3026", "禾伸堂", "TWSE"]],
    "13. 記憶體與控制IC": [["2408", "南亞科", "TWSE"], ["2344", "華邦電", "TWSE"], ["8299", "群聯", "TPEX"], ["3260", "威剛", "TPEX"], ["4967", "十銓", "TWSE"], ["3006", "晶豪科", "TWSE"]],
    "14. 石英元件與高速傳輸": [["3042", "晶技", "TWSE"], ["2484", "希華", "TWSE"], ["3221", "台嘉碩", "TPEX"], ["4966", "譜瑞-KY", "TPEX"], ["5269", "祥碩", "TWSE"]],
    "15. 重電電網與綠能儲能": [["1519", "華城", "TWSE"], ["1513", "中興電", "TWSE"], ["1503", "士電", "TWSE"], ["1514", "亞力", "TWSE"], ["1504", "東元", "TWSE"], ["2371", "大同", "TWSE"]],
    "16. 貨櫃航運與塑化原物料": [["2603", "長榮", "TWSE"], ["2609", "陽明", "TWSE"], ["2615", "萬海", "TWSE"], ["1303", "南亞", "TWSE"], ["1101", "台泥", "TWSE"], ["2002", "中鋼", "TWSE"]]
}

# ==========================================
# 1. 檔案讀寫與設定檔管理 (含自動載入全台股 2100+ 檔股票與 ETF)
# ==========================================
def load_sector_map():
    os.makedirs(DATA_DIR, exist_ok=True)
    sec_map = {k: [list(x) for x in v] for k, v in DEFAULT_SECTOR_STOCKS_MAP.items()}
    if os.path.exists(CUSTOM_SECTORS_FILE):
        try:
            with open(CUSTOM_SECTORS_FILE, "r", encoding="utf-8") as f: sec_map.update(json.load(f))
        except Exception: pass
    return sec_map

def save_sector_map(sec_map):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CUSTOM_SECTORS_FILE, "w", encoding="utf-8") as f: json.dump(sec_map, f, ensure_ascii=False, indent=2)

def save_config(cfg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_config():
    os.makedirs(DATA_DIR, exist_ok=True)
    cfg = {
        "lock_tab1": False, "pwd_tab1": "VIP888", "lock_tab2": False, "pwd_tab2": "TICK888",
        "lock_tab3": True, "pwd_tab3": "FUT888", "lock_tab4": False, "pwd_tab4": "VIP888",
        "public_promo_mode": False, "gemini_api_key": "", "finmind_token": "",
        "broker_line_url": "https://line.me/ti/p/~your_line_id",
        "mkt_foreign_oi": -36850, "mkt_foreign_oi_chg": -1420, "mkt_trust_oi": 24500, "mkt_dealer_oi": -12800,
        "mkt_spot_foreign": 159.22, "mkt_spot_trust": 118.07, "mkt_spot_dealer": 21.65,
        "mkt_margin_bal": 6233.87, "mkt_margin_chg": -104.93, "mkt_margin_chg_3d": -147.13,
        "mkt_short_bal": 217708, "mkt_short_chg": 1169, "cnn_fear_greed": 34,
        "mkt_chip_date": ""
    }
    try:
        for k in list(cfg.keys()):
            if k in st.secrets: cfg[k] = st.secrets[k]
    except Exception: pass

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: saved = json.load(f)
            cfg.update(saved)
        except Exception: pass
    return cfg

def read_csv_safely(filepath):
    for enc in ["utf-8-sig", "utf-8", "big5", "cp950"]:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            if "代號" in df.columns: df["代號"] = df["代號"].astype(str).str.strip().str.replace(".0", "", regex=False)
            return df
        except Exception: continue
    return pd.DataFrame()

def sync_stock_code_list_online():
    headers, stock_dict = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, {}
    # 完整收錄：所有 4 碼上市櫃普通股 + 所有 00 開頭之股票/高股息/債券(B)/槓反(L/R)/期貨(U)/主動型(A) ETF！
    valid_pattern = re.compile(r"^(\d{4}|00\d{2,4}[A-Z]?)$")
    for url, mkt, c_key, n_key in [
        ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", "TWSE", "Code", "Name"),
        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes", "TPEX", "SecuritiesCompanyCode", "CompanyName")
    ]:
        try:
            r = GLOBAL_HTTP_SESSION.get(url, headers=headers, timeout=12, verify=False)
            if r.status_code == 200:
                for item in r.json():
                    code, name = str(item.get(c_key, "")).strip(), str(item.get(n_key, "")).strip()
                    if valid_pattern.match(code) and name:
                        stock_dict[code] = {"代號": code, "名稱": name, "市場": mkt, "投本比": 0.0, "外本比": 0.0}
        except Exception: pass
    if len(stock_dict) > 500:
        df_new = pd.DataFrame(list(stock_dict.values())).sort_values("代號")
        df_new.to_csv(QUOTES_FILE, index=False, encoding="utf-8-sig")
        return True, f"🎉 成功更新 {len(df_new)} 檔上市櫃股票與全品項 ETF 名冊！"
    return False, "同步清單失敗，請稍後再試。"

def sync_taifex_futures_online():
    headers, records = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, {}
    try:
        resp = GLOBAL_HTTP_SESSION.get("https://www.taifex.com.tw/cht/5/stockMargining", headers=headers, timeout=12, verify=False)
        resp.encoding = "utf-8"
        for r_html in re.findall(r"<tr[^>]*>(.*?)</tr>", resp.text, re.S):
            clean_txt = " ".join(re.sub(r"<[^>]+>", " ", r_html).split())
            m_code = re.search(r"\b(\d{4}|00\d{2,4}[A-Z]?)\b", clean_txt)
            if m_code:
                code = m_code.group(1)
                rates = [float(x) for x in re.findall(r"(\d{2}\.\d{1,2})%", clean_txt) if 10.0 <= float(x) <= 50.0]
                zh_match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{2,8}期)", clean_txt)
                fut_name = (zh_match.group(1) if zh_match else f"{code}期").replace("小型", "")
                if code not in records:
                    records[code] = {"代號": code, "期貨簡稱": fut_name, "標準期貨": "有", "小型期貨": "有" if "小型" in clean_txt else "無", "保證金比例": max(rates) if rates else 13.50}
                else: records[code]["小型期貨"] = "有"
    except Exception as e: return False, f"連線異常：{e}"
    if records:
        df_new = pd.DataFrame(list(records.values()))
        df_new.to_csv(FUTURES_FILE, index=False, encoding="utf-8-sig")
        return True, f"🎉 成功同步 {len(df_new)} 檔個股期貨與保證金級距！"
    return False, "未能從期交所解析出資料。"

def init_sample_csvs():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(QUOTES_FILE):
        pd.DataFrame([
            ["2330", "台積電", "TWSE", 0.0, 0.0], ["2383", "台光電", "TWSE", 0.0, 0.0], ["3017", "奇鋐", "TWSE", 0.0, 0.0],
            ["0050", "元大台灣50", "TWSE", 0.0, 0.0], ["0056", "元大高股息", "TWSE", 0.0, 0.0], ["00878", "國泰永續高股息", "TWSE", 0.0, 0.0],
            ["00919", "群益台灣精選高息", "TWSE", 0.0, 0.0], ["00937B", "群益ESG投等債20+", "TPEX", 0.0, 0.0], ["00679B", "元大美債20年", "TPEX", 0.0, 0.0]
        ], columns=["代號", "名稱", "市場", "投本比", "外本比"]).to_csv(QUOTES_FILE, index=False, encoding="utf-8-sig")
    if not os.path.exists(FUTURES_FILE):
        pd.DataFrame([
            ["2330", "台積電期", "有", "有", 13.50], ["2383", "台光電期", "有", "有", 20.25], ["3017", "奇鋐期", "有", "有", 20.25],
            ["2603", "長榮期", "有", "有", 13.50], ["1101", "台泥期", "有", "有", 13.50], ["1303", "南亞期", "有", "有", 20.25],
            ["3189", "景碩期", "有", "無", 21.60], ["3037", "欣興期", "有", "有", 21.60], ["8358", "金居期", "有", "無", 24.30]
        ], columns=["代號", "期貨簡稱", "標準期貨", "小型期貨", "保證金比例"]).to_csv(FUTURES_FILE, index=False, encoding="utf-8-sig")
    if not os.path.exists(CB_FILE):
        pd.DataFrame([
            ["2383", "23835", "台光電五", 585.0, 118.5, "2028-05-15"], ["3017", "30175", "奇鋐五", 630.0, 115.0, "2028-09-20"], ["2603", "26034", "長榮四", 195.0, 112.0, "2027-11-01"]
        ], columns=["代號", "CB代號", "CB名稱", "轉換價", "CB收盤價", "到期日"]).to_csv(CB_FILE, index=False, encoding="utf-8-sig")

    # 【關鍵自動滿血】只要檢測到股票名冊少於 500 檔（例如只有預設的 9 檔），開機自動去證交所與櫃買中心抓滿 2,100+ 檔股票與 ETF！
    try:
        df_q = read_csv_safely(QUOTES_FILE)
        if len(df_q) < 500:
            sync_stock_code_list_online()
        df_f = read_csv_safely(FUTURES_FILE)
        if len(df_f) < 50:
            sync_taifex_futures_online()
    except Exception:
        pass

# ==========================================
# 2. 升降檔位與當沖數學試算核心
# ==========================================
def get_tw_tick_size(price, is_up=True):
    p = round(float(price), 2)
    for limit, tick in [(10, 0.01), (50, 0.05), (100, 0.10), (500, 0.50), (1000, 1.00)]:
        if (p < limit if is_up else p <= limit): return tick
    return 5.00

def step_tw_ticks(base_price, n_ticks):
    curr = round(float(base_price), 2)
    if n_ticks == 0: return curr
    d = 1 if n_ticks > 0 else -1
    for _ in range(abs(int(n_ticks))):
        curr = round(curr + d * get_tw_tick_size(curr, is_up=(d > 0)), 2)
        if curr <= 0.01: return 0.01
    return curr

def calc_trade_row_min20(buy_p, sell_p, lots, fold, tax_rate):
    fee_rate = 0.001425 * (fold / 10.0)
    buy_amt, sell_amt = int(round(buy_p * 1000.0 * lots)), int(round(sell_p * 1000.0 * lots))
    fee_buy = max(20, math.floor(buy_amt * fee_rate)) if buy_amt > 0 else 0
    fee_sell = max(20, math.floor(sell_amt * fee_rate)) if sell_amt > 0 else 0
    tax = math.floor(sell_amt * tax_rate)
    total_fee, total_cost = fee_buy + fee_sell, fee_buy + fee_sell + tax
    gross_pnl, net_pnl = sell_amt - buy_amt, (sell_amt - buy_amt) - total_cost

    long_be_price = round(((buy_amt + fee_buy + max(20, buy_amt * fee_rate)) / max(1e-6, 1.0 - tax_rate)) / (1000.0 * lots), 2)
    short_be_price = round(max(0.01, (sell_amt - fee_sell - tax - max(20, sell_amt * fee_rate)) / (1000.0 * lots)), 2)

    long_win_ticks, long_win_price = 1, step_tw_ticks(buy_p, 1)
    for t_i in range(1, 25):
        cand_s = step_tw_ticks(buy_p, t_i)
        c_amt = int(round(cand_s * 1000.0 * lots))
        if (c_amt - buy_amt - fee_buy - max(20, math.floor(c_amt * fee_rate)) - math.floor(c_amt * tax_rate)) > 0:
            long_win_ticks, long_win_price = t_i, cand_s; break

    short_win_ticks, short_win_price = 1, step_tw_ticks(sell_p, -1)
    for t_i in range(1, 25):
        cand_b = step_tw_ticks(sell_p, -t_i)
        c_amt = int(round(cand_b * 1000.0 * lots))
        if (sell_amt - c_amt - max(20, math.floor(c_amt * fee_rate)) - fee_sell - tax) > 0:
            short_win_ticks, short_win_price = t_i, cand_b; break

    return {
        "buy_amt": buy_amt, "sell_amt": sell_amt, "fee_buy": fee_buy, "fee_sell": fee_sell,
        "total_fee": total_fee, "tax": tax, "total_cost": total_cost, "gross_pnl": gross_pnl,
        "net_pnl": net_pnl, "roi_pct": round((net_pnl / (buy_amt + fee_buy)) * 100.0, 2) if buy_amt > 0 else 0.0,
        "long_be_price": long_be_price, "short_be_price": short_be_price,
        "long_win_ticks": long_win_ticks, "long_win_price": long_win_price,
        "short_win_ticks": short_win_ticks, "short_win_price": short_win_price
    }

def calculate_cdp(high, low, close):
    cdp, pt = (high + low + 2 * close) / 4.0, high - low
    return {"AH": round(cdp + pt, 2), "NH": round(2 * cdp - low, 2), "CDP": round(cdp, 2), "NL": round(2 * cdp - high, 2), "AL": round(cdp - pt, 2), "PT": round(pt, 2)}

# ==========================================
# 3. 技術指標、三週期K線 (日K/60分K/5分K) 與盤前09:00時間閘門引擎
# ==========================================
def clean_holiday_phantom_bars(df_in, is_index=False):
    if df_in.empty: return df_in
    df = df_in.copy()
    df = df[df.index.dayofweek < 5]
    if df.empty: return df

    now_tw = pd.Timestamp.now(tz="Asia/Taipei")
    today_str = now_tw.strftime("%Y-%m-%d")
    is_pre_market = (now_tw.hour < 9)

    if len(df) > 1 and df.index[-1].strftime("%Y-%m-%d") == today_str:
        last_h, last_l, last_v = float(df["High"].iloc[-1]), float(df["Low"].iloc[-1]), float(df["Volume"].iloc[-1])
        if is_pre_market or (abs(last_h - last_l) < 1e-5 and last_v <= 0):
            df = df.iloc[:-1]

    if not is_index:
        df = df[~((df["Volume"] <= 0) & ((df["High"] - df["Low"]).abs() < 1e-5))]
    else:
        if len(df) > 5:
            prev_c = df["Close"].shift(1)
            phantom_idx = ((df["High"] - df["Low"]).abs() < 1e-4) & ((df["Close"] - prev_c).abs() < 1e-4)
            df = df[~phantom_idx]
    return df

def compute_td_sequential_and_bbands(df_in):
    df = df_in.copy()
    df["MA5"], df["MA20"], df["MA60"] = df["Close"].rolling(5).mean(), df["Close"].rolling(20).mean(), df["Close"].rolling(60).mean()
    std20 = df["Close"].rolling(20).std(ddof=0)
    df["BB_Upper"], df["BB_Lower"] = df["MA20"] + 2.0 * std20, df["MA20"] - 2.0 * std20

    closes = df["Close"].values
    n_len = len(closes)
    raw_buy, raw_sell, disp_buy, disp_sell = [0]*n_len, [0]*n_len, [0]*n_len, [0]*n_len
    b_cnt = s_cnt = 0
    for i in range(n_len):
        if i >= 4:
            if closes[i] < closes[i - 4]: b_cnt, s_cnt = (b_cnt + 1 if b_cnt < 9 else 1), 0
            elif closes[i] > closes[i - 4]: s_cnt, b_cnt = (s_cnt + 1 if s_cnt < 9 else 1), 0
            else: b_cnt = s_cnt = 0
        raw_buy[i], raw_sell[i] = b_cnt, s_cnt

    for i in range(n_len):
        if raw_buy[i] == 9:
            for k in range(9):
                if i - k >= 0: disp_buy[i - k] = 9 - k
        if raw_sell[i] == 9:
            for k in range(9):
                if i - k >= 0: disp_sell[i - k] = 9 - k

    if n_len > 0 and 0 < raw_buy[-1] < 9:
        for k in range(raw_buy[-1]):
            if n_len - 1 - k >= 0: disp_buy[n_len - 1 - k] = raw_buy[-1] - k
    if n_len > 0 and 0 < raw_sell[-1] < 9:
        for k in range(raw_sell[-1]):
            if n_len - 1 - k >= 0: disp_sell[n_len - 1 - k] = raw_sell[-1] - k

    df["TD_Buy"], df["TD_Sell"], df["TD_Buy_Disp"], df["TD_Sell_Disp"] = raw_buy, raw_sell, disp_buy, disp_sell
    return df

def calc_kd_rsi_macd(hist):
    low_9, high_9 = hist["Low"].rolling(9).min(), hist["High"].rolling(9).max()
    rsv = (((hist["Close"] - low_9) / (high_9 - low_9 + 1e-9)) * 100).fillna(50)
    k_vals, d_vals = [50.0], [50.0]
    for r in rsv:
        k_vals.append((2/3) * k_vals[-1] + (1/3) * float(r))
        d_vals.append((2/3) * d_vals[-1] + (1/3) * k_vals[-1])
    dif = hist["Close"].ewm(span=12, adjust=False).mean() - hist["Close"].ewm(span=26, adjust=False).mean()
    osc = dif - dif.ewm(span=9, adjust=False).mean()
    delta = hist["Close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    rsi14 = round(float((100 - (100 / (1 + rs))).iloc[-1]), 1) if len(hist) >= 15 else 50.0
    return round(k_vals[-1], 1), round(d_vals[-1], 1), round(k_vals[-2], 1), round(d_vals[-2], 1), round(float(osc.iloc[-1]), 2), round(float(osc.iloc[-2]), 2) if len(osc)>=2 else 0.0, rsi14

def fetch_kline_df_bypass_ssl(code, market_hint="TWSE", range_str="6mo"):
    error_logs, is_idx = [], code in ["^TWII", "TAIEX"]
    symbols = ["%5ETWII"] if is_idx else [f"{code}{sfx}" for sfx in ([".TWO", ".TW"] if market_hint == "TPEX" else [".TW", ".TWO"])]
    ts_bucket = int(time.time() // 180)

    for sym in symbols:
        for host in ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]:
            try:
                url = f"https://{host}/v8/finance/chart/{sym}?range={range_str}&interval=1d&includePrePost=false&_ts={ts_bucket}"
                resp = GLOBAL_HTTP_SESSION.get(url, timeout=5, verify=False)
                if resp.status_code == 200:
                    res_list = resp.json().get("chart", {}).get("result", [])
                    if res_list:
                        res_obj = res_list[0]
                        timestamps = res_obj.get("timestamp", [])
                        quote = res_obj.get("indicators", {}).get("quote", [{}])[0]
                        if timestamps and "close" in quote:
                            tw_dates = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert("Asia/Taipei").normalize()
                            df_tmp = pd.DataFrame({
                                "Open": quote.get("open", quote["close"]), "High": quote.get("high", quote["close"]),
                                "Low": quote.get("low", quote["close"]), "Close": quote["close"], "Volume": quote.get("volume", [0]*len(timestamps))
                            }, index=tw_dates)
                            df_tmp = df_tmp[~df_tmp.index.duplicated(keep="last")].dropna(subset=["Close"])
                            for col in ["Open", "High", "Low"]: df_tmp[col] = df_tmp[col].fillna(df_tmp["Close"])
                            df_tmp["Volume"] = df_tmp["Volume"].fillna(0)
                            df_tmp = clean_holiday_phantom_bars(df_tmp, is_index=is_idx)
                            if len(df_tmp) >= 5: return df_tmp, ""
            except Exception as e: error_logs.append(f"Y({host[:6]}):{str(e)[:35]}")

    try:
        start_dt = (pd.Timestamp.now() - pd.Timedelta(days=190 if range_str == "6mo" else 75)).strftime("%Y-%m-%d")
        resp = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params={"dataset": "TaiwanStockPrice", "data_id": "TAIEX" if is_idx else code, "start_date": start_dt}, timeout=7, verify=False)
        if resp.status_code == 200 and resp.json().get("data"):
            df_fm = pd.DataFrame(resp.json()["data"])
            df_fm["Date"] = pd.to_datetime(df_fm["date"]).dt.tz_localize("Asia/Taipei")
            df_fm = df_fm.set_index("Date")
            df_fm = df_fm[~df_fm.index.duplicated(keep="last")]
            vol_col = "Trading_Volume" if "Trading_Volume" in df_fm.columns else ("volume" if "volume" in df_fm.columns else None)
            df_tmp = pd.DataFrame({
                "Open": df_fm["open"].astype(float), "High": df_fm["max"].astype(float),
                "Low": df_fm["min"].astype(float), "Close": df_fm["close"].astype(float),
                "Volume": df_fm[vol_col].astype(float) if vol_col else 0.0
            }).dropna(subset=["Close"])
            df_tmp = clean_holiday_phantom_bars(df_tmp, is_index=is_idx)
            if len(df_tmp) >= 5: return df_tmp, ""
    except Exception as e: error_logs.append(f"FM:{str(e)[:40]}")
    return pd.DataFrame(), " | ".join(error_logs[:2])

@st.cache_data(ttl=180)
def fetch_intraday_kline_full(code, market_hint="TWSE", interval="5m"):
    range_str = "5d" if interval == "5m" else "1mo"
    ts_bucket = int(time.time() // 180)
    for sfx in ([".TWO", ".TW"] if market_hint == "TPEX" else [".TW", ".TWO"]):
        for host in ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]:
            try:
                url = f"https://{host}/v8/finance/chart/{code}{sfx}?range={range_str}&interval={interval}&includePrePost=false&_ts={ts_bucket}"
                resp = GLOBAL_HTTP_SESSION.get(url, timeout=5, verify=False)
                if resp.status_code == 200:
                    res_list = resp.json().get("chart", {}).get("result", [])
                    if res_list:
                        timestamps = res_list[0].get("timestamp", [])
                        quote = res_list[0].get("indicators", {}).get("quote", [{}])[0]
                        if timestamps and "close" in quote:
                            dt_idx = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert("Asia/Taipei")
                            df_intra = pd.DataFrame({
                                "DateStr": dt_idx.strftime("%m/%d %H:%M"),
                                "ShortDate": dt_idx.strftime("%m/%d %H:%M"),
                                "Open": quote.get("open", quote["close"]),
                                "High": quote.get("high", quote["close"]),
                                "Low": quote.get("low", quote["close"]),
                                "Close": quote["close"],
                                "Volume": quote.get("volume", [0]*len(timestamps))
                            }).dropna(subset=["Close"])
                            for col in ["Open", "High", "Low"]:
                                df_intra[col] = df_intra[col].fillna(df_intra["Close"])
                            df_intra["Volume"] = (df_intra["Volume"].fillna(0) / 1000.0).round(0)
                            df_intra = df_intra[df_intra["Volume"] > 0].reset_index(drop=True)
                            if len(df_intra) >= 15:
                                df_intra = compute_td_sequential_and_bbands(df_intra)
                                k_v, d_v, _, _, osc_v, _, rsi_v = calc_kd_rsi_macd(df_intra)
                                latest = df_intra.iloc[-1]
                                close_p = round(float(latest["Close"]), 2)
                                ma5 = round(float(latest["MA5"]), 2) if pd.notna(latest["MA5"]) else close_p
                                ma20 = round(float(latest["MA20"]), 2) if pd.notna(latest["MA20"]) else close_p
                                ma60 = round(float(latest["MA60"]), 2) if pd.notna(latest["MA60"]) else ma20
                                bb_up = round(float(latest["BB_Upper"]), 2) if pd.notna(latest["BB_Upper"]) else close_p
                                bb_dn = round(float(latest["BB_Lower"]), 2) if pd.notna(latest["BB_Lower"]) else close_p
                                deduct20 = round(float(df_intra["Close"].iloc[-20]), 2) if len(df_intra) >= 20 else close_p
                                tail_n = 85 if interval == "5m" else 80
                                return {
                                    "ok": True, "interval": interval, "time_str": str(latest["DateStr"]),
                                    "close": close_p, "ma5": ma5, "ma20": ma20, "ma60": ma60,
                                    "bb_upper": bb_up, "bb_lower": bb_dn, "deduct": deduct20,
                                    "td_buy": int(latest["TD_Buy"]), "td_sell": int(latest["TD_Sell"]),
                                    "K": k_v, "D": d_v, "macd_osc": osc_v, "rsi": rsi_v,
                                    "records": df_intra.tail(tail_n).to_dict("records")
                                }
            except Exception: continue
    return {"ok": False, "interval": interval, "records": []}

def evaluate_mtf_resonance(tech_1d, tech_60m, tech_5m, cdp_vals, bull_c="#FF6B6B", bear_c="#2ECC71", warn_c="#F1C40F"):
    cdp_p = cdp_vals["CDP"]
    nh_p, nl_p = cdp_vals["NH"], cdp_vals["NL"]

    def _parse_tf(t_obj, label, is_5m=False):
        if not t_obj or not t_obj.get("ok"):
            return {"週期": label, "趨勢與扣抵": "資料載入中", "布林通道位階": "-", "神奇九轉(TD9)": "-", "KD / RSI 動能": "-", "bias": 0, "td_b": 0, "td_s": 0}
        c, m20, ded = t_obj["close"], t_obj["ma20"], t_obj["deduct"]
        bb_u, bb_l = t_obj["bb_upper"], t_obj["bb_lower"]
        tb, ts = t_obj["td_buy"], t_obj["td_sell"]
        kv, dv, rv = t_obj["K"], t_obj["D"], t_obj["rsi"]

        if is_5m:
            if c >= m20 and c >= cdp_p: trend_str, bias = f"🔴 站上20MA({m20}) & 站上CDP({cdp_p})", 1
            elif c < m20 and c < cdp_p: trend_str, bias = f"🟢 跌破20MA({m20}) & 低於CDP({cdp_p})", -1
            else: trend_str, bias = f"⚖️ 20MA({m20}) 與 CDP({cdp_p}) 間交戰", 0
        else:
            if c >= m20 and c >= ded: trend_str, bias = f"🔴 站上20MA({m20}) ＋ 扣抵({ded})助漲", 1
            elif c < m20 and c < ded: trend_str, bias = f"🟢 跌破20MA({m20}) ＋ 扣抵({ded})反壓", -1
            elif c >= m20: trend_str, bias = f"🟡 站上20MA({m20}) (惟扣抵{ded}較高)", 1
            else: trend_str, bias = f"🟡 低於20MA({m20}) (惟扣抵{ded}在低檔)", -1

        if c >= bb_u: bb_str = f"🔥 突破上軌 ({bb_u}) 強勢鈍化"
        elif c <= bb_l: bb_str = f"🌱 觸及下軌 ({bb_l}) 超跌區"
        elif c >= m20: bb_str = f"📈 中軌至上軌 ({bb_u}) 偏強區"
        else: bb_str = f"📉 中軌至下軌 ({bb_l}) 整理區"

        if tb >= 8: td_str = f"🔥 ▲低{tb} (短線超跌轉折訊號！)"
        elif tb > 0: td_str = f"▲ 低九計數：第 {tb} 根"
        elif ts >= 8: td_str = f"⚠️ ▼高{ts} (短線高檔衰竭警戒！)"
        elif ts > 0: td_str = f"▼ 高九計數：第 {ts} 根"
        else: td_str = "⚪ 無連續計數"

        kd_str = f"{'🔴金叉' if kv >= dv else '🟢死叉'} K({kv}) / D({dv}) ｜ RSI {rv}"
        return {"週期": label, "趨勢與扣抵": trend_str, "布林通道位階": bb_str, "神奇九轉(TD9)": td_str, "KD / RSI 動能": kd_str, "bias": bias, "td_b": tb, "td_s": ts, "k_up": kv >= dv}

    r_1d = _parse_tf(tech_1d, "📅 日 K (波段大方向)", is_5m=False)
    r_60m = _parse_tf(tech_60m, "⏱️ 60分K (隔日/波段轉折)", is_5m=False)
    r_5m = _parse_tf(tech_5m, "⚡ 5分K (當沖進出場扳機)", is_5m=True)

    b1, b60, b5 = r_1d["bias"], r_60m["bias"], r_5m["bias"]
    low_td_signals = [name for name, r in [("日K", r_1d), ("60分K", r_60m), ("5分K", r_5m)] if r["td_b"] >= 7]
    high_td_signals = [name for name, r in [("日K", r_1d), ("60分K", r_60m), ("5分K", r_5m)] if r["td_s"] >= 7]

    if b1 > 0 and b60 > 0 and b5 > 0:
        title = "🔥 【三週期多方強勢共振】日K ＋ 60分K ＋ 5分K 同步站上均線與 CDP 分水嶺！"
        color = bull_c
        desc = f"目前大（日K）、中（60分K）、小（5分K）三個時間週期趨勢一致偏多！盤中只要守穩 **CDP 分水嶺（{cdp_p}元）** 或 **5分K之20MA（{tech_5m.get('ma20', cdp_p)}元）**，順勢偏多操作勝率最高，切勿逆勢摸頭猜頂。"
    elif b1 > 0 and b60 > 0 and b5 <= 0:
        title = "🎯 【長多短回洗盤格局】日K 與 60分K 波段偏多，5分K 盤中拉回測試支撐！"
        color = warn_c
        desc = f"大方向（日K與60分K）均線維持多頭保護，僅 5分K 短線拉回整理。這屬於標準「多頭趨勢中的盤中震盪洗盤」，可密切留意 **5分K 出現 ▲低8/低9**、觸及 **布林下軌（{tech_5m.get('bb_lower', nl_p)}元）** 或 **CDP 常態支撐 NL（{nl_p}元）** 後重新站回 5分K 均線的低接契機！"
    elif b1 < 0 and b60 < 0 and b5 < 0:
        if len(low_td_signals) >= 2:
            title = f"🌱 【空方宣洩末端 × 多週期低九共振】({'＋'.join(low_td_signals)} 同步進入低九轉折區！)"
            color = warn_c
            desc = f"雖然三週期均線仍處空方壓制，但 **{' 與 '.join(low_td_signals)}** 已同步出現連續下跌第 7~9 根的動能衰竭訊號！此時追空極易被急彈軋到，空單宜逢低於 **NL（{nl_p}元）/ 布林下軌** 分批停利，搶反彈者可等 5分K 站回 20MA 再出手。"
        else:
            title = "❄️ 【三週期空方壓制共振】日K ＋ 60分K ＋ 5分K 同步受制於均線與 CDP 反壓！"
            color = bear_c
            desc = f"大中小三個週期同步處於空頭壓制結構，上方月線與 **CDP 分水嶺（{cdp_p}元）** 構成雙重蓋頭反壓。盤中若有反彈至 **5分K 20MA** 或 **NH 壓力（{nh_p}元）** 附近受阻，宜採取偏空避險或觀望策略，切忌盲目攤平接刀。"
    elif b1 < 0 and (b60 > 0 or b5 > 0):
        title = "⚡ 【跌深反彈搶短格局】日K 仍在月線下，但 60分K / 5分K 率先轉強站上均線！"
        color = warn_c
        desc = f"短線分K（5分K/60分K）已率先吹響反彈號角並站上短期均線，適合短線當沖做多搶反彈；但因日K大趨勢上方仍有 **日K月線（{tech_1d['ma20']}元）** 反壓，多單走到 **5分K/60分K 布林上軌** 或出現 **▼高8/高9** 時宜果斷分批停利！"
    else:
        title = "⚖️ 【多空週期交錯震盪】各週期方向尚未一致，宜依 CDP 支撐壓力與九轉訊號區間操作"
        color = warn_c
        desc = f"目前日K、60分K與5分K處於多空拉鋸整理。盤中當沖建議以 **CDP 分水嶺（{cdp_p}元）** 為強弱界線，往下靠近 **NL 支撐（{nl_p}元）＋ 5分K低九** 找支撐、往上靠近 **NH 壓力（{nh_p}元）＋ 5分K高九** 留意調節。"

    if high_td_signals and b5 >= 0:
        desc += f" ⚠️ **特別提醒：{'、'.join(high_td_signals)} 已進入 ▼高7~高9 高檔九轉區，短線追高需防乖離拉回！**"
    elif low_td_signals and b5 <= 0:
        desc += f" 💡 **特別提醒：{'、'.join(low_td_signals)} 已進入 ▲低7~低9 低檔九轉區，隨時留意破底翻止跌訊號！**"

    return {"title": title, "color": color, "desc": desc, "table": [
        {k: r[k] for k in ["週期", "趨勢與扣抵", "布林通道位階", "神奇九轉(TD9)", "KD / RSI 動能"]}
        for r in (r_1d, r_60m, r_5m)
    ]}

@st.cache_data(ttl=300)
def fetch_technical_indicators(code, market_hint="TWSE"):
    hist, err_msg = fetch_kline_df_bypass_ssl(code, market_hint, range_str="6mo")
    if hist.empty or len(hist) < 5: return {"ok": False, "err_msg": err_msg}
    hist = compute_td_sequential_and_bbands(hist)
    latest = hist.iloc[-1]
    trade_date = hist.index[-1].strftime("%Y-%m-%d")
    close_p, high_p, low_p = round(float(latest["Close"]), 2), round(float(latest["High"]), 2), round(float(latest["Low"]), 2)
    if abs(high_p - low_p) < 1e-4 and len(hist) >= 2:
        prev_bar = hist.iloc[-2]
        half_r = max(0.5, round((float(prev_bar["High"]) - float(prev_bar["Low"])) * 0.5, 2))
        high_p, low_p = round(close_p + half_r, 2), round(max(0.01, close_p - half_r), 2)

    ma5 = round(float(hist["MA5"].iloc[-1]), 2) if pd.notna(hist["MA5"].iloc[-1]) else close_p
    ma20 = round(float(hist["MA20"].iloc[-1]), 2) if pd.notna(hist["MA20"].iloc[-1]) else close_p
    ma60 = round(float(hist["MA60"].iloc[-1]), 2) if pd.notna(hist["MA60"].iloc[-1]) else ma20
    bb_up = round(float(hist["BB_Upper"].iloc[-1]), 2) if pd.notna(hist["BB_Upper"].iloc[-1]) else close_p
    bb_dn = round(float(hist["BB_Lower"].iloc[-1]), 2) if pd.notna(hist["BB_Lower"].iloc[-1]) else close_p
    deduct20, deduct_date = (round(float(hist["Close"].iloc[-20]), 2), hist.index[-20].strftime("%Y-%m-%d")) if len(hist) >= 20 else (close_p, trade_date)
    k_val, d_val, _, _, osc_today, osc_prev, rsi14 = calc_kd_rsi_macd(hist)
    vol_ma5 = float(hist["Volume"].tail(5).mean())
    vol_ratio = round(float(latest["Volume"]) / vol_ma5, 2) if vol_ma5 > 0 else 1.0

    hist_60 = hist.tail(60).copy()
    hist_60["DateStr"] = hist_60.index.strftime("%Y-%m-%d")
    hist_60["ShortDate"] = hist_60.index.strftime("%m-%d")
    return {
        "ok": True, "date": trade_date, "high": high_p, "low": low_p, "close": close_p,
        "ma5": ma5, "ma20": ma20, "ma60": ma60, "bb_upper": bb_up, "bb_lower": bb_dn,
        "td_buy": int(hist["TD_Buy"].iloc[-1]), "td_sell": int(hist["TD_Sell"].iloc[-1]),
        "deduct": deduct20, "deduct_date": deduct_date, "K": k_val, "D": d_val,
        "macd_osc": osc_today, "macd_prev": osc_prev, "rsi": rsi14, "vol_ratio": vol_ratio,
        "kline_60": hist_60[["DateStr", "ShortDate", "Open", "High", "Low", "Close", "Volume", "MA5", "MA20", "MA60", "BB_Upper", "BB_Lower", "TD_Buy", "TD_Sell", "TD_Buy_Disp", "TD_Sell_Disp"]].to_dict("records")
    }

@st.cache_data(ttl=3600)
def fetch_chip_data_20d(code, fm_token=""):
    empty_periods = {w: {"f": 0, "t": 0, "d": 0, "tot": 0} for w in [1, 3, 5, 10, 20]}
    try:
        params = {"dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_id": code, "start_date": (pd.Timestamp.now() - pd.Timedelta(days=50)).strftime("%Y-%m-%d")}
        if fm_token: params["token"] = fm_token
        resp = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=8, verify=False)
        if resp.status_code == 200 and resp.json().get("data"):
            df_c = pd.DataFrame(resp.json()["data"])
            last_20_dates = sorted(df_c["date"].unique())[-20:]
            df_20 = df_c[df_c["date"].isin(last_20_dates)].copy()
            df_20["net_lots"] = (df_20["buy"].astype(float) - df_20["sell"].astype(float)) / 1000.0
            daily_rows = []
            for dt_str in sorted(last_20_dates, reverse=True):
                sub_d = df_20[df_20["date"] == dt_str]
                f_d = int(round(sub_d[sub_d["name"].str.contains("Foreign", case=False, na=False)]["net_lots"].sum()))
                t_d = int(round(sub_d[sub_d["name"].str.contains("Investment_Trust", case=False, na=False)]["net_lots"].sum()))
                d_d = int(round(sub_d[sub_d["name"].str.contains("Dealer", case=False, na=False)]["net_lots"].sum()))
                daily_rows.append({"交易日期": dt_str, "外資買賣超(張)": f_d, "投信買賣超(張)": t_d, "自營商買賣超(張)": d_d, "三大法人合計(張)": f_d + t_d + d_d})
            periods = {w: {"f": sum(r["外資買賣超(張)"] for r in daily_rows[:w]), "t": sum(r["投信買賣超(張)"] for r in daily_rows[:w]), "d": sum(r["自營商買賣超(張)"] for r in daily_rows[:w]), "tot": sum(r["三大法人合計(張)"] for r in daily_rows[:w])} for w in [1, 3, 5, 10, 20]}
            return {
                "ok": True, "periods": periods,
                "foreign_5d": periods[5]["f"], "trust_5d": periods[5]["t"], "dealer_5d": periods[5]["d"], "total_5d": periods[5]["tot"],
                "foreign_10d": periods[10]["f"], "trust_10d": periods[10]["t"], "dealer_10d": periods[10]["d"], "total_10d": periods[10]["tot"],
                "daily_table": daily_rows
            }
    except Exception: pass
    return {"ok": False, "periods": empty_periods, "foreign_5d": 0, "trust_5d": 0, "dealer_5d": 0, "total_5d": 0, "foreign_10d": 0, "trust_10d": 0, "dealer_10d": 0, "total_10d": 0, "daily_table": []}

@st.cache_data(ttl=3600)
def fetch_margin_short_20d(code, fm_token=""):
    empty_m_periods = {w: {"m_chg": 0, "s_chg": 0} for w in [1, 3, 5, 10, 20]}
    try:
        params = {"dataset": "TaiwanStockMarginPurchaseShortSale", "data_id": code, "start_date": (pd.Timestamp.now() - pd.Timedelta(days=50)).strftime("%Y-%m-%d")}
        if fm_token: params["token"] = fm_token
        resp = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=8, verify=False)
        if resp.status_code == 200 and resp.json().get("data"):
            df_20 = pd.DataFrame(resp.json()["data"]).sort_values("date").tail(20).copy()
            daily_rows = []
            for _, r in df_20.iloc[::-1].iterrows():
                m_bal, m_prev, m_limit = int(float(r.get("MarginPurchaseTodayBalance", 0))), int(float(r.get("MarginPurchaseYesterdayBalance", 0))), int(float(r.get("MarginPurchaseLimit", 0)))
                s_bal, s_prev = int(float(r.get("ShortSaleTodayBalance", 0))), int(float(r.get("ShortSaleYesterdayBalance", 0)))
                daily_rows.append({
                    "交易日期": str(r["date"]), "融資餘額(張)": m_bal, "融資增減(張)": m_bal - m_prev,
                    "融資使用率(%)": round((m_bal / m_limit) * 100, 2) if m_limit > 0 else 0.0,
                    "融券餘額(張)": s_bal, "融券增減(張)": s_bal - s_prev,
                    "券資比(%)": round((s_bal / m_bal) * 100, 2) if m_bal > 0 else 0.0, "_limit": m_limit
                })
            if daily_rows:
                latest = daily_rows[0]
                m_periods = {w: {"m_chg": sum(x["融資增減(張)"] for x in daily_rows[:w]), "s_chg": sum(x["融券增減(張)"] for x in daily_rows[:w])} for w in [1, 3, 5, 10, 20]}
                return {
                    "ok": True, "eligible": (latest["_limit"] > 0) or (latest["融資餘額(張)"] > 0), "periods": m_periods,
                    "margin_bal": latest["融資餘額(張)"], "margin_chg": latest["融資增減(張)"], "margin_util": latest["融資使用率(%)"],
                    "short_bal": latest["融券餘額(張)"], "short_chg": latest["融券增減(張)"], "short_margin_ratio": latest["券資比(%)"],
                    "daily_table": [{k: v for k, v in item.items() if k != "_limit"} for item in daily_rows]
                }
    except Exception: pass
    return {"ok": False, "eligible": False, "periods": empty_m_periods, "margin_bal": 0, "margin_chg": 0, "margin_util": 0.0, "short_bal": 0, "short_chg": 0, "short_margin_ratio": 0.0, "daily_table": []}

@st.cache_data(ttl=900)
def fetch_market_breadth_and_fear_greed(fallback_fg=34):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json", "Referer": "https://edition.cnn.com/markets/fear-and-greed"}
    up_cnt = down_cnt = flat_cnt = 0
    breadth_ok = False
    for url, c_key, chg_key in [
        ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", "Code", "Change"),
        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes", "SecuritiesCompanyCode", "Change")
    ]:
        try:
            r_mkt = GLOBAL_HTTP_SESSION.get(url, headers=headers, timeout=8, verify=False)
            if r_mkt.status_code == 200:
                for it in r_mkt.json():
                    if not re.match(r"^\d{4}$", str(it.get(c_key, "")).strip()): continue
                    chg_str = str(it.get(chg_key, "0")).replace(",", "").replace("+", "").replace(" ", "").strip()
                    try:
                        chg_v = float(chg_str)
                        if chg_v > 0: up_cnt += 1
                        elif chg_v < 0: down_cnt += 1
                        else: flat_cnt += 1
                    except Exception: flat_cnt += 1
        except Exception: pass

    if (up_cnt + down_cnt) > 100: breadth_ok = True

    fg_score, fg_source = int(fallback_fg), "後台校準值"
    try:
        r_cnn = GLOBAL_HTTP_SESSION.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata", headers=headers, timeout=5, verify=False)
        if r_cnn.status_code == 200:
            score_val = r_cnn.json().get("fear_and_greed", {}).get("score")
            if score_val is not None: fg_score, fg_source = int(round(float(score_val))), "CNN自動連線"
    except Exception: pass
    return {"breadth_ok": breadth_ok, "up_cnt": up_cnt, "down_cnt": down_cnt, "flat_cnt": flat_cnt, "adl_diff": up_cnt - down_cnt, "up_ratio": round((up_cnt / max(1, up_cnt + down_cnt)) * 100, 1) if breadth_ok else 50.0, "fg_score": fg_score, "fg_source": fg_source}

@st.cache_data(ttl=300)
def fetch_taiex_market_data():
    hist, err_msg = fetch_kline_df_bypass_ssl("^TWII", "TWSE", range_str="6mo")
    if hist.empty or len(hist) < 20: return {"ok": False, "err_msg": err_msg}
    hist = compute_td_sequential_and_bbands(hist)
    latest, prev = hist.iloc[-1], hist.iloc[-2]
    close_p, open_p, high_p, low_p = [round(float(latest[k]), 1) for k in ("Close", "Open", "High", "Low")]
    prev_close, prev_open, prev_low = [round(float(prev[k]), 1) for k in ("Close", "Open", "Low")]
    if abs(high_p - low_p) < 1.0:
        half_r = max(80.0, round((float(prev["High"]) - float(prev["Low"])) * 0.5, 1))
        high_p, low_p = round(close_p + half_r, 1), round(close_p - half_r, 1)

    ma5, ma20 = round(float(hist["MA5"].iloc[-1]), 1), round(float(hist["MA20"].iloc[-1]), 1)
    ma60 = round(float(hist["MA60"].iloc[-1]), 1) if pd.notna(hist["MA60"].iloc[-1]) else ma20
    bb_up = round(float(hist["BB_Upper"].iloc[-1]), 1) if pd.notna(hist["BB_Upper"].iloc[-1]) else close_p
    bb_dn = round(float(hist["BB_Lower"].iloc[-1]), 1) if pd.notna(hist["BB_Lower"].iloc[-1]) else close_p
    prev_bb_dn = round(float(hist["BB_Lower"].iloc[-2]), 1) if pd.notna(hist["BB_Lower"].iloc[-2]) else prev_close
    k_val, d_val, prev_k, prev_d, _, _, rsi14 = calc_kd_rsi_macd(hist)

    lower_shadow = min(open_p, close_p) - low_p
    has_long_lower_shadow = (lower_shadow / max(1.0, high_p - low_p)) >= 0.42 and (lower_shadow >= 80)
    is_bull_engulf = (close_p > open_p) and (prev_close < prev_open) and (close_p >= prev_open) and (open_p <= prev_close)
    no_new_low = low_p >= prev_low
    reclaimed_bb_low = (low_p <= bb_dn or prev_low <= prev_bb_dn) and (close_p > bb_dn)

    bb_status = "🚨 跌破布林下軌 (極端超跌宣洩中)" if close_p < bb_dn else ("✅ 破底後重新站回布林下軌 (止跌訊號！)" if reclaimed_bb_low else ("🔥 突破布林上軌 (極強勢鈍化)" if close_p >= bb_up else ("📈 位於布林中軌(月線)與上軌之間" if close_p >= ma20 else "⚠️ 位於布林中軌(月線)與下軌之間")))
    k_pattern_list = ([f"✅長下影線({int(lower_shadow)}點)"] if has_long_lower_shadow else []) + (["✅紅K吞噬"] if is_bull_engulf else []) + (["✅未破前日低點"] if no_new_low else ["⚠️跌破前日低點"])

    hist_60 = hist.tail(60).copy()
    hist_60["DateStr"] = hist_60.index.strftime("%Y-%m-%d")
    hist_60["ShortDate"] = hist_60.index.strftime("%m-%d")
    return {
        "ok": True, "date": hist.index[-1].strftime("%Y-%m-%d"), "close": close_p, "open": open_p, "chg": round(close_p - prev_close, 1),
        "high": high_p, "low": low_p, "ma5": ma5, "ma20": ma20, "ma60": ma60, "bias20": round(((close_p - ma20) / ma20) * 100.0, 2) if ma20 > 0 else 0.0,
        "bb_upper": bb_up, "bb_lower": bb_dn, "bb_status": bb_status, "reclaimed_bb_low": reclaimed_bb_low,
        "k_pattern_str": " ｜ ".join(k_pattern_list), "has_long_shadow": has_long_lower_shadow, "is_bull_engulf": is_bull_engulf, "no_new_low": no_new_low,
        "td_buy": int(hist["TD_Buy"].iloc[-1]), "td_sell": int(hist["TD_Sell"].iloc[-1]), "K": k_val, "D": d_val, "prev_K": prev_k, "prev_D": prev_d, "rsi": rsi14,
        "deduct": round(float(hist["Close"].iloc[-20]), 1), "deduct_date": hist.index[-20].strftime("%Y-%m-%d"),
        "kline_60": hist_60[["DateStr", "ShortDate", "Open", "High", "Low", "Close", "MA5", "MA20", "MA60", "BB_Upper", "BB_Lower", "TD_Buy", "TD_Sell", "TD_Buy_Disp", "TD_Sell_Disp"]].to_dict("records")
    }

@st.cache_data(ttl=600)
def scan_sector_performance(sector_map_json_str, margins_dict):
    sec_map = json.loads(sector_map_json_str)
    tasks = [(sec_name, item[0], item[1], item[2]) for sec_name, s_list in sec_map.items() for item in s_list]
    sector_records = {k: [] for k in sec_map.keys()}

    def _worker(task_item):
        sec_name, code, name, mkt = task_item
        sub, _ = fetch_kline_df_bypass_ssl(code, mkt, range_str="2mo")
        if sub.empty or len(sub) < 6: return None
        close_p, prev_1d, prev_5d = round(float(sub["Close"].iloc[-1]), 2), float(sub["Close"].iloc[-2]), float(sub["Close"].iloc[-6])
        ma20 = round(float(sub["Close"].tail(20).mean()), 2) if len(sub) >= 20 else close_p
        m_rate = float(margins_dict.get(code, 13.5)) / 100.0
        return sec_name, {
            "代號": code, "名稱": name, "最新收盤(元)": close_p,
            "近1日漲跌(%)": round(((close_p - prev_1d) / prev_1d) * 100, 2) if prev_1d > 0 else 0.0,
            "近5日漲跌(%)": round(((close_p - prev_5d) / prev_5d) * 100, 2) if prev_5d > 0 else 0.0,
            "月線(20MA)": ma20, "趨勢位階": "✅站上月線" if close_p >= ma20 else "⚠️月線之下",
            "1口個股期保證金": f"{int(close_p * 2000 * m_rate):,} 元" if code in margins_dict else "無期貨"
        }

    with ThreadPoolExecutor(max_workers=16) as ex:
        for fut in as_completed([ex.submit(_worker, t) for t in tasks]):
            try:
                res = fut.result()
                if res: sector_records[res[0]].append(res[1])
            except Exception: continue

    summary_list = []
    for sec_name, items in sector_records.items():
        if items:
            top_stock = sorted(items, key=lambda x: x["近5日漲跌(%)"], reverse=True)[0]
            lead_str = f"{top_stock['代號']} {top_stock['名稱']} ({top_stock['近5日漲跌(%)']:+}%)"
            summary_list.append({
                "族群名稱": sec_name, "成分股數": f"{len(items)} 檔",
                "近1日平均漲跌(%)": round(sum(x["近1日漲跌(%)"] for x in items) / len(items), 2),
                "近5日平均漲跌(%)": round(sum(x["近5日漲跌(%)"] for x in items) / len(items), 2),
                "領漲指標股": lead_str, "近5日領漲指標股": lead_str,
                "stocks": sorted(items, key=lambda x: x["近5日漲跌(%)"], reverse=True)
            })
    return sorted(summary_list, key=lambda x: x["近5日平均漲跌(%)"], reverse=True)

@st.cache_data(ttl=1800)
def fetch_stock_news(code, name):
    raw_items, headers = [], {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    bad_words = {"南亞": ["南亞科", "南亞電"], "台塑": ["台塑化"], "聯電": ["聯電集團"], "中鋼": ["中鋼構"], "長榮": ["長榮航", "長榮鋼", "長榮航太"], "陽明": ["陽明交大"], "富邦": ["富邦媒"]}.get(name, [])
    for q_str in [f'"{code}" "{name}" when:7d', f'"{name}" 股 when:7d', f'{code} {name}']:
        try:
            resp = GLOBAL_HTTP_SESSION.get(f"https://news.google.com/rss/search?q={urllib.parse.quote(q_str)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", headers=headers, timeout=6, verify=False)
            if resp.status_code == 200:
                for item in ET.fromstring(resp.content).findall(".//item")[:25]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    if not title or name not in title: continue
                    temp_t = title
                    for bw in bad_words: temp_t = temp_t.replace(bw, "")
                    if name not in temp_t: continue
                    try:
                        dt = parsedate_to_datetime(item.find("pubDate").text)
                        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                    except Exception: dt = datetime.now(timezone.utc)
                    raw_items.append({"title": title, "link": item.find("link").text if item.find("link") is not None else "#", "dt": dt})
            if len(raw_items) >= 3: break
        except Exception: continue

    raw_items.sort(key=lambda x: x["dt"], reverse=True)
    seen_titles, final_news, now_utc = set(), [], datetime.now(timezone.utc)
    for item in raw_items:
        clean_t = item["title"].split(" - ")[0].strip()
        if clean_t in seen_titles: continue
        seen_titles.add(clean_t)
        diff_h = max(0, int((now_utc - item["dt"]).total_seconds() // 3600))
        ago_str = (f"{diff_h} 小時前" if diff_h > 0 else "剛剛") if diff_h < 24 else f"{diff_h // 24} 天前 ({item['dt'].strftime('%m/%d')})"
        t_text = item["title"]
        tag = "📊 財報營收" if any(w in t_text for w in ["營收", "EPS", "財報", "獲利", "毛利", "配息", "股利"]) else ("🏛️ 法人籌碼" if any(w in t_text for w in ["外資", "投信", "法人", "買超", "賣超", "目標價"]) else ("🎙️ 公司動態" if any(w in t_text for w in ["法說", "股東會", "股臨會", "董座", "擴產", "訂單", "併購"]) else "📰 盤勢焦點"))
        final_news.append({"title": item["title"], "link": item["link"], "date_str": item["dt"].strftime("%Y-%m-%d %H:%M"), "ago": ago_str, "tag": tag})
        if len(final_news) >= 4: break
    return {"news": final_news}

# ==========================================
# 4. 量化評分與證交所/期交所官方直連同步工具
# ==========================================
def evaluate_three_pillars(tech, chip, bull_c="#FF6B6B", bear_c="#2ECC71", warn_c="#F1C40F"):
    close_p, ma20, ma60, deduct = tech["close"], tech["ma20"], tech["ma60"], tech["deduct"]
    k_val, d_val, macd_osc, rsi_val = tech["K"], tech["D"], tech["macd_osc"], tech["rsi"]
    breakdown = [("📈 趨勢底分", "+10 分", "基礎分數")]
    t_score = 10 + (15 if close_p >= ma20 else 0) + (10 if close_p >= deduct else 0) + (5 if close_p >= ma60 else 0)
    breakdown.extend([
        ("📈 月線位階 (20MA)", "+15 分" if close_p >= ma20 else "+0 分", f"收盤 {close_p} {'≥' if close_p >= ma20 else '<'} 月線 {ma20}"),
        ("📈 月線扣抵保護", "+10 分" if close_p >= deduct else "+0 分", f"收盤 {close_p} {'≥' if close_p >= deduct else '<'} 20日前扣抵 {deduct}"),
        ("📈 季線保護 (60MA)", "+5 分" if close_p >= ma60 else "+0 分", f"收盤 {close_p} {'≥' if close_p >= ma60 else '<'} 季線 {ma60}")
    ])

    m_score = 5 + (10 if k_val >= d_val else 0) + (10 if macd_osc >= 0 else 0) + (5 if 50 <= rsi_val <= 80 else (2 if rsi_val > 80 else 0))
    breakdown.extend([
        ("⚡ 動能底分", "+5 分", "基礎分數"),
        ("⚡ 日 KD 方向", "+10 分" if k_val >= d_val else "+0 分", f"K值({k_val}) {'≥' if k_val >= d_val else '<'} D值({d_val})"),
        ("⚡ MACD 柱狀體", "+10 分" if macd_osc >= 0 else "+0 分", f"柱值 {macd_osc} {'≥ 0 (紅柱)' if macd_osc >= 0 else '< 0 (綠柱)'}"),
        ("⚡ RSI(14) 強弱", "+5 分" if 50 <= rsi_val <= 80 else ("+2 分" if rsi_val > 80 else "+0 分"), f"RSI 為 {rsi_val}")
    ])

    c_score, f_10d, t_10d, tot_10d = 14, chip["foreign_10d"], chip["trust_10d"], chip["total_10d"]
    if chip["ok"]:
        if t_10d > 0 and f_10d > 0: c_score, c_msg = 30, f"外資({f_10d:+,}張)與投信({t_10d:+,}張) 土洋同步買超"
        elif tot_10d > 0 and (t_10d > 0 or f_10d > 0): c_score, c_msg = 22, f"三大法人近10日合計淨買超 ({tot_10d:+,}張)"
        elif tot_10d < 0 and (t_10d > 0 or f_10d > 0): c_score, c_msg = 10, f"土洋對作且近10日合計淨賣超 ({tot_10d:+,}張)"
        elif t_10d < 0 and f_10d < 0: c_score, c_msg = 4, f"外資({f_10d:+,}張)與投信({t_10d:+,}張) 同步調節提款"
        else: c_score, c_msg = 14, "法人買賣超持平"
        breakdown.append(("💰 三大法人籌碼(近10日)", f"+{c_score} 分", c_msg))

    is_trend_up, is_chip_buy = (close_p >= ma20 and close_p >= deduct), (chip["ok"] and tot_10d > 0)
    if is_trend_up and is_chip_buy and (k_val >= d_val):
        verdict, v_color, v_desc = "🔥 三面多方共振（趨勢助漲 ＋ 指標金叉 ＋ 法人淨買超）", bull_c, "白話結論：股價站穩月線且扣抵低檔保護，搭配技術指標偏多與法人真金白銀買超，屬標準多頭順風結構。"
    elif (not is_trend_up) and chip["ok"] and (tot_10d < 0):
        verdict, v_color, v_desc = "❄️ 趨勢與籌碼雙重修正（月線反壓 ＋ 法人調節提款）", bear_c, "白話結論：股價受制於月線反壓且法人近10日合計站在賣方，短線追價風險高，宜留意空方避險策略。"
    elif is_trend_up and chip["ok"] and (tot_10d < 0):
        verdict, v_color, v_desc = "⚠️ 價強籌碼背離（技術面站上月線，但法人合計逢高調節）", warn_c, "白話結論：雖然均線維持多頭助漲，但近10日三大法人總合呈現逢高調節，短線操作不宜過度追高，留意拉回支撐。"
    elif (not is_trend_up) and is_chip_buy:
        verdict, v_color, v_desc = "🌱 低檔法人吃貨訊號（股價整理中，但法人逆勢承接）", warn_c, "白話結論：股價雖尚未正式突破月線反壓，但三大法人近10日開始低檔逆勢買超築底，可留意後續能否帶量站回月線。"
    else:
        verdict, v_color, v_desc = "⚖️ 多空區間拉鋸（指標與籌碼訊號分歧，箱型震盪）", warn_c, "白話結論：目前均線、動能指標與法人籌碼尚未出現同向共振，盤勢以區間震盪為主，適合依下方 CDP 支撐壓力高出低進。"

    return {"total": t_score + m_score + c_score, "t_score": t_score, "m_score": m_score, "c_score": c_score, "verdict": verdict, "v_color": v_color, "v_desc": v_desc, "breakdown": breakdown}

def extract_stocks_from_image_via_gemini(image_bytes, mime_type, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    prompt = "請幫我從這張台股看盤或概念股截圖中，辨識出所有出現的台股 4 碼代號（或中文股票名稱）。請只回傳台股 4 碼代號或股票名稱，用逗號分隔即可，例如：2330, 2317, 3017, 奇鋐, 台積電"
    payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("utf-8")}}]}]}
    resp = GLOBAL_HTTP_SESSION.post(url, json=payload, timeout=15, verify=False)
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip() if resp.status_code == 200 else ""

def fetch_taifex_foreign_tx_oi_csv(fm_token=""):
    sess = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.taifex.com.tw/cht/3/futContractsDate",
        "Origin": "https://www.taifex.com.tw"
    }
    now_dt = pd.Timestamp.now()

    try:
        sess.get("https://www.taifex.com.tw/cht/3/futContractsDate", headers=headers, timeout=5, verify=False)
        start_dt = now_dt - pd.Timedelta(days=14)
        payload = {"queryType": "1", "goDay": "", "doQuery": "1", "dateaddcnt": "", "queryStartDate": start_dt.strftime("%Y/%m/%d"), "queryEndDate": now_dt.strftime("%Y/%m/%d"), "commodityId": "TX"}
        r = sess.post("https://www.taifex.com.tw/cht/3/futContractsDateDown", data=payload, headers=headers, timeout=8, verify=False)
        if r.status_code == 200 and len(r.content) > 100:
            for enc in ["cp950", "utf-8-sig", "utf-8", "big5"]:
                txt = r.content.decode(enc, errors="ignore")
                if "外資" in txt and ("期貨" in txt or "TX" in txt):
                    date_oi_map = {}
                    for row in csv.reader(io.StringIO(txt)):
                        if len(row) >= 12:
                            row_str = " ".join(str(c) for c in row[:4])
                            if ("臺股期貨" in row_str or "台股期貨" in row_str or "TX" in row_str) and "外資" in row_str:
                                candidates = [row[13]] if len(row) > 13 else []
                                candidates.append(row[-2])
                                for cand in candidates:
                                    v_clean = str(cand).replace(",", "").replace(" ", "").strip()
                                    if re.match(r"^-?\d+$", v_clean):
                                        dt_key = str(row[0]).strip().replace("-", "/")
                                        date_oi_map[dt_key] = int(v_clean)
                                        break
                    if len(date_oi_map) >= 2:
                        sorted_dts = sorted(date_oi_map.keys())
                        return {"mkt_foreign_oi": date_oi_map[sorted_dts[-1]], "mkt_foreign_oi_chg": date_oi_map[sorted_dts[-1]] - date_oi_map[sorted_dts[-2]]}
    except Exception: pass

    try:
        found_ois = []
        for d_back in range(0, 10):
            q_date = (now_dt - pd.Timedelta(days=d_back)).strftime("%Y/%m/%d")
            r_html = sess.post("https://www.taifex.com.tw/cht/3/futContractsDate", data={"queryType": "1", "goDay": "", "doQuery": "1", "dateaddcnt": "", "queryDate": q_date, "commodityId": "TX"}, headers=headers, timeout=6, verify=False)
            if r_html.status_code == 200 and ("外資及陸資" in r_html.text):
                for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", r_html.text, re.S):
                    if "外資及陸資" in tr:
                        tds = [re.sub(r"<[^>]+>", "", td).replace(",", "").strip() for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
                        nums = [int(x) for x in tds if re.match(r"^-?\d+$", x)]
                        if len(nums) >= 6:
                            found_ois.append((q_date, nums[-2]))
                            break
            if len(found_ois) >= 2: break
        if len(found_ois) >= 2: return {"mkt_foreign_oi": found_ois[0][1], "mkt_foreign_oi_chg": found_ois[0][1] - found_ois[1][1]}
        elif len(found_ois) == 1: return {"mkt_foreign_oi": found_ois[0][1]}
    except Exception: pass

    try:
        start_dt = (now_dt - pd.Timedelta(days=15)).strftime("%Y-%m-%d")
        params = {"dataset": "TaiwanFuturesInstitutionalInvestors", "data_id": "TX", "start_date": start_dt}
        if fm_token: params["token"] = fm_token
        r_fm = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=8, verify=False)
        if r_fm.status_code == 200 and r_fm.json().get("data"):
            df_f = pd.DataFrame(r_fm.json()["data"])
            sub_f = df_f[df_f["institutional_investors"].astype(str).str.contains("外資|Foreign", case=False, na=False)].sort_values("date")
            if len(sub_f) >= 2:
                oi_today = int(float(sub_f.iloc[-1]["long_open_interest_balance_volume"]) - float(sub_f.iloc[-1]["short_open_interest_balance_volume"]))
                oi_prev = int(float(sub_f.iloc[-2]["long_open_interest_balance_volume"]) - float(sub_f.iloc[-2]["short_open_interest_balance_volume"]))
                return {"mkt_foreign_oi": oi_today, "mkt_foreign_oi_chg": oi_today - oi_prev}
    except Exception: pass

    return {}

def sync_market_institutional_online(fm_token=""):
    headers, res = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, {}
    now_dt = pd.Timestamp.now()

    for d_back in range(0, 7):
        q_date = (now_dt - pd.Timedelta(days=d_back)).strftime("%Y%m%d")
        try:
            r_spot = GLOBAL_HTTP_SESSION.get(f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json&dayDate={q_date}", headers=headers, timeout=6, verify=False)
            if r_spot.status_code == 200 and r_spot.json().get("stat") == "OK" and r_spot.json().get("data"):
                f_amt = t_amt = d_amt = 0.0
                for row in r_spot.json()["data"]:
                    title = str(row[0]).strip()
                    diff_yi = round(float(str(row[3]).replace(",", "")) / 1e8, 2)
                    if "外資及陸資" in title and "不含" in title: f_amt = diff_yi
                    elif "投信" in title: t_amt = diff_yi
                    elif "自營商" in title: d_amt += diff_yi
                res.update({"mkt_spot_foreign": f_amt, "mkt_spot_trust": t_amt, "mkt_spot_dealer": round(d_amt, 2), "mkt_chip_date": q_date})
                break
        except Exception: continue

    margin_history = []
    for d_back in range(0, 12):
        q_date = (now_dt - pd.Timedelta(days=d_back)).strftime("%Y%m%d")
        try:
            r_mg = GLOBAL_HTTP_SESSION.get(f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?response=json&date={q_date}&selectType=MS", headers=headers, timeout=6, verify=False)
            if r_mg.status_code == 200 and r_mg.json().get("stat") == "OK":
                tables = r_mg.json().get("tables", [])
                if tables and tables[0].get("data"):
                    t_data = tables[0]["data"]
                    m_today = m_prev = s_today = s_prev = None
                    for row in t_data:
                        item_name = str(row[0]).strip()
                        if "融資金額" in item_name:
                            m_prev = round(float(str(row[4]).replace(",", "")) / 1e5, 2)
                            m_today = round(float(str(row[5]).replace(",", "")) / 1e5, 2)
                        elif "融券" in item_name and "交易單位" in item_name:
                            s_prev = int(float(str(row[4]).replace(",", "")))
                            s_today = int(float(str(row[5]).replace(",", "")))
                    if m_today is not None:
                        margin_history.append({"date": q_date, "m_today": m_today, "m_prev": m_prev, "s_today": s_today, "s_prev": s_prev})
                        if len(margin_history) >= 3: break
        except Exception: continue

    if margin_history:
        latest_m = margin_history[0]
        res["mkt_margin_bal"] = latest_m["m_today"]
        res["mkt_margin_chg"] = round(latest_m["m_today"] - latest_m["m_prev"], 2)
        res["mkt_margin_chg_3d"] = round(latest_m["m_today"] - margin_history[2]["m_prev"], 2) if len(margin_history) >= 3 else res["mkt_margin_chg"]
        if latest_m["s_today"] is not None:
            res["mkt_short_bal"] = latest_m["s_today"]
            res["mkt_short_chg"] = latest_m["s_today"] - latest_m["s_prev"]

    res.update(fetch_taifex_foreign_tx_oi_csv(fm_token))
    return res

@st.cache_data(ttl=1800)
def auto_sync_market_chips_cached(fm_token=""):
    cfg = load_config()
    mkt_res = sync_market_institutional_online(fm_token)
    if mkt_res:
        cfg.update(mkt_res)
        save_config(cfg)
    return cfg
