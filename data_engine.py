# ==============================================================================
# ⚠️ 【重要防呆提醒】本檔案是：data_engine.py (後端資料引擎 v12.6)
# 請確認 GitHub 網頁頂端的檔名是 data_engine.py 再貼上！切勿貼到 stock_arsenal_v1.py！
# ==============================================================================
import os, re, io, csv, json, math, time, base64, urllib.parse, urllib3, requests
from requests.adapters import HTTPAdapter
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import streamlit as st

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GLOBAL_HTTP_SESSION = requests.Session()
_adapter = HTTPAdapter(pool_connections=24, pool_maxsize=24, max_retries=1)
GLOBAL_HTTP_SESSION.mount("https://", _adapter)
GLOBAL_HTTP_SESSION.mount("http://", _adapter)
GLOBAL_HTTP_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
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
    "7. PCB硬板與伺服器板": [["2368", "金像電", "TWSE"], ["3044", "健鼎", "TWSE"], ["2313", "華通", "TWSE"], ["3167", "大量", "TWSE"], ["8155", "博智", "TPEX"], ["5439", "高技", "TPEX"]],
    "8. ABF與IC載板": [["3037", "欣興", "TWSE"], ["3189", "景碩", "TWSE"], ["8046", "南電", "TWSE"], ["4958", "臻鼎-KY", "TWSE"]],
    "9. AI伺服器與組裝代工": [["2317", "鴻海", "TWSE"], ["2382", "廣達", "TWSE"], ["3231", "緯創", "TWSE"], ["6669", "緯穎", "TWSE"], ["2356", "英業達", "TWSE"], ["2376", "技嘉", "TWSE"], ["2357", "華碩", "TWSE"]],
    "10. ASIC矽智財與IC設計": [["3661", "世芯-KY", "TWSE"], ["3443", "創意", "TWSE"], ["2454", "聯發科", "TWSE"], ["3529", "力旺", "TPEX"], ["6643", "M31", "TPEX"], ["5274", "信驊", "TPEX"], ["3035", "智原", "TWSE"]],
    "11. 800VDC電源與BBU備援電池": [["2308", "台達電", "TWSE"], ["2301", "光寶科", "TWSE"], ["6781", "AES-KY", "TWSE"], ["3211", "順達", "TPEX"], ["4931", "新盛力", "TPEX"], ["6558", "興能高", "TWSE"]],
    "12. TLVR電感與被動元件": [["2327", "國巨", "TWSE"], ["2492", "華新科", "TWSE"], ["3357", "臺慶科", "TPEX"], ["2375", "凱美", "TWSE"], ["3026", "禾伸堂", "TWSE"]],
    "13.記憶體與控制IC": [["2408", "南亞科", "TWSE"], ["2344", "華邦電", "TWSE"], ["8299", "群聯", "TPEX"], ["3260", "威剛", "TPEX"], ["4967", "十銓", "TWSE"], ["3006", "晶豪科", "TWSE"]],
    "14. 石英元件與高速傳輸": [["3042", "晶技", "TWSE"], ["2484", "希華", "TWSE"], ["3221", "台嘉碩", "TPEX"], ["4966", "譜瑞-KY", "TPEX"], ["5269", "祥碩", "TWSE"]],
    "15. 重電電網與綠能儲能": [["1519", "華城", "TWSE"], ["1513", "中興電", "TWSE"], ["1503", "士電", "TWSE"], ["1514", "亞力", "TWSE"], ["1504", "東元", "TWSE"], ["2371", "大同", "TWSE"]],
    "16. 貨櫃航運與塑化原物料": [["2603", "長榮", "TWSE"], ["2609", "陽明", "TWSE"], ["2615", "萬海", "TWSE"], ["1303", "南亞", "TWSE"], ["1101", "台泥", "TWSE"], ["2002", "中鋼", "TWSE"]]
}

TWSE_IND_CODE_MAP = {
    "01": "水泥工業", "02": "食品工業", "03": "塑膠工業", "04": "紡織纖維", "05": "電機機械",
    "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙工業", "10": "鋼鐵工業", "11": "橡膠工業",
    "12": "汽車工業", "14": "建材營造", "15": "航運業", "16": "觀光餐旅", "17": "金融保險",
    "18": "貿易百貨", "19": "綜合企業", "20": "其他產業", "21": "化學工業", "22": "生技醫療業",
    "23": "油電燃氣業", "24": "半導體業", "25": "電腦及週邊設備業", "26": "光電業", "27": "通信網路業",
    "28": "電子零組件業", "29": "電子通路業", "30": "資訊服務業", "31": "其他電子業", "32": "文化創意業",
    "33": "農業科技", "34": "電子商務", "35": "綠能環保", "36": "數位雲端", "37": "運動休閒", "38": "居家生活"
}

PRECISE_SUBSECTOR_OVERRIDES = {
    "2471": "資訊服務與資安軟體", "2468": "資訊服務與資安軟體", "6214": "資訊服務與資安軟體",
    "3029": "資訊服務與資安軟體", "6112": "資訊服務與資安軟體", "5203": "資訊服務與資安軟體",
    "6183": "資訊服務與資安軟體", "4953": "資訊服務與資安軟體", "6690": "資訊服務與資安軟體",
    "6569": "資訊服務與資安軟體", "6689": "資訊服務與資安軟體", "3130": "資訊服務與資安軟體",
    "2453": "資訊服務與資安軟體", "5403": "資訊服務與資安軟體", "6148": "資訊服務與資安軟體",
    "2323": "光電與面板顯示", "2409": "光電與面板顯示", "3481": "光電與面板顯示", "6116": "光電與面板顯示",
    "2474": "電腦及週邊設備業", "2353": "電腦及週邊設備業", "2324": "電腦及週邊設備業", "2352": "電腦及週邊設備業",
    "2466": "電子零組件業"
}

INDUSTRY_TO_SECTOR_BRIDGE = {
    "通信網路業": "4. CPO矽光子與光通訊",
    "電腦及週邊設備業": "9. AI伺服器與組裝代工",
    "電機機械": "15. 重電電網與綠能儲能", "電器電纜": "15. 重電電網與綠能儲能", "綠能環保": "15. 重電電網與綠能儲能",
    "航運業": "16. 貨櫃航運與塑化原物料", "鋼鐵工業": "16. 貨櫃航運與塑化原物料", "塑膠工業": "16. 貨櫃航運與塑化原物料",
    "電子零組件業": "7. PCB硬板與伺服器板",
    "半導體業": "10. ASIC矽智財與IC設計"
}

def md_bold_to_html(txt):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", str(txt)).replace("\n", "<br>")

def clean_ai_markdown_text(raw_txt):
    """將 Gemini 輸出的超大 # 標題轉為乾淨粗體，並清除斷尾殘留的孤立 ** 符號"""
    txt = str(raw_txt).replace("`", "**")
    txt = re.sub(r"(?m)^#{1,4}\s*(.+)$", r"📌 **\1**", txt)
    txt = re.sub(r"\*\*\s*$", "", txt.strip())
    return txt

def parse_roc_date_str(roc_str):
    m = re.search(r"(\d{2,3})[/年\-\.](\d{1,2})[/月\-\.](\d{1,2})", str(roc_str).strip())
    if m: return f"{int(m.group(1)) + 1911:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None

def safe_float(val, default=0.0):
    m = re.search(r"[-+]?\d*\.?\d+", str(val).replace(",", ""))
    return float(m.group(0)) if (m and m.group(0) not in ["", "-", "+"]) else default

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
        "mkt_foreign_oi": -36850, "mkt_foreign_oi_chg": -1420, "mkt_spot_foreign": 159.22,
        "mkt_spot_trust": 118.07, "mkt_spot_dealer": 21.65, "mkt_margin_bal": 6233.87,
        "mkt_margin_chg": -104.93, "mkt_margin_chg_3d": -147.13, "mkt_short_bal": 217708,
        "mkt_short_chg": 1169, "cnn_fear_greed": 34, "mkt_chip_date": ""
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_cfg = json.load(f)
                for k, v in file_cfg.items():
                    if v is not None and str(v).strip() != "": cfg[k] = v
        except Exception: pass
    try:
        for k in list(cfg.keys()):
            if k in st.secrets:
                sec_v = st.secrets[k]
                if isinstance(sec_v, bool) or (sec_v is not None and str(sec_v).strip() != ""):
                    cfg[k] = sec_v
    except Exception: pass
    return cfg

@st.cache_data(ttl=3600)
def _discover_available_flash_models(clean_k):
    found = []
    try:
        r = GLOBAL_HTTP_SESSION.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={urllib.parse.quote(clean_k)}", timeout=5, verify=False)
        if r.status_code == 200 and r.json().get("models"):
            for m in r.json()["models"]:
                m_name = str(m.get("name", "")).replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods and "flash" in m_name.lower() and "pro" not in m_name.lower():
                    found.append(m_name)
    except Exception:
        pass
    found.sort(reverse=True)
    return found

def call_gemini_generate_content(prompt_text, api_key, timeout_sec=18):
    """
    【v12.6 防斷尾升級】強制設定 maxOutputTokens=2500，確保即使模型啟動內部思考 (Thinking)，也有充足配額完整輸出全文！
    """
    clean_k = str(api_key).strip()
    if not clean_k: return "", "未填寫 Gemini API Key"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"maxOutputTokens": 2500, "temperature": 0.3}
    }

    default_candidates = ["gemini-3.0-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash"]
    dynamic_flash = _discover_available_flash_models(clean_k)
    candidate_models = []
    for m in (default_candidates + dynamic_flash):
        if m not in candidate_models:
            candidate_models.append(m)

    err_detail = ""
    for model_name in candidate_models[:5]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={urllib.parse.quote(clean_k)}"
            r = GLOBAL_HTTP_SESSION.post(url, json=payload, timeout=timeout_sec, verify=False)
            if r.status_code == 200:
                cands = r.json().get("candidates", [])
                if cands and cands[0].get("content", {}).get("parts"):
                    full_txt = "".join(p.get("text", "") for p in cands[0]["content"]["parts"] if "text" in p)
                    if full_txt.strip():
                        return clean_ai_markdown_text(full_txt), ""
            err_msg = r.json().get("error", {}).get("message", f"HTTP {r.status_code}") if r.text else f"HTTP {r.status_code}"
            err_detail = err_msg
            m_suggest = re.search(r"models/(gemini-[a-zA-Z0-9\.\-]+)", err_msg)
            if m_suggest:
                sug_model = m_suggest.group(1)
                if sug_model not in candidate_models and "pro" not in sug_model.lower():
                    url_s = f"https://generativelanguage.googleapis.com/v1beta/models/{sug_model}:generateContent?key={urllib.parse.quote(clean_k)}"
                    r_s = GLOBAL_HTTP_SESSION.post(url_s, json=payload, timeout=timeout_sec, verify=False)
                    if r_s.status_code == 200:
                        cands = r_s.json().get("candidates", [])
                        if cands and cands[0].get("content", {}).get("parts"):
                            full_txt = "".join(p.get("text", "") for p in cands[0]["content"]["parts"] if "text" in p)
                            if full_txt.strip():
                                return clean_ai_markdown_text(full_txt), ""
        except Exception as e:
            err_detail = str(e)
    return "", err_detail

def read_csv_safely(filepath):
    for enc in ["utf-8-sig", "utf-8", "big5", "cp950"]:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            if "代號" in df.columns: df["代號"] = df["代號"].astype(str).str.strip().str.replace(".0", "", regex=False)
            return df
        except Exception: continue
    return pd.DataFrame()

@st.cache_data(ttl=43200)
def get_master_stock_dictionary():
    stock_dict, valid_pat = {}, re.compile(r"^(00\d{2,4}[A-Za-z]?|\d{4})$")
    preset_list = [
        ("2330", "台積電", "TWSE"), ("3167", "大量", "TWSE"), ("0050", "元大台灣50", "TWSE"),
        ("0056", "元大高股息", "TWSE"), ("00878", "國泰永續高股息", "TWSE"), ("00919", "群益台灣精選高息", "TWSE"),
        ("00929", "復華台灣科技優息", "TWSE"), ("00940", "元大台灣價值高息", "TWSE"), ("00877", "復華中國5G", "TPEX"),
        ("00631L", "元大台灣50正2", "TWSE"), ("00632R", "元大台灣50反1", "TWSE"), ("00937B", "群益ESG投等債20+", "TPEX"),
        ("00679B", "元大美債20年", "TPEX"), ("00687B", "國泰20年美債", "TPEX"), ("6214", "精誠", "TWSE"), ("00406A", "主動中信台灣收益", "TWSE")
    ]
    for c, n, m in preset_list: stock_dict[c] = {"代號": c, "名稱": n, "市場": m, "投本比": 0.0, "外本比": 0.0}
    for s_list in DEFAULT_SECTOR_STOCKS_MAP.values():
        for c, n, m in s_list: stock_dict[c] = {"代號": c, "名稱": n, "市場": m, "投本比": 0.0, "外本比": 0.0}
    for url, mkt, c_key, n_key in [
        ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", "TWSE", "Code", "Name"),
        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes", "TPEX", "SecuritiesCompanyCode", "CompanyName")
    ]:
        try:
            r = GLOBAL_HTTP_SESSION.get(url, timeout=8, verify=False)
            if r.status_code == 200:
                for it in r.json():
                    c, n = str(it.get(c_key, "")).strip().upper(), str(it.get(n_key, "")).strip()
                    if valid_pat.match(c) and n: stock_dict[c] = {"代號": c, "名稱": n, "市場": mkt, "投本比": 0.0, "外本比": 0.0}
        except Exception: pass
    if len(stock_dict) < 1200:
        try:
            r_fm = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params={"dataset": "TaiwanStockInfo"}, timeout=7, verify=False)
            if r_fm.status_code == 200 and r_fm.json().get("data"):
                for it in r_fm.json()["data"]:
                    c, n, tp = str(it.get("stock_id", "")).strip().upper(), str(it.get("stock_name", "")).strip(), str(it.get("type", "twse")).lower()
                    if valid_pat.match(c) and n and c not in stock_dict:
                        stock_dict[c] = {"代號": c, "名稱": n, "市場": "TPEX" if ("tpex" in tp or c.endswith("B")) else "TWSE", "投本比": 0.0, "外本比": 0.0}
        except Exception: pass
    return stock_dict

