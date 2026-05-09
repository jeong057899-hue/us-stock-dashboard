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

st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}
section[data-testid="stSidebar"] {
    background-color: #0f172a;
}
.card {
    background: linear-gradient(145deg, #111827, #0b1220);
    border: 1px solid #263244;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 0 18px rgba(0,0,0,0.25);
}
.news-card {
    background-color: #111827;
    border: 1px solid #263244;
    border-radius: 14px;
    padding: 14px;
    height: 145px;
    overflow: hidden;
}
.news-title {
    font-size: 14px;
    font-weight: 600;
    line-height: 1.35;
}
.news-meta {
    color: #9ca3af;
    font-size: 12px;
}
.compact-table {
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 사이드바
# =========================
st.sidebar.title("⚙️ 설정")

auto_refresh = st.sidebar.checkbox("자동 갱신", value=False)
refresh_seconds = st.sidebar.selectbox("갱신 주기", [30, 60, 120, 300], index=1)

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh")

if st.sidebar.button("🔄 수동 새로고침"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

custom_symbol = st.sidebar.text_input(
    "🔎 티커 검색",
    placeholder="예: NVDA, QQQ, SOXL, PLTR, ^VIX"
).upper().strip()

st.sidebar.markdown("---")

chart_period = st.sidebar.selectbox(
    "차트 기간",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=0
)

chart_interval = st.sidebar.selectbox(
    "차트 간격",
    ["1m", "5m", "15m", "30m", "1h", "1d"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("무료 데이터 기반")
st.sidebar.caption("yfinance + Yahoo Finance RSS")
st.sidebar.caption("실시간 데이터는 지연될 수 있습니다.")

# =========================
# 기본 티커
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
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
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
# 데이터 함수
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
    else:
        if delta is None or pd.isna(delta):
            st.metric(label, value)
        else:
            st.metric(label, value, f"{delta}%")

def color_change(value):
    if pd.isna(value):
        return ""
    if value > 0:
        return "color: #00c853"
    elif value < 0:
        return "color: #ff5252"
    return ""

# =========================
# 데이터 로드
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
# 시장 상태 판단
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
    market_status = "🟢 Risk On"
    market_comment = "성장주와 위험자산에 우호적인 환경입니다."
elif risk_score <= -2:
    market_status = "🔴 Risk Off"
    market_comment = "변동성, 금리, 달러 강세 등을 경계해야 합니다."
else:
    market_status = "🟡 중립"
    market_comment = "방향성이 뚜렷하지 않아 주요 지표 확인이 필요합니다."

# =========================
# 헤더
# =========================
header_left, header_right = st.columns([3, 1])

with header_left:
    st.title("📈 미국 주식 시장 인텔리전스 대시보드")
    st.caption("성장주 · 나스닥100 · 반도체 · 금리 · 달러 · 뉴스 기반 시장 판단 시스템")

with header_right:
    st.metric("시장 상태", market_status)
    st.caption(market_comment)

# =========================
# 핵심 카드
# =========================
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    safe_metric("QQQ", qqq_price, qqq_change)
with c2:
    safe_metric("NVDA", nvda_price, nvda_change)
with c3:
    safe_metric("VIX", vix_price, vix_change)
with c4:
    safe_metric("10년물 금리", tnx_price, tnx_change)
with c5:
    safe_metric("DXY", dxy_price, dxy_change)
with c6:
    safe_metric("SMH", smh_price, smh_change)

st.markdown("---")

# =========================
# 메인 영역
# =========================
main_left, main_mid, main_right = st.columns([2.2, 0.9, 0.95])

with main_left:
    chart_header_left, chart_header_right = st.columns([1, 1])

    with chart_header_left:
        st.subheader("📊 실시간형 차트")

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
            height=520,
            xaxis_rangeslider_visible=False,
            margin=dict(l=15, r=15, t=45, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("차트 데이터를 불러오지 못했습니다.")

with main_mid:
    st.subheader("🧭 시장 판단")

    st.metric("종합 판단", market_status)
    st.metric(
        "변동성 위험",
        "높음" if vix_price and vix_price > 25 else "보통" if vix_price and vix_price > 18 else "낮음",
        f"VIX {vix_price}"
    )
    st.metric(
        "금리 부담",
        "높음" if tnx_change and tnx_change > 1 else "보통",
        f"10Y {tnx_price}"
    )
    st.metric(
        "반도체 모멘텀",
        "강함" if smh_change and smh_change > 1 else "약함" if smh_change and smh_change < -1 else "보통",
        f"SMH {smh_change}%"
    )

    st.info(market_comment)

with main_right:
    st.subheader("🚨 급등락 감지")

    alert_df = df[
        (df["변동률(%)"].notna()) &
        ((df["변동률(%)"] >= 3) | (df["변동률(%)"] <= -3))
    ][["이름", "티커", "변동률(%)"]]

    if not alert_df.empty:
        st.dataframe(alert_df, use_container_width=True, hide_index=True, height=300)
    else:
        st.success("±3% 이상 급등락 없음")

    st.subheader("📝 요약")
    st.markdown(
        f"""
        - QQQ: **{qqq_change}%**
        - NVDA: **{nvda_change}%**
        - VIX: **{vix_price}**
        - 10Y: **{tnx_price}**
        - DXY: **{dxy_price}**
        """
    )

# =========================
# 뉴스 compact
# =========================
st.subheader("📰 주요 시장 뉴스")

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
                    <br>
                    <div class="news-meta">{row['시간']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    st.warning("뉴스 데이터를 불러오지 못했습니다.")

# =========================
# 전체 시장 데이터 compact
# =========================
st.subheader("📊 전체 시장 데이터")

table_left, table_right = st.columns(2)

market_df = df.iloc[:10].copy()
stock_df = df.iloc[10:].copy()

with table_left:
    st.caption("지수 / 거시 / 섹터")
    st.dataframe(
        market_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=310
    )

with table_right:
    st.caption("주요 관심 종목")
    st.dataframe(
        stock_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=310
    )

st.caption(f"마지막 갱신 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
