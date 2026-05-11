import html
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import feedparser
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="나스닥 시황 모니터링 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# Session defaults
# =========================================================
DEFAULTS = {
    "theme_mode": "다크 모드",
    "auto_refresh": False,
    "refresh_seconds": 60,
    "chart_period": "1d",
    "chart_interval": "5m",
    "focus_symbols": [],
    "economic_memo": "CPI 발표 확인\nPPI 발표 확인\nFOMC 일정 확인\nPCE 물가 확인\n고용보고서 확인\n연준 인사 발언 확인",
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def get_kst_now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Seoul"))


# =========================================================
# Settings are rendered directly in the header area.
# No hidden sidebar / expander is used.
# =========================================================
custom_symbol = st.session_state.get("custom_symbol", "")

# =========================================================
# Theme variables
# =========================================================
if st.session_state.theme_mode == "라이트 모드":
    APP_BG = "linear-gradient(135deg, #f8fafc 0%, #e5edf7 45%, #f8fafc 100%)"
    PANEL_BG = "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(241,245,249,0.96))"
    TEXT_MAIN = "#0f172a"
    TEXT_SUB = "#475569"
    BORDER = "#cbd5e1"
    INPUT_BG = "#ffffff"
    PLOT_BG = "rgba(248,250,252,0.95)"
    TICKER_BG = "linear-gradient(145deg, rgba(255,255,255,0.96), rgba(241,245,249,0.96))"
    TEMPLATE = "plotly_white"
else:
    APP_BG = "radial-gradient(circle at top left, #102033 0%, #080d16 45%, #05070d 100%)"
    PANEL_BG = "linear-gradient(145deg, rgba(17,24,39,0.96), rgba(9,15,27,0.96))"
    TEXT_MAIN = "#f8fafc"
    TEXT_SUB = "#94a3b8"
    BORDER = "#26364c"
    INPUT_BG = "#0f172a"
    PLOT_BG = "rgba(8,13,22,0.95)"
    TICKER_BG = "linear-gradient(145deg, rgba(17,24,39,0.96), rgba(8,13,22,0.96))"
    TEMPLATE = "plotly_dark"

# =========================================================
# CSS
# =========================================================
st.markdown(
    f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{ background: {APP_BG} !important; }}
.stApp {{ background: {APP_BG}; color: {TEXT_MAIN}; }}
header[data-testid="stHeader"] {{ background: transparent !important; height: 0.5rem !important; }}
.block-container {{ padding-top: 0.4rem !important; padding-left: 1.45rem; padding-right: 1.45rem; max-width: 98.8vw !important; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; visibility: hidden !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}

[data-testid="stMetric"] {{ background: {PANEL_BG}; border: 1px solid {BORDER}; padding: 14px 16px; border-radius: 16px; min-height: 96px; box-shadow: 0 10px 24px rgba(0,0,0,0.18); }}
[data-testid="stMetricLabel"] {{ color: {TEXT_SUB}; font-size: 0.78rem; }}
[data-testid="stMetricValue"] {{ color: {TEXT_MAIN}; font-size: 1.42rem; font-weight: 800; }}
[data-testid="stMetricDelta"] {{ font-size: 0.78rem; }}

.panel {{ background: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 17px; padding: 15px; margin-bottom: 13px; color: {TEXT_MAIN}; box-shadow: 0 10px 24px rgba(0,0,0,0.18); }}
.panel-title {{ font-size: 1.05rem; font-weight: 850; margin: 8px 0 10px 0; color: {TEXT_MAIN}; }}

.stSelectbox > div > div, .stTextInput > div > div > input, .stTextArea textarea {{ background-color: {INPUT_BG} !important; border: 1px solid {BORDER} !important; color: {TEXT_MAIN} !important; }}
button {{ border-radius: 10px !important; }}

.badge-green {{ color: #22c55e; font-weight: 850; }}
.badge-red {{ color: #ef4444; font-weight: 850; }}
.badge-yellow {{ color: #f59e0b; font-weight: 850; }}
.comment-title {{ font-weight: 850; font-size: 0.9rem; color: {TEXT_MAIN}; }}
.comment-desc {{ font-size: 0.80rem; color: {TEXT_SUB}; line-height: 1.45; margin-top: 5px; }}
.comment-signal {{ font-size: 0.78rem; color: #38bdf8; margin-top: 5px; }}

.news-card {{ background: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 14px; padding: 12px; min-height: 116px; max-height: 116px; overflow: hidden; margin-bottom: 8px; }}
.news-title {{ font-size: 0.80rem; line-height: 1.35; font-weight: 750; }}
.news-title a {{ color: {TEXT_MAIN} !important; text-decoration: none; }}
.news-title a:hover {{ color: #38bdf8 !important; text-decoration: underline; }}
.news-meta {{ font-size: 0.68rem; color: {TEXT_SUB}; margin-top: 6px; }}
.news-link {{ font-size: 0.74rem; color: #38bdf8; margin-top: 6px; }}

div[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 13px; overflow: hidden; }}

.focus-card {{ background: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 15px; padding: 10px 11px; min-height: 92px; box-shadow: 0 8px 18px rgba(0,0,0,0.16); }}
.focus-name {{ font-weight: 850; font-size: 0.82rem; color: {TEXT_MAIN}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.focus-sub {{ color: {TEXT_SUB}; font-size: 0.66rem; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.focus-price {{ font-weight: 850; font-size: 0.98rem; text-align: right; color: {TEXT_MAIN}; }}
.focus-stat {{ color: {TEXT_SUB}; font-size: 0.66rem; }}
.focus-delete button {{ height: 28px !important; min-height: 28px !important; padding: 2px 6px !important; font-size: 0.70rem !important; }}


.settings-card {{ background: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 16px; padding: 10px 12px; box-shadow: 0 10px 24px rgba(0,0,0,0.18); }}
.settings-title {{ font-weight: 900; font-size: 0.86rem; color: {TEXT_MAIN}; margin-bottom: 6px; }}

/* Dark mode hardening for Streamlit native widgets */
[data-testid="stDataFrame"] div, [data-testid="stTable"] div {{ color: {TEXT_MAIN}; }}
[data-testid="stDataFrame"] [role="gridcell"], [data-testid="stDataFrame"] [role="columnheader"] {{ background-color: {INPUT_BG} !important; color: {TEXT_MAIN} !important; }}
[data-testid="stDataFrame"] [role="columnheader"] {{ font-weight: 800 !important; }}

.tv-card {{ background: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 17px; padding: 10px; margin-bottom: 16px; box-shadow: 0 10px 24px rgba(0,0,0,0.18); min-height: 500px; }}
.tv-caption {{ color: {TEXT_SUB}; font-size: 0.75rem; margin-top: -4px; margin-bottom: 8px; }}

/* top settings checkbox visibility */
label[data-testid="stWidgetLabel"] p {{ font-weight: 850 !important; color: {TEXT_MAIN} !important; }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Aliases and assets
# =========================================================
korean_alias = {
    "엔비디아": "NVDA", "nvidia": "NVDA", "엔비": "NVDA",
    "애플": "AAPL", "apple": "AAPL",
    "마이크로소프트": "MSFT", "마소": "MSFT", "ms": "MSFT",
    "아마존": "AMZN", "amazon": "AMZN",
    "메타": "META", "페이스북": "META",
    "테슬라": "TSLA", "tesla": "TSLA",
    "구글": "GOOGL", "알파벳": "GOOGL", "google": "GOOGL",
    "amd": "AMD", "에이엠디": "AMD",
    "브로드컴": "AVGO", "broadcom": "AVGO",
    "넷플릭스": "NFLX", "netflix": "NFLX",
    "팔란티어": "PLTR", "palantir": "PLTR",
    "솔리드파워": "SLDP", "solid power": "SLDP", "sldp": "SLDP",
    "로켓랩": "RKLB", "rocket lab": "RKLB", "rklb": "RKLB",
    "tsmc": "TSM", "대만반도체": "TSM", "대만 반도체": "TSM",
    "암홀딩스": "ARM", "arm": "ARM",
    "소파이": "SOFI", "sofi": "SOFI",
    "루시드": "LCID", "lucid": "LCID",
    "리비안": "RIVN", "rivian": "RIVN",
    "코인베이스": "COIN", "coinbase": "COIN",
    "마이크론": "MU", "micron": "MU",
    "인텔": "INTC", "intel": "INTC",
    "퀄컴": "QCOM", "qualcomm": "QCOM",
    "슈퍼마이크로": "SMCI", "슈마컴": "SMCI", "supermicro": "SMCI",
    "아이온큐": "IONQ", "ionq": "IONQ",
    "나스닥": "QQQ", "qqq": "QQQ",
    "티큐": "TQQQ", "티큐큐큐": "TQQQ", "tqqq": "TQQQ",
    "속슬": "SOXL", "soxl": "SOXL",
    "spy": "SPY", "s&p500": "SPY",
    "비트코인": "BTC-USD", "bitcoin": "BTC-USD", "btc": "BTC-USD",
}


def normalize_search_query(query: str) -> str:
    key = query.strip().lower()
    return korean_alias.get(key, query.strip())

market_assets = {
    "NASDAQ100 ETF": "QQQ",
    "나스닥 현물": "^IXIC",
    "S&P500 현물": "^GSPC",
    "나스닥 선물": "NQ=F",
    "S&P500 선물": "ES=F",
    "VIX": "^VIX",
    "미국 10년물 금리": "^TNX",
    "달러 인덱스": "DX-Y.NYB",
    "금": "GC=F",
    "유가 WTI": "CL=F",
    "비트코인": "BTC-USD",
    "반도체 ETF": "SMH",
    "반도체 지수": "^SOX",
}
watchlist_assets = {
    "Nvidia": "NVDA",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Meta": "META",
    "Tesla": "TSLA",
    "Alphabet": "GOOGL",
    "AMD": "AMD",
    "Broadcom": "AVGO",
    "Netflix": "NFLX",
    "Palantir": "PLTR",
    "TSMC": "TSM",
    "ARM": "ARM",
    "SOXL": "SOXL",
    "TQQQ": "TQQQ",
}
tickers = {**market_assets, **watchlist_assets}
if "custom_symbol" in locals() and custom_symbol:
    tickers[f"검색 추가: {custom_symbol}"] = custom_symbol

# =========================================================
# Data functions
# =========================================================
@st.cache_data(ttl=60)
def get_price_data(ticker_dict: dict) -> pd.DataFrame:
    rows = []
    for name, symbol in ticker_dict.items():
        try:
            hist = yf.Ticker(symbol).history(period="1mo")
            if len(hist) >= 2:
                prev_close = hist["Close"].iloc[-2]
                current_price = hist["Close"].iloc[-1]
                change_pct = ((current_price - prev_close) / prev_close) * 100
                volume = hist["Volume"].iloc[-1]
                avg_volume = hist["Volume"].iloc[-21:-1].mean()
                volume_ratio = None if pd.isna(avg_volume) or avg_volume == 0 else volume / avg_volume
                rows.append({
                    "이름": name,
                    "티커": symbol,
                    "현재가": round(float(current_price), 2),
                    "변동률(%)": round(float(change_pct), 2),
                    "거래량": int(volume) if not pd.isna(volume) else 0,
                    "평균거래량대비": round(float(volume_ratio), 2) if volume_ratio is not None else None,
                })
            else:
                rows.append({
                    "이름": name,
                    "티커": symbol,
                    "현재가": None,
                    "변동률(%)": None,
                    "거래량": None,
                    "평균거래량대비": None,
                })
        except Exception:
            rows.append({"이름": name, "티커": symbol, "현재가": None, "변동률(%)": None, "거래량": None, "평균거래량대비": None})
    df_result = pd.DataFrame(rows)
    for col in ["현재가", "변동률(%)", "거래량", "평균거래량대비"]:
        df_result[col] = pd.to_numeric(df_result[col], errors="coerce")
    return df_result


@st.cache_data(ttl=60)
def get_chart_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    return yf.Ticker(symbol).history(period=period, interval=interval)


@st.cache_data(ttl=300)
def get_market_news() -> pd.DataFrame:
    rss_urls = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US",
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=QQQ,NVDA,AMD,AVGO,TSLA,META,MSFT&region=US&lang=en-US",
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=BTC-USD,GC=F,CL=F&region=US&lang=en-US",
    ]
    bullish = ["surge", "gain", "rise", "beat", "record", "growth", "bull", "rally", "strong", "optimism", "outperform"]
    bearish = ["fall", "drop", "fear", "cut", "war", "inflation", "selloff", "recession", "decline", "weak", "risk", "miss"]
    fed = ["fed", "powell", "rate", "fomc", "yield", "treasury"]
    ai = ["ai", "nvidia", "semiconductor", "chip", "amd", "broadcom", "tsmc"]
    macro = ["inflation", "cpi", "ppi", "jobs", "unemployment", "gdp", "oil", "gold", "dollar"]
    geo = ["war", "tariff", "china", "russia", "israel", "iran", "sanction", "export control"]
    news_list = []
    seen = set()
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title
            if title in seen:
                continue
            seen.add(title)
            lower = title.lower()
            sentiment = "🟡 중립"
            if any(w in lower for w in bullish):
                sentiment = "🟢 긍정"
            if any(w in lower for w in bearish):
                sentiment = "🔴 부정"
            category = "일반"
            if any(w in lower for w in fed):
                category = "금리/연준"
            elif any(w in lower for w in ai):
                category = "AI/반도체"
            elif any(w in lower for w in macro):
                category = "거시경제"
            elif any(w in lower for w in geo):
                category = "국제정세"
            news_list.append({"분위기": sentiment, "분류": category, "뉴스 제목": title, "링크": entry.link, "시간": entry.get("published", "")})
    return pd.DataFrame(news_list[:16])



def koreanize_headline(title: str) -> str:
    t = str(title)
    low = t.lower()
    topic = "미국 증시"
    if any(w in low for w in ["nvidia", "amd", "broadcom", "semiconductor", "chip", "ai"]):
        topic = "AI/반도체"
    elif any(w in low for w in ["fed", "powell", "rate", "yield", "treasury"]):
        topic = "연준/금리"
    elif any(w in low for w in ["inflation", "cpi", "ppi", "jobs", "payroll"]):
        topic = "거시지표"
    elif any(w in low for w in ["oil", "gold", "dollar", "bitcoin", "crypto"]):
        topic = "원자재/달러/코인"
    elif any(w in low for w in ["tariff", "china", "iran", "israel", "war", "trade"]):
        topic = "국제정세/정책"
    tone = "중립 흐름"
    if any(w in low for w in ["surge", "rally", "gain", "rise", "up", "beat", "strong", "record", "outperform"]):
        tone = "긍정 신호"
    elif any(w in low for w in ["fall", "drop", "down", "miss", "weak", "risk", "fear", "selloff", "cut"]):
        tone = "주의 신호"
    short = re.sub(r"\s+", " ", t).strip()
    if len(short) > 95:
        short = short[:92] + "..."
    return f"[{topic}·{tone}] {short}"


def news_to_korean_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df
    df_copy = raw_df.copy()
    df_copy["표시 제목"] = df_copy["뉴스 제목"].apply(koreanize_headline)
    return df_copy


@st.cache_data(ttl=180)
def get_saveticker_news() -> pd.DataFrame:
    base = "https://www.saveticker.com/app/news"
    try:
        r = requests.get(base, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
        text = r.text or ""
        found = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{12,180})</a>', text, flags=re.I)
        rows = []
        for href, title in found[:12]:
            clean = re.sub(r"\s+", " ", html.unescape(title)).strip()
            if clean and "뉴스" not in clean and len(clean) > 10:
                link = href if href.startswith("http") else "https://www.saveticker.com" + href
                rows.append({"분위기": "🟡 중립", "분류": "세이브티커", "뉴스 제목": clean, "표시 제목": koreanize_headline(clean), "링크": link, "시간": ""})
        if rows:
            return pd.DataFrame(rows[:12])
    except Exception:
        pass
    fallback = get_market_news()
    fallback = news_to_korean_df(fallback)
    if not fallback.empty:
        fallback["분류"] = fallback["분류"].astype(str) + " / 세이브티커 대체"
    return fallback


def tradingview_symbol(symbol: str) -> str:
    mapping = {
        "QQQ": "NASDAQ:QQQ", "^IXIC": "NASDAQ:IXIC", "^GSPC": "SP:SPX",
        "NQ=F": "CME_MINI:NQ1!", "ES=F": "CME_MINI:ES1!", "^VIX": "TVC:VIX",
        "^TNX": "TVC:US10Y", "DX-Y.NYB": "TVC:DXY", "GC=F": "COMEX:GC1!",
        "CL=F": "NYMEX:CL1!", "BTC-USD": "BINANCE:BTCUSDT", "SMH": "NASDAQ:SMH",
        "^SOX": "NASDAQ:SOX", "SPY": "AMEX:SPY", "TQQQ": "NASDAQ:TQQQ", "SOXL": "AMEX:SOXL",
    }
    if symbol in mapping:
        return mapping[symbol]
    clean = symbol.replace("-USD", "USDT")
    if clean.endswith("USDT"):
        return f"BINANCE:{clean}"
    if clean.startswith("^"):
        return clean.replace("^", "NASDAQ:")
    return f"NASDAQ:{clean}"


def tradingview_interval(interval: str) -> str:
    mapping = {
        "1m": "1",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "60",
        "1d": "D",
    }
    return mapping.get(interval, "5")


def render_tradingview_widget(symbol: str, theme_mode: str, interval: str = "5m", height: int = 430):
    tv_symbol = tradingview_symbol(symbol)
    tv_theme = "light" if theme_mode == "라이트 모드" else "dark"
    tv_interval = tradingview_interval(interval)

    widget = f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;">
      <div class="tradingview-widget-container__widget" style="height:{height}px;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {{
        "autosize": true,
        "symbol": "{tv_symbol}",
        "interval": "{tv_interval}",
        "timezone": "Asia/Seoul",
        "theme": "{tv_theme}",
        "style": "1",
        "locale": "kr",
        "enable_publishing": false,
        "allow_symbol_change": false,
        "hide_side_toolbar": false,
        "calendar": false,
        "support_host": "https://www.tradingview.com"
      }}
      </script>
    </div>
    """
    components.html(widget, height=height + 8, scrolling=False)

def styled_df(dataframe: pd.DataFrame, color_subset=None):
    styler = dataframe.style.set_properties(**{"background-color": INPUT_BG, "color": TEXT_MAIN, "border-color": BORDER})
    if color_subset:
        styler = styler.map(color_change, subset=color_subset)
    return styler


@st.cache_data(ttl=300)
def search_yahoo_symbols(query: str) -> list:
    if not query:
        return []
    normalized = normalize_search_query(query)
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": normalized, "quotesCount": 10, "newsCount": 0, "lang": "en-US", "region": "US"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        quotes = r.json().get("quotes", [])
        results = []
        for q in quotes:
            symbol = q.get("symbol")
            quote_type = q.get("quoteType") or ""
            if quote_type in ["EQUITY", "ETF"] and symbol:
                results.append({
                    "symbol": symbol,
                    "name": q.get("shortname") or q.get("longname") or symbol,
                    "exchange": q.get("exchDisp") or q.get("exchange") or "",
                    "type": quote_type,
                })
        if not results and normalized.upper():
            results.append({"symbol": normalized.upper(), "name": normalized.upper(), "exchange": "직접 입력", "type": "UNKNOWN"})
        return results
    except Exception:
        return []


@st.cache_data(ttl=120)
def get_searched_stock_data(symbol: str) -> dict | None:
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        info = stock.info
        if hist.empty or len(hist) < 2:
            return None
        current = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]
        change = ((current - prev) / prev) * 100
        volume = hist["Volume"].iloc[-1]
        avg_volume = hist["Volume"].iloc[-21:-1].mean()
        volume_ratio = volume / avg_volume if avg_volume and avg_volume > 0 else None
        market_cap = info.get("marketCap")
        return {
            "symbol": symbol,
            "name": info.get("shortName") or info.get("longName") or symbol,
            "price": round(float(current), 2),
            "change": round(float(change), 2),
            "volume": int(volume) if not pd.isna(volume) else 0,
            "volume_ratio": round(float(volume_ratio), 2) if volume_ratio else None,
            "market_cap": f"{market_cap / 1_000_000_000:.2f}B" if market_cap else "정보 없음",
            "sector": info.get("sector", "정보 없음"),
            "industry": info.get("industry", "정보 없음"),
            "recommendation": info.get("recommendationKey", "정보 없음"),
            "target_price": info.get("targetMeanPrice"),
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_stock_specific_news(symbol: str) -> list:
    try:
        feed = feedparser.parse(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US")
        return [{"title": e.title, "link": e.link, "time": e.get("published", "")} for e in feed.entries[:5]]
    except Exception:
        return []


def get_metric(dataframe: pd.DataFrame, ticker: str):
    row = dataframe[dataframe["티커"] == ticker]
    if row.empty:
        return None, None
    return row["현재가"].values[0], row["변동률(%)"].values[0]


def safe_metric(label: str, value, delta=None):
    if value is None or pd.isna(value):
        st.metric(label, "N/A")
    elif delta is None or pd.isna(delta):
        st.metric(label, value)
    else:
        st.metric(label, value, f"{delta}%")


def color_change(value):
    if pd.isna(value):
        return ""
    if value > 0:
        return "color: #22c55e; font-weight: 700"
    if value < 0:
        return "color: #ef4444; font-weight: 700"
    return ""


def analyze_searched_stock(stock_data, stock_news, qqq_change, vix_price, tnx_change, dxy_change, smh_change):
    score = 0
    reasons = []
    change = stock_data.get("change")
    volume_ratio = stock_data.get("volume_ratio")
    sector = stock_data.get("sector", "")
    industry = stock_data.get("industry", "")
    recommendation = stock_data.get("recommendation", "")
    if change is not None:
        if change >= 3:
            score += 2; reasons.append("당일 강한 상승 흐름")
        elif change >= 1:
            score += 1; reasons.append("양호한 상승 흐름")
        elif change <= -3:
            score -= 2; reasons.append("급락 구간")
        elif change <= -1:
            score -= 1; reasons.append("약세 흐름")
    if volume_ratio is not None:
        if volume_ratio >= 2:
            score += 2; reasons.append("평균 대비 거래량 급증")
        elif volume_ratio >= 1.5:
            score += 1; reasons.append("거래량 증가")
    if qqq_change is not None and qqq_change > 0:
        score += 1; reasons.append("나스닥 우호적")
    elif qqq_change is not None and qqq_change < -1:
        score -= 1; reasons.append("나스닥 약세 부담")
    if vix_price is not None and vix_price > 25:
        score -= 2; reasons.append("VIX 고위험 구간")
    elif vix_price is not None and vix_price < 18:
        score += 1; reasons.append("VIX 안정 구간")
    if tnx_change is not None and tnx_change > 1:
        score -= 1; reasons.append("금리 상승 부담")
    if dxy_change is not None and dxy_change > 0.5:
        score -= 1; reasons.append("달러 강세 부담")
    tech_words = ["Technology", "Semiconductor", "Software", "Information Technology", "Electronic"]
    if any(w.lower() in f"{sector} {industry}".lower() for w in tech_words) and smh_change is not None and smh_change > 1:
        score += 1; reasons.append("기술/반도체 섹터 우호")
    news_text = " ".join([n["title"] for n in stock_news]).lower()
    if any(w in news_text for w in ["beat", "growth", "surge", "rally", "upgrade", "outperform", "strong", "raises"]):
        score += 1; reasons.append("최근 뉴스 긍정 신호")
    if any(w in news_text for w in ["miss", "cut", "drop", "lawsuit", "risk", "weak", "downgrade", "fall", "warning"]):
        score -= 1; reasons.append("최근 뉴스 리스크 신호")
    if recommendation in ["buy", "strong_buy"]:
        score += 1; reasons.append("애널리스트 컨센서스 우호")
    elif recommendation in ["sell", "underperform"]:
        score -= 2; reasons.append("애널리스트 컨센서스 부정적")
    if score >= 4:
        return "🟢 관심 구간", "시장 환경과 종목 모멘텀이 비교적 우호적입니다. 다만 장기 투자 관점에서는 분할 접근과 추가 확인이 필요합니다.", reasons or ["특이 신호 제한"], score
    if score >= 1:
        return "🟡 관망 / 추적", "일부 긍정 신호는 있으나 확신도는 높지 않습니다. 뉴스, 거래량, 실적 방향성을 추가 확인하는 구간입니다.", reasons or ["특이 신호 제한"], score
    return "🔴 리스크 경계", "현재 데이터 기준으로는 적극 접근보다 리스크 관리와 추가 확인이 우선입니다.", reasons or ["특이 신호 제한"], score


def score_candidates(dataframe, news_df, vix_price, tnx_change, smh_change):
    candidate_df = dataframe[dataframe["티커"].isin(watchlist_assets.values())].copy()
    if candidate_df.empty:
        return pd.DataFrame()
    scores = []
    titles = " ".join(news_df["뉴스 제목"].astype(str).tolist()).lower() if not news_df.empty else ""
    for _, row in candidate_df.iterrows():
        score = 0; reasons = []
        change = row["변동률(%)"]; volume_ratio = row["평균거래량대비"]; ticker = row["티커"]; name = row["이름"]
        if pd.notna(change):
            if change >= 3: score += 3; reasons.append("강한 상승률")
            elif change >= 1: score += 2; reasons.append("상승 흐름")
            elif change <= -3: score -= 2; reasons.append("급락 주의")
            elif change <= -1: score -= 1; reasons.append("약세 흐름")
        if pd.notna(volume_ratio):
            if volume_ratio >= 2: score += 3; reasons.append("거래량 급증")
            elif volume_ratio >= 1.5: score += 2; reasons.append("거래량 증가")
        if ticker in ["NVDA", "AMD", "AVGO", "TSM", "ARM", "SOXL"] and smh_change is not None and smh_change > 1:
            score += 1; reasons.append("반도체 섹터 우호")
        if vix_price is not None and vix_price > 25: score -= 1; reasons.append("VIX 위험 부담")
        if tnx_change is not None and tnx_change > 1: score -= 1; reasons.append("금리 상승 부담")
        if ticker.lower() in titles or name.lower() in titles: score += 1; reasons.append("뉴스 언급")
        signal = "🟢 관심 후보" if score >= 4 else "🟡 관찰" if score >= 2 else "🔴 리스크 경계" if score <= -2 else "⚪ 관망"
        scores.append({"이름": name, "티커": ticker, "변동률(%)": change, "거래량배율": volume_ratio, "점수": score, "신호": signal, "근거": ", ".join(reasons) if reasons else "특이 신호 제한"})
    return pd.DataFrame(scores).sort_values("점수", ascending=False)

# =========================================================
# Load data
# =========================================================
df = get_price_data(tickers)
news_df = get_saveticker_news()
qqq_price, qqq_change = get_metric(df, "QQQ")
spy_price, spy_change = get_metric(df, "^GSPC")
nasdaq_price, nasdaq_change = get_metric(df, "^IXIC")
vix_price, vix_change = get_metric(df, "^VIX")
tnx_price, tnx_change = get_metric(df, "^TNX")
dxy_price, dxy_change = get_metric(df, "DX-Y.NYB")
smh_price, smh_change = get_metric(df, "SMH")
btc_price, btc_change = get_metric(df, "BTC-USD")
candidate_df = score_candidates(df, news_df, vix_price, tnx_change, smh_change)

risk_score = 0
if qqq_change is not None: risk_score += 1 if qqq_change > 0 else -1 if qqq_change < -1 else 0
if spy_change is not None: risk_score += 1 if spy_change > 0 else -1 if spy_change < -1 else 0
if vix_price is not None: risk_score += 1 if vix_price < 18 else -2 if vix_price > 25 else 0
if tnx_change is not None and tnx_change > 1: risk_score -= 1
if dxy_change is not None and dxy_change > 0.5: risk_score -= 1
if smh_change is not None: risk_score += 1 if smh_change > 1 else -1 if smh_change < -1 else 0
if risk_score >= 3:
    market_status = "Risk On"; market_emoji = "🟢"; market_comment = "성장주와 위험자산에 우호적인 환경입니다."
elif risk_score <= -2:
    market_status = "Risk Off"; market_emoji = "🔴"; market_comment = "변동성, 금리, 달러 강세 등을 경계해야 합니다."
else:
    market_status = "중립"; market_emoji = "🟡"; market_comment = "방향성이 뚜렷하지 않아 주요 지표 확인이 필요합니다."


def build_market_comments():
    comments = []
    if smh_change is not None:
        comments.append("🟢 반도체 강세: AI/반도체 섹터 모멘텀이 우호적입니다." if smh_change >= 3 else "🔴 반도체 약세: 성장주와 AI 관련주에 부담 가능성이 있습니다." if smh_change <= -2 else "🟡 반도체 중립: 뚜렷한 방향성은 제한적입니다.")
    if qqq_change is not None:
        comments.append("🟢 나스닥 강세: 성장주 중심 위험선호가 나타나고 있습니다." if qqq_change >= 1.5 else "🔴 나스닥 약세: 성장주 비중 확대는 신중한 구간입니다." if qqq_change <= -1.5 else "🟡 나스닥 중립: 방향성 확인이 필요합니다.")
    if vix_price is not None:
        comments.append("🔴 변동성 확대: 시장 불안 심리가 커진 상태입니다." if vix_price >= 25 else "🟢 변동성 안정: 위험자산에 상대적으로 우호적입니다." if vix_price <= 18 else "🟡 변동성 보통: 급격한 공포 신호는 제한적입니다.")
    if tnx_change is not None:
        comments.append("🔴 금리 상승 부담: 빅테크 밸류에이션에 부담 요인입니다." if tnx_change >= 1 else "🟢 금리 하락 우호: 성장주에는 상대적으로 우호적입니다." if tnx_change <= -1 else "🟡 금리 중립: 시장 영향은 제한적입니다.")
    if dxy_change is not None:
        comments.append("🔴 달러 강세: 위험자산에는 부담 요인입니다." if dxy_change >= 0.5 else "🟢 달러 약세: 위험자산 선호에 우호적일 수 있습니다." if dxy_change <= -0.5 else "🟡 달러 중립: 달러 움직임은 제한적입니다.")
    while len(comments) < 4:
        comments.append(market_comment)
    return comments[:4]

market_comments = build_market_comments()

# =========================================================
# Header: title + visible settings + ticker
# =========================================================
header_left, header_settings, header_right = st.columns([1.22, 1.30, 1.35])
with header_left:
    st.title("📈 나스닥 시황 모니터링 대시보드")
    st.caption("나스닥100 · 성장주 · 반도체 · 금리 · 달러 · 원자재 · 뉴스 기반 시장 판단 시스템")

with header_settings:
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown('<div class="settings-title">⚙️ 대시보드 설정</div>', unsafe_allow_html=True)
    hs1, hs2, hs3 = st.columns([0.86, 0.72, 0.72])
    with hs1:
        st.session_state.theme_mode = st.selectbox(
            "테마",
            ["다크 모드", "라이트 모드"],
            index=["다크 모드", "라이트 모드"].index(st.session_state.theme_mode),
            key="theme_mode_header",
        )
    with hs2:
        st.session_state.auto_refresh = st.checkbox(
            "자동 갱신",
            value=st.session_state.auto_refresh,
            key="auto_refresh_header",
        )
    with hs3:
        refresh_options = [5, 15, 30, 45, 60]
        current_refresh = st.session_state.refresh_seconds if st.session_state.refresh_seconds in refresh_options else 30
        st.session_state.refresh_seconds = st.selectbox(
            "주기(초)",
            refresh_options,
            index=refresh_options.index(current_refresh),
            key="refresh_seconds_header",
        )

    hs4, hs5, hs6 = st.columns([0.72, 0.72, 0.95])
    with hs4:
        chart_period_options = ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
        st.session_state.chart_period = st.selectbox(
            "차트기간",
            chart_period_options,
            index=chart_period_options.index(st.session_state.chart_period),
            key="chart_period_header",
        )
    with hs5:
        chart_interval_options = ["1m", "5m", "15m", "30m", "1h", "1d"]
        st.session_state.chart_interval = st.selectbox(
            "간격",
            chart_interval_options,
            index=chart_interval_options.index(st.session_state.chart_interval),
            key="chart_interval_header",
        )
    with hs6:
        st.session_state.custom_symbol = st.text_input(
            "빠른티커",
            value=st.session_state.get("custom_symbol", ""),
            placeholder="NVDA",
            key="custom_symbol_header",
        ).upper().strip()
    if st.button("🔄 수동 새로고침", key="manual_refresh_header", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.auto_refresh:
    st_autorefresh(interval=st.session_state.refresh_seconds * 1000, key="auto_refresh")

with header_right:
    news_items = news_df.head(4)["표시 제목"].tolist() if (not news_df.empty and "표시 제목" in news_df.columns) else (news_df.head(4)["뉴스 제목"].tolist() if not news_df.empty else ["뉴스 데이터를 불러오는 중입니다."])
    while len(news_items) < 4:
        news_items.append("뉴스 데이터를 불러오는 중입니다.")
    safe_news = [html.escape(str(item)) for item in news_items[:4]]
    safe_comments = [html.escape(str(item)) for item in market_comments[:4]]
    rolling_html = f"""
    <html><head><style>
    body {{ margin:0; background:transparent; font-family:Arial,sans-serif; color:{TEXT_MAIN}; }}
    .ticker-wrap {{ width:100%; min-height:120px; background:{TICKER_BG}; border:1px solid {BORDER}; border-radius:18px; padding:12px 14px; box-sizing:border-box; overflow:hidden; }}
    .top-row {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }}
    .status-pill {{ display:inline-flex; align-items:center; padding:7px 16px; border-radius:999px; background:rgba(34,197,94,0.10); border:1px solid rgba(34,197,94,0.35); color:#22c55e; font-weight:800; font-size:15px; }}
    .time {{ font-size:12px; color:{TEXT_SUB}; }}
    .ticker-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; align-items:start; }}
    .ticker-title {{ font-size:12px; color:{TEXT_SUB}; margin-bottom:6px; font-weight:800; }}
    .ticker-window {{ height:24px; overflow:hidden; border-top:1px solid {BORDER}; padding-top:6px; }}
    .ticker-track {{ animation: slideTicker 12s infinite; }}
    .ticker-item {{ height:24px; line-height:24px; font-size:13px; color:{TEXT_MAIN}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
    @keyframes slideTicker {{ 0% {{transform:translateY(0)}} 22% {{transform:translateY(0)}} 25% {{transform:translateY(-24px)}} 47% {{transform:translateY(-24px)}} 50% {{transform:translateY(-48px)}} 72% {{transform:translateY(-48px)}} 75% {{transform:translateY(-72px)}} 97% {{transform:translateY(-72px)}} 100% {{transform:translateY(0)}} }}
    </style></head><body><div class="ticker-wrap"><div class="top-row"><div class="status-pill">{market_emoji} {market_status}</div><div class="time">{get_kst_now().strftime('%H:%M:%S')} KST</div></div><div class="ticker-grid"><div><div class="ticker-title">📰 주요 뉴스</div><div class="ticker-window"><div class="ticker-track"><div class="ticker-item">{safe_news[0]}</div><div class="ticker-item">{safe_news[1]}</div><div class="ticker-item">{safe_news[2]}</div><div class="ticker-item">{safe_news[3]}</div></div></div></div><div><div class="ticker-title">🧠 시장 코멘트</div><div class="ticker-window"><div class="ticker-track"><div class="ticker-item">{safe_comments[0]}</div><div class="ticker-item">{safe_comments[1]}</div><div class="ticker-item">{safe_comments[2]}</div><div class="ticker-item">{safe_comments[3]}</div></div></div></div></div></div></body></html>
    """
    components.html(rolling_html, height=126)

if hasattr(st, "dialog"):
    @st.dialog("오늘의 실시간 시장현황")
    def market_dialog():
        top_candidates = "관심 후보 없음"
        if not candidate_df.empty:
            top_candidates = "\n".join([
                f"- {row['이름']}({row['티커']}): {row['신호']} / {row['근거']}"
                for _, row in candidate_df.head(3).iterrows()
            ])
        news_lines = "뉴스 데이터 없음"
        if not news_df.empty:
            title_col = "표시 제목" if "표시 제목" in news_df.columns else "뉴스 제목"
            news_lines = "\n".join([f"- {t}" for t in news_df[title_col].head(4).tolist()])
        sector_lines = []
        sector_map = {
            "기술/나스닥": qqq_change,
            "반도체": smh_change,
            "대형주/S&P500": spy_change,
            "가상자산": btc_change,
            "원유": get_metric(df, "CL=F")[1],
            "금": get_metric(df, "GC=F")[1],
            "달러": dxy_change,
            "금리": tnx_change,
        }
        for sector, change_value in sector_map.items():
            if change_value is None or pd.isna(change_value):
                sector_lines.append(f"- {sector}: 데이터 확인 필요")
            elif change_value >= 1:
                sector_lines.append(f"- {sector}: 강세/우호 흐름 ({change_value}%)")
            elif change_value <= -1:
                sector_lines.append(f"- {sector}: 약세/부담 흐름 ({change_value}%)")
            else:
                sector_lines.append(f"- {sector}: 중립권 등락 ({change_value}%)")
        risk_notes = []
        if vix_price is not None:
            risk_notes.append("VIX 안정권" if vix_price < 18 else "VIX 경계권" if vix_price < 25 else "VIX 고위험권")
        if tnx_change is not None:
            risk_notes.append("금리 상승 부담 제한" if tnx_change <= 0.5 else "금리 상승 부담 존재")
        if dxy_change is not None:
            risk_notes.append("달러 강세 부담 제한" if dxy_change <= 0.5 else "달러 강세 부담 존재")
        st.markdown(f"""
### 오늘의 실시간 시장현황

**종합 판단:** {market_emoji} {market_status}  
**요약:** {market_comment}

**핵심 지표**  
QQQ {qqq_change}% · 나스닥 {nasdaq_change}% · S&P500 {spy_change}% · VIX {vix_price} · 10Y {tnx_price} · DXY {dxy_price} · SMH {smh_change}% · BTC {btc_change}%

**섹터/자산별 흐름**  
{chr(10).join(sector_lines)}

**리스크 체크**  
- {" / ".join(risk_notes) if risk_notes else "리스크 지표 데이터 확인 필요"}

**주요 뉴스 헤드라인**  
{news_lines}

**현재 데이터 기반 관심 후보**  
{top_candidates}

**해석 메모**  
무료 지연 데이터, 주요 헤드라인, 지수·섹터·금리·달러·원자재 흐름을 함께 본 시장 관찰용 신호입니다. 단기 매매 지시가 아니라 장기/스윙 관점의 환경 점검용입니다.
""")
        st.caption(f"생성 시각: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")
    if st.button("📌 오늘의 실시간 시장현황 보기", use_container_width=True):
        market_dialog()

# =========================================================
# Top metrics
# =========================================================
top_metric_list = [
    ("💎 QQQ", "QQQ"), ("📈 나스닥", "^IXIC"), ("📊 S&P500", "^GSPC"), ("🧭 나스닥 선물", "NQ=F"), ("🧭 S&P 선물", "ES=F"),
    ("🛡️ VIX", "^VIX"), ("🏛️ 10년물 금리", "^TNX"), ("💵 DXY", "DX-Y.NYB"), ("🥇 금", "GC=F"), ("🛢️ 유가 WTI", "CL=F"),
    ("₿ 비트코인", "BTC-USD"), ("🔲 SMH", "SMH"), ("🧩 SOX", "^SOX"), ("🟩 NVDA", "NVDA"), ("🔴 AMD", "AMD"),
]
for row_start in range(0, len(top_metric_list), 5):
    cols = st.columns(5)
    for idx, (label, symbol) in enumerate(top_metric_list[row_start:row_start + 5]):
        price, change = get_metric(df, symbol)
        with cols[idx]:
            safe_metric(label, price, change)

# =========================================================
# 4-way TradingView chart monitor + market judgment + alerts
# =========================================================
st.markdown('<div class="panel-title">📊 실시간 차트 4분할 모니터링</div>', unsafe_allow_html=True)

chart_names = list(tickers.keys())
chart_defaults = ["나스닥 선물", "NASDAQ100 ETF", "비트코인", "반도체 ETF"]
chart_rows = [st.columns(2), st.columns(2)]

for chart_idx in range(4):
    row = chart_idx // 2
    col = chart_idx % 2
    with chart_rows[row][col]:
        default_name = chart_defaults[chart_idx]
        default_idx = chart_names.index(default_name) if default_name in chart_names else 0
        selected_name = st.selectbox(
            f"차트 {chart_idx + 1}",
            chart_names,
            index=default_idx,
            key=f"tv_chart_select_{chart_idx}",
            label_visibility="collapsed",
        )
        selected_symbol = tickers[selected_name]
        tv_symbol_for_caption = tradingview_symbol(selected_symbol)
        st.markdown(
            f"<div class='tv-caption'>TradingView 실시간 차트 · {selected_name} ({selected_symbol}) · {tv_symbol_for_caption} · 한국시간(KST)</div>",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tv-card">', unsafe_allow_html=True)
        render_tradingview_widget(
            selected_symbol,
            st.session_state.theme_mode,
            interval=st.session_state.chart_interval,
            height=490,
        )
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# Four horizontal information partitions
# =========================================================
info_col1, info_col2, info_col3, info_col4 = st.columns(4)

vol_status = "높음" if vix_price and vix_price > 25 else "보통" if vix_price and vix_price > 18 else "낮음"
rate_status = "높음" if tnx_change and tnx_change > 1 else "보통"
semi_status = "강함" if smh_change and smh_change > 1 else "약함" if smh_change and smh_change < -1 else "보통"

with info_col1:
    st.markdown('<div class="panel-title">🧭 시장 종합 판단</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="panel" style="min-height:255px;">
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid {BORDER}; padding-bottom:12px;">
            <span>종합 판단</span><span class="badge-green">{market_emoji} {market_status}</span>
        </div>
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid {BORDER}; padding:13px 0;">
            <span>변동성 위험</span><span class="badge-yellow">{vol_status} (VIX {vix_price})</span>
        </div>
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid {BORDER}; padding:13px 0;">
            <span>금리 부담</span><span class="badge-yellow">{rate_status} (10Y {tnx_price})</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding-top:13px;">
            <span>반도체 모멘텀</span><span class="badge-green">{semi_status} (SMH {smh_change}%)</span>
        </div>
        <div style="margin-top:18px; color:#38bdf8; font-size:0.84rem; line-height:1.45;">{market_comment}</div>
    </div>
    """, unsafe_allow_html=True)

with info_col2:
    st.markdown('<div class="panel-title">📅 경제 이벤트 체크</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div class='panel' style='min-height:255px;'><div style='white-space:pre-line; font-size:0.84rem; color:{TEXT_SUB}; line-height:1.55;'>{st.session_state.economic_memo}</div></div>",
        unsafe_allow_html=True,
    )

with info_col3:
    st.markdown('<div class="panel-title">🚨 급등락 / 거래량 감지</div>', unsafe_allow_html=True)
    alert_df = df[
        (df["변동률(%)"].notna())
        & ((df["변동률(%)"].abs() >= 3) | (df["평균거래량대비"].fillna(0) >= 1.8))
    ][["이름", "티커", "변동률(%)", "평균거래량대비"]]
    if not alert_df.empty:
        st.dataframe(
            styled_df(alert_df, color_subset=["변동률(%)"]),
            use_container_width=True,
            hide_index=True,
            height=255,
        )
    else:
        st.markdown("<div class='panel' style='min-height:255px;'>급등락/거래량 이상 신호 없음</div>", unsafe_allow_html=True)

with info_col4:
    st.markdown('<div class="panel-title">🎯 현재 관심 후보</div>', unsafe_allow_html=True)
    if not candidate_df.empty:
        st.dataframe(
            candidate_df.head(6)[["이름", "티커", "신호", "점수", "근거"]],
            use_container_width=True,
            hide_index=True,
            height=255,
        )
    else:
        st.markdown("<div class='panel' style='min-height:255px;'>관심 후보 데이터 없음</div>", unsafe_allow_html=True)

# =========================================================
# Search left + focus monitor right: this uses the red empty area
# =========================================================
search_left, focus_right = st.columns([1.15, 0.85])
with search_left:
    st.markdown('<div class="panel-title">🔍 종목 검색 분석</div>', unsafe_allow_html=True)
    stock_search_query = st.text_input("종목명 또는 티커 검색", placeholder="예: 엔비디아, 솔리드파워, 로켓랩, SLDP, NVDA, SOXL", key="stock_search_box")
    if stock_search_query:
        normalized_query = normalize_search_query(stock_search_query)
        search_results = search_yahoo_symbols(normalized_query)
        if search_results:
            option_labels = [f"{item['symbol']} | {item['name']} | {item['exchange']} | {item['type']}" for item in search_results]
            selected_option = st.selectbox("검색 결과 선택", option_labels, key="selected_search_result")
            selected_symbol_for_analysis = search_results[option_labels.index(selected_option)]["symbol"]
            stock_data = get_searched_stock_data(selected_symbol_for_analysis)
            stock_news = get_stock_specific_news(selected_symbol_for_analysis)
            if stock_data:
                signal, comment, reasons, score = analyze_searched_stock(stock_data, stock_news, qqq_change, vix_price, tnx_change, dxy_change, smh_change)
                add_col, info_col = st.columns([1, 1])
                with add_col:
                    if st.button(f"⭐ {selected_symbol_for_analysis} 보유/관심종목 추가", use_container_width=True):
                        if selected_symbol_for_analysis not in st.session_state.focus_symbols:
                            st.session_state.focus_symbols.append(selected_symbol_for_analysis)
                            st.success(f"{selected_symbol_for_analysis} 추가 완료")
                        else:
                            st.info(f"{selected_symbol_for_analysis}는 이미 등록되어 있습니다.")
                with info_col:
                    st.caption("오른쪽 보유/관심종목 모니터링에서 확인됩니다.")
                s1, s2, s3, s4 = st.columns(4)
                with s1: st.metric("현재가", stock_data["price"], f"{stock_data['change']}%")
                with s2: st.metric("거래량", f"{stock_data['volume']:,}")
                with s3: st.metric("평균 대비 거래량", f"{stock_data['volume_ratio']}배" if stock_data["volume_ratio"] else "N/A")
                with s4: st.metric("판단", signal)
                analysis_left, analysis_right = st.columns([1.35, 1])
                with analysis_left:
                    st.markdown(f"""
                    <div class="panel"><div class="comment-title">{stock_data['name']} ({selected_symbol_for_analysis})</div><div class="comment-desc">시가총액: {stock_data['market_cap']}<br>섹터: {stock_data['sector']}<br>산업: {stock_data['industry']}<br>애널리스트 평가: {stock_data['recommendation']}<br>평균 목표가: {stock_data['target_price']}</div><br><div class="comment-title">📌 종합 해석</div><div class="comment-desc">{comment}</div><div class="comment-signal">점수: {score} / 신호: {signal}</div></div>
                    """, unsafe_allow_html=True)
                with analysis_right:
                    reason_html = "".join([f"<div style='border-bottom:1px solid {BORDER}; padding:7px 0;'>• {reason}</div>" for reason in reasons])
                    st.markdown(f"<div class='panel'><div class='comment-title'>📍 분석 근거</div><div class='comment-desc'>{reason_html}</div></div>", unsafe_allow_html=True)
                st.markdown("**최신 관련 뉴스**")
                if stock_news:
                    news_cols_for_stock = st.columns(2)
                    for idx, news in enumerate(stock_news[:4]):
                        with news_cols_for_stock[idx % 2]:
                            st.markdown(f"<div class='news-card'><div class='news-title'><a href='{news['link']}' target='_blank'>{koreanize_headline(news['title'])}</a></div><div class='news-link'>뉴스 보기 →</div><div class='news-meta'>{news['time']}</div></div>", unsafe_allow_html=True)
                else:
                    st.info("해당 종목 관련 뉴스를 불러오지 못했습니다.")
                st.caption("이 판단은 데이터 기반 시장 관찰 신호이며, 투자 권유 또는 투자 자문이 아닙니다.")
            else:
                st.warning("해당 종목 데이터를 불러오지 못했습니다. 티커를 다시 확인하세요.")
        else:
            st.warning("검색 결과가 없습니다. 한글명은 등록된 별칭만 지원하며, 영문명 또는 티커 입력이 가장 정확합니다.")
with focus_right:
    st.markdown('<div class="panel-title">⭐ 보유/관심종목 모니터링</div>', unsafe_allow_html=True)
    if st.session_state.focus_symbols:
        focus_cols = st.columns(2)
        for idx, symbol in enumerate(list(st.session_state.focus_symbols)):
            data = get_searched_stock_data(symbol)
            with focus_cols[idx % 2]:
                if data:
                    change = data["change"]
                    change_class = "badge-green" if change >= 0 else "badge-red"
                    volume_ratio_text = f"{data['volume_ratio']}배" if data["volume_ratio"] else "N/A"
                    st.markdown(f"""
                    <div class="focus-card"><div style="display:flex; justify-content:space-between; gap:8px; align-items:flex-start;"><div style="min-width:0; flex:1;"><div class="focus-name">{data['name']} ({symbol})</div><div class="focus-sub">{data['sector']} · {data['industry']}</div></div><div style="min-width:65px; text-align:right;"><div class="focus-price">{data['price']}</div><div class="{change_class}" style="font-size:0.76rem;">{data['change']}%</div></div></div><div style="margin-top:8px; display:grid; grid-template-columns:1fr 1fr; gap:5px;"><div class="focus-stat">거래량<br><b>{data['volume']:,}</b></div><div class="focus-stat" style="text-align:right;">평균대비<br><b>{volume_ratio_text}</b></div></div></div>
                    """, unsafe_allow_html=True)
                    st.markdown('<div class="focus-delete">', unsafe_allow_html=True)
                    if st.button(f"삭제: {symbol}", key=f"remove_{symbol}", use_container_width=True):
                        st.session_state.focus_symbols.remove(symbol)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning(f"{symbol} 데이터를 불러오지 못했습니다.")
    else:
        st.info("종목 검색 분석에서 보유/관심종목을 추가하세요.")

# =========================================================
# Market tables
# =========================================================
st.markdown('<div class="panel-title">📊 전체 시장 데이터</div>', unsafe_allow_html=True)
table_left, table_right = st.columns(2)
market_df = df[df["티커"].isin(market_assets.values())].copy()
stock_df = df[df["티커"].isin(watchlist_assets.values())].copy()
with table_left:
    st.caption("지수 / 거시 / 선물 / 원자재 / 섹터")
    st.dataframe(styled_df(market_df, color_subset=["변동률(%)"]), use_container_width=True, hide_index=True, height=430)
with table_right:
    st.caption("Watchlist / 주요 관심 종목")
    st.dataframe(styled_df(stock_df, color_subset=["변동률(%)"]), use_container_width=True, hide_index=True, height=430)

st.caption(f"마지막 갱신 시각: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")
st.caption("본 대시보드는 정보 제공 목적이며, 투자 조언이 아닙니다. 표시되는 관심 후보와 종목 분석은 매수·매도 추천이 아니라 시장 관찰용 신호입니다.")
st.caption("© JJS. 제작자 동의 없이 무단 배포, 복제, 수정, 재공유 및 불펌을 금지합니다.")