def sync_stock_code_list_online():
    get_master_stock_dictionary.clear()
    stock_dict = get_master_stock_dictionary()
    if len(stock_dict) > 500:
        df_new = pd.DataFrame(list(stock_dict.values())).sort_values("代號")
        os.makedirs(DATA_DIR, exist_ok=True)
        df_new.to_csv(QUOTES_FILE, index=False, encoding="utf-8-sig")
        return True, f"🎉 成功更新 {len(df_new)} 檔上市櫃股票與全品項 ETF！"
    return False, "同步清單失敗。"

def sync_taifex_futures_online():
    records = {}
    try:
        resp = GLOBAL_HTTP_SESSION.get("https://www.taifex.com.tw/cht/5/stockMargining", timeout=10, verify=False)
        resp.encoding = "utf-8"
        for r_html in re.findall(r"<tr[^>]*>(.*?)</tr>", resp.text, re.S):
            clean_txt = " ".join(re.sub(r"<[^>]+>", " ", r_html).split())
            m_code = re.search(r"(?<![0-9A-Za-z])(00\d{2,4}[A-Za-z]?|\d{4})(?![0-9A-Za-z])", clean_txt)
            if m_code:
                code = m_code.group(1).upper()
                rates = [float(x) for x in re.findall(r"(\d{2}\.\d{1,2})%", clean_txt) if 10.0 <= float(x) <= 50.0]
                zh_m = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{2,8}期)", clean_txt)
                fut_name = (zh_m.group(1) if zh_m else f"{code}期").replace("小型", "")
                if code not in records:
                    records[code] = {"代號": code, "期貨簡稱": fut_name, "標準期貨": "有", "小型期貨": "有" if "小型" in clean_txt else "無", "保證金比例": max(rates) if rates else 13.50}
                else: records[code]["小型期貨"] = "有"
    except Exception as e: return False, f"連線異常：{e}"
    if records:
        pd.DataFrame(list(records.values())).to_csv(FUTURES_FILE, index=False, encoding="utf-8-sig")
        return True, f"🎉 成功同步 {len(records)} 檔個股期貨！"
    return False, "未能解析出期貨資料。"

def init_sample_csvs():
    os.makedirs(DATA_DIR, exist_ok=True)
    master_dict = get_master_stock_dictionary()
    if not os.path.exists(QUOTES_FILE) or len(read_csv_safely(QUOTES_FILE)) < 500:
        if len(master_dict) > 50:
            pd.DataFrame(list(master_dict.values())).sort_values("代號").to_csv(QUOTES_FILE, index=False, encoding="utf-8-sig")
    if not os.path.exists(FUTURES_FILE):
        pd.DataFrame([["2330", "台積電期", "有", "有", 13.50]], columns=["代號", "期貨簡稱", "標準期貨", "小型期貨", "保證金比例"]).to_csv(FUTURES_FILE, index=False, encoding="utf-8-sig")
    if not os.path.exists(CB_FILE):
        pd.DataFrame([["2383", "23835", "台光電五", 585.0, 118.5, "2028-05-15"]], columns=["代號", "CB代號", "CB名稱", "轉換價", "CB收盤價", "到期日"]).to_csv(CB_FILE, index=False, encoding="utf-8-sig")

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
    net_pnl = (sell_amt - buy_amt) - total_cost
    long_be = round(((buy_amt + fee_buy + max(20, buy_amt * fee_rate)) / max(1e-6, 1.0 - tax_rate)) / (1000.0 * lots), 2)
    short_be = round(max(0.01, (sell_amt - fee_sell - tax - max(20, sell_amt * fee_rate)) / (1000.0 * lots)), 2)

    long_wt, long_wp = 1, step_tw_ticks(buy_p, 1)
    for t_i in range(1, 25):
        cs = step_tw_ticks(buy_p, t_i)
        ca = int(round(cs * 1000.0 * lots))
        if (ca - buy_amt - fee_buy - max(20, math.floor(ca * fee_rate)) - math.floor(ca * tax_rate)) > 0:
            long_wt, long_wp = t_i, cs; break

    short_wt, short_wp = 1, step_tw_ticks(sell_p, -1)
    for t_i in range(1, 25):
        cb = step_tw_ticks(sell_p, -t_i)
        ca = int(round(cb * 1000.0 * lots))
        if (sell_amt - ca - max(20, math.floor(ca * fee_rate)) - fee_sell - tax) > 0:
            short_wt, short_wp = t_i, cb; break

    return {
        "buy_amt": buy_amt, "sell_amt": sell_amt, "fee_buy": fee_buy, "fee_sell": fee_sell,
        "total_fee": total_fee, "tax": tax, "total_cost": total_cost, "net_pnl": net_pnl,
        "roi_pct": round((net_pnl / (buy_amt + fee_buy)) * 100.0, 2) if buy_amt > 0 else 0.0,
        "long_be_price": long_be, "short_be_price": short_be,
        "long_win_ticks": long_wt, "long_win_price": long_wp,
        "short_win_ticks": short_wt, "short_win_price": short_wp
    }

def calculate_cdp(high, low, close):
    cdp, pt = (high + low + 2 * close) / 4.0, high - low
    return {"AH": round(cdp + pt, 2), "NH": round(2 * cdp - low, 2), "CDP": round(cdp, 2), "NL": round(2 * cdp - high, 2), "AL": round(cdp - pt, 2), "PT": round(pt, 2)}

def clean_holiday_phantom_bars(df_in, is_index=False):
    if df_in.empty: return df_in
    df = df_in[df_in.index.dayofweek < 5].copy()
    if df.empty: return df
    now_tw = pd.Timestamp.now(tz="Asia/Taipei")
    today_str = now_tw.strftime("%Y-%m-%d")
    now_hhmm = now_tw.hour * 100 + now_tw.minute
    if len(df) >= 1 and df.index[-1].strftime("%Y-%m-%d") == today_str:
        if now_hhmm < 900: df = df.iloc[:-1]
    if not is_index:
        df = df[~((df["Volume"] <= 0) & ((df["High"] - df["Low"]).abs() < 1e-5))]
    elif len(df) > 5:
        df = df[~(((df["High"] - df["Low"]).abs() < 1e-4) & ((df["Close"] - df["Close"].shift(1)).abs() < 1e-4))]
    return df

@st.cache_data(ttl=300)
def _fetch_twse_official_taiex_kline():
    now_tw = pd.Timestamp.now(tz="Asia/Taipei")
    prev_m = now_tw - pd.Timedelta(days=28)
    month_strs = sorted(list({prev_m.strftime("%Y%m01"), now_tw.strftime("%Y%m01")}))
    rows = {}
    for m_str in month_strs:
        try:
            r = GLOBAL_HTTP_SESSION.get(f"https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?date={m_str}&response=json", timeout=5, verify=False)
            if r.status_code == 200 and r.json().get("stat") == "OK":
                for item in r.json().get("data", []):
                    dt_s = parse_roc_date_str(item[0])
                    if dt_s:
                        op, hp, lp, cp = safe_float(item[1]), safe_float(item[2]), safe_float(item[3]), safe_float(item[4])
                        if cp > 0: rows[pd.Timestamp(dt_s)] = {"Open": op, "High": hp, "Low": lp, "Close": cp, "Volume": 0.0}
        except Exception: continue
    if rows: return pd.DataFrame.from_dict(rows, orient="index").sort_index()
    return pd.DataFrame()

