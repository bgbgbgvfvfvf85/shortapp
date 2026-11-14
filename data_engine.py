# 檔案名稱：data_engine.py (v11.0 機構全維度動態評分 + 營收YoY加速度 + 匯率/費半相關係數 + 全市場活水自動歸類族群引擎)
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
# 0. 全域 TCP 連線池 (省去重複 SSL 握手時間)
# ==========================================
GLOBAL_HTTP_SESSION = requests.Session()
_adapter = HTTPAdapter(pool_connections=24, pool_maxsize=24, max_retries=1)
GLOBAL_HTTP_SESSION.mount("https://", _adapter)
GLOBAL_HTTP_SESSION.mount("http://", _adapter)
GLOBAL_HTTP_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache", "Pragma": "no-cache"
})

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arsenal_data")
QUOTES_FILE, FUTURES_FILE, CB_FILE = [os.path.join(DATA_DIR, f) for f in ("daily_quotes.csv", "futures_list.csv", "cb_list.csv")]
CONFIG_FILE, CUSTOM_SECTORS_FILE = [os.path.join(DATA_DIR, f) for f in ("config.json", "custom_sectors.json")]
INDUSTRY_CACHE_FILE = os.path.join(DATA_DIR, "industry_map.json")
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

# 官方產業與關鍵字自動映射至 16 大族群規則 (讓全市場新飆股自動歸隊！)
OFFICIAL_IND_TO_16_MAP = {
    "通信網路業": "4. CPO矽光子與光通訊",
    "電腦及週邊設備業": "9. AI伺服器與組裝代工",
    "電機機械": "15. 重電電網與綠能儲能",
    "航運業": "16. 貨櫃航運與塑化原物料",
    "鋼鐵工業": "16. 貨櫃航運與塑化原物料",
    "塑膠工業": "16. 貨櫃航運與塑化原物料",
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
    error_logs = []
    is_idx = code in ["^TWII", "TAIEX", "^SOX", "TWD=X"]
    if code in ["^TWII", "TAIEX"]: symbols = ["%5ETWII"]
    elif code == "^SOX": symbols = ["%5ESOX"]
    elif code == "TWD=X": symbols = ["TWD%3DX"]
    else: symbols = [f"{code}{sfx}" for sfx in ([".TWO", ".TW"] if market_hint == "TPEX" else [".TW", ".TWO"])]
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

    if code not in ["^SOX", "TWD=X"]:
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
    prev_1d = hist.iloc[-2] if len(hist) >= 2 else latest
    prev_5d = hist.iloc[-6] if len(hist) >= 6 else prev_1d
    trade_date = hist.index[-1].strftime("%Y-%m-%d")
    close_p, high_p, low_p = round(float(latest["Close"]), 2), round(float(latest["High"]), 2), round(float(latest["Low"]), 2)
    chg_1d_pct = round(((close_p - float(prev_1d["Close"])) / max(0.01, float(prev_1d["Close"]))) * 100.0, 2)
    chg_5d_pct = round(((close_p - float(prev_5d["Close"])) / max(0.01, float(prev_5d["Close"]))) * 100.0, 2)

    if abs(high_p - low_p) < 1e-4 and len(hist) >= 2:
        half_r = max(0.5, round((float(prev_1d["High"]) - float(prev_1d["Low"])) * 0.5, 2))
        high_p, low_p = round(close_p + half_r, 2), round(max(0.01, close_p - half_r), 2)

    ma5 = round(float(hist["MA5"].iloc[-1]), 2) if pd.notna(hist["MA5"].iloc[-1]) else close_p
    ma20 = round(float(hist["MA20"].iloc[-1]), 2) if pd.notna(hist["MA20"].iloc[-1]) else close_p
    ma60 = round(float(hist["MA60"].iloc[-1]), 2) if pd.notna(hist["MA60"].iloc[-1]) else ma20
    bb_up = round(float(hist["BB_Upper"].iloc[-1]), 2) if pd.notna(hist["BB_Upper"].iloc[-1]) else close_p
    bb_dn = round(float(hist["BB_Lower"].iloc[-1]), 2) if pd.notna(hist["BB_Lower"].iloc[-1]) else close_p
    deduct20, deduct_date = (round(float(hist["Close"].iloc[-20]), 2), hist.index[-20].strftime("%Y-%m-%d")) if len(hist) >= 20 else (close_p, trade_date)
    k_val, d_val, _, _, osc_today, osc_prev, rsi14 = calc_kd_rsi_macd(hist)
    vol_ma5 = float(hist["Volume"].tail(5).mean())
    vol_5d_lots = max(1.0, round(float(hist["Volume"].tail(5).sum()) / 1000.0, 1))
    vol_ratio = round(float(latest["Volume"]) / vol_ma5, 2) if vol_ma5 > 0 else 1.0

    # 與大盤加權指數比對算出 Alpha (相對強弱度)
    mkt_1d_pct = mkt_5d_pct = 0.0
    try:
        m_hist, _ = fetch_kline_df_bypass_ssl("^TWII", "TWSE", range_str="2mo")
        if len(m_hist) >= 6:
            mc, mp1, mp5 = float(m_hist["Close"].iloc[-1]), float(m_hist["Close"].iloc[-2]), float(m_hist["Close"].iloc[-6])
            mkt_1d_pct = round(((mc - mp1) / mp1) * 100.0, 2)
            mkt_5d_pct = round(((mc - mp5) / mp5) * 100.0, 2)
    except Exception: pass

    alpha_1d = round(chg_1d_pct - mkt_1d_pct, 2)
    alpha_5d = round(chg_5d_pct - mkt_5d_pct, 2)

    hist_60 = hist.tail(60).copy()
    hist_60["DateStr"] = hist_60.index.strftime("%Y-%m-%d")
    hist_60["ShortDate"] = hist_60.index.strftime("%m-%d")
    return {
        "ok": True, "date": trade_date, "high": high_p, "low": low_p, "close": close_p,
        "chg_1d_pct": chg_1d_pct, "chg_5d_pct": chg_5d_pct, "alpha_1d": alpha_1d, "alpha_5d": alpha_5d,
        "vol_5d_lots": vol_5d_lots, "ma5": ma5, "ma20": ma20, "ma60": ma60, "bb_upper": bb_up, "bb_lower": bb_dn,
        "td_buy": int(hist["TD_Buy"].iloc[-1]), "td_sell": int(hist["TD_Sell"].iloc[-1]),
        "deduct": deduct20, "deduct_date": deduct_date, "K": k_val, "D": d_val,
        "macd_osc": osc_today, "macd_prev": osc_prev, "rsi": rsi14, "vol_ratio": vol_ratio,
        "kline_60": hist_60[["DateStr", "ShortDate", "Open", "High", "Low", "Close", "Volume", "MA5", "MA20", "MA60", "BB_Upper", "BB_Lower", "TD_Buy", "TD_Sell", "TD_Buy_Disp", "TD_Sell_Disp"]].to_dict("records")
    }

@st.cache_data(ttl=3600)
def fetch_revenue_and_shareholding(code, fm_token=""):
    """
    【v11.0 機構基本面與外本比/投本比引擎】
    1. 抓取近 16 個月營收，計算最新月營收 YoY(%) 以及「近 3 個月平均 YoY」，判斷營收成長是在「加速」還是「高檔鈍化」！
    2. 抓取 TaiwanStockShareholding 計算總發行股數，進而將外資與投信買賣超換算為真實「外本比(%)」與「投本比(%)」！
    """
    res = {"rev_ok": False, "rev_month": "", "yoy_latest": 0.0, "yoy_prev": 0.0, "yoy_3m_avg": 0.0, "yoy_accel": 0.0, "total_shares_lots": 0}
    if str(code).startswith("00"): return res
    try:
        start_dt = (pd.Timestamp.now() - pd.Timedelta(days=520)).strftime("%Y-%m-%d")
        params = {"dataset": "TaiwanStockMonthRevenue", "data_id": code, "start_date": start_dt}
        if fm_token: params["token"] = fm_token
        r_rev = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=6, verify=False)
        if r_rev.status_code == 200 and r_rev.json().get("data"):
            df_r = pd.DataFrame(r_rev.json()["data"]).sort_values(["revenue_year", "revenue_month"])
            rev_map = {(int(r["revenue_year"]), int(r["revenue_month"])): float(r["revenue"]) for _, r in df_r.iterrows()}
            yoy_list = []
            for (y, m), rev_val in sorted(rev_map.items()):
                prev_y_rev = rev_map.get((y - 1, m), 0.0)
                if prev_y_rev > 0:
                    yoy_pct = round(((rev_val - prev_y_rev) / prev_y_rev) * 100.0, 2)
                    yoy_list.append((f"{y}/{m:02d}", yoy_pct))
            if len(yoy_list) >= 3:
                res["rev_ok"] = True
                res["rev_month"] = yoy_list[-1][0]
                res["yoy_latest"] = yoy_list[-1][1]
                res["yoy_prev"] = yoy_list[-2][1]
                prev_3 = [x[1] for x in yoy_list[-4:-1]] if len(yoy_list) >= 4 else [x[1] for x in yoy_list[:-1]]
                res["yoy_3m_avg"] = round(sum(prev_3) / len(prev_3), 2)
                res["yoy_accel"] = round(res["yoy_latest"] - res["yoy_3m_avg"], 2)
    except Exception: pass

    try:
        start_sh = (pd.Timestamp.now() - pd.Timedelta(days=15)).strftime("%Y-%m-%d")
        params_sh = {"dataset": "TaiwanStockShareholding", "data_id": code, "start_date": start_sh}
        if fm_token: params_sh["token"] = fm_token
        r_sh = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params_sh, timeout=5, verify=False)
        if r_sh.status_code == 200 and r_sh.json().get("data"):
            df_sh = pd.DataFrame(r_sh.json()["data"]).sort_values("date")
            shares = float(df_sh.iloc[-1].get("NumberOfSharesIssued", 0))
            if shares > 0:
                res["total_shares_lots"] = int(shares / 1000.0)
    except Exception: pass
    return res

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

