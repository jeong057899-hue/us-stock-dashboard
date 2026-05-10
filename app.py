import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from zoneinfo import ZoneInfo
import feedparser
import requests
import html
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="나스닥 시황 모니터링 대시보드",
    page_icon="📈",
    layout="wide"
)

# =========================
# Sidebar - Theme First
# =========================
st.sidebar.markdown("## ⚙️ 설정")

theme_mode = st.sidebar.selectbox(
    "화면 테마",
    ["다크 모드", "라이트 모드"],
    index=0
)

if theme_mode == "라이트 모드":
    APP_BG = "linear-gradient(135deg, #f8fafc 0%, #e5edf7 45%, #f8fafc 100%)"
    SIDEBAR_BG = "linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%)"
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
    SIDEBAR_BG = "linear-gradient(180deg, #0c1524 0%, #07101d 100%)"
    PANEL_BG = "linear-gradient(145deg, rgba(17,24,39,0.96), rgba(9,15,27,0.96))"
    TEXT_MAIN = "#f8fafc"
    TEXT_SUB = "#94a3b8"
    BORDER = "#26364c"
    INPUT_BG = "#0f172a"
    PLOT_BG = "rgba(8,13,22,0.95)"
    TICKER_BG = "linear-gradient(145deg, rgba(17,24,39,0.96), rgba(8,13,22,0.96))"
    TEMPLATE = "plotly_dark"

# =========================
# CSS
# =========================
st.markdown(f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{
    background: {APP_BG} !important;
}}

.stApp {{
    background: {APP_BG};
    color: {TEXT_MAIN};
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
    height: 2.2rem !important;
}}

[data-testid="stHeader"]::before {{
    background: transparent !important;
}}

.block-container {{
    padding-top: 0.35rem !important;
    padding-left: 1.6rem;
    padding-right: 1.6rem;
    max-width: 98.5vw !important;
}}

section[data-testid="stSidebar"] {{
    background: {SIDEBAR_BG};
    border-right: 1px solid {BORDER};
}}

section[data-testid="stSidebar"] * {{
    color: {TEXT_MAIN};
}}

[data-testid="stMetric"] {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    padding: 15px 17px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.20);
    min-height: 105px;
}}

[data-testid="stMetricLabel"] {{
    color: {TEXT_SUB};
    font-size: 0.80rem;
}}

[data-testid="stMetricValue"] {{
    color: {TEXT_MAIN};
    font-size: 1.50rem;
    font-weight: 750;
}}

[data-testid="stMetricDelta"] {{
    font-size: 0.80rem;
}}

.panel {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 10px 26px rgba(0,0,0,0.20);
    margin-bottom: 14px;
    color: {TEXT_MAIN};
}}

.panel-title {{
    font-size: 1.08rem;
    font-weight: 800;
    margin-bottom: 12px;
    color: {TEXT_MAIN};
}}

.status-pill {{
    display: inline-flex;
    align-items: center;
    padding: 7px 16px;
    border-radius: 999px;
    background: rgba(34,197,94,0.10);
    border: 1px solid rgba(34,197,94,0.35);
    color: #22c55e;
    font-weight: 800;
    font-size: 1.05rem;
}}

.news-card {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 15px;
    padding: 14px;
    min-height: 132px;
    max-height: 132px;
    overflow: hidden;
    margin-bottom: 10px;
}}

.news-card:hover {{
    transform: translateY(-2px);
    transition: 0.2s;
    border-color: #38bdf8;
}}

.news-meta {{
    font-size: 0.74rem;
    color: {TEXT_SUB};
    margin-bottom: 8px;
}}

.news-title {{
    font-size: 0.88rem;
    line-height: 1.35;
    font-weight: 700;
}}

.news-title a {{
    color: {TEXT_MAIN} !important;
    text-decoration: none;
}}

.news-title a:hover {{
    color: #38bdf8 !important;
    text-decoration: underline;
}}

.news-link {{
    font-size: 0.8rem;
    color: #38bdf8;
    margin-top: 8px;
}}

.badge-green {{
    color: #22c55e;
    font-weight: 800;
}}

.badge-red {{
    color: #ef4444;
    font-weight: 800;
}}

.badge-yellow {{
    color: #f59e0b;
    font-weight: 800;
}}

.comment-title {{
    font-weight: 800;
    font-size: 0.92rem;
    color: {TEXT_MAIN};
}}

.comment-desc {{
    font-size: 0.82rem;
    color: {TEXT_SUB};
    line-height: 1.4;
    margin-top: 5px;
}}

.comment-signal {{
    font-size: 0.78rem;
    color: #38bdf8;
    margin-top: 5px;
}}

div[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 14px;
    overflow: hidden;
}}

.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea textarea {{
    background-color: {INPUT_BG} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT_MAIN} !important;
}}

button {{
    border-radius: 10px !important;
}}

.focus-card {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 14px 16px;
    margin-bottom: 8px;
    min-height: 118px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.18);
}}

.focus-name {{
    font-weight: 850;
    font-size: 1.02rem;
    color: {TEXT_MAIN};
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.focus-sub {{
    color: {TEXT_SUB};
    font-size: 0.78rem;
    margin-top: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.focus-price {{
    font-weight: 850;
    font-size: 1.18rem;
    text-align: right;
    color: {TEXT_MAIN};
}}

.focus-stat {{
    color: {TEXT_SUB};
    font-size: 0.78rem;
}}

/* Streamlit 기본 툴바/메뉴 숨김: 사이드바 여닫기 버튼은 유지 */
#MainMenu {{
    visibility: hidden;
}}

#GithubIcon {{
    visibility: hidden;
}}