@st.cache_data(ttl=300)
def _fetch_twse_tpex_official_stock_kline(code, market_hint="TWSE"):
    now_tw = pd.Timestamp.now(tz="Asia/Taipei")
    prev_m = now_tw - pd.Timedelta(days=28)
    month_strs = sorted(list({prev_m.strftime("%Y%m01"), now_tw.strftime("%Y%m01")}))
    rows = {}
    if market_hint == "TWSE":
        for m_str in month_strs:
            try:
                r = GLOBAL_HTTP_SESSION.get(f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date={m_str}&stockNo={code}&response=json", timeout=5, verify=False)
                if r.status_code == 200 and r.json().get("stat") == "OK":
                    for item in r.json().get("data", []):
                        dt_s = parse_roc_date_str(item[0])
                        if dt_s:
                            vol_sh = safe_float(item[1])
                            op, hp, lp, cp = safe_float(item[3]), safe_float(item[4]), safe_float(item[5]), safe_float(item[6])
                            if cp > 0: rows[pd.Timestamp(dt_s)] = {"Open": op, "High": hp, "Low": lp, "Close": cp, "Volume": vol_sh}
            except Exception: continue
    else:
        for m_str in [prev_m.strftime("%Y/%m/01"), now_tw.strftime("%Y/%m/01")]:
            try:
                r = GLOBAL_HTTP_SESSION.get(f"https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingStock?code={code}&date={m_str}&response=json", timeout=5, verify=False)
                if r.status_code == 200:
                    j_data = r.json()
                    t_data = j_data.get("tables", [{}])[0].get("data", []) if "tables" in j_data else j_data.get("aaData", [])
                    for item in t_data:
                        dt_s = parse_roc_date_str(item[0])
                        if dt_s:
                            vol_sh = safe_float(item[1]) * 1000.0
                            op, hp, lp, cp = safe_float(item[3]), safe_float(item[4]), safe_float(item[5]), safe_float(item[6])
                            if cp > 0: rows[pd.Timestamp(dt_s)] = {"Open": op, "High": hp, "Low": lp, "Close": cp, "Volume": vol_sh}
            except Exception: continue
    if rows: return pd.DataFrame.from_dict(rows, orient="index").sort_index()
    return pd.DataFrame()

def _fetch_official_finmind_daily_kline(code, is_idx=False, days_back=190):
    try:
        cfg_local = load_config()
        fm_tok = str(cfg_local.get("finmind_token", "")).strip()
        start_dt = (pd.Timestamp.now() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
        params = {"dataset": "TaiwanStockPrice", "data_id": "TAIEX" if is_idx else code, "start_date": start_dt}
        if fm_tok: params["token"] = fm_tok
        resp = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=5, verify=False)
        if resp.status_code == 200 and resp.json().get("data"):
            df_fm = pd.DataFrame(resp.json()["data"])
            df_fm["Date"] = pd.to_datetime(df_fm["date"]).dt.normalize()
            df_fm = df_fm.set_index("Date")
            df_fm = df_fm[~df_fm.index.duplicated(keep="last")]
            v_col = "Trading_Volume" if "Trading_Volume" in df_fm.columns else ("volume" if "volume" in df_fm.columns else None)
            df_real = pd.DataFrame({
                "Open": df_fm["open"].astype(float), "High": df_fm["max"].astype(float),
                "Low": df_fm["min"].astype(float), "Close": df_fm["close"].astype(float),
                "Volume": df_fm[v_col].astype(float) if v_col else 0.0
            }).dropna(subset=["Close"])
            df_real = df_real[df_real["Close"] > 0]
            return clean_holiday_phantom_bars(df_real, is_index=is_idx)
    except Exception: pass
    return pd.DataFrame()

def fetch_kline_df_bypass_ssl(code, market_hint="TWSE", range_str="6mo", verify_official=True):
    is_idx = code in ["^TWII", "TAIEX", "^SOX", "TWD=X"]
    if str(code).upper().endswith("B"): market_hint = "TPEX"
    if code == "^TWII": symbols = ["%5ETWII"]
    elif code == "^SOX": symbols = ["%5ESOX"]
    elif code == "TWD=X": symbols = ["TWD%3DX"]
    else: symbols = [f"{code}{sfx}" for sfx in ([".TWO", ".TW"] if market_hint == "TPEX" else [".TW", ".TWO"])]
    ts_b = int(time.time() // 120)

    df_yf = pd.DataFrame()
    for sym in symbols:
        for host in ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]:
            try:
                resp = GLOBAL_HTTP_SESSION.get(f"https://{host}/v8/finance/chart/{sym}?range={range_str}&interval=1d&includePrePost=false&_ts={ts_b}", timeout=5, verify=False)
                if resp.status_code == 200:
                    res = resp.json().get("chart", {}).get("result", [])
                    if res and res[0].get("timestamp") and "close" in res[0].get("indicators", {}).get("quote", [{}])[0]:
                        ts, q = res[0]["timestamp"], res[0]["indicators"]["quote"][0]
                        tz_target = "America/New_York" if code == "^SOX" else "Asia/Taipei"
                        dt_idx = pd.to_datetime(ts, unit="s", utc=True).tz_convert(tz_target).normalize().tz_localize(None)
                        df_tmp = pd.DataFrame({"Open": q.get("open", q["close"]), "High": q.get("high", q["close"]), "Low": q.get("low", q["close"]), "Close": q["close"], "Volume": q.get("volume", [0]*len(ts))}, index=dt_idx)
                        df_tmp = df_tmp[~df_tmp.index.duplicated(keep="last")].dropna(subset=["Close"])
                        for c in ["Open", "High", "Low"]: df_tmp[c] = df_tmp[c].fillna(df_tmp["Close"])
                        df_tmp["Volume"] = df_tmp["Volume"].fillna(0)
                        df_tmp = clean_holiday_phantom_bars(df_tmp, is_index=is_idx)
                        if len(df_tmp) >= 5: df_yf = df_tmp; break
            except Exception: continue
        if not df_yf.empty: break

    if verify_official and code not in ["^SOX", "TWD=X"]:
        df_off = _fetch_twse_official_taiex_kline() if code in ["^TWII", "TAIEX"] else _fetch_twse_tpex_official_stock_kline(code, market_hint)
        df_fm = _fetch_official_finmind_daily_kline(code, is_idx=is_idx, days_back=(190 if range_str == "6mo" else 65))
        base_df = df_yf.copy() if not df_yf.empty else pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        if not df_fm.empty:
            for dt_k, r_k in df_fm.iterrows(): base_df.loc[dt_k] = r_k
        if not df_off.empty:
            for dt_k, r_k in df_off.iterrows(): base_df.loc[dt_k] = r_k
        if not base_df.empty:
            base_df = clean_holiday_phantom_bars(base_df.sort_index(), is_index=is_idx)
            if len(base_df) >= 5: return base_df, ""

    if not df_yf.empty and len(df_yf) >= 5: return df_yf, ""
    return pd.DataFrame(), "連線逾時"

def compute_td_sequential_and_bbands(df_in):
    df = df_in.copy()
    df["MA5"], df["MA20"], df["MA60"] = df["Close"].rolling(5).mean(), df["Close"].rolling(20).mean(), df["Close"].rolling(60).mean()
    std20 = df["Close"].rolling(20).std(ddof=0)
    df["BB_Upper"], df["BB_Lower"] = df["MA20"] + 2.0 * std20, df["MA20"] - 2.0 * std20
    closes, n_len = df["Close"].values, len(df)
    raw_b, raw_s, disp_b, disp_s = [0]*n_len, [0]*n_len, [0]*n_len, [0]*n_len
    b_c = s_c = 0
    for i in range(n_len):
        if i >= 4:
            if closes[i] < closes[i - 4]: b_c, s_c = (b_c + 1 if b_c < 9 else 1), 0
            elif closes[i] > closes[i - 4]: s_c, b_c = (s_c + 1 if s_c < 9 else 1), 0
            else: b_c = s_c = 0
        raw_b[i], raw_s[i] = b_c, s_c
    for i in range(n_len):
        if raw_b[i] == 9:
            for k in range(9):
                if i - k >= 0: disp_b[i - k] = 9 - k
        if raw_s[i] == 9:
            for k in range(9):
                if i - k >= 0: disp_s[i - k] = 9 - k
    if n_len > 0 and 0 < raw_b[-1] < 9:
        for k in range(raw_b[-1]):
            if n_len - 1 - k >= 0: disp_b[n_len - 1 - k] = raw_b[-1] - k
    if n_len > 0 and 0 < raw_s[-1] < 9:
        for k in range(raw_s[-1]):
            if n_len - 1 - k >= 0: disp_s[n_len - 1 - k] = raw_s[-1] - k
    df["TD_Buy"], df["TD_Sell"], df["TD_Buy_Disp"], df["TD_Sell_Disp"] = raw_b, raw_s, disp_b, disp_s
    return df

def calc_kd_rsi_macd(hist):
    low_9, high_9 = hist["Low"].rolling(9).min(), hist["High"].rolling(9).max()
    rsv = (((hist["Close"] - low_9) / (high_9 - low_9 + 1e-9)) * 100).fillna(50)
    k_v, d_v = [50.0], [50.0]
    for r in rsv:
        k_v.append((2/3) * k_v[-1] + (1/3) * float(r))
        d_v.append((2/3) * d_v[-1] + (1/3) * k_v[-1])
    dif = hist["Close"].ewm(span=12, adjust=False).mean() - hist["Close"].ewm(span=26, adjust=False).mean()
    osc = dif - dif.ewm(span=9, adjust=False).mean()
    delta = hist["Close"].diff()
    rs = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean() / ((-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean() + 1e-9)
    rsi14 = round(float((100 - (100 / (1 + rs))).iloc[-1]), 1) if len(hist) >= 15 else 50.0
    k_prev = round(k_v[-2], 1) if len(k_v) >= 2 else 50.0
    d_prev = round(d_v[-2], 1) if len(d_v) >= 2 else 50.0
    osc_prev = round(float(osc.iloc[-2]), 2) if len(osc) >= 2 else 0.0
    return round(k_v[-1], 1), round(d_v[-1], 1), k_prev, d_prev, round(float(osc.iloc[-1]), 2), osc_prev, rsi14

@st.cache_data(ttl=120)
def fetch_intraday_kline_full(code, market_hint="TWSE", interval="5m"):
    if str(code).upper().endswith("B"): market_hint = "TPEX"
    range_str, ts_b = ("5d" if interval == "5m" else "1mo"), int(time.time() // 120)
    for sfx in ([".TWO", ".TW"] if market_hint == "TPEX" else [".TW", ".TWO"]):
        for host in ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]:
            try:
                resp = GLOBAL_HTTP_SESSION.get(f"https://{host}/v8/finance/chart/{code}{sfx}?range={range_str}&interval={interval}&includePrePost=false&_ts={ts_b}", timeout=5, verify=False)
                if resp.status_code == 200:
                    res = resp.json().get("chart", {}).get("result", [])
                    if res and res[0].get("timestamp"):
                        ts, q = res[0]["timestamp"], res[0]["indicators"]["quote"][0]
                        dt_idx = pd.to_datetime(ts, unit="s", utc=True).tz_convert("Asia/Taipei")
                        hhmm = dt_idx.hour * 100 + dt_idx.minute
                        df_i = pd.DataFrame({"DateStr": dt_idx.strftime("%m/%d %H:%M"), "ShortDate": dt_idx.strftime("%m/%d %H:%M"), "hhmm": hhmm, "Open": q.get("open", q["close"]), "High": q.get("high", q["close"]), "Low": q.get("low", q["close"]), "Close": q["close"], "Volume": q.get("volume", [0]*len(ts))}).dropna(subset=["Close"])
                        for c in ["Open", "High", "Low"]: df_i[c] = df_i[c].fillna(df_i["Close"])
                        df_i["Volume"] = (df_i["Volume"].fillna(0) / 1000.0).round(0)
                        df_i = df_i[(df_i["Volume"] > 0) & (df_i["hhmm"] >= 900) & (df_i["hhmm"] <= 1335)].reset_index(drop=True)
                        if len(df_i) >= 15:
                            df_i = compute_td_sequential_and_bbands(df_i)
                            k_v, d_v, _, _, osc_v, _, rsi_v = calc_kd_rsi_macd(df_i)
                            lt = df_i.iloc[-1]
                            cp = round(float(lt["Close"]), 2)
                            return {
                                "ok": True, "interval": interval, "time_str": str(lt["DateStr"]), "close": cp,
                                "ma5": round(float(lt["MA5"]), 2) if pd.notna(lt["MA5"]) else cp,
                                "ma20": round(float(lt["MA20"]), 2) if pd.notna(lt["MA20"]) else cp,
                                "ma60": round(float(lt["MA60"]), 2) if pd.notna(lt["MA60"]) else cp,
                                "bb_upper": round(float(lt["BB_Upper"]), 2) if pd.notna(lt["BB_Upper"]) else cp,
                                "bb_lower": round(float(lt["BB_Lower"]), 2) if pd.notna(lt["BB_Lower"]) else cp,
                                "deduct": round(float(df_i["Close"].iloc[-20]), 2) if len(df_i) >= 20 else cp,
                                "td_buy": int(lt["TD_Buy"]), "td_sell": int(lt["TD_Sell"]), "K": k_v, "D": d_v, "macd_osc": osc_v, "rsi": rsi_v,
                                "records": df_i.tail(85 if interval == "5m" else 80).to_dict("records")
                            }
            except Exception: continue
    return {"ok": False, "interval": interval, "records": []}

@st.cache_data(ttl=180)
def fetch_technical_indicators(code, market_hint="TWSE"):
    if str(code).upper().endswith("B"): market_hint = "TPEX"
    hist, err_msg = fetch_kline_df_bypass_ssl(code, market_hint, range_str="6mo", verify_official=True)
    if hist.empty or len(hist) < 5: return {"ok": False, "err_msg": err_msg}
    hist = compute_td_sequential_and_bbands(hist)
    lt = hist.iloc[-1]
    cp, hp, lp = round(float(lt["Close"]), 2), round(float(lt["High"]), 2), round(float(lt["Low"]), 2)
    if abs(hp - lp) < 1e-4 and len(hist) >= 2:
        pv = hist.iloc[-2]
        hr = max(0.5, round((float(pv["High"]) - float(pv["Low"])) * 0.5, 2))
        hp, lp = round(cp + hr, 2), round(max(0.01, cp - hr), 2)
    prev_1d = round(float(hist["Close"].iloc[-2]), 2) if len(hist) >= 2 else cp
    prev_5d = float(hist["Close"].iloc[-6]) if len(hist) >= 6 else prev_1d
    chg_1d_pct = round(((cp - prev_1d) / prev_1d) * 100.0, 2) if prev_1d > 0 else 0.0
    chg_5d_pct = round(((cp - prev_5d) / prev_5d) * 100.0, 2) if prev_5d > 0 else 0.0
    vol_5d_lots = round(float(hist["Volume"].tail(5).sum()) / 1000.0, 1)
    vol_ma5 = float(hist["Volume"].tail(5).mean())
    k_val, d_val, _, _, osc_today, osc_prev, rsi14 = calc_kd_rsi_macd(hist)
    hist_60 = hist.tail(60).copy()
    hist_60["DateStr"], hist_60["ShortDate"] = hist_60.index.strftime("%Y-%m-%d"), hist_60.index.strftime("%m-%d")
    return {
        "ok": True, "date": hist.index[-1].strftime("%Y-%m-%d"), "high": hp, "low": lp, "close": cp, "prev_close": prev_1d,
        "chg_1d_pct": chg_1d_pct, "chg_5d_pct": chg_5d_pct, "vol_5d_lots": max(1.0, vol_5d_lots),
        "ma5": round(float(lt["MA5"]), 2) if pd.notna(lt["MA5"]) else cp,
        "ma20": round(float(lt["MA20"]), 2) if pd.notna(lt["MA20"]) else cp,
        "ma60": round(float(lt["MA60"]), 2) if pd.notna(lt["MA60"]) else cp,
        "bb_upper": round(float(lt["BB_Upper"]), 2) if pd.notna(lt["BB_Upper"]) else cp,
        "bb_lower": round(float(lt["BB_Lower"]), 2) if pd.notna(lt["BB_Lower"]) else cp,
        "td_buy": int(lt["TD_Buy"]), "td_sell": int(lt["TD_Sell"]),
        "deduct": round(float(hist["Close"].iloc[-20]), 2) if len(hist) >= 20 else cp,
        "K": k_val, "D": d_val, "macd_osc": osc_today, "macd_prev": osc_prev, "rsi": rsi14,
        "vol_ratio": round(float(lt["Volume"]) / vol_ma5, 2) if vol_ma5 > 0 else 1.0,
        "kline_60": hist_60[["DateStr", "ShortDate", "Open", "High", "Low", "Close", "Volume", "MA5", "MA20", "MA60", "BB_Upper", "BB_Lower", "TD_Buy", "TD_Sell", "TD_Buy_Disp", "TD_Sell_Disp"]].to_dict("records")
    }

@st.cache_data(ttl=3600)
def fetch_fundamental_revenue_and_shareholding(code, fm_token=""):
    res = {"has_rev": False, "rev_month": "-", "yoy_latest": 0.0, "yoy_3m_avg": 0.0, "yoy_accel": 0.0, "mom_latest": 0.0, "foreign_hold_pct": 0.0, "foreign_hold_chg_5d": 0.0}
    if str(code).startswith("00"): return res
    try:
        start_rev = (pd.Timestamp.now() - pd.Timedelta(days=500)).strftime("%Y-%m-%d")
        p_rev = {"dataset": "TaiwanStockMonthRevenue", "data_id": code, "start_date": start_rev}
        if fm_token: p_rev["token"] = fm_token
        r_rev = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=p_rev, timeout=6, verify=False)
        if r_rev.status_code == 200 and r_rev.json().get("data"):
            df_r = pd.DataFrame(r_rev.json()["data"]).sort_values(["revenue_year", "revenue_month"])
            df_r["rev"] = df_r["revenue"].astype(float)
            df_r["ym"] = df_r["revenue_year"].astype(str) + "-" + df_r["revenue_month"].astype(str).str.zfill(2)
            rev_map = dict(zip(zip(df_r["revenue_year"].astype(int), df_r["revenue_month"].astype(int)), df_r["rev"]))
            yoy_list = []
            for _, row in df_r.iterrows():
                y, m, cur_v = int(row["revenue_year"]), int(row["revenue_month"]), float(row["rev"])
                prev_y_v = rev_map.get((y - 1, m), 0.0)
                if prev_y_v > 0: yoy_list.append((row["ym"], round(((cur_v - prev_y_v) / prev_y_v) * 100.0, 2), cur_v))
            if len(yoy_list) >= 3:
                yoy_latest, yoy_3m_avg = yoy_list[-1][1], round(sum(x[1] for x in yoy_list[-3:]) / 3.0, 2)
                prev_m_v = yoy_list[-2][2]
                mom_latest = round(((yoy_list[-1][2] - prev_m_v) / prev_m_v) * 100.0, 2) if prev_m_v > 0 else 0.0
                res.update({"has_rev": True, "rev_month": yoy_list[-1][0], "yoy_latest": yoy_latest, "yoy_3m_avg": yoy_3m_avg, "yoy_accel": round(yoy_latest - yoy_3m_avg, 2), "mom_latest": mom_latest})
    except Exception: pass

    try:
        start_sh = (pd.Timestamp.now() - pd.Timedelta(days=20)).strftime("%Y-%m-%d")
        p_sh = {"dataset": "TaiwanStockShareholding", "data_id": code, "start_date": start_sh}
        if fm_token: p_sh["token"] = fm_token
        r_sh = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=p_sh, timeout=5, verify=False)
        if r_sh.status_code == 200 and r_sh.json().get("data"):
            df_s = pd.DataFrame(r_sh.json()["data"]).sort_values("date")
            if len(df_s) >= 2:
                latest_r, prev5_r = float(df_s["ForeignInvestmentSharesRatio"].iloc[-1]), float(df_s["ForeignInvestmentSharesRatio"].iloc[max(0, len(df_s)-6)])
                res.update({"foreign_hold_pct": round(latest_r, 2), "foreign_hold_chg_5d": round(latest_r - prev5_r, 2)})
    except Exception: pass
    return res