# ==========================================
# 4. 全市場 1800+ 檔官方產業分類快取與活水族群掃描引擎
# ==========================================
@st.cache_data(ttl=86400)
def fetch_all_market_industry_map():
    """
    從證交所 (t187ap03_L) 與櫃買中心 (tpex_mainboard_company_info) 抓取全台灣上市櫃公司之官方產業分類代碼與名稱！
    """
    if os.path.exists(INDUSTRY_CACHE_FILE):
        try:
            with open(INDUSTRY_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if len(cached) > 1000: return cached
        except Exception: pass

    ind_code_map = {
        "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維", "05": "電機機械",
        "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙工業", "10": "鋼鐵工業", "11": "橡膠工業",
        "12": "汽車工業", "14": "建材營造", "15": "航運業", "16": "觀光餐旅", "17": "金融保險",
        "18": "貿易百貨", "20": "其他業", "21": "化學工業", "22": "生技醫療業", "23": "油電燃氣業",
        "24": "半導體業", "25": "電腦及週邊設備業", "26": "光電業", "27": "通信網路業",
        "28": "電子零組件業", "29": "電子通路業", "30": "資訊服務業", "31": "其他電子業",
        "32": "文化創意業", "33": "農業科技業", "34": "電子商務", "35": "綠能環保",
        "36": "數位雲端", "37": "運動休閒", "38": "居家生活"
    }
    stock_ind = {}
    for url, c_k, i_k in [
        ("https://openapi.twse.com.tw/v1/opendata/t187ap03_L", "公司代號", "產業別"),
        ("https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O", "SecuritiesCompanyCode", "CompanyCategory")
    ]:
        try:
            r = GLOBAL_HTTP_SESSION.get(url, timeout=8, verify=False)
            if r.status_code == 200:
                for it in r.json():
                    c = str(it.get(c_k, "")).strip()
                    raw_i = str(it.get(i_k, "")).strip().zfill(2)
                    if re.match(r"^\d{4}$", c):
                        stock_ind[c] = ind_code_map.get(raw_i, raw_i if len(raw_i) > 2 else "其他電子與傳產")
        except Exception: pass

    if len(stock_ind) < 500:
        try:
            r_fm = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params={"dataset": "TaiwanStockInfo"}, timeout=8, verify=False)
            if r_fm.status_code == 200 and r_fm.json().get("data"):
                for it in r_fm.json()["data"]:
                    c, cat = str(it.get("stock_id", "")).strip(), str(it.get("industry_category", "")).strip()
                    if re.match(r"^\d{4}$", c) and cat: stock_ind[c] = cat
        except Exception: pass

    if len(stock_ind) > 500:
        try:
            with open(INDUSTRY_CACHE_FILE, "w", encoding="utf-8") as f: json.dump(stock_ind, f, ensure_ascii=False)
        except Exception: pass
    return stock_ind

