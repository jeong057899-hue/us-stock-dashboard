import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import feedparser
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="미국 주식 시장 인텔리전스 대시보드",
    page_icon="📈",
    layout="wide"
)

# =========================
# CSS
# =========================
st.markdown("""
<style>
:root {
    --bg: #080d16;
    --panel: #0f1724;
    --panel2: #111c2d;
    --border: #233247;
    --text: #f8fafc;
    --muted: #94a3b8;
    --green: #22c55e;
    --red: #ef4444;
    --blue: #38bdf8;
    --yellow: #f59e0b;
}

.stApp {
    background: radial-gradient(circle at top left, #102033 0%, #080d16 45%, #05070d 100%);
    color: var(--text);
}

.block-container {
    padding-top: 1.2rem;
    padding-left: 1.7rem;
    padding-right: 1.7rem;
    max-width: 1500px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1524 0%, #07101d 100%);
    border-right: 1px solid #1e293b;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #111827, #0b1322);
    border: 1px solid #253449;
    padding: 16px 18px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.22);
}

[data-testid="stMetricLabel"] {
    color: #cbd5e1;
    font-size: 0.85rem;
}

[data-testid="stMetricValue"] {
    font-size: 1.85rem;
    font-weight: 750;
}

[data-testid="stMetricDelta"] {
    font-size: 0.85rem;
}

.panel {
    background: linear-gradient(145deg, rgba(17,24,39,0.96), rgba(9,15,27,0.96));
    border: 1px solid #26364c;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 26px rgba(0,0,0,0.25);
    margin-bottom: 16px;
}

.panel-title {
    font-size: 1.08rem;
    font-weight: 800;
    margin-bottom: 14px;
    color: #f8fafc;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 7px 16px;
    border-radius: 999px;
    background: rgba(34,197,94,0.10);
    border: 1px solid rgba(34,197,94,0.35);
    color: #86efac;
    font-weight: 800;
    font-size: 1.1rem;
}

.news-card {
    background: linear-gradient(145deg, #111827, #0a1220);
    border: 1px solid #26364c;
    border-radius: 15px;
    padding: 14px;
    min-height: 142px;
    max-height: 142px;
    overflow: hidden;
}

.news-meta {
    font-size: 0.74rem;
    color: #94a3b8;
    margin-bottom: 8px;
}

.news-title {
    font-size: 0.9rem;
    line-height: 1.35;
    font-weight: 700;
}

.news-title a {
    color: #e5e7eb !important;
    text-decoration: none;
}

.news-title a:hover {
    color: #38bdf8 !important;
    text-decoration: underline;
}

.news-link {
    font-size: 0.8rem;
    color: #38bdf8;
    margin-top: 9px;
}

.badge-green {
    color: #22c55e;
    font-weight: 800;
}

.badge-red {
    color: #ef4444;
    font-weight: 800;
}

.badge-yellow {
    color: #f59e0b;
    font-weight: 800;
}

hr {
    border-color: #1e293b;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #26364c;
    border-radius: 14px;
    overflow: hidden;
}

.stSelectbox > div > div,
.stTextInput > div > div > input {
    background-color: #0f172a !important;
    border: 1px solid #26364c !important;
    color: #f8fafc !important;
}

button {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Sidebar
# =========================
st.sidebar.title("⚙️ 설정")

auto_refresh = st.sidebar.toggle("자동 갱신", value=False)
refresh_seconds = st.sidebar.selectbox("갱신 주기", [30, 60, 120, 300], index=1)

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh")

if st.sidebar.button("🔄 수동 새로고침", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

custom_symbol = st.sidebar.text_input(
    "🔎 티커 검색",
    placeholder="예: NVDA, QQQ, SOXL, PLTR, ^VIX"
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
st.sidebar.info("무료 데이터 기반\n\nyfinance + Yahoo Finance RSS\n\n실시간 데이터는 지연될 수 있습니다.")
st.sidebar.caption(f"마지막 갱신\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# =========================
# Tickers
# =========================
default_tickers = {
    "S&P500 ETF": "SPY",
    "NASDAQ100 ETF": "QQQ",
    "DOW ETF": "DIA",
    "Russell2000 ETF": "IWM",
    "VIX": "^VIX",
    "미국 10년물 금리": "^TNX",
    "달러 인덱스": "DX-Y.NYB",
    "금": "GC=F",
    "유가 WTI": "CL=F",
    "반도체 ETF": "SMH",
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
}

tickers = default_tickers.copy()
if custom_symbol:
    tickers[f"검색 종목: {custom_symbol}"] = custom_symbol

# =========================
# Data functions
# =========================
@st.cache_data(ttl=60)
def get_price_data(ticker_dict):
    rows = []

    for name, symbol in ticker_dict.items():
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="2d")

            if len(hist) >= 2:
                prev_close = hist["Close"].iloc[-2]
                current_price = hist["Close"].iloc[-1]
                change_pct = ((current_price - prev_close) / prev_close) * 100
                volume = hist["Volume"].iloc[-1]

                rows.append({
                    "이름": name,
                    "티커": symbol,
                    "현재가": round(current_price, 2),
                    "변동률(%)": round(change_pct, 2),
                    "거래량": int(volume)
                })
            else:
                rows.append({
                    "이름": name,
                    "티커": symbol,
                    "현재가": None,
                    "변동률(%)": None,
                    "거래량": None
                })

        except Exception:
            rows.append({
                "이름": name,
                "티커": symbol,
                "현재가": None,
                "변동률(%)": None,
                "거래량": None
            })

    return pd.DataFrame(rows)

@st.cache_data(ttl=60)
def get_chart_data(symbol, period, interval):
    stock = yf.Ticker(symbol)
    return stock.history(period=period, interval=interval)

@st.cache_data(ttl=300)
def get_market_news():
    rss_url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US"
    feed = feedparser.parse(rss_url)

    bullish_keywords = ["surge", "gain", "rise", "beat", "record", "growth", "bull", "rally", "strong", "optimism"]
    bearish_keywords = ["fall", "drop", "fear", "cut", "war", "inflation", "selloff", "recession", "decline", "weak", "risk"]
    fed_keywords = ["fed", "powell", "rate", "fomc", "yield"]
    ai_keywords = ["ai", "nvidia", "semiconductor", "chip", "amd", "broadcom"]
    macro_keywords = ["inflation", "cpi", "ppi", "jobs", "unemployment", "gdp"]

    news_list = []

    for entry in feed.entries[:8]:
        title = entry.title
        link = entry.link
        published = entry.get("published", "")
        lower_title = title.lower()

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

        news_list.append({
            "분위기": sentiment,
            "분류": category,
            "뉴스 제목": title,
            "링크": link,
            "시간": published
        })

    return pd.DataFrame(news_list)

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

# =========================
# Load Data
# =========================
df = get_price_data(tickers)

qqq_price, qqq_change = get_metric(df, "QQQ")
spy_price, spy_change = get_metric(df, "SPY")
nvda_price, nvda_change = get_metric(df, "NVDA")
vix_price, vix_change = get_metric(df, "^VIX")
tnx_price, tnx_change = get_metric(df, "^TNX")
dxy_price, dxy_change = get_metric(df, "DX-Y.NYB")
smh_price, smh_change = get_metric(df, "SMH")

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

# =========================
# Header
# =========================
header_left, header_right = st.columns([3.2, 1])

with header_left:
    st.title("📈 미국 주식 시장 인텔리전스 대시보드")
    st.caption("성장주 · 나스닥100 · 반도체 · 금리 · 달러 · 뉴스 기반 실시간 시장 판단 시스템")

with header_right:
    st.markdown(
        f"""
        <div style="text-align:right; padding-top:10px;">
            <div style="font-size:0.85rem; color:#94a3b8;">시장 상태</div>
            <div class="status-pill">{market_emoji} {market_status}</div>
            <div style="font-size:0.8rem; color:#94a3b8; margin-top:10px;">{market_comment}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Key Metrics
# =========================
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    safe_metric("💎 QQQ", qqq_price, qqq_change)
with k2:
    safe_metric("🟩 NVDA", nvda_price, nvda_change)
with k3:
    safe_metric("🛡️ VIX", vix_price, vix_change)
with k4:
    safe_metric("🏛️ 10년물 금리", tnx_price, tnx_change)
with k5:
    safe_metric("💵 DXY", dxy_price, dxy_change)
with k6:
    safe_metric("🔲 SMH", smh_price, smh_change)

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
        index=1,
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
            template="plotly_dark",
            height=500,
            xaxis_rangeslider_visible=False,
            margin=dict(l=12, r=12, t=42, b=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,13,22,0.95)",
            font=dict(color="#e5e7eb")
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("차트 데이터를 불러오지 못했습니다.")

with middle:
    st.markdown('<div class="panel-title">🧭 시장 종합 판단</div>', unsafe_allow_html=True)

    vol_status = "높음" if vix_price and vix_price > 25 else "보통" if vix_price and vix_price > 18 else "낮음"
    rate_status = "높음" if tnx_change and tnx_change > 1 else "보통"
    semi_status = "강함" if smh_change and smh_change > 1 else "약함" if smh_change and smh_change < -1 else "보통"

    st.markdown(f"""
    <div class="panel">
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #26364c; padding-bottom:12px;">
            <span>종합 판단</span><span class="badge-green">{market_emoji} {market_status}</span>
        </div>
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #26364c; padding:13px 0;">
            <span>변동성 위험</span><span class="badge-yellow">{vol_status} (VIX {vix_price})</span>
        </div>
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #26364c; padding:13px 0;">
            <span>금리 부담</span><span class="badge-yellow">{rate_status} (10Y {tnx_price})</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding-top:13px;">
            <span>반도체 모멘텀</span><span class="badge-green">{semi_status} (SMH {smh_change}%)</span>
        </div>
        <div style="margin-top:20px; color:#93c5fd; font-size:0.88rem;">{market_comment}</div>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel-title">🚨 급등락 감지</div>', unsafe_allow_html=True)

    alert_df = df[
        (df["변동률(%)"].notna()) &
        ((df["변동률(%)"] >= 3) | (df["변동률(%)"] <= -3))
    ][["이름", "티커", "변동률(%)"]]

    if not alert_df.empty:
        st.dataframe(
            alert_df.style.map(color_change, subset=["변동률(%)"]),
            use_container_width=True,
            hide_index=True,
            height=255
        )
    else:
        st.success("±3% 이상 급등락 없음")

    st.markdown('<div class="panel-title">📝 요약</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="panel">
        <div>QQQ: <b>{qqq_change}%</b></div>
        <div>NVDA: <b>{nvda_change}%</b></div>
        <div>VIX: <b>{vix_price}</b></div>
        <div>10Y: <b>{tnx_price}</b></div>
        <div>DXY: <b>{dxy_price}</b></div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# News
# =========================
st.markdown('<div class="panel-title">📰 주요 시장 뉴스</div>', unsafe_allow_html=True)

news_df = get_market_news()

if not news_df.empty:
    news_cols = st.columns(4)

    for idx, row in news_df.head(8).iterrows():
        with news_cols[idx % 4]:
            st.markdown(
                f"""
                <div class="news-card">
                    <div class="news-meta">{row['분위기']} | {row['분류']}</div>
                    <div class="news-title">
                        <a href="{row['링크']}" target="_blank">{row['뉴스 제목']}</a>
                    </div>
                    <div class="news-link">더 보기 →</div>
                    <div class="news-meta">{row['시간']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    st.warning("뉴스 데이터를 불러오지 못했습니다.")

# =========================
# Market Table
# =========================
st.markdown('<div class="panel-title">📊 전체 시장 데이터</div>', unsafe_allow_html=True)

table_left, table_right = st.columns(2)

market_df = df.iloc[:10].copy()
stock_df = df.iloc[10:].copy()

with table_left:
    st.caption("지수 / 거시 / 섹터")
    st.dataframe(
        market_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=300
    )

with table_right:
    st.caption("주요 관심 종목")
    st.dataframe(
        stock_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=300
    )

st.caption(f"마지막 갱신 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("본 대시보드는 정보 제공 목적이며, 투자 조언이 아닙니다.")