@st.cache_data(ttl=3600)
def fetch_chip_data_20d(code, fm_token=""):
    empty_p = {w: {"f": 0, "t": 0, "d": 0, "tot": 0} for w in [1, 3, 5, 10, 20]}
    try:
        params = {"dataset": "TaiwanStockInstitutionalInvestorsBuySell", "data_id": code, "start_date": (pd.Timestamp.now() - pd.Timedelta(days=50)).strftime("%Y-%m-%d")}
        if fm_token: params["token"] = fm_token
        resp = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=7, verify=False)
        if resp.status_code == 200 and resp.json().get("data"):
            df_c = pd.DataFrame(resp.json()["data"])
            dates = sorted(df_c["date"].unique())[-20:]
            df_20 = df_c[df_c["date"].isin(dates)].copy()
            df_20["net_lots"] = (df_20["buy"].astype(float) - df_20["sell"].astype(float)) / 1000.0
            rows = []
            for dt_s in sorted(dates, reverse=True):
                sub = df_20[df_20["date"] == dt_s]
                f_d = int(round(sub[sub["name"].str.contains("Foreign", case=False, na=False)]["net_lots"].sum()))
                t_d = int(round(sub[sub["name"].str.contains("Investment_Trust", case=False, na=False)]["net_lots"].sum()))
                d_d = int(round(sub[sub["name"].str.contains("Dealer", case=False, na=False)]["net_lots"].sum()))
                rows.append({"交易日期": dt_s, "外資買賣超(張)": f_d, "投信買賣超(張)": t_d, "自營商買賣超(張)": d_d, "三大法人合計(張)": f_d + t_d + d_d})
            periods = {w: {"f": sum(r["外資買賣超(張)"] for r in rows[:w]), "t": sum(r["投信買賣超(張)"] for r in rows[:w]), "d": sum(r["自營商買賣超(張)"] for r in rows[:w]), "tot": sum(r["三大法人合計(張)"] for r in rows[:w])} for w in [1, 3, 5, 10, 20]}
            return {"ok": True, "periods": periods, "foreign_5d": periods[5]["f"], "trust_5d": periods[5]["t"], "dealer_5d": periods[5]["d"], "total_5d": periods[5]["tot"], "foreign_10d": periods[10]["f"], "trust_10d": periods[10]["t"], "dealer_10d": periods[10]["d"], "total_10d": periods[10]["tot"], "daily_table": rows}
    except Exception: pass
    return {"ok": False, "periods": empty_p, "foreign_5d": 0, "trust_5d": 0, "dealer_5d": 0, "total_5d": 0, "foreign_10d": 0, "trust_10d": 0, "dealer_10d": 0, "total_10d": 0, "daily_table": []}

@st.cache_data(ttl=3600)
def fetch_margin_short_20d(code, fm_token=""):
    empty_m = {w: {"m_chg": 0, "s_chg": 0} for w in [1, 3, 5, 10, 20]}
    try:
        params = {"dataset": "TaiwanStockMarginPurchaseShortSale", "data_id": code, "start_date": (pd.Timestamp.now() - pd.Timedelta(days=50)).strftime("%Y-%m-%d")}
        if fm_token: params["token"] = fm_token
        resp = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=7, verify=False)
        if resp.status_code == 200 and resp.json().get("data"):
            df_20 = pd.DataFrame(resp.json()["data"]).sort_values("date").tail(20).copy()
            rows = []
            for _, r in df_20.iloc[::-1].iterrows():
                mb, mp, ml = int(float(r.get("MarginPurchaseTodayBalance", 0))), int(float(r.get("MarginPurchaseYesterdayBalance", 0))), int(float(r.get("MarginPurchaseLimit", 0)))
                sb, sp = int(float(r.get("ShortSaleTodayBalance", 0))), int(float(r.get("ShortSaleYesterdayBalance", 0)))
                rows.append({"交易日期": str(r["date"]), "融資餘額(張)": mb, "融資增減(張)": mb - mp, "融資使用率(%)": round((mb / ml) * 100, 2) if ml > 0 else 0.0, "融券餘額(張)": sb, "融券增減(張)": sb - sp, "券資比(%)": round((sb / mb) * 100, 2) if mb > 0 else 0.0, "_limit": ml})
            if rows:
                lt = rows[0]
                m_p = {w: {"m_chg": sum(x["融資增減(張)"] for x in rows[:w]), "s_chg": sum(x["融券增減(張)"] for x in rows[:w])} for w in [1, 3, 5, 10, 20]}
                return {"ok": True, "eligible": (lt["_limit"] > 0) or (lt["融資餘額(張)"] > 0), "periods": m_p, "margin_bal": lt["融資餘額(張)"], "margin_chg": lt["融資增減(張)"], "margin_util": lt["融資使用率(%)"], "short_bal": lt["融券餘額(張)"], "short_chg": lt["融券增減(張)"], "short_margin_ratio": lt["券資比(%)"], "daily_table": [{k: v for k, v in it.items() if k != "_limit"} for it in rows]}
    except Exception: pass
    return {"ok": False, "eligible": False, "periods": empty_m, "margin_bal": 0, "margin_chg": 0, "margin_util": 0.0, "short_bal": 0, "short_chg": 0, "short_margin_ratio": 0.0, "daily_table": []}

def build_smart_diagnostic_reasons(code, name, tech, chip, margin_info, fund_info, eval_res, news_list):
    c, ma5, ma20, ma60, ded = tech["close"], tech["ma5"], tech["ma20"], tech["ma60"], tech["deduct"]
    chg_1d, chg_5d = tech["chg_1d_pct"], tech["chg_5d_pct"]
    alpha_1d, alpha_5d = eval_res["alpha_1d"], eval_res["alpha_5d"]
    p_c = chip["periods"]
    tot_1d, tot_5d, f_5d, t_5d = p_c[1]["tot"], p_c[5]["tot"], p_c[5]["f"], p_c[5]["t"]
    m_chg_5d = margin_info["periods"][5]["m_chg"] if (margin_info and margin_info.get("ok")) else 0
    is_etf = str(code).startswith("00")
    bias20 = round(((c - ma20) / ma20) * 100.0, 2) if ma20 > 0 else 0.0

    is_weak = (eval_res["total"] < 48) or (chg_1d < -1.0) or (chg_5d < -2.0) or (c < ma20)
    header = f"📉 **【為什麼 {code} {name} 近期表現偏弱？系統自動歸因診斷】**" if is_weak else f"📈 **【{code} {name} 近期強弱動能歸因診斷】**"
    reasons = []

    if c < ma20 and c < ma5:
        reasons.append(f"**① 均線反壓與扣抵蓋頭**：現價（**{c}元**）同時跌破五日線（**{ma5}元**）與 20MA 月線均價（**{ma20}元**，月線乖離率 **{bias20:+.2f}%**），且 20 日扣抵值在 **{ded}元** 形成上檔壓力，短中期技術面處於空方排列。")
    elif c >= ma20 and c < ma5:
        reasons.append(f"**① 短線漲多拉回修正**：現價（**{c}元**）雖守在 20MA 月線均價（**{ma20}元**）之上，但短線跌破五日線（**{ma5}元**），屬於波段偏多下的短線獲利了結洗盤。")
    else:
        reasons.append(f"**① 均線多頭助漲**：現價（**{c}元**）站穩五日線（**{ma5}元**）與 20MA 月線均價（**{ma20}元**）之上，技術面具備支撐。")

    if is_etf and any(w in name for w in ["中國", "陸", "滬", "深", "恒生", "港", "美債", "日", "越"]):
        reasons.append(f"**② 海外標的指數與匯率連動（關鍵主因）**：**{code} {name}** 屬於追蹤海外資產之 ETF（近1日 **{chg_1d:+.2f}%** ／ 近5日 **{chg_5d:+.2f}%**），走勢直接受其追蹤之海外成分股指數（如陸港股 5G/通信板塊或海外債市）回檔拖累，與台股加權指數脫鉤（5日對抗台股 Alpha 為 **{alpha_5d:+.2f}%**）。")
    elif alpha_1d < -0.5 or alpha_5d < -1.5:
        reasons.append(f"**② 資金排擠效應（落後大盤 Alpha）**：近 1 日相對大盤強弱 Alpha 為 **{alpha_1d:+.2f}%**（近 5 日 Alpha **{alpha_5d:+.2f}%**），代表市場主力資金目前未駐足於此，表現明顯落後大盤。")
    else:
        reasons.append(f"**② 相對大盤抗跌領漲**：近 1 日對抗大盤 Alpha 為 **{alpha_1d:+.2f}%**（近 5 日 **{alpha_5d:+.2f}%**），資金強度優於大盤均值。")

    if tot_5d < 0 and m_chg_5d > 0:
        reasons.append(f"**③ 籌碼結構惡化（法人提款、散戶融資接刀）**：近 5 日三大法人合計賣超 **{tot_5d:+,} 張**（外資 **{f_5d:+,}**、投信 **{t_5d:+,}**，佔成交量 **{eval_res['inst_vol_ratio']:+.1f}%**），但近 5 日散戶融資卻逆勢增加 **{m_chg_5d:+,} 張**，籌碼凌亂導致上檔賣壓沉重。")
    elif tot_5d < 0:
        reasons.append(f"**③ 法人調節賣壓**：近 5 日三大法人合計調節 **{tot_5d:+,} 張**（最新 1 日 **{tot_1d:+,} 張**），缺乏外資或投信連續買盤點火。")
    else:
        reasons.append(f"**③ 法人買盤支撐**：近 5 日三大法人合計買超 **{tot_5d:+,} 張**（最新 1 日 **{tot_1d:+,} 張**，佔量 **{eval_res['inst_vol_ratio']:+.1f}%**）。")

    if not is_etf and fund_info and fund_info.get("has_rev"):
        yoy, acc = fund_info["yoy_latest"], fund_info["yoy_accel"]
        if yoy < 0 or acc < -5:
            reasons.append(f"**④ 基本面營收動能放緩**：最新 {fund_info['rev_month']} 月營收年增率為 **{yoy:+.1f}%**（成長加速度 **{acc:+.1f}%**），業績動能降溫。")
        elif yoy >= 15 and c < ma20:
            reasons.append(f"**④ 提防高檔利多鈍化**：雖 {fund_info['rev_month']} 營收 YoY 達 **{yoy:+.1f}%**，但股價不漲反破月線，顯示市場已提前反應或出現利多出盡。")

    if news_list:
        top_news = " ／ ".join([n["title"].split(" - ")[0] for n in news_list[:2]])
        reasons.append(f"**📰 近期市場消息面線索**：{top_news}")

    return header + "\n" + "\n".join([f"- {r}" for r in reasons])