[data-testid="stToolbar"] {{
    display: none !important;
}}

[data-testid="stDecoration"] {{
    display: none !important;
}}

[data-testid="stStatusWidget"] {{
    display: none !important;
}}

footer {{
    visibility: hidden;
}}
/* ⚙️ 설정 버튼 스타일 */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 75px !important;
    left: 12px !important;
    z-index: 999999 !important;
    width: 42px !important;
    height: 42px !important;
    border-radius: 50% !important;
    background: rgba(15, 23, 42, 0.95) !important;
    border: 1px solid #38bdf8 !important;
    box-shadow: 0 0 18px rgba(56,189,248,0.45) !important;
}

[data-testid="collapsedControl"] svg {
    display: none !important;
}

[data-testid="collapsedControl"]::before {
    content: "⚙️";
    font-size: 22px;
    line-height: 42px;
    width: 42px;
    height: 42px;
    text-align: center;
}

</style>
""", unsafe_allow_html=True)

# =========================
# Time
# =========================
def get_kst_now():
    return datetime.now(ZoneInfo("Asia/Seoul"))

# =========================
# Korean Alias
# =========================
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
    "tsmc": "TSM", "대만반도체": "TSM", "대만 반도체": "TSM",
    "암홀딩스": "ARM", "arm": "ARM",
    "소파이": "SOFI", "sofi": "SOFI",
    "루시드": "LCID", "lucid": "LCID",
    "리비안": "RIVN", "rivian": "RIVN",
    "코인베이스": "COIN", "coinbase": "COIN",
    "마이크론": "MU", "micron": "MU",
    "인텔": "INTC", "intel": "INTC",
    "퀄컴": "QCOM", "qualcomm": "QCOM",
    "어도비": "ADBE", "adobe": "ADBE",
    "세일즈포스": "CRM", "salesforce": "CRM",
    "오라클": "ORCL", "oracle": "ORCL",
    "스노우플레이크": "SNOW", "snowflake": "SNOW",
    "슈퍼마이크로": "SMCI", "슈마컴": "SMCI", "supermicro": "SMCI",
    "델": "DELL", "dell": "DELL",
    "아이온큐": "IONQ", "ionq": "IONQ",
    "로빈후드": "HOOD", "hood": "HOOD",
    "로블록스": "RBLX", "roblox": "RBLX",
    "우버": "UBER", "uber": "UBER",
    "스포티파이": "SPOT", "spotify": "SPOT",
    "쇼피파이": "SHOP", "shopify": "SHOP",
    "도큐사인": "DOCU", "docusign": "DOCU",
    "크라우드스트라이크": "CRWD", "crowdstrike": "CRWD",
    "팔로알토": "PANW", "palo alto": "PANW",
    "로켓랩": "RKLB", "rocket lab": "RKLB", "rklb": "RKLB",
    "나스닥": "QQQ", "qqq": "QQQ",
    "티큐": "TQQQ", "티큐큐큐": "TQQQ", "tqqq": "TQQQ",
    "속슬": "SOXL", "soxl": "SOXL",
    "spy": "SPY", "s&p500": "SPY",
    "비트코인": "BTC-USD", "bitcoin": "BTC-USD", "btc": "BTC-USD",
}

def normalize_search_query(query):
    key = query.strip().lower()
    return korean_alias.get(key, query.strip())

# =========================
# Session State
# =========================
if "show_market_briefing" not in st.session_state:
    st.session_state.show_market_briefing = False

if "focus_symbols" not in st.session_state:
    st.session_state.focus_symbols = []

# =========================
# Sidebar
# =========================
auto_refresh = st.sidebar.checkbox("자동 갱신", value=False)

refresh_seconds = st.sidebar.selectbox(
    "갱신 주기",
    [15, 30, 60, 120, 300],
    index=2
)

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh")

if st.sidebar.button("🔄 수동 새로고침", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

custom_symbol = st.sidebar.text_input(
    "🔎 빠른 티커 추가",
    placeholder="예: NVDA, QQQ, SOXL, PLTR, BTC-USD"
).upper().strip()

st.sidebar.divider()

chart_period = st.sidebar.selectbox(
    "차트 기간",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=0
)

chart_interval = st.sidebar.selectbox(
    "차트 간격",
    ["1m", "5m", "15m", "30m", "1h", "1d"],
    index=1
)

st.sidebar.divider()

economic_memo = st.sidebar.text_area(
    "📅 경제 이벤트 메모",
    value="CPI 발표 확인\nPPI 발표 확인\nFOMC 일정 확인\nPCE 물가 확인\n고용보고서 확인\n연준 인사 발언 확인",
    height=130
)

st.sidebar.divider()
st.sidebar.info("무료 데이터 기반\n\nyfinance + Yahoo Finance RSS\n\n실시간 데이터는 지연될 수 있습니다.")
st.sidebar.caption(f"마지막 갱신\n{get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")

# =========================
# Assets
# =========================
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

tickers = {}
tickers.update(market_assets)
tickers.update(watchlist_assets)

if custom_symbol:
    tickers[f"검색 추가: {custom_symbol}"] = custom_symbol

# =========================
# Data Functions
# =========================
@st.cache_data(ttl=60)
def get_price_data(ticker_dict):
    rows = []

    for name, symbol in ticker_dict.items():
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")

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
                    "현재가": round(current_price, 2),
                    "변동률(%)": round(change_pct, 2),
                    "거래량": int(volume) if not pd.isna(volume) else 0,
                    "평균거래량대비": round(volume_ratio, 2) if volume_ratio is not None else None
                })
            else:
                rows.append({
                    "이름": name,
                    "티커": symbol,
                    "현재가": None,
                    "변동률(%)": None,
                    "거래량": None,
                    "평균거래량대비": None
                })

        except Exception:
            rows.append({
                "이름": name,
                "티커": symbol,
                "현재가": None,
                "변동률(%)": None,
                "거래량": None,
                "평균거래량대비": None
            })

    df_result = pd.DataFrame(rows)

    for col in ["현재가", "변동률(%)", "거래량", "평균거래량대비"]:
        df_result[col] = pd.to_numeric(df_result[col], errors="coerce")

    return df_result

@st.cache_data(ttl=60)
def get_chart_data(symbol, period, interval):
    stock = yf.Ticker(symbol)
    return stock.history(period=period, interval=interval)

@st.cache_data(ttl=300)
def get_market_news():
    rss_urls = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US",
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=QQQ,NVDA,AMD,AVGO,TSLA,META,MSFT&region=US&lang=en-US",
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=BTC-USD,GC=F,CL=F&region=US&lang=en-US",
    ]

    bullish_keywords = ["surge", "gain", "rise", "beat", "record", "growth", "bull", "rally", "strong", "optimism", "outperform"]
    bearish_keywords = ["fall", "drop", "fear", "cut", "war", "inflation", "selloff", "recession", "decline", "weak", "risk", "miss"]
    fed_keywords = ["fed", "powell", "rate", "fomc", "yield", "treasury"]
    ai_keywords = ["ai", "nvidia", "semiconductor", "chip", "amd", "broadcom", "tsmc"]
    macro_keywords = ["inflation", "cpi", "ppi", "jobs", "unemployment", "gdp", "oil", "gold", "dollar"]
    geopolitical_keywords = ["war", "tariff", "china", "russia", "israel", "iran", "sanction", "export control"]

    news_list = []
    seen_titles = set()

    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)

        for entry in feed.entries[:10]:
            title = entry.title
            link = entry.link
            published = entry.get("published", "")
            lower_title = title.lower()

            if title in seen_titles:
                continue

            seen_titles.add(title)

            sentiment = "🟡 중립"
            if any(word in lower_title for word in bullish_keywords):
                sentiment = "🟢 긍정"
            if any(word in lower_title for word in bearish_keywords):
                sentiment = "🔴 부정"

            category = "일반"
            if any(word in lower_title for word in fed_keywords):
                category = "금리/연준"
            elif any(word in lower_title for word in ai_keywords):
                category = "AI/반도체"
            elif any(word in lower_title for word in macro_keywords):
                category = "거시경제"
            elif any(word in lower_title for word in geopolitical_keywords):
                category = "국제정세"

            news_list.append({
                "분위기": sentiment,
                "분류": category,
                "뉴스 제목": title,
                "링크": link,
                "시간": published
            })

    return pd.DataFrame(news_list[:16])

@st.cache_data(ttl=300)
def search_yahoo_symbols(query):
    if not query:
        return []

    normalized_query = normalize_search_query(query)

    url = "https://query1.finance.yahoo.com/v1/finance/search"
    params = {
        "q": normalized_query,
        "quotesCount": 10,
        "newsCount": 0,
        "lang": "en-US",
        "region": "US"
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        data = r.json()
        quotes = data.get("quotes", [])
        results = []

        for q in quotes:
            symbol = q.get("symbol")
            name = q.get("shortname") or q.get("longname") or ""
            exchange = q.get("exchDisp") or q.get("exchange") or ""
            quote_type = q.get("quoteType") or ""

            if quote_type in ["EQUITY", "ETF"] and symbol:
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "exchange": exchange,
                    "type": quote_type
                })

        if not results and normalized_query.upper():
            results.append({
                "symbol": normalized_query.upper(),
                "name": normalized_query.upper(),
                "exchange": "직접 입력",
                "type": "UNKNOWN"
            })

        return results

    except Exception:
        return []

@st.cache_data(ttl=120)
def get_searched_stock_data(symbol):
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

        volume_ratio = None
        if avg_volume and avg_volume > 0:
            volume_ratio = volume / avg_volume

        market_cap = info.get("marketCap")
        market_cap_text = f"{market_cap / 1_000_000_000:.2f}B" if market_cap else "정보 없음"

        return {
            "symbol": symbol,
            "name": info.get("shortName") or info.get("longName") or symbol,
            "price": round(current, 2),
            "change": round(change, 2),
            "volume": int(volume) if not pd.isna(volume) else 0,
            "volume_ratio": round(volume_ratio, 2) if volume_ratio else None,
            "market_cap": market_cap_text,
            "sector": info.get("sector", "정보 없음"),
            "industry": info.get("industry", "정보 없음"),
            "recommendation": info.get("recommendationKey", "정보 없음"),
            "target_price": info.get("targetMeanPrice"),
        }

    except Exception:
        return None

@st.cache_data(ttl=300)
def get_stock_specific_news(symbol):
    try:
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        feed = feedparser.parse(rss_url)

        news = []

        for entry in feed.entries[:5]:
            news.append({
                "title": entry.title,
                "link": entry.link,
                "time": entry.get("published", "")
            })

        return news

    except Exception:
        return []

def get_metric(dataframe, ticker):
    row = dataframe[dataframe["티커"] == ticker]
    if row.empty:
        return None, None
    return row["현재가"].values[0], row["변동률(%)"].values[0]

def safe_metric(label, value, delta=None):
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
            score += 2
            reasons.append("당일 강한 상승 흐름")
        elif change >= 1:
            score += 1
            reasons.append("양호한 상승 흐름")
        elif change <= -3:
            score -= 2
            reasons.append("급락 구간")
        elif change <= -1:
            score -= 1
            reasons.append("약세 흐름")

    if volume_ratio is not None:
        if volume_ratio >= 2:
            score += 2
            reasons.append("평균 대비 거래량 급증")
        elif volume_ratio >= 1.5:
            score += 1
            reasons.append("거래량 증가")

    if qqq_change is not None and qqq_change > 0:
        score += 1
        reasons.append("나스닥 우호적")
    elif qqq_change is not None and qqq_change < -1:
        score -= 1
        reasons.append("나스닥 약세 부담")

    if vix_price is not None and vix_price > 25:
        score -= 2
        reasons.append("VIX 고위험 구간")
    elif vix_price is not None and vix_price < 18:
        score += 1
        reasons.append("VIX 안정 구간")

    if tnx_change is not None and tnx_change > 1:
        score -= 1
        reasons.append("금리 상승 부담")

    if dxy_change is not None and dxy_change > 0.5:
        score -= 1
        reasons.append("달러 강세 부담")

    tech_words = ["Technology", "Semiconductor", "Software", "Information Technology", "Electronic"]
    if any(word.lower() in f"{sector} {industry}".lower() for word in tech_words):
        if smh_change is not None and smh_change > 1:
            score += 1
            reasons.append("기술/반도체 섹터 우호")

    news_text = " ".join([n["title"] for n in stock_news]).lower()

    positive_words = ["beat", "growth", "surge", "rally", "upgrade", "outperform", "strong", "raises"]
    negative_words = ["miss", "cut", "drop", "lawsuit", "risk", "weak", "downgrade", "fall", "warning"]

    if any(w in news_text for w in positive_words):
        score += 1
        reasons.append("최근 뉴스 긍정 신호")
    if any(w in news_text for w in negative_words):
        score -= 1
        reasons.append("최근 뉴스 리스크 신호")

    if recommendation in ["buy", "strong_buy"]:
        score += 1
        reasons.append("애널리스트 컨센서스 우호")
    elif recommendation in ["sell", "underperform"]:
        score -= 2
        reasons.append("애널리스트 컨센서스 부정적")

    if score >= 4:
        final_signal = "🟢 관심 구간"
        comment = "시장 환경과 종목 모멘텀이 비교적 우호적입니다. 다만 장기 투자 관점에서는 분할 접근과 추가 확인이 필요합니다."
    elif score >= 1:
        final_signal = "🟡 관망 / 추적"
        comment = "일부 긍정 신호는 있으나 확신도는 높지 않습니다. 뉴스, 거래량, 실적 방향성을 추가 확인하는 구간입니다."
    else:
        final_signal = "🔴 리스크 경계"
        comment = "현재 데이터 기준으로는 적극 접근보다 리스크 관리와 추가 확인이 우선입니다."

    if not reasons:
        reasons.append("특이 신호 제한")

    return final_signal, comment, reasons, score

def score_candidates(dataframe, news_df, vix_price, tnx_change, smh_change):
    candidate_df = dataframe[dataframe["티커"].isin(watchlist_assets.values())].copy()

    if candidate_df.empty:
        return pd.DataFrame()

    scores = []

    for _, row in candidate_df.iterrows():
        score = 0
        reasons = []

        change = row["변동률(%)"]
        volume_ratio = row["평균거래량대비"]
        ticker = row["티커"]
        name = row["이름"]

        if pd.notna(change):
            if change >= 3:
                score += 3
                reasons.append("강한 상승률")
            elif change >= 1:
                score += 2
                reasons.append("상승 흐름")
            elif change <= -3:
                score -= 2
                reasons.append("급락 주의")
            elif change <= -1:
                score -= 1
                reasons.append("약세 흐름")

        if pd.notna(volume_ratio):
            if volume_ratio >= 2:
                score += 3
                reasons.append("거래량 급증")
            elif volume_ratio >= 1.5:
                score += 2
                reasons.append("거래량 증가")

        semi_tickers = ["NVDA", "AMD", "AVGO", "TSM", "ARM", "SOXL"]
        if ticker in semi_tickers and smh_change is not None and smh_change > 1:
            score += 1
            reasons.append("반도체 섹터 우호")

        if vix_price is not None and vix_price > 25:
            score -= 1
            reasons.append("VIX 위험 부담")

        if tnx_change is not None and tnx_change > 1:
            score -= 1
            reasons.append("금리 상승 부담")

        if not news_df.empty:
            titles = " ".join(news_df["뉴스 제목"].astype(str).tolist()).lower()
            if ticker.lower() in titles or name.lower() in titles:
                score += 1
                reasons.append("뉴스 언급")

        if score >= 4:
            signal = "🟢 관심 후보"
        elif score >= 2:
            signal = "🟡 관찰"
        elif score <= -2:
            signal = "🔴 리스크 경계"
        else:
            signal = "⚪ 관망"

        scores.append({
            "이름": name,
            "티커": ticker,
            "변동률(%)": change,
            "거래량배율": volume_ratio,
            "점수": score,
            "신호": signal,
            "근거": ", ".join(reasons) if reasons else "특이 신호 제한"
        })

    result = pd.DataFrame(scores)
    return result.sort_values("점수", ascending=False)

# =========================
# Data Load
# =========================
df = get_price_data(tickers)
news_df = get_market_news()

qqq_price, qqq_change = get_metric(df, "QQQ")
spy_price, spy_change = get_metric(df, "^GSPC")
nasdaq_price, nasdaq_change = get_metric(df, "^IXIC")
vix_price, vix_change = get_metric(df, "^VIX")
tnx_price, tnx_change = get_metric(df, "^TNX")
dxy_price, dxy_change = get_metric(df, "DX-Y.NYB")
smh_price, smh_change = get_metric(df, "SMH")
btc_price, btc_change = get_metric(df, "BTC-USD")

candidate_df = score_candidates(df, news_df, vix_price, tnx_change, smh_change)

# =========================
# Market Status
# =========================
risk_score = 0

if qqq_change is not None:
    risk_score += 1 if qqq_change > 0 else -1 if qqq_change < -1 else 0

if spy_change is not None:
    risk_score += 1 if spy_change > 0 else -1 if spy_change < -1 else 0

if vix_price is not None:
    risk_score += 1 if vix_price < 18 else -2 if vix_price > 25 else 0

if tnx_change is not None and tnx_change > 1:
    risk_score -= 1

if dxy_change is not None and dxy_change > 0.5:
    risk_score -= 1

if smh_change is not None:
    risk_score += 1 if smh_change > 1 else -1 if smh_change < -1 else 0

if risk_score >= 3:
    market_status = "Risk On"
    market_emoji = "🟢"
    market_comment = "성장주와 위험자산에 우호적인 환경입니다."
elif risk_score <= -2:
    market_status = "Risk Off"
    market_emoji = "🔴"
    market_comment = "변동성, 금리, 달러 강세 등을 경계해야 합니다."
else:
    market_status = "중립"
    market_emoji = "🟡"
    market_comment = "방향성이 뚜렷하지 않아 주요 지표 확인이 필요합니다."

def build_market_comments():
    comments = []

    if smh_change is not None:
        if smh_change >= 3:
            comments.append("🟢 반도체 강세: AI/반도체 섹터 모멘텀이 우호적입니다.")
        elif smh_change <= -2:
            comments.append("🔴 반도체 약세: 성장주와 AI 관련주에 부담 가능성이 있습니다.")
        else:
            comments.append("🟡 반도체 중립: 뚜렷한 방향성은 제한적입니다.")

    if qqq_change is not None:
        if qqq_change >= 1.5:
            comments.append("🟢 나스닥 강세: 성장주 중심 위험선호가 나타나고 있습니다.")
        elif qqq_change <= -1.5:
            comments.append("🔴 나스닥 약세: 성장주 비중 확대는 신중한 구간입니다.")
        else:
            comments.append("🟡 나스닥 중립: 방향성 확인이 필요합니다.")

    if vix_price is not None:
        if vix_price >= 25:
            comments.append("🔴 변동성 확대: 시장 불안 심리가 커진 상태입니다.")
        elif vix_price <= 18:
            comments.append("🟢 변동성 안정: 위험자산에 상대적으로 우호적입니다.")
        else:
            comments.append("🟡 변동성 보통: 급격한 공포 신호는 제한적입니다.")

    if tnx_change is not None:
        if tnx_change >= 1:
            comments.append("🔴 금리 상승 부담: 빅테크 밸류에이션에 부담 요인입니다.")
        elif tnx_change <= -1:
            comments.append("🟢 금리 하락 우호: 성장주에는 상대적으로 우호적입니다.")
        else:
            comments.append("🟡 금리 중립: 시장 영향은 제한적입니다.")

    if dxy_change is not None:
        if dxy_change >= 0.5:
            comments.append("🔴 달러 강세: 위험자산에는 부담 요인입니다.")
        elif dxy_change <= -0.5:
            comments.append("🟢 달러 약세: 위험자산 선호에 우호적일 수 있습니다.")
        else:
            comments.append("🟡 달러 중립: 달러 움직임은 제한적입니다.")

    if not comments:
        comments.append("🟡 데이터 확인 중: 시장 코멘트를 생성할 정보가 부족합니다.")

    while len(comments) < 4:
        comments.append(market_comment)

    return comments[:4]

market_comments = build_market_comments()

def build_market_briefing():
    top_news = news_df.head(3)["뉴스 제목"].tolist() if not news_df.empty else []

    top_candidate_text = "관심 후보 없음"
    if not candidate_df.empty:
        top = candidate_df.iloc[0]
        top_candidate_text = f"{top['이름']}({top['티커']}) - {top['신호']} / 근거: {top['근거']}"

    issue_lines = ""
    for title in top_news:
        issue_lines += f"- {title}\n"

    return f"""