@st.cache_data(ttl=600)
def fetch_all_market_snapshot():
    """
    0.8 秒極速抓取全市場 2,100+ 檔上市櫃最新收盤價、單日漲跌幅、成交張數與成交值！
    """
    snap = {}
    # 1. 上市 TWSE
    try:
        r_tw = GLOBAL_HTTP_SESSION.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", timeout=8, verify=False)
        if r_tw.status_code == 200:
            for it in r_tw.json():
                c = str(it.get("Code", "")).strip()
                if not re.match(r"^\d{4}$", c): continue
                try:
                    cp = float(str(it.get("ClosingPrice", "0")).replace(",", ""))
                    chg = float(str(it.get("Change", "0")).replace(",", "").replace("+", "").replace("X", ""))
                    vol_sh = float(str(it.get("TradeVolume", "0")).replace(",", ""))
                    val_ntd = float(str(it.get("TradeValue", "0")).replace(",", ""))
                    prev_p = cp - chg
                    chg_pct = round((chg / prev_p) * 100.0, 2) if prev_p > 0 else 0.0
                    if cp > 0:
                        snap[c] = {"code": c, "name": str(it.get("Name", c)).strip(), "mkt": "TWSE", "close": cp, "chg_pct": chg_pct, "vol_lots": int(vol_sh // 1000), "val_yi": round(val_ntd / 1e8, 2)}
                except Exception: continue
    except Exception: pass

    # 2. 上櫃 TPEX
    try:
        r_tp = GLOBAL_HTTP_SESSION.get("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes", timeout=8, verify=False)
        if r_tp.status_code == 200:
            for it in r_tp.json():
                c = str(it.get("SecuritiesCompanyCode", "")).strip()
                if not re.match(r"^\d{4}$", c): continue
                try:
                    cp = float(str(it.get("Close", "0")).replace(",", ""))
                    chg = float(str(it.get("Change", "0")).replace(",", "").replace("+", ""))
                    vol_sh = float(str(it.get("TradingShares", "0")).replace(",", ""))
                    val_ntd = float(str(it.get("TransactionAmount", "0")).replace(",", ""))
                    prev_p = cp - chg
                    chg_pct = round((chg / prev_p) * 100.0, 2) if prev_p > 0 else 0.0
                    if cp > 0:
                        snap[c] = {"code": c, "name": str(it.get("CompanyName", c)).strip(), "mkt": "TPEX", "close": cp, "chg_pct": chg_pct, "vol_lots": int(vol_sh // 1000), "val_yi": round(val_ntd / 1e8, 2)}
                except Exception: continue
    except Exception: pass
    return snap

@st.cache_data(ttl=900)
def fetch_market_breadth_and_fear_greed(fallback_fg=34):
    snap = fetch_all_market_snapshot()
    up_cnt = sum(1 for v in snap.values() if v["chg_pct"] > 0)
    down_cnt = sum(1 for v in snap.values() if v["chg_pct"] < 0)
    flat_cnt = sum(1 for v in snap.values() if v["chg_pct"] == 0)
    breadth_ok = (up_cnt + down_cnt) > 100

    fg_score, fg_source = int(fallback_fg), "後台校準值"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json", "Referer": "https://edition.cnn.com/markets/fear-and-greed"}
        r_cnn = GLOBAL_HTTP_SESSION.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata", headers=headers, timeout=5, verify=False)
        if r_cnn.status_code == 200:
            score_val = r_cnn.json().get("fear_and_greed", {}).get("score")
            if score_val is not None: fg_score, fg_source = int(round(float(score_val))), "CNN自動連線"
    except Exception: pass
    return {"breadth_ok": breadth_ok, "up_cnt": up_cnt, "down_cnt": down_cnt, "flat_cnt": flat_cnt, "adl_diff": up_cnt - down_cnt, "up_ratio": round((up_cnt / max(1, up_cnt + down_cnt)) * 100, 1) if breadth_ok else 50.0, "fg_score": fg_score, "fg_source": fg_source}

@st.cache_data(ttl=600)
def fetch_macro_fx_and_sox(taiex_kline_records):
    """
    【v11.0 總體資金與國際連動引擎】
    1. 抓取美元兌新台幣匯率 (TWD=X)：判斷外資熱錢是匯入(升值)還是匯出(貶值)
    2. 抓取美股費城半導體指數 (^SOX)：並自動計算與台股加權指數「近 20 日滾動皮爾森相關係數 (r)」！
    """
    res = {
        "fx_ok": False, "usd_twd": 32.0, "fx_chg_5d": 0.0, "fx_ma20": 32.0, "fx_status": "匯率中性",
        "sox_ok": False, "sox_close": 5000.0, "sox_chg_1d": 0.0, "sox_chg_5d": 0.0, "sox_corr_20d": 0.65
    }
    try:
        df_fx, _ = fetch_kline_df_bypass_ssl("TWD=X", "TWSE", range_str="2mo")
        if len(df_fx) >= 20:
            c_fx = round(float(df_fx["Close"].iloc[-1]), 3)
            p5_fx = round(float(df_fx["Close"].iloc[-6]), 3)
            m20_fx = round(float(df_fx["Close"].tail(20).mean()), 3)
            chg5 = round(c_fx - p5_fx, 3)
            status = "🟢 台幣升值熱錢流入" if (c_fx < m20_fx and chg5 <= 0) else ("🚨 台幣貶值資金外流" if (c_fx > m20_fx and chg5 >= 0.08) else "⚖️ 匯率區間震盪")
            res.update({"fx_ok": True, "usd_twd": c_fx, "fx_chg_5d": chg5, "fx_ma20": m20_fx, "fx_status": status})
    except Exception: pass

    try:
        df_sox, _ = fetch_kline_df_bypass_ssl("^SOX", "TWSE", range_str="3mo")
        if len(df_sox) >= 22:
            c_s, p1_s, p5_s = float(df_sox["Close"].iloc[-1]), float(df_sox["Close"].iloc[-2]), float(df_sox["Close"].iloc[-6])
            sox_1d = round(((c_s - p1_s) / p1_s) * 100.0, 2)
            sox_5d = round(((c_s - p5_s) / p5_s) * 100.0, 2)
            # 計算近 20 日費半與台股漲跌幅之皮爾森相關係數 (r)
            df_tw = pd.DataFrame(taiex_kline_records)
            tw_ret = df_tw["Close"].pct_change().dropna().tail(20).reset_index(drop=True)
            sox_ret = df_sox["Close"].pct_change().dropna().tail(20).reset_index(drop=True)
            min_len = min(len(tw_ret), len(sox_ret))
            corr_val = round(float(tw_ret.tail(min_len).corr(sox_ret.tail(min_len))), 2) if min_len >= 10 else 0.65
            if pd.isna(corr_val): corr_val = 0.50
            res.update({"sox_ok": True, "sox_close": round(c_s, 1), "sox_chg_1d": sox_1d, "sox_chg_5d": sox_5d, "sox_corr_20d": corr_val})
    except Exception: pass
    return res

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
    """
    【v11.0 全市場活水自動歸類族群引擎】
    1. 結合「16 大戰略族群核心股」與「證交所/櫃買全市場 1,800+ 檔官方產業分類」！
    2. 自動從全市場掃描今日「成交值 > 3 億 且 單日上漲 ≥ 2.5%」的強勢新面孔：
       • 若其所屬產業對應 16 大族群，自動併入該族群並標示『🔥[動態新星]』！
       • 若資金湧入原本 16 類以外的官方產業（如：生技醫療、化學工業、建材營造、金融保險、資訊服務等），自動整隊浮現為『🌟 [動態主流] XX族群』！
    3. 每一檔入榜股票 100% 都有明確的族群歸屬，徹底告別死板名單與無分類雜牌軍！
    """
    sec_map = json.loads(sector_map_json_str)
    ind_map = fetch_all_market_industry_map()
    snap_all = fetch_all_market_snapshot()

    existing_codes = {item[0] for s_list in sec_map.values() for item in s_list}
    dynamic_sec_map = {k: [list(x) for x in v] for k, v in sec_map.items()}

    # 從全市場 1800+ 檔中篩選出今日帶量轉強的新面孔 (成交值 >= 3億 且 漲幅 >= 2.0%)
    hot_candidates = sorted(
        [v for k, v in snap_all.items() if k not in existing_codes and v["val_yi"] >= 3.0 and v["chg_pct"] >= 2.0],
        key=lambda x: (x["chg_pct"] * math.log10(max(2.0, x["val_yi"]))),
        reverse=True
    )

    extra_industry_buckets = {}
    for cand in hot_candidates[:35]:
        c_code, c_name, c_mkt = cand["code"], cand["name"], cand["mkt"]
        ind_cat = ind_map.get(c_code, "其他電子業")

        # 依關鍵字與官方產業智慧歸隊至 16 大族群或新主流產業籃
        target_16 = None
        if any(k in c_name for k in ["光", "訊", "波", "聯", "華星"]): target_16 = "4. CPO矽光子與光通訊"
        elif any(k in c_name for k in ["散熱", "雙", "奇", "力致", "高力"]): target_16 = "5. AI散熱與水冷模組"
        elif any(k in c_name for k in ["電", "亞力", "華城", "中興", "森崴", "雲豹"]): target_16 = "15. 重電電網與綠能儲能"
        elif ind_cat in OFFICIAL_IND_TO_16_MAP: target_16 = OFFICIAL_IND_TO_16_MAP[ind_cat]

        if target_16 and target_16 in dynamic_sec_map and len(dynamic_sec_map[target_16]) < 10:
            dynamic_sec_map[target_16].append([c_code, f"{c_name} 🔥[動態新星]", c_mkt])
        else:
            bucket_name = f"🌟 [動態主流] {ind_cat}族群"
            extra_industry_buckets.setdefault(bucket_name, []).append([c_code, f"{c_name} 🔥[帶量轉強]", c_mkt])

    # 若某個新興官方產業今日有 >= 2 檔帶量強勢股（或單檔超級強勢股），直接整隊浮現進排行榜！
    for b_name, b_stocks in extra_industry_buckets.items():
        if len(b_stocks) >= 2:
            dynamic_sec_map[b_name] = b_stocks[:7]

    tasks = [(sec_name, item[0], item[1], item[2]) for sec_name, s_list in dynamic_sec_map.items() for item in s_list]
    sector_records = {k: [] for k in dynamic_sec_map.keys()}

    def _worker(task_item):
        sec_name, code, name, mkt = task_item
        sub, _ = fetch_kline_df_bypass_ssl(code, mkt, range_str="2mo")
        if sub.empty or len(sub) < 6: return None
        close_p, prev_1d, prev_5d = round(float(sub["Close"].iloc[-1]), 2), float(sub["Close"].iloc[-2]), float(sub["Close"].iloc[-6])
        ma20 = round(float(sub["Close"].tail(20).mean()), 2) if len(sub) >= 20 else close_p
        m_rate = float(margins_dict.get(code, 13.5)) / 100.0
        ind_label = ind_map.get(code, "電子/傳產")
        return sec_name, {
            "代號": code, "名稱": name, "官方產業": ind_label, "最新收盤(元)": close_p,
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
            new_star_cnt = sum(1 for x in items if "🔥" in x["名稱"])
            cnt_label = f"{len(items)} 檔" + (f" (含🔥新星{new_star_cnt}檔)" if new_star_cnt > 0 else "")
            summary_list.append({
                "族群名稱": sec_name, "成分股數": cnt_label,
                "近1日平均漲跌(%)": round(sum(x["近1日漲跌(%)"] for x in items) / len(items), 2),
                "近5日平均漲跌(%)": round(sum(x["近5日漲跌(%)"] for x in items) / len(items), 2),
                "領漲指標股": lead_str, "近5日領漲指標股": lead_str,
                "stocks": sorted(items, key=lambda x: x["近5日漲跌(%)"], reverse=True)
            })
    return sorted(summary_list, key=lambda x: (x["近1日平均漲跌(%)"] * 0.45 + x["近5日平均漲跌(%)"] * 0.55), reverse=True)

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
# 5. 【v11.0 機構全維度動態評分引擎】(個股 4 維度 vs 大盤 5 維度)
# ==========================================
def evaluate_stock_comprehensive(tech, chip, margin_info=None, tech_60m=None, tech_5m=None, rev_info=None, bull_c="#FF6B6B", bear_c="#2ECC71", warn_c="#F1C40F"):
    """
    【v11.0 個股 100 分制 4 大動態維度評分】
    1. 相對大盤強弱 (Alpha) & 日K趨勢 (滿分 25 分)
    2. 三週期共振 (60分K/5分K) & 動能指標 (滿分 25 分)
    3. 外本比/投本比 (吃貨濃度%) & 資券乾淨度 (滿分 30 分)
    4. 月營收 YoY 加速度 (ΔYoY) & 利多出盡檢驗 (滿分 20 分；若無營收資料如ETF則按比例換算至100分)
    """
    c, ma5, ma20, ma60, ded = tech["close"], tech["ma5"], tech["ma20"], tech["ma60"], tech["deduct"]
    alpha_1d, alpha_5d = tech.get("alpha_1d", 0.0), tech.get("alpha_5d", 0.0)
    kv, dv, macd_osc, rsi_val, vol_r = tech["K"], tech["D"], tech["macd_osc"], tech["rsi"], tech["vol_ratio"]
    vol_5d_lots = max(1.0, tech.get("vol_5d_lots", 5000.0))
    cdp_p = round((tech["high"] + tech["low"] + 2 * c) / 4.0, 2)

    breakdown = []

    # ----------------------------------------------------
    # 維度 1：相對大盤強弱 (Alpha) & 日K趨勢 (滿分 25 分)
    # ----------------------------------------------------
    # Alpha 動態分 (0 ~ 10 分)：比較近1日與近5日跑贏大盤幅度
    s_a1 = max(0, min(5, int(round((alpha_1d + 2.5) * 1.0))))
    s_a5 = max(0, min(5, int(round((alpha_5d + 5.0) * 0.5))))
    s_alpha = s_a1 + s_a5
    # 日K均線與扣抵 (0 ~ 15 分)
    s_ma = (4 if c >= ma5 else 0) + (6 if c >= ma20 else 0) + (2 if c >= ma60 else 0) + (3 if c >= ded else 0)
    d1_score = s_alpha + s_ma
    breakdown.append((
        "🛡️ 1. 相對大盤強弱(Alpha) & 日K趨勢", f"{d1_score} / 25 分",
        f"對抗大盤Alpha：1日({alpha_1d:+.2f}%) / 5日({alpha_5d:+.2f}%) ➔ +{s_alpha}分 ｜ 均線：5MA({'+' if c>=ma5 else '-'}) / 月線({'+' if c>=ma20 else '-'}) / 扣抵({'+' if c>=ded else '-'}) ➔ +{s_ma}分"
    ))

    # ----------------------------------------------------
    # 維度 2：三週期共振 (60分/5分K) & 動能指標 (滿分 25 分)
    # ----------------------------------------------------
    s_60m = 4
    if tech_60m and tech_60m.get("ok"):
        s_60m = (5 if c >= tech_60m["ma20"] else 0) +