def evaluate_mtf_resonance(tech_1d, tech_60m, tech_5m, cdp_vals, bull_c="#FF6B6B", bear_c="#2ECC71", warn_c="#F1C40F"):
    ah_p, nh_p, nl_p, al_p = cdp_vals["AH"], cdp_vals["NH"], cdp_vals["NL"], cdp_vals["AL"]
    def _parse(t_obj, label, is_5m=False):
        if not t_obj or not t_obj.get("ok"):
            return {"週期": label, "趨勢與扣抵": "載入中", "布林通道位階": "-", "神奇九轉(TD9)": "-", "KD / RSI 動能": "-", "bias": 0, "td_b": 0, "td_s": 0}
        c, m20, ded, bbu, bbl, tb, ts, kv, dv, rv = t_obj["close"], t_obj["ma20"], t_obj["deduct"], t_obj["bb_upper"], t_obj["bb_lower"], t_obj["td_buy"], t_obj["td_sell"], t_obj["K"], t_obj["D"], t_obj["rsi"]
        if is_5m:
            t_str, bias = (f"🔴 站上20MA({m20}) & 守穩NL({nl_p})", 1) if (c >= m20 and c >= nl_p) else ((f"🟢 跌破20MA({m20}) & 弱勢整理", -1) if c < m20 else (f"⚖️ 20MA({m20}) 附近交戰", 0))
        else:
            t_str, bias = (f"🔴 站上20MA({m20})＋扣抵({ded})助漲", 1) if (c >= m20 and c >= ded) else ((f"🟢 跌破20MA({m20})＋扣抵({ded})反壓", -1) if (c < m20 and c < ded) else (f"🟡 站上20MA (扣抵{ded})" if c >= m20 else f"🟡 低於20MA (扣抵{ded})", 1 if c >= m20 else -1))
        bb_s = f"🔥 突破上軌({bbu})鈍化" if c >= bbu else (f"🌱 觸及下軌({bbl})超跌" if c <= bbl else (f"📈 中軌至上軌偏強" if c >= m20 else f"📉 中軌至下軌整理"))
        td_s = f"🔥 ▲低{tb} (轉折訊號)" if tb >= 8 else (f"▲ 低九第 {tb} 根" if tb > 0 else (f"⚠️ ▼高{ts} (衰竭警戒)" if ts >= 8 else (f"▼ 高九第 {ts} 根" if ts > 0 else "⚪ 無連續計數")))
        return {"週期": label, "趨勢與扣抵": t_str, "布林通道位階": bb_s, "神奇九轉(TD9)": td_s, "KD / RSI 動能": f"{'🔴金叉' if kv>=dv else '🟢死叉'} K({kv})/D({dv})｜RSI {rv}", "bias": bias, "td_b": tb, "td_s": ts}

    r1, r60, r5 = _parse(tech_1d, "📅 日 K (波段大方向)"), _parse(tech_60m, "⏱️ 60分K (隔日/波段)"), _parse(tech_5m, "⚡ 5分K (當沖扳機)", True)
    b1, b60, b5 = r1["bias"], r60["bias"], r5["bias"]
    low_tds = [n for n, r in [("日K", r1), ("60分K", r60), ("5分K", r5)] if r["td_b"] >= 7]
    if b1 > 0 and b60 > 0 and b5 > 0:
        t, clr, d = "🔥 【三週期多方強勢共振】日K ＋ 60分K ＋ 5分K 同步站上均線助漲！", bull_c, f"大中小三週期趨勢一致偏多！盤中拉回守穩 **5分K 20MA（{tech_5m.get('ma20', nl_p)}元）** 或 **NL常態支撐（{nl_p}元）** 順勢偏多勝率最高；上方壓力觀察 **NH（{nh_p}元）** 與 **AH（{ah_p}元）**。"
    elif b1 > 0 and b60 > 0 and b5 <= 0:
        t, clr, d = "🎯 【長多短回洗盤格局】日K 與 60分K 波段偏多，5分K 盤中拉回測試支撐！", warn_c, f"波段均線維持多頭保護，僅 5分K 短線拉回洗盤。重點觀察回測 **NL常態支撐（{nl_p}元）〜 AL極端破底（{al_p}元）** 或出現 **5分K ▲低8/低9** 時重新站回均線的低接契機！"
    elif b1 < 0 and b60 < 0 and b5 < 0:
        if len(low_tds) >= 2: t, clr, d = f"🌱 【空方宣洩末端 × 多週期低九共振】({'＋'.join(low_tds)} 同步進入低九轉折區！)", warn_c, f"雖均線偏空，但 **{'與'.join(low_tds)}** 已同步出現連續下跌第 7~9 根衰竭訊號，空單靠近 **NL（{nl_p}元）〜 AL（{al_p}元）** 宜分批停利，勿盲目追空！"
        else: t, clr, d = "❄️ 【三週期空方壓制共振】日K ＋ 60分K ＋ 5分K 同步受制於均線反壓！", bear_c, f"三週期同步處於空頭壓制，盤中反彈至 **NH常態壓力（{nh_p}元）〜 AH（{ah_p}元）** 或 5分K 20MA 受阻時，宜偏空避險或觀望，切勿盲目接刀。"
    else:
        t, clr, d = "⚖️ 【多空週期交錯震盪】各週期方向分歧，宜依 AH/NH/NL/AL 區間與九轉操作", warn_c, f"目前長短週期方向分歧，盤中建議靠近下方 **NL支撐（{nl_p}元）／ AL（{al_p}元）＋低九** 找支撐、往上靠近 **NH壓力（{nh_p}元）／ AH（{ah_p}元）＋高九** 留意調節。"
    return {"title": t, "color": clr, "desc": md_bold_to_html(d), "table": [{k: r[k] for k in ["週期", "趨勢與扣抵", "布林通道位階", "神奇九轉(TD9)", "KD / RSI 動能"]} for r in (r1, r60, r5)]}

def evaluate_three_pillars(tech, chip, bull_c="#FF6B6B", bear_c="#2ECC71", warn_c="#F1C40F", tech_60m=None, tech_5m=None, margin_info=None, fund_info=None, taiex_info=None, code_str=""):
    c, ma5, ma20, ma60, ded = tech["close"], tech["ma5"], tech["ma20"], tech["ma60"], tech["deduct"]
    kv, dv, macd_osc, rsi = tech["K"], tech["D"], tech["macd_osc"], tech["rsi"]
    chg_1d, chg_5d = tech.get("chg_1d_pct", 0.0), tech.get("chg_5d_pct", 0.0)
    vol_5d_lots = max(1.0, tech.get("vol_5d_lots", 5000.0))
    cdp_v = calculate_cdp(tech["high"], tech["low"], c)
    is_etf = str(code_str).startswith("00")
    bias20 = round(((c - ma20) / ma20) * 100.0, 2) if ma20 > 0 else 0.0

    mkt_1d_pct = round((taiex_info["chg"] / max(1.0, taiex_info["close"] - taiex_info["chg"])) * 100.0, 2) if (taiex_info and taiex_info.get("ok")) else 0.0
    mkt_5d_pct = taiex_info.get("chg_5d_pct", 0.0) if (taiex_info and taiex_info.get("ok")) else 0.0
    alpha_1d, alpha_5d = round(chg_1d - mkt_1d_pct, 2), round(chg_5d - mkt_5d_pct, 2)

    breakdown = []
    s_alpha = max(0, min(10, int(round(5.0 + alpha_1d * 1.2 + alpha_5d * 0.5))))
    s_ma = (4 if c >= ma5 else 0) + (6 if c >= ma20 else 0) + (2 if c >= ma60 else 0) + (3 if c >= ded else 0)
    d1_score = s_alpha + s_ma
    breakdown.append(("🛡️ 1. 相對大盤強弱(Alpha) & 日K均線", f"{d1_score} / 25 分", f"對抗大盤 Alpha：單日{alpha_1d:+.2f}% / 5日{alpha_5d:+.2f}% (+{s_alpha}分)｜均線5/20/60MA與扣抵 (+{s_ma}分)"))

    s_60m = ((5 if tech_60m["close"] >= tech_60m["ma20"] else 0) + (3 if tech_60m["K"] >= tech_60m["D"] else 0)) if (tech_60m and tech_60m.get("ok")) else 4
    s_5m = ((4 if tech_5m["close"] >= tech_5m["ma20"] else 0) + (3 if tech_5m["K"] >= tech_5m["D"] else 0)) if (tech_5m and tech_5m.get("ok")) else 3
    s_ind = (4 if kv >= dv else (1 if kv < 20 else 0)) + (3 if macd_osc >= 0 else 0) + (3 if 50 <= rsi <= 78 else (1 if rsi > 78 else 0))
    d2_score = s_60m + s_5m + s_ind
    breakdown.append(("⚡ 2. 三週期(60分/5分K)共振 & 動能", f"{d2_score} / 25 分", f"60分K位階 (+{s_60m}分)｜5分K位階 (+{s_5m}分)｜日KD/MACD/RSI (+{s_ind}分)"))

    p_c = chip["periods"]
    tot_1d, tot_3d, tot_5d, t_5d = p_c[1]["tot"], p_c[3]["tot"], p_c[5]["tot"], p_c[5]["t"]
    inst_vol_ratio = max(-99.9, min(99.9, round((tot_5d / vol_5d_lots) * 100.0, 2)))
    trust_vol_ratio = max(-99.9, min(99.9, round((t_5d / vol_5d_lots) * 100.0, 2)))
    f_hold_chg = fund_info.get("foreign_hold_chg_5d", 0.0) if fund_info else 0.0

    s_conc = max(0, min(12, int(round(6.0 + inst_vol_ratio * 0.35 + (3.0 if trust_vol_ratio >= 3.0 else (1.5 if t_5d > 0 else 0.0)) + (2.0 if f_hold_chg > 0.2 else 0.0)))))
    s_accel = (5 if tot_1d > 0 else (2 if tot_1d == 0 else 0)) + (5 if tot_3d > 0 else (2 if tot_3d == 0 else 0))
    m_chg_5d = margin_info["periods"][5]["m_chg"] if (margin_info and margin_info.get("ok")) else 0
    sm_ratio = margin_info.get("short_margin_ratio", 0.0) if margin_info else 0.0
    s_mg = 8 if (tot_5d > 0 and m_chg_5d <= 0) else ((6 if sm_ratio >= 15 else 5) if (tot_5d > 0 and m_chg_5d > 0) else (4 if (tot_5d <= 0 and m_chg_5d < 0) else 1))
    d3_score = s_conc + s_accel + s_mg
    breakdown.append(("💰 3. 外本比/投本比濃度 & 資券結構", f"{d3_score} / 30 分", f"5日法人佔成交量 {inst_vol_ratio:+.1f}% / 外資持股比增減 {f_hold_chg:+.2f}% (+{s_conc}分)｜近1/3日點火 (+{s_accel}分)｜5日融資{m_chg_5d:+,}張 (+{s_mg}分)"))

    rev_warn_str = ""
    if fund_info and fund_info.get("has_rev") and not is_etf:
        yoy, yoy_avg, accel = fund_info["yoy_latest"], fund_info["yoy_3m_avg"], fund_info["yoy_accel"]
        s_yoy = 8 if yoy >= 25 else (6 if yoy >= 10 else (4 if yoy > 0 else (2 if yoy > -10 else 0)))
        s_acc = 7 if accel >= 5.0 else (5 if accel >= 0 else (2 if accel > -10 else 0))
        if yoy >= 15 and c < ma20 and tot_5d < 0:
            s_react, s_acc = 0, max(0, s_acc - 3)
            rev_note = f"⚠️ {fund_info['rev_month']}營收YoY {yoy:+.1f}%雖高，惟股價破月線+法人賣超 (嚴防高檔利多出盡！+0分)"
            rev_warn_str = f"惟須注意 {fund_info['rev_month']} 營收年增率雖達 {yoy:+.1f}%，但股價跌破月線且法人調節，嚴防『利多出盡』。"
        elif yoy > 0 and c >= ma20:
            s_react = 5
            rev_note = f"✅ {fund_info['rev_month']}營收YoY {yoy:+.1f}% (較3月均{yoy_avg:+.1f}% {'加速' if accel>=0 else '降速'}{accel:+.1f}%)＋站穩月線 (+5分)"
            rev_warn_str = f"基本面 {fund_info['rev_month']} 營收年增 {yoy:+.1f}%（較近3月均值{'加速' if accel>=0 else '微調'} {accel:+.1f}%），具業績保護。"
        else:
            s_react = 2
            rev_note = f"{fund_info['rev_month']}營收YoY {yoy:+.1f}%｜加速度 {accel:+.1f}%"
            rev_warn_str = f"基本面 {fund_info['rev_month']} 營收年增 {yoy:+.1f}%（加速度 {accel:+.1f}%）。"
        d4_score = s_yoy + s_acc + s_react
        breakdown.append(("🚀 4. 營收YoY加速度 & 利多出盡檢驗", f"{d4_score} / 20 分", rev_note))
    else:
        d4_score = int(round(((d1_score + d2_score + d3_score) / 80.0) * 20.0))
        breakdown.append(("🏦 4. ETF 均線乖離與波段位階評分", f"{d4_score} / 20 分", f"月線乖離率 {bias20:+.2f}%｜依技術與籌碼比例動態換算"))
        if is_etf:
            rev_warn_str = f"（註：本標的為 ETF，月線乖離率為 {bias20:+.2f}%；自營商買賣超多屬造市商申贖套利，實戰請優先觀察『布林下軌＋低九轉折』與『散戶融資增減』！）"

    total = max(0, min(100, d1_score + d2_score + d3_score + d4_score))

    chip_dir = f"三大法人近5日買超 {tot_5d:+,} 張（最新1日 {tot_1d:+,} 張，佔成交量 {inst_vol_ratio:+.1f}%）" if tot_5d > 0 else f"三大法人近5日調節 {tot_5d:+,} 張（最新1日 {tot_1d:+,} 張，佔成交量 {inst_vol_ratio:+.1f}%）"
    mg_dir = f"且5日融資減少 {abs(m_chg_5d):,} 張（籌碼流向安定）" if m_chg_5d < 0 else (f"惟5日融資增加 {m_chg_5d:,} 張（留意散戶浮額）" if m_chg_5d > 0 else "")

    if total >= 70:
        verdict, v_color = "🔥 機構級多方強勢共振（跑贏大盤 Alpha ＋ 均線助漲 ＋ 籌碼優勢）", bull_c
        v_desc = (
            f"📌 **【看懂指標意義】**：目前現價（{c}元）站上 20MA 月線均價（{ma20}元）且強於大盤（單日Alpha {alpha_1d:+.2f}%），{chip_dir}{mg_dir}。{rev_warn_str}\n"
            f"🎯 **【後續動作與關鍵價位】**：大方向屬多頭順風，切忌在急拉衝高至 **NH常態壓力（{cdp_v['NH']}元）～ AH極端突破（{cdp_v['AH']}元）** 時追高；實戰上宜等待盤中 5分K 拉回測試 **NL常態支撐（{cdp_v['NL']}元）** 或 5分K 20MA 不破時順勢切入。"
        )
    elif total >= 50:
        verdict, v_color = "📈 偏多震盪輪動（波段結構偏多，短線留意分K支撐與籌碼續航）", bull_c
        v_desc = (
            f"📌 **【看懂指標意義】**：目前現價（{c}元）中長線結構維持偏多（20MA 月線均價 {ma20}元、單日Alpha {alpha_1d:+.2f}%），{chip_dir}{mg_dir}。{rev_warn_str}\n"
            f"🎯 **【後續動作與關鍵價位】**：屬偏多但短線有震盪洗盤需求，建議盯緊 60分K 與 5分K 是否同步守穩均線。下檔防守點看 **NL常態支撐（{cdp_v['NL']}元）** 與 **AL極端破底（{cdp_v['AL']}元）**，上檔過 **NH壓力（{cdp_v['NH']}元）** 需有量能配合。"
        )
    elif total >= 35:
        verdict, v_color = "⚖️ 多空交戰拉鋸（技術與籌碼訊號分歧，宜區間靈活應對）", warn_c
        v_desc = (
            f"📌 **【看懂指標意義】**：目前現價（{c}元）與籌碼出現分歧（20MA 月線均價 {ma20}元、{chip_dir}），缺乏一致性的單邊動能。{rev_warn_str}\n"
            f"🎯 **【後續動作與關鍵價位】**：不宜盲目追漲殺跌，建議採箱型區間操作——回測下方 **NL常態支撐（{cdp_v['NL']}元）～ AL（{cdp_v['AL']}元）** 且 5分K 出低九轉折時找短多機會；反彈靠近 **NH常態壓力（{cdp_v['NH']}元）～ AH（{cdp_v['AH']}元）** 見高九受阻則先行調節。"
        )
    else:
        verdict, v_color = "❄️ 空方壓制修正警戒（均線反壓 ＋ 籌碼調節，留意超跌低九轉折）", bear_c
        v_desc = (
            f"📌 **【看懂指標意義】**：目前現價（{c}元）受制於 20MA 月線均價（{ma20}元）反壓（月線負乖離 {bias20:+.2f}%、單日Alpha {alpha_1d:+.2f}%），{chip_dir}{mg_dir}，短線賣壓沉重。{rev_warn_str}\n"
            f"🎯 **【後續動作與關鍵價位】**：{'若為主題/存股型 ETF，可觀察追蹤標的止穩且日K/60分K出現『▲低9』觸及布林下軌時再分批布局；' if is_etf else '在尚未帶量站回 60分K 20MA 與日K五日線前，切勿盲目摸底接刀！'}盤中反彈壓力看 **NH（{cdp_v['NH']}元）～ AH（{cdp_v['AH']}元）**；下檔支撐觀察 **NL（{cdp_v['NL']}元）** 與 **AL（{cdp_v['AL']}元）**。"
        )

    return {"total": total, "t_score": d1_score, "m_score": d2_score, "c_score": d3_score, "f_score": d4_score, "alpha_1d": alpha_1d, "alpha_5d": alpha_5d, "inst_vol_ratio": inst_vol_ratio, "verdict": verdict, "v_color": v_color, "v_desc": v_desc, "v_desc_html": md_bold_to_html(v_desc), "breakdown": breakdown}