### 오늘의 실시간 시장현황

**종합 판단:** {market_emoji} {market_status}

**핵심 지표**
- QQQ: {qqq_change}%
- 나스닥 현물: {nasdaq_change}%
- S&P500: {spy_change}%
- VIX: {vix_price}
- 10년물 금리: {tnx_price}
- DXY: {dxy_price}
- 반도체 ETF(SMH): {smh_change}%
- 비트코인: {btc_change}%

**시장 해석**
{market_comment}

**금일 주요 뉴스**
{issue_lines if issue_lines else "- 뉴스 데이터를 불러오지 못했습니다."}

**현재 데이터 기반 관심 후보**
{top_candidate_text}

**주의**
이 평가는 무료 지연 데이터와 뉴스 헤드라인 기반의 자동 해석입니다. 매수·매도 지시가 아니라 시장 관찰용 신호입니다.
"""

# =========================
# Header
# =========================
header_left, header_right = st.columns([2.25, 1.35])

with header_left:
    st.title("📈 나스닥 시황 모니터링 대시보드")
    st.caption("나스닥100 · 성장주 · 반도체 · 금리 · 달러 · 원자재 · 뉴스 기반 시장 판단 시스템")

with header_right:
    news_items = news_df.head(4)["뉴스 제목"].tolist() if not news_df.empty else ["뉴스 데이터를 불러오는 중입니다."]
    while len(news_items) < 4:
        news_items.append("뉴스 데이터를 불러오는 중입니다.")

    safe_news_items = [html.escape(str(item)) for item in news_items[:4]]
    safe_market_comments = [html.escape(str(item)) for item in market_comments[:4]]

    rolling_html = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            background: transparent;
            font-family: Arial, sans-serif;
            color: {TEXT_MAIN};
        }}

        .ticker-wrap {{
            width: 100%;
            min-height: 126px;
            background: {TICKER_BG};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 12px 14px;
            box-sizing: border-box;
            overflow: hidden;
        }}

        .top-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .status-pill {{
            display: inline-flex;
            align-items: center;
            padding: 7px 16px;
            border-radius: 999px;
            background: rgba(34,197,94,0.10);
            border: 1px solid rgba(34,197,94,0.35);
            color: #22c55e;
            font-weight: 800;
            font-size: 15px;
        }}

        .time {{
            font-size: 12px;
            color: {TEXT_SUB};
        }}

        .ticker-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            align-items: start;
        }}

        .ticker-col {{
            min-width: 0;
        }}

        .ticker-title {{
            font-size: 12px;
            color: {TEXT_SUB};
            margin-bottom: 6px;
            font-weight: 800;
        }}

        .ticker-window {{
            height: 24px;
            overflow: hidden;
            position: relative;
            border-top: 1px solid {BORDER};
            padding-top: 6px;
        }}

        .ticker-track {{
            animation: slideTicker 12s infinite;
        }}

        .ticker-item {{
            height: 24px;
            line-height: 24px;
            font-size: 13px;
            color: {TEXT_MAIN};
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        @keyframes slideTicker {{
            0% {{ transform: translateY(0px); }}
            22% {{ transform: translateY(0px); }}
            25% {{ transform: translateY(-24px); }}
            47% {{ transform: translateY(-24px); }}
            50% {{ transform: translateY(-48px); }}
            72% {{ transform: translateY(-48px); }}
            75% {{ transform: translateY(-72px); }}
            97% {{ transform: translateY(-72px); }}
            100% {{ transform: translateY(0px); }}
        }}
    </style>
    </head>
    <body>
        <div class="ticker-wrap">
            <div class="top-row">
                <div class="status-pill">{market_emoji} {market_status}</div>
                <div class="time">{get_kst_now().strftime('%H:%M:%S')} KST</div>
            </div>

            <div class="ticker-grid">
                <div class="ticker-col">
                    <div class="ticker-title">📰 주요 뉴스</div>
                    <div class="ticker-window">
                        <div class="ticker-track">
                            <div class="ticker-item">{safe_news_items[0]}</div>
                            <div class="ticker-item">{safe_news_items[1]}</div>
                            <div class="ticker-item">{safe_news_items[2]}</div>
                            <div class="ticker-item">{safe_news_items[3]}</div>
                        </div>
                    </div>
                </div>

                <div class="ticker-col">
                    <div class="ticker-title">🧠 시장 코멘트</div>
                    <div class="ticker-window">
                        <div class="ticker-track">
                            <div class="ticker-item">{safe_market_comments[0]}</div>
                            <div class="ticker-item">{safe_market_comments[1]}</div>
                            <div class="ticker-item">{safe_market_comments[2]}</div>
                            <div class="ticker-item">{safe_market_comments[3]}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    components.html(rolling_html, height=130)

if hasattr(st, "dialog"):
    @st.dialog("오늘의 실시간 시장현황")
    def market_dialog():
        st.markdown(build_market_briefing())
        st.caption(f"생성 시각: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")

    if st.button("📌 오늘의 실시간 시장현황 보기", use_container_width=True):
        market_dialog()
else:
    if st.button("📌 오늘의 실시간 시장현황 보기", use_container_width=True):
        st.session_state.show_market_briefing = not st.session_state.show_market_briefing

    if st.session_state.show_market_briefing:
        with st.expander("오늘의 실시간 시장현황", expanded=True):
            st.markdown(build_market_briefing())

# =========================
# Key Metrics
# =========================
top_metric_list = [
    ("💎 QQQ", "QQQ"),
    ("📈 나스닥", "^IXIC"),
    ("📊 S&P500", "^GSPC"),
    ("🧭 나스닥 선물", "NQ=F"),
    ("🧭 S&P 선물", "ES=F"),
    ("🛡️ VIX", "^VIX"),
    ("🏛️ 10년물 금리", "^TNX"),
    ("💵 DXY", "DX-Y.NYB"),
    ("🥇 금", "GC=F"),
    ("🛢️ 유가 WTI", "CL=F"),
    ("₿ 비트코인", "BTC-USD"),
    ("🔲 SMH", "SMH"),
    ("🧩 SOX", "^SOX"),
    ("🟩 NVDA", "NVDA"),
    ("🔴 AMD", "AMD"),
]

for row_start in range(0, len(top_metric_list), 5):
    cols = st.columns(5)
    for idx, (label, symbol) in enumerate(top_metric_list[row_start:row_start + 5]):
        price, change = get_metric(df, symbol)
        with cols[idx]:
            safe_metric(label, price, change)

st.markdown("")

# =========================
# Main Layout
# =========================
left, middle, right = st.columns([2.15, 0.9, 0.95])

with left:
    st.markdown('<div class="panel-title">📊 실시간 차트</div>', unsafe_allow_html=True)

    selected_name = st.selectbox(
        "차트 종목",
        list(tickers.keys()),
        index=0,
        label_visibility="collapsed"
    )

    selected_symbol = tickers[selected_name]
    chart_data = get_chart_data(selected_symbol, chart_period, chart_interval)

    if not chart_data.empty:
        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=chart_data.index,
                open=chart_data["Open"],
                high=chart_data["High"],
                low=chart_data["Low"],
                close=chart_data["Close"],
                name=selected_symbol
            )
        )

        fig.update_layout(
            title=f"{selected_name} ({selected_symbol})",
            template=TEMPLATE,
            height=360,
            xaxis_rangeslider_visible=False,
            margin=dict(l=12, r=12, t=42, b=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=PLOT_BG,
            font=dict(color=TEXT_MAIN)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("차트 데이터를 불러오지 못했습니다.")

    st.markdown('<div class="panel-title">🔍 종목 검색 분석</div>', unsafe_allow_html=True)

    stock_search_query = st.text_input(
        "종목명 또는 티커 검색",
        placeholder="예: 엔비디아, 솔리드파워, 로켓랩, SLDP, NVDA, SOXL",
        key="stock_search_box"
    )

    if stock_search_query:
        normalized_query = normalize_search_query(stock_search_query)
        search_results = search_yahoo_symbols(normalized_query)

        if search_results:
            option_labels = [
                f"{item['symbol']} | {item['name']} | {item['exchange']} | {item['type']}"
                for item in search_results
            ]

            selected_option = st.selectbox(
                "검색 결과 선택",
                option_labels,
                key="selected_search_result"
            )

            selected_index = option_labels.index(selected_option)
            selected_symbol_for_analysis = search_results[selected_index]["symbol"]

            stock_data = get_searched_stock_data(selected_symbol_for_analysis)
            stock_news = get_stock_specific_news(selected_symbol_for_analysis)

            if stock_data:
                signal, comment, reasons, score = analyze_searched_stock(
                    stock_data,
                    stock_news,
                    qqq_change,
                    vix_price,
                    tnx_change,
                    dxy_change,
                    smh_change
                )

                add_col, info_col = st.columns([1, 1])

                with add_col:
                    if st.button(f"⭐ {selected_symbol_for_analysis} 보유/관심종목 추가", use_container_width=True):
                        if selected_symbol_for_analysis not in st.session_state.focus_symbols:
                            st.session_state.focus_symbols.append(selected_symbol_for_analysis)
                            st.success(f"{selected_symbol_for_analysis} 추가 완료")
                        else:
                            st.info(f"{selected_symbol_for_analysis}는 이미 등록되어 있습니다.")

                with info_col:
                    st.caption("아래 보유/관심종목 모니터링 패널에서 집중 확인됩니다.")

                s1, s2, s3, s4 = st.columns(4)

                with s1:
                    st.metric("현재가", stock_data["price"], f"{stock_data['change']}%")

                with s2:
                    st.metric("거래량", f"{stock_data['volume']:,}")

                with s3:
                    if stock_data["volume_ratio"]:
                        st.metric("평균 대비 거래량", f"{stock_data['volume_ratio']}배")
                    else:
                        st.metric("평균 대비 거래량", "N/A")

                with s4:
                    st.metric("판단", signal)

                analysis_left, analysis_right = st.columns([1.4, 1])

                with analysis_left:
                    st.markdown(
                        f"""
                        <div class="panel">
                            <div class="comment-title">{stock_data['name']} ({selected_symbol_for_analysis})</div>
                            <div class="comment-desc">
                                시가총액: {stock_data['market_cap']}<br>
                                섹터: {stock_data['sector']}<br>
                                산업: {stock_data['industry']}<br>
                                애널리스트 평가: {stock_data['recommendation']}<br>
                                평균 목표가: {stock_data['target_price']}
                            </div>
                            <br>
                            <div class="comment-title">📌 종합 해석</div>
                            <div class="comment-desc">{comment}</div>
                            <div class="comment-signal">점수: {score} / 신호: {signal}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with analysis_right:
                    reason_html = ""
                    for reason in reasons:
                        reason_html += f"""
                        <div style="border-bottom:1px solid {BORDER}; padding:8px 0;">
                            • {reason}
                        </div>
                        """

                    st.markdown(
                        f"""
                        <div class="panel">
                            <div class="comment-title">📍 분석 근거</div>
                            <div class="comment-desc">
                                {reason_html}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("**최신 관련 뉴스**")

                if stock_news:
                    news_cols_for_stock = st.columns(2)
                    for idx, news in enumerate(stock_news[:4]):
                        with news_cols_for_stock[idx % 2]:
                            st.markdown(
                                f"""
                                <div class="news-card">
                                    <div class="news-title">
                                        <a href="{news['link']}" target="_blank">{news['title']}</a>
                                    </div>
                                    <div class="news-link">뉴스 보기 →</div>
                                    <div class="news-meta">{news['time']}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                else:
                    st.info("해당 종목 관련 뉴스를 불러오지 못했습니다.")

                st.caption("이 판단은 데이터 기반 시장 관찰 신호이며, 투자 권유 또는 투자 자문이 아닙니다.")

            else:
                st.warning("해당 종목 데이터를 불러오지 못했습니다. 티커를 다시 확인하세요.")

        else:
            st.warning("검색 결과가 없습니다. 한글명은 등록된 별칭만 지원하며, 영문명 또는 티커 입력이 가장 정확합니다.")

with middle:
    st.markdown('<div class="panel-title">🧭 시장 종합 판단</div>', unsafe_allow_html=True)

    vol_status = "높음" if vix_price and vix_price > 25 else "보통" if vix_price and vix_price > 18 else "낮음"
    rate_status = "높음" if tnx_change and tnx_change > 1 else "보통"
    semi_status = "강함" if smh_change and smh_change > 1 else "약함" if smh_change and smh_change < -1 else "보통"

    st.markdown(f"""
    <div class="panel">
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
        <div style="margin-top:20px; color:#38bdf8; font-size:0.88rem;">{market_comment}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="panel-title">📅 경제 이벤트 체크</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="panel">
            <div style="white-space:pre-line; font-size:0.86rem; color:{TEXT_SUB};">{economic_memo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with right:
    st.markdown('<div class="panel-title">🚨 급등락 / 거래량 감지</div>', unsafe_allow_html=True)

    alert_df = df[
        (df["변동률(%)"].notna()) &
        (
            (df["변동률(%)"].abs() >= 3) |
            (df["평균거래량대비"].fillna(0) >= 1.8)
        )
    ][["이름", "티커", "변동률(%)", "평균거래량대비"]]

    if not alert_df.empty:
        st.dataframe(
            alert_df.style.map(color_change, subset=["변동률(%)"]),
            use_container_width=True,
            hide_index=True,
            height=235
        )
    else:
        st.success("급등락/거래량 이상 신호 없음")

    st.markdown('<div class="panel-title">🎯 현재 관심 후보</div>', unsafe_allow_html=True)

    if not candidate_df.empty:
        st.dataframe(
            candidate_df.head(5)[["이름", "티커", "신호", "점수", "근거"]],
            use_container_width=True,
            hide_index=True,
            height=235
        )
    else:
        st.info("관심 후보 데이터 없음")

# =========================
# Full-width Focus Monitor
# =========================
st.markdown('<div class="panel-title">⭐ 보유/관심종목 모니터링</div>', unsafe_allow_html=True)

if st.session_state.focus_symbols:
    focus_cols = st.columns(3)

    for idx, symbol in enumerate(list(st.session_state.focus_symbols)):
        data = get_searched_stock_data(symbol)
        col = focus_cols[idx % 3]

        with col:
            if data:
                change = data["change"]
                change_class = "badge-green" if change >= 0 else "badge-red"
                volume_ratio_text = f"{data['volume_ratio']}배" if data["volume_ratio"] else "N/A"

                st.markdown(
                    f"""
                    <div class="focus-card">
                        <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
                            <div style="min-width:0; flex:1;">
                                <div class="focus-name">{data['name']} ({symbol})</div>
                                <div class="focus-sub">{data['sector']} · {data['industry']}</div>
                            </div>
                            <div style="min-width:90px; text-align:right;">
                                <div class="focus-price">{data['price']}</div>
                                <div class="{change_class}">{data['change']}%</div>
                            </div>
                        </div>
                        <div style="margin-top:13px; display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                            <div class="focus-stat">거래량<br><b>{data['volume']:,}</b></div>
                            <div class="focus-stat" style="text-align:right;">평균대비<br><b>{volume_ratio_text}</b></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(f"삭제: {symbol}", key=f"remove_{symbol}", use_container_width=True):
                    st.session_state.focus_symbols.remove(symbol)
                    st.rerun()
            else:
                st.warning(f"{symbol} 데이터를 불러오지 못했습니다.")
else:
    st.info("종목 검색 분석에서 보유/관심종목을 추가하세요.")

# =========================
# Market Table
# =========================
st.markdown('<div class="panel-title">📊 전체 시장 데이터</div>', unsafe_allow_html=True)

table_left, table_right = st.columns(2)

market_df = df[df["티커"].isin(market_assets.values())].copy()
stock_df = df[df["티커"].isin(watchlist_assets.values())].copy()

with table_left:
    st.caption("지수 / 거시 / 선물 / 원자재 / 섹터")
    st.dataframe(
        market_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=430
    )

with table_right:
    st.caption("Watchlist / 주요 관심 종목")
    st.dataframe(
        stock_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=430
    )

st.caption(f"마지막 갱신 시각: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")
st.caption("본 대시보드는 정보 제공 목적이며, 투자 조언이 아닙니다. 표시되는 관심 후보와 종목 분석은 매수·매도 추천이 아니라 시장 관찰용 신호입니다.")
st.caption("© JJS. 제작자 동의 없이 무단 배포, 복제, 수정, 재공유 및 불펌을 금지합니다.")