def fetch_macro_fx_and_sox(taiex_hist_df=None):
    res = {"fx_rate": 32.15, "fx_chg_5d": 0.0, "fx_ma20": 32.15, "sox_close": 5000.0, "sox_chg_1d_pct": 0.0, "sox_ma20": 5000.0, "sox_corr_20d": 0.65}
    try:
        df_fx, _ = fetch_kline_df_bypass_ssl("TWD=X", range_str="2mo", verify_official=False)
        if not df_fx.empty and len(df_fx) >= 6:
            fx_c, fx_p5 = round(float(df_fx["Close"].iloc[-1]), 3), float(df_fx["Close"].iloc[-6])
            res.update({"fx_rate": fx_c, "fx_chg_5d": round(fx_c - fx_p5, 3), "fx_ma20": round(float(df_fx["Close"].tail(20).mean()), 3)})
    except Exception: pass
    try:
        df_sox, _ = fetch_kline_df_bypass_ssl("^SOX", range_str="3mo", verify_official=False)
        if not df_sox.empty and len(df_sox) >= 20:
            sc, sp1 = round(float(df_sox["Close"].iloc[-1]), 1), float(df_sox["Close"].iloc[-2])
            res.update({"sox_close": sc, "sox_chg_1d_pct": round(((sc - sp1) / sp1) * 100.0, 2) if sp1 > 0 else 0.0, "sox_ma20": round(float(df_sox["Close"].tail(20).mean()), 1)})
            if taiex_hist_df is not None and len(taiex_hist_df) >= 20:
                s_ret = df_sox["Close"].pct_change().rename("sox")
                t_ret = taiex_hist_df["Close"].pct_change().rename("twii")
                aligned_same = pd.concat([s_ret, t_ret], axis=1).dropna().tail(20)
                aligned_lag1 = pd.concat([s_ret.shift(1), t_ret], axis=1).dropna().tail(20)
                c_same = aligned_same["sox"].corr(aligned_same["twii"]) if len(aligned_same) >= 12 else 0.5
                c_lag1 = aligned_lag1["sox"].corr(aligned_lag1["twii"]) if len(aligned_lag1) >= 12 else 0.5
                best_corr = max(c_same if pd.notna(c_same) else 0.5, c_lag1 if pd.notna(c_lag1) else 0.5)
                res["sox_corr_20d"] = round(float(best_corr), 2)
    except Exception: pass
    return res

def evaluate_taiex_market_score(taiex, cfg, breadth_fg, macro_info=None, bull_c="#FF6B6B", bear_c="#2ECC71", warn_c="#F1C40F"):
    c, ma5, ma20, ma60, ded = taiex["close"], taiex["ma5"], taiex["ma20"], taiex["ma60"], taiex["deduct"]
    chg, bias20, kv, dv = taiex["chg"], taiex["bias20"], taiex["K"], taiex["D"]
    prev_c = round(c - chg, 1)
    chg_pct = round((chg / max(1.0, prev_c)) * 100.0, 2)
    sp_f, sp_t, sp_d = float(cfg.get("mkt_spot_foreign", 0.0)), float(cfg.get("mkt_spot_trust", 0.0)), float(cfg.get("mkt_spot_dealer", 0.0))
    sp_tot = round(sp_f + sp_t + sp_d, 2)
    foi, foi_chg, m_chg, m_chg3 = int(cfg.get("mkt_foreign_oi", -30000)), int(cfg.get("mkt_foreign_oi_chg", 0)), float(cfg.get("mkt_margin_chg", 0.0)), float(cfg.get("mkt_margin_chg_3d", 0.0))
    up_ratio, fg_score = float(breadth_fg.get("up_ratio", 50.0)), int(breadth_fg.get("fg_score", 50))
    macro = macro_info or {"fx_rate": 32.15, "fx_chg_5d": 0.0, "fx_ma20": 32.15, "sox_close": 5000.0, "sox_chg_1d_pct": 0.0, "sox_ma20": 5000.0, "sox_corr_20d": 0.65}
    mkt_cdp = calculate_cdp(taiex["high"], taiex["low"], c)

    breakdown = []
    fx_c, fx_chg5, fx_m20 = macro["fx_rate"], macro["fx_chg_5d"], macro["fx_ma20"]
    s_fx = (5 if fx_chg5 <= 0 else (2 if fx_chg5 < 0.15 else 0)) + (3 if fx_c <= fx_m20 else 0)
    corr_r, sox_c, sox_m20, sox_chg = macro["sox_corr_20d"], macro["sox_close"], macro["sox_ma20"], macro["sox_chg_1d_pct"]
    raw_sox_score = (4 if sox_c >= sox_m20 else 0) + max(0, min(3, int(round(sox_chg + 1.5))))
    if corr_r >= 0.55:
        s_sox, sox_note = raw_sox_score, f"費半 {sox_chg:+.2f}% (20日高相關 r={corr_r} ➔ 全權重 +{raw_sox_score}分)"
    elif corr_r >= 0.25:
        s_sox = int(round(raw_sox_score * 0.5 + (3.5 if c >= ma5 else 1.0) * 0.5))
        sox_note = f"費半 {sox_chg:+.2f}% (中度相關 r={corr_r} ➔ 折半權重 +{s_sox}分)"
    else:
        s_sox = 7 if c >= ma20 else (4 if c >= ma5 else 1)
        sox_note = f"⚠️ 近期與費半脫鉤 (r={corr_r})，自動改依台股自身內資位階計分 (+{s_sox}分)"
    macro_score = s_fx + s_sox
    breakdown.append(("🌎 1. 新台幣匯率活水 & 費半相關性 (滿分15)", f"{macro_score} / 15 分", f"台幣匯率 {fx_c} ({'升值熱錢流入' if fx_chg5<=0 else '貶值外流'} 5日{fx_chg5:+.2f}元 ➔ +{s_fx}分)｜{sox_note}"))

    s_ma = (5 if c >= ma5 else 0) + (8 if c >= ma20 else 0) + (4 if c >= ma60 else 0) + (3 if c >= ded else 0)
    s_bias = max(0, min(5, int(round((bias20 + 6.0) / 1.8))))
    t_score = s_ma + s_bias
    breakdown.append(("📈 2. 大盤均線與乖離位階 (滿分25)", f"{t_score} / 25 分", f"5/20/60MA與扣抵 (+{s_ma}分)｜月線乖離率 {bias20:+.2f}% (+{s_bias}分)"))

    s_chg = max(0, min(9, int(round((chg_pct + 2.5) * 2.0))))
    s_kd = 3 if kv >= dv else (1 if kv < 20 else 0)
    s_bb = 3 if c >= taiex["bb_lower"] else (2 if taiex.get("has_long_shadow") else 0)
    m_score = s_chg + s_kd + s_bb
    breakdown.append(("⚡ 3. 單日漲跌幅與K棒動能 (滿分15)", f"{m_score} / 15 分", f"單日 {chg:+.1f}點 ({chg_pct:+.2f}% ➔ +{s_chg}分)｜KD (+{s_kd}分)｜布林與下影線 (+{s_bb}分)"))

    s_sp_tot = max(0, min(12, int(round((sp_tot + 600.0) / 80.0))))
    s_sp_f = max(0, min(4, int(round((sp_f + 300.0) / 120.0))))
    s_sp_t = 2 if sp_t > 0 else 0
    s_foi = max(0, min(4, int(round((foi + 45000) / 9000.0)))) + (3 if foi_chg >= 1500 else (2 if foi_chg > 0 else (1 if foi_chg > -1500 else 0)))
    s_mg = (5 if -30 <= m_chg <= 50 else 3) if chg >= 0 else (4 if m_chg <= -50 else (3 if m_chg < 0 else 1))
    c_score = s_sp_tot + s_sp_f + s_sp_t + s_foi + s_mg
    breakdown.append(("🏛️ 4. 法人期現貨百億級距 & 資券 (滿分30)", f"{c_score} / 30 分", f"現貨合計 {sp_tot:+.1f}億 (+{s_sp_tot+s_sp_f+s_sp_t}分)｜外資期貨 {foi:,}口/單日{foi_chg:+,} (+{s_foi}分)｜融資 {m_chg:+.1f}億 (+{s_mg}分)"))

    s_br = max(0, min(10, int(round(up_ratio / 10.0))))
    s_fg = max(0, min(5, int(round(fg_score / 20.0))))
    b_score = s_br + s_fg
    breakdown.append(("🌡️ 5. 上市櫃騰落廣度 & 恐慌情緒 (滿分15)", f"{b_score} / 15 分", f"上漲家數佔比 {up_ratio}% (+{s_br}分)｜CNN情緒 {fg_score} (+{s_fg}分)"))

    total = max(0, min(100, macro_score + t_score + m_score + c_score + b_score))

    fx_meaning = f"新台幣匯率 {fx_c}（近5日{fx_chg5:+.2f}元，{'外資熱錢留台支撐' if fx_chg5<=0 else '短線資金有匯出壓力'}）"
    chip_meaning = f"三大法人現貨合計 {sp_tot:+.1f} 億（外資期貨未平倉 {foi:,} 口，單日 {foi_chg:+,} 口），上市櫃上漲家數佔比 {up_ratio}%"
    if total >= 70:
        light, clr = "🟢 綠燈｜多頭強勢順風（匯率熱錢流入＋均線助漲＋法人推升）", bull_c
        summary_action = f"📌 **【大盤總結論與實戰意義】**：最新指數 **{c:,} 點**（昨日收盤 {prev_c:,} 點，今日 {chg:+} 點），穩健站上 **20MA 月線均價（{ma20:,}點）** 且 {fx_meaning}，{chip_meaning}，市場賺錢效應極佳！\n🎯 **【後續動作提醒】**：順風盤可積極從下方主流族群挑選跑贏大盤（正Alpha）的領頭羊操作；明日大盤支撐看 **NL（{mkt_cdp['NL']:,}點）**，壓力看 **NH（{mkt_cdp['NH']:,}點）** 與 **AH（{mkt_cdp['AH']:,}點）**。"
        ct, cb = "🔥 大盤處於多方強勢順風區！想掌握今日領漲主流股的切入位階嗎？", "💬 點此私訊您的專屬營業員：索取【今日主流強勢股深度籌碼清單】"
    elif total >= 50:
        light, clr = "🟢 偏多綠黃燈｜多方控盤輪動（守穩支撐，主流族群輪動表現）", bull_c
        summary_action = f"📌 **【大盤總結論與實戰意義】**：最新指數 **{c:,} 點**（昨日收盤 {prev_c:,} 點，今日 {chg:+} 點），結構維持偏多（**20MA 月線均價 {ma20:,}點**，乖離 {bias20:+.2f}%），{fx_meaning}，{chip_meaning}。代表指數空間雖溫和，但內資與個股輪動非常活絡！\n🎯 **【後續動作提醒】**：採取「重個股、輕指數」策略，鎖定下方帶有 🔥 標記的動態入榜強勢股，趁盤中回測支撐布局；大盤下檔防守看 **NL（{mkt_cdp['NL']:,}點）**，上檔觀察 **NH（{mkt_cdp['NH']:,}點）**。"
        ct, cb = "📈 大盤維持偏多輪動格局！想檢視手中持股是否在主流資金軌道上嗎？", "💬 點此私訊您的專屬營業員：預約【持股強弱診斷與主流換股討論】"
    elif total >= 35:
        light, clr = "🟡 黃燈｜多空交戰拉鋸（均線與籌碼分歧，宜選股不選市）", warn_c
        summary_action = f"📌 **【大盤總結論與實戰意義】**：最新指數 **{c:,} 點**（昨日收盤 {prev_c:,} 點，今日 {chg:+} 點），與籌碼訊號分歧（**20MA 月線均價 {ma20:,}點**，{fx_meaning}，{chip_meaning}），多空在關鍵均線附近激烈交戰，追高容易被洗！\n🎯 **【後續動作提醒】**：資金控管宜維持 5 成以下，淘汰破線弱勢股，僅針對有法人買超且守穩月線的抗跌股做短線區間應對；大盤區間重點盯緊下檔 **NL（{mkt_cdp['NL']:,}點）～ AL（{mkt_cdp['AL']:,}點）** 與上檔 **NH（{mkt_cdp['NH']:,}點）**。"
        ct, cb = "🛡️ 大盤處於多空交戰拉鋸區！想了解如何利用短線當沖或期貨避險靈活應對嗎？", "💬 點此私訊您的專屬營業員：預約【1對1 持股健檢 & 短線操作策略討論】"
    else:
        light, clr = "🚨 紅燈｜空方修正／超跌警戒（破線提款＋融資清洗，緊盯止跌訊號）", bear_c
        summary_action = f"📌 **【大盤總結論與實戰意義】**：最新指數 **{c:,} 點**（昨日收盤 {prev_c:,} 點，今日 {chg:+} 點），目前位於 **20MA 月線均價（{ma20:,}點）** 之下（月線負乖離 {bias20:+.2f}%），{fx_meaning}，{chip_meaning}，融資近3日累計 {m_chg3:+.1f} 億，盤勢處於空方宣洩與浮額清洗階段！\n🎯 **【後續動作提醒】**：在尚未同時出現「①重新站回5MA（{ma5:,}點）或布林下軌、②外資期貨空單回補、③融資大幅減肥」三大止跌訊號前，多看少做或利用個股期避險；明日下檔支撐觀察 **NL（{mkt_cdp['NL']:,}點）** 與 **AL（{mkt_cdp['AL']:,}點）**，反彈壓力看 **NH（{mkt_cdp['NH']:,}點）**。"
        ct, cb = "🚨 盤勢進入急跌宣洩與融資清洗階段！想掌握大盤何時出現破底翻止跌訊號嗎？", "💬 點此私訊您的專屬營業員：預約【持股壓力測試 & 超跌反彈布局討論】"

    return {"total": total, "light": light, "color": clr, "summary_action": summary_action, "summary_action_html": md_bold_to_html(summary_action), "cta_title": ct, "cta_btn": cb, "breakdown": breakdown, "macro": macro}

@st.cache_data(ttl=86400)
def fetch_all_stock_industry_map():
    ind_map = dict(PRECISE_SUBSECTOR_OVERRIDES)
    try:
        r = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params={"dataset": "TaiwanStockInfo"}, timeout=6, verify=False)
        if r.status_code == 200 and r.json().get("data"):
            for it in r.json()["data"]:
                c, cat = str(it.get("stock_id", "")).strip(), str(it.get("industry_category", "")).strip()
                if re.match(r"^\d{4}$", c) and cat and cat not in ["Index", "ETF", "大盤", "電子工業", "其他"]:
                    if cat in ["資訊服務業", "數位雲端"]: ind_map[c] = "資訊服務與資安軟體"
                    else: ind_map.setdefault(c, cat)
    except Exception: pass

    for url in [
        "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
        "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"
    ]:
        try:
            r_tw = GLOBAL_HTTP_SESSION.get(url, timeout=6, verify=False)
            if r_tw.status_code == 200:
                for it in r_tw.json():
                    c = str(it.get("公司代號", it.get("SecuritiesCompanyCode", ""))).strip()
                    raw_ind = str(it.get("產業別", it.get("Industry", ""))).strip().zfill(2)
                    if re.match(r"^\d{4}$", c):
                        mapped_cat = TWSE_IND_CODE_MAP.get(raw_ind, raw_ind if not raw_ind.isdigit() else "")
                        if mapped_cat in ["資訊服務業", "數位雲端", "電子商務"]: ind_map[c] = "資訊服務與資安軟體"
                        elif mapped_cat and mapped_cat not in ["電子工業"]: ind_map[c] = mapped_cat
        except Exception: pass
    return ind_map

@st.cache_data(ttl=600)
def fetch_full_market_snapshot_and_breadth(fallback_fg=34):
    up_cnt = down_cnt = flat_cnt = 0
    market_snap = {}
    for url, mkt, c_k, n_k, cl_k, chg_k, val_k in [
        ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", "TWSE", "Code", "Name", "ClosingPrice", "Change", "TradeValue"),
        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes", "TPEX", "SecuritiesCompanyCode", "CompanyName", "Close", "Change", "TransactionAmount")
    ]:
        try:
            r = GLOBAL_HTTP_SESSION.get(url, timeout=8, verify=False)
            if r.status_code == 200:
                for it in r.json():
                    code = str(it.get(c_k, "")).strip().upper()
                    if not re.match(r"^(00\d{2,4}[A-Z]?|\d{4})$", code): continue
                    name = str(it.get(n_k, "")).strip()
                    try:
                        close_v = safe_float(it.get(cl_k, "0"))
                        chg_v = safe_float(it.get(chg_k, "0"))
                        val_v = safe_float(it.get(val_k, "0"))
                        prev_v = close_v - chg_v
                        pct_v = round((chg_v / prev_v) * 100.0, 2) if prev_v > 0 else 0.0
                        if re.match(r"^\d{4}$", code):
                            if chg_v > 0: up_cnt += 1
                            elif chg_v < 0: down_cnt += 1
                            else: flat_cnt += 1
                        if close_v > 0:
                            market_snap[code] = {"code": code, "name": name, "mkt": mkt, "close": close_v, "chg_1d_pct": pct_v, "trade_val_yi": round(val_v / 1e8, 2)}
                    except Exception: flat_cnt += 1
        except Exception: pass

    breadth_ok = (up_cnt + down_cnt) > 100
    fg_score, fg_source = int(fallback_fg), "後台校準值"
    try:
        r_cnn = GLOBAL_HTTP_SESSION.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata", headers={"Accept": "application/json", "Referer": "https://edition.cnn.com/"}, timeout=4, verify=False)
        if r_cnn.status_code == 200 and r_cnn.json().get("fear_and_greed", {}).get("score") is not None:
            fg_score, fg_source = int(round(float(r_cnn.json()["fear_and_greed"]["score"]))), "CNN自動連線"
    except Exception: pass

    return {
        "breadth_ok": breadth_ok, "up_cnt": up_cnt, "down_cnt": down_cnt, "flat_cnt": flat_cnt,
        "adl_diff": up_cnt - down_cnt, "up_ratio": round((up_cnt / max(1, up_cnt + down_cnt)) * 100, 1) if breadth_ok else 50.0,
        "fg_score": fg_score, "fg_source": fg_source, "market_snap": market_snap
    }

def fetch_market_breadth_and_fear_greed(fallback_fg=34):
    return fetch_full_market_snapshot_and_breadth(fallback_fg)

@st.cache_data(ttl=180)
def fetch_taiex_market_data():
    hist, err_msg = fetch_kline_df_bypass_ssl("^TWII", "TWSE", range_str="6mo", verify_official=True)
    if hist.empty or len(hist) < 20: return {"ok": False, "err_msg": err_msg}
    hist = compute_td_sequential_and_bbands(hist)
    lt, pv = hist.iloc[-1], hist.iloc[-2]
    cp, op, hp, lp = [round(float(lt[k]), 1) for k in ("Close", "Open", "High", "Low")]
    pc, po, pl = [round(float(pv[k]), 1) for k in ("Close", "Open", "Low")]
    p5 = float(hist["Close"].iloc[-6]) if len(hist) >= 6 else pc
    if abs(hp - lp) < 1.0:
        hr = max(80.0, round((float(pv["High"]) - float(pv["Low"])) * 0.5, 1))
        hp, lp = round(cp + hr, 1), round(cp - hr, 1)
    ma5, ma20 = round(float(hist["MA5"].iloc[-1]), 1), round(float(hist["MA20"].iloc[-1]), 1)
    ma60 = round(float(hist["MA60"].iloc[-1]), 1) if pd.notna(hist["MA60"].iloc[-1]) else ma20
    bbu, bbd = round(float(hist["BB_Upper"].iloc[-1]), 1), round(float(hist["BB_Lower"].iloc[-1]), 1)
    p_bbd = round(float(hist["BB_Lower"].iloc[-2]), 1) if pd.notna(hist["BB_Lower"].iloc[-2]) else pc
    kv, dv, pkv, pdv, _, _, rsi14 = calc_kd_rsi_macd(hist)
    l_sh = min(op, cp) - lp
    has_l_sh = (l_sh / max(1.0, hp - lp)) >= 0.42 and (l_sh >= 80)
    is_eng = (cp > op) and (pc < po) and (cp >= po) and (op <= pc)
    no_nl = lp >= pl
    rec_bb = (lp <= bbd or pl <= p_bbd) and (cp > bbd)
    bb_st = "🚨 跌破布林下軌 (極端超跌)" if cp < bbd else ("✅ 破底站回布林下軌 (止跌訊號)" if rec_bb else ("🔥 突破布林上軌 (強勢鈍化)" if cp >= bbu else ("📈 布林中軌至上軌間" if cp >= ma20 else "⚠️ 布林中軌至下軌間")))
    k_pats = ([f"✅長下影線({int(l_sh)}點)"] if has_l_sh else []) + (["✅紅K吞噬"] if is_eng else []) + (["✅未破前低"] if no_nl else ["⚠️跌破前低"])
    hist_60 = hist.tail(60).copy()
    hist_60["DateStr"], hist_60["ShortDate"] = hist_60.index.strftime("%Y-%m-%d"), hist_60.index.strftime("%m-%d")
    macro_info = fetch_macro_fx_and_sox(hist)
    return {
        "ok": True, "date": hist.index[-1].strftime("%Y-%m-%d"), "close": cp, "prev_close": pc, "open": op, "chg": round(cp - pc, 1),
        "chg_5d_pct": round(((cp - p5) / p5) * 100.0, 2) if p5 > 0 else 0.0,
        "high": hp, "low": lp, "ma5": ma5, "ma20": ma20, "ma60": ma60, "bias20": round(((cp - ma20) / ma20) * 100.0, 2) if ma20 > 0 else 0.0,
        "bb_upper": bbu, "bb_lower": bbd, "bb_status": bb_st, "reclaimed_bb_low": rec_bb,
        "k_pattern_str": " ｜ ".join(k_pats), "has_long_shadow": has_l_sh, "is_bull_engulf": is_eng, "no_new_low": no_nl,
        "td_buy": int(hist["TD_Buy"].iloc[-1]), "td_sell": int(hist["TD_Sell"].iloc[-1]), "K": kv, "D": dv, "prev_K": pkv, "prev_D": pdv, "rsi": rsi14,
        "deduct": round(float(hist["Close"].iloc[-20]), 1), "deduct_date": hist.index[-20].strftime("%Y-%m-%d"),
        "macro": macro_info,
        "kline_60": hist_60[["DateStr", "ShortDate", "Open", "High", "Low", "Close", "MA5", "MA20", "MA60", "BB_Upper", "BB_Lower", "TD_Buy", "TD_Sell", "TD_Buy_Disp", "TD_Sell_Disp"]].to_dict("records")
    }

@st.cache_data(ttl=600)
def scan_sector_performance(sector_map_json_str, margins_dict):
    raw_sec_map = json.loads(sector_map_json_str)
    sec_map = {k: [[x[0], str(x[1]).replace("🔥", ""), x[2]] for x in v] for k, v in raw_sec_map.items()}
    ind_map = fetch_all_stock_industry_map()
    snap_data = fetch_full_market_snapshot_and_breadth().get("market_snap", {})
    existing_codes = {item[0] for s_list in sec_map.values() for item in s_list}

    hot_candidates = sorted(
        [v for k, v in snap_data.items() if re.match(r"^\d{4}$", k) and k not in existing_codes and v["trade_val_yi"] >= 3.0 and v["chg_1d_pct"] >= 1.5],
        key=lambda x: (x["chg_1d_pct"] * 0.6 + min(20, x["trade_val_yi"]) * 0.4), reverse=True
    )[:36]

    extra_ind_buckets = {}
    for hc in hot_candidates:
        c, n, mkt = hc["code"], hc["name"], hc["mkt"]
        ind_cat = ind_map.get(c, "")
        if not ind_cat or ind_cat in ["電子工業", "其他電子業", "其他"]:
            if any(k in n for k in ["資", "軟", "網", "雲", "數", "訊", "精誠", "華經"]): ind_cat = "資訊服務與資安軟體"
            elif any(k in n for k in ["光", "電", "晶", "環", "顯示"]): ind_cat = "光電與電子零組件"
            else: ind_cat = "利基型科技與電子週邊"

        target_sec = INDUSTRY_TO_SECTOR_BRIDGE.get(ind_cat)
        if target_sec and target_sec in sec_map and len(sec_map[target_sec]) < 10:
            sec_map[target_sec].append([c, f"{n}🔥", mkt])
            existing_codes.add(c)
        else:
            dyn_sec_name = f"🌟 [動態主流] {ind_cat}"
            extra_ind_buckets.setdefault(dyn_sec_name, []).append([c, f"{n}🔥", mkt])

    for dyn_name, dyn_list in extra_ind_buckets.items():
        if len(dyn_list) >= 2: sec_map[dyn_name] = dyn_list[:8]

    tasks = [(sec_name, item[0], item[1], item[2]) for sec_name, s_list in sec_map.items() for item in s_list]
    sector_records = {k: [] for k in sec_map.keys()}

    def _worker(task_item):
        sec_name, code, name, mkt = task_item
        sub, _ = fetch_kline_df_bypass_ssl(code, mkt, range_str="2mo", verify_official=False)
        snap_it = snap_data.get(code)
        if sub.empty or len(sub) < 6:
            if not snap_it: return None
            close_p, chg_1d = snap_it["close"], snap_it["chg_1d_pct"]
            chg_5d, ma20 = chg_1d, close_p
        else:
            close_p = snap_it["close"] if snap_it else round(float(sub["Close"].iloc[-1]), 2)
            prev_1d = float(sub["Close"].iloc[-2])
            prev_5d = float(sub["Close"].iloc[-6])
            chg_1d = snap_it["chg_1d_pct"] if snap_it else (round(((close_p - prev_1d) / prev_1d) * 100, 2) if prev_1d > 0 else 0.0)
            chg_5d = round(((close_p - prev_5d) / prev_5d) * 100, 2) if prev_5d > 0 else 0.0
            ma20 = round(float(sub["Close"].tail(20).mean()), 2) if len(sub) >= 20 else close_p
        m_rate = float(margins_dict.get(code, 13.5)) / 100.0
        return sec_name, {
            "代號": code, "名稱": name, "最新收盤(元)": close_p,
            "近1日漲跌(%)": chg_1d,
            "近5日漲跌(%)": chg_5d,
            "月線(20MA)": ma20, "趨勢位階": "✅站上月線" if close_p >= ma20 else "⚠️月線之下",
            "1口個股期保證金": f"{int(close_p * 2000 * m_rate):,} 元" if code in margins_dict else "無期貨",
            "_mkt": mkt
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
    return sorted(summary_list, key=lambda x: (x["近1日平均漲跌(%)"] * 0.4 + x["近5日平均漲跌(%)"] * 0.6), reverse=True)

@st.cache_data(ttl=1800)
def fetch_stock_news(code, name):
    raw_items, clean_n = [], name.replace("🔥", "").strip()
    bad_w = {"南亞": ["南亞科", "南亞電"], "台塑": ["台塑化"], "長榮": ["長榮航", "長榮鋼"]}.get(clean_n, [])
    junk_patterns = ["明細總覽", "發放日總覽", "走勢圖", "技術分析", "股價查詢", "即時報價", "討論區", "| 股市", "｜股市", "基本資料"]
    for q_s in [f'"{code}" "{clean_n}" when:7d', f'"{clean_n}" 股 when:7d']:
        try:
            resp = GLOBAL_HTTP_SESSION.get(f"https://news.google.com/rss/search?q={urllib.parse.quote(q_s)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant", timeout=5, verify=False)
            if resp.status_code == 200:
                for it in ET.fromstring(resp.content).findall(".//item")[:25]:
                    t = it.find("title").text if it.find("title") is not None else ""
                    if not t or clean_n not in t: continue
                    ct_check = t.split(" - ")[0].strip()
                    if len(ct_check) < 11 or any(jp in t for jp in junk_patterns): continue
                    tmp = t
                    for bw in bad_w: tmp = tmp.replace(bw, "")
                    if clean_n not in tmp: continue
                    try:
                        dt = parsedate_to_datetime(it.find("pubDate").text)
                        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
                    except Exception: dt = datetime.now(timezone.utc)
                    raw_items.append({"title": t, "link": it.find("link").text if it.find("link") is not None else "#", "dt": dt})
            if len(raw_items) >= 3: break
        except Exception: continue
    raw_items.sort(key=lambda x: x["dt"], reverse=True)
    seen, final_n, now_u = set(), [], datetime.now(timezone.utc)
    for it in raw_items:
        ct = it["title"].split(" - ")[0].strip()
        if ct in seen: continue
        seen.add(ct)
        dh = max(0, int((now_u - it["dt"]).total_seconds() // 3600))
        ago = (f"{dh} 小時前" if dh > 0 else "剛剛") if dh < 24 else f"{dh // 24} 天前 ({it['dt'].strftime('%m/%d')})"
        tag = "📊 財報營收" if any(w in ct for w in ["營收", "EPS", "財報", "獲利", "毛利", "配息"]) else ("🏛️ 法人籌碼" if any(w in ct for w in ["外資", "投信", "法人", "買超", "目標價"]) else "📰 盤勢焦點")
        final_n.append({"title": it["title"], "link": it["link"], "ago": ago, "tag": tag})
        if len(final_n) >= 4: break
    return {"news": final_n}

def extract_stocks_from_image_via_gemini(image_bytes, mime_type, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": "請從截圖辨識所有台股代號或股票名稱，用逗號分隔回傳"}, {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("utf-8")}}]}]}
    resp = GLOBAL_HTTP_SESSION.post(url, json=payload, timeout=15, verify=False)
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip() if resp.status_code == 200 else ""

def fetch_taifex_foreign_tx_oi_csv(fm_token=""):
    sess = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.taifex.com.tw/cht/3/futContractsDate"}
    now_dt = pd.Timestamp.now()
    try:
        sess.get("https://www.taifex.com.tw/cht/3/futContractsDate", headers=headers, timeout=4, verify=False)
        r = sess.post("https://www.taifex.com.tw/cht/3/futContractsDateDown", data={"queryType": "1", "doQuery": "1", "queryStartDate": (now_dt - pd.Timedelta(days=14)).strftime("%Y/%m/%d"), "queryEndDate": now_dt.strftime("%Y/%m/%d"), "commodityId": "TX"}, headers=headers, timeout=7, verify=False)
        if r.status_code == 200 and len(r.content) > 100:
            for enc in ["cp950", "utf-8-sig", "utf-8"]:
                txt = r.content.decode(enc, errors="ignore")
                if "外資" in txt:
                    d_map = {}
                    for row in csv.reader(io.StringIO(txt)):
                        if len(row) >= 12 and "外資" in " ".join(str(c) for c in row[:4]):
                            for cand in ([row[13]] if len(row) > 13 else []) + [row[-2]]:
                                vc = str(cand).replace(",", "").strip()
                                if re.match(r"^-?\d+$", vc): d_map[str(row[0]).strip().replace("-", "/")] = int(vc); break
                    if len(d_map) >= 2:
                        s_dts = sorted(d_map.keys())
                        return {"mkt_foreign_oi": d_map[s_dts[-1]], "mkt_foreign_oi_chg": d_map[s_dts[-1]] - d_map[s_dts[-2]]}
    except Exception: pass
    try:
        params = {"dataset": "TaiwanFuturesInstitutionalInvestors", "data_id": "TX", "start_date": (now_dt - pd.Timedelta(days=15)).strftime("%Y-%m-%d")}
        if fm_token: params["token"] = fm_token
        r_fm = GLOBAL_HTTP_SESSION.get("https://api.finmindtrade.com/api/v4/data", params=params, timeout=7, verify=False)
        if r_fm.status_code == 200 and r_fm.json().get("data"):
            df_f = pd.DataFrame(r_fm.json()["data"])
            sub = df_f[df_f["institutional_investors"].astype(str).str.contains("外資|Foreign", case=False, na=False)].sort_values("date")
            if len(sub) >= 2:
                oi1 = int(float(sub.iloc[-1]["long_open_interest_balance_volume"]) - float(sub.iloc[-1]["short_open_interest_balance_volume"]))
                oi0 = int(float(sub.iloc[-2]["long_open_interest_balance_volume"]) - float(sub.iloc[-2]["short_open_interest_balance_volume"]))
                return {"mkt_foreign_oi": oi1, "mkt_foreign_oi_chg": oi1 - oi0}
    except Exception: pass
    return {}

def sync_market_institutional_online(fm_token=""):
    res, now_dt = {}, pd.Timestamp.now()
    for d_b in range(0, 7):
        qd = (now_dt - pd.Timedelta(days=d_b)).strftime("%Y%m%d")
        try:
            r_sp = GLOBAL_HTTP_SESSION.get(f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json&dayDate={qd}", timeout=5, verify=False)
            if r_sp.status_code == 200 and r_sp.json().get("stat") == "OK" and r_sp.json().get("data"):
                f_a = t_a = d_a = 0.0
                for row in r_sp.json()["data"]:
                    t, v = str(row[0]).strip(), round(float(str(row[3]).replace(",", "")) / 1e8, 2)
                    if "外資及陸資" in t and "不含" in t: f_a = v
                    elif "投信" in t: t_a = v
                    elif "自營商" in t: d_a += v
                res.update({"mkt_spot_foreign": f_a, "mkt_spot_trust": t_a, "mkt_spot_dealer": round(d_a, 2), "mkt_chip_date": qd}); break
        except Exception: continue

    m_hist = []
    for d_b in range(0, 12):
        qd = (now_dt - pd.Timedelta(days=d_b)).strftime("%Y%m%d")
        try:
            r_mg = GLOBAL_HTTP_SESSION.get(f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?response=json&date={qd}&selectType=MS", timeout=5, verify=False)
            if r_mg.status_code == 200 and r_mg.json().get("stat") == "OK":
                tbs = r_mg.json().get("tables", [])
                if tbs and tbs[0].get("data"):
                    mt = mp = st_v = sp_v = None
                    for row in tbs[0]["data"]:
                        nm = str(row[0]).strip()
                        if "融資金額" in nm: mp, mt = round(float(str(row[4]).replace(",", "")) / 1e5, 2), round(float(str(row[5]).replace(",", "")) / 1e5, 2)
                        elif "融券" in nm and "交易單位" in nm: sp_v, st_v = int(float(str(row[4]).replace(",", ""))), int(float(str(row[5]).replace(",", "")))
                    if mt is not None:
                        m_hist.append({"mt": mt, "mp": mp, "st": st_v, "sp": sp_v})
                        if len(m_hist) >= 3: break
        except Exception: continue

    if m_hist:
        lt = m_hist[0]
        res["mkt_margin_bal"], res["mkt_margin_chg"] = lt["mt"], round(lt["mt"] - lt["mp"], 2)
        res["mkt_margin_chg_3d"] = round(lt["mt"] - m_hist[2]["mp"], 2) if len(m_hist) >= 3 else res["mkt_margin_chg"]
        if lt["st"] is not None: res["mkt_short_bal"], res["mkt_short_chg"] = lt["st"], lt["st"] - lt["sp"]

    res.update(fetch_taifex_foreign_tx_oi_csv(fm_token))
    return res

@st.cache_data(ttl=1800)
def auto_sync_market_chips_cached(fm_token=""):
    cfg = load_config()
    mkt_res = sync_market_institutional_online(fm_token)
    if mkt_res: cfg.update(mkt_res); save_config(cfg)
    return cfg
