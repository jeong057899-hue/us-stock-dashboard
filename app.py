import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import feedparser
from streamlit_autorefresh import st_autorefresh

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="미국 주식 시장 인텔리전스 대시보드",
    page_icon="📈",
    layout="wide"
)

# =========================
# 사이드바
# =========================
st.sidebar.header("⚙️ 설정")

auto_refresh = st.sidebar.checkbox("자동 갱신 켜기", value=False)

refresh_seconds = st.sidebar.selectbox(
    "자동 갱신 주기",
    [30, 60, 120, 300],
    index=1
)

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh")

if st.sidebar.button("🔄 수동 새로고침"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("무료 데이터 기반: yfinance + Yahoo Finance RSS")

# =========================
# 제목
# =========================
st.title("📈 미국 주식 시장 인텔리전스 대시보드")
st.caption("미국 성장주 / 나스닥100 / 반도체 / 거시경제 중심 개인 투자 대시보드")

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

# =========================
# 검색 기능
# =========================
st.subheader("🔎 원하는 주식 / ETF / 지수 검색")

custom_symbol = st.text_input(
    "티커 입력 예: AAPL, NVDA, QQQ, SPY, SOXL, TQQQ, PLTR, ^VIX, ^IXIC",
    value=""
).upper().strip()

tickers = default_tickers.copy()

if custom_symbol:
    tickers[f"검색 종목: {custom_symbol}"] = custom_symbol

# =========================
# 데이터 수집
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

df = get_price_data(tickers)

def get_metric(dataframe, ticker):
    row = dataframe[dataframe["티커"] == ticker]

    if row.empty:
        return None, None

    price = row["현재가"].values[0]
    change = row["변동률(%)"].values[0]

    return price, change

# =========================
# 핵심 시장 카드
# =========================
st.subheader("📌 핵심 시장 지표")

qqq_price, qqq_change = get_metric(df, "QQQ")
nvda_price, nvda_change = get_metric(df, "NVDA")
vix_price, vix_change = get_metric(df, "^VIX")
tnx_price, tnx_change = get_metric(df, "^TNX")
dxy_price, dxy_change = get_metric(df, "DX-Y.NYB")
smh_price, smh_change = get_metric(df, "SMH")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("QQQ", qqq_price, f"{qqq_change}%")

with col2:
    st.metric("NVDA", nvda_price, f"{nvda_change}%")

with col3:
    st.metric("VIX", vix_price, f"{vix_change}%")

with col4:
    st.metric("10년물", tnx_price, f"{tnx_change}%")

with col5:
    st.metric("DXY", dxy_price, f"{dxy_change}%")

with col6:
    st.metric("SMH", smh_price, f"{smh_change}%")

# =========================
# 시장 상태 판단
# =========================
st.subheader("🧭 시장 상태 종합 판단")

spy_price, spy_change = get_metric(df, "SPY")

risk_score = 0

if qqq_change is not None:
    if qqq_change > 0:
        risk_score += 1
    elif qqq_change < -1:
        risk_score -= 1

if spy_change is not None:
    if spy_change > 0:
        risk_score += 1
    elif spy_change < -1:
        risk_score -= 1

if vix_price is not None:
    if vix_price < 18:
        risk_score += 1
    elif vix_price > 25:
        risk_score -= 2

if tnx_change is not None and tnx_change > 1:
    risk_score -= 1

if dxy_change is not None and dxy_change > 0.5:
    risk_score -= 1

if smh_change is not None:
    if smh_change > 1:
        risk_score += 1
    elif smh_change < -1:
        risk_score -= 1

if risk_score >= 3:
    market_status = "🟢 Risk On"
    market_comment = "성장주와 위험자산에 우호적인 분위기입니다."
elif risk_score <= -2:
    market_status = "🔴 Risk Off"
    market_comment = "변동성, 금리, 달러 강세 등으로 방어적 접근이 필요합니다."
else:
    market_status = "🟡 중립"
    market_comment = "방향성이 뚜렷하지 않아 주요 지표 확인이 필요합니다."

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("시장 상태", market_status)

with m2:
    st.metric("변동성 위험", "높음" if vix_price and vix_price > 25 else "보통" if vix_price and vix_price > 18 else "낮음")

with m3:
    st.metric("금리 부담", "높음" if tnx_change and tnx_change > 1 else "보통")

with m4:
    st.metric("반도체 모멘텀", "강함" if smh_change and smh_change > 1 else "약함" if smh_change and smh_change < -1 else "보통")

st.info(market_comment)

# =========================
# 주요 시장 테이블
# =========================
st.subheader("📊 주요 지수 / 관심 종목 / 검색 종목")

def color_change(value):
    if pd.isna(value):
        return ""
    if value > 0:
        return "color: #00c853"
    elif value < 0:
        return "color: #ff5252"
    return ""

styled_df = df.style.applymap(
    color_change,
    subset=["변동률(%)"]
)

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)

# =========================
# 차트
# =========================
st.subheader("📈 실시간형 차트 모니터링")

selected_name = st.selectbox(
    "차트로 볼 종목을 선택하세요",
    list(tickers.keys()),
    index=1
)

selected_symbol = tickers[selected_name]

chart_period = st.selectbox(
    "조회 기간",
    ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
    index=0
)

chart_interval = st.selectbox(
    "차트 간격",
    ["1m", "5m", "15m", "30m", "1h", "1d"],
    index=0
)

@st.cache_data(ttl=60)
def get_chart_data(symbol, period, interval):
    stock = yf.Ticker(symbol)
    return stock.history(period=period, interval=interval)

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
        title=f"{selected_name} ({selected_symbol}) 차트",
        xaxis_title="시간",
        yaxis_title="가격",
        template="plotly_dark",
        height=550,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("차트 데이터를 불러오지 못했습니다. 티커가 정확한지 확인해 주세요.")

# =========================
# 급등락 / 이상 움직임 감지
# =========================
st.subheader("🚨 급등락 / 이상 움직임 감지")

alert_df = df[
    (df["변동률(%)"].notna()) &
    ((df["변동률(%)"] >= 3) | (df["변동률(%)"] <= -3))
]

if not alert_df.empty:
    st.warning("변동률 ±3% 이상 종목이 감지되었습니다.")
    st.dataframe(alert_df, use_container_width=True, hide_index=True)
else:
    st.success("현재 ±3% 이상 급등락 종목은 없습니다.")

# =========================
# 뉴스
# =========================
st.subheader("📰 미국 증시 주요 뉴스")

@st.cache_data(ttl=300)
def get_market_news():
    rss_url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US"

    feed = feedparser.parse(rss_url)
    news_list = []

    bullish_keywords = [
        "surge", "gain", "rise", "beat", "record", "growth",
        "bull", "rally", "strong", "optimism"
    ]

    bearish_keywords = [
        "fall", "drop", "fear", "cut", "war", "inflation",
        "selloff", "recession", "decline", "weak", "risk"
    ]

    fed_keywords = ["fed", "powell", "rate", "fomc", "yield"]
    ai_keywords = ["ai", "nvidia", "semiconductor", "chip", "amd", "broadcom"]
    macro_keywords = ["inflation", "cpi", "ppi", "jobs", "unemployment", "gdp"]

    for entry in feed.entries[:15]:
        title = entry.title
        link = entry.link
        published = entry.get("published", "")
        lower_title = title.lower()

        sentiment = "🟡 중립"

        if any(word in lower_title for word in bullish_keywords):
            sentiment = "🟢 긍정 가능"

        if any(word in lower_title for word in bearish_keywords):
            sentiment = "🔴 부정 가능"

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

news_df = get_market_news()

if not news_df.empty:
    for _, row in news_df.iterrows():
        st.markdown(
            f"""
            **{row['분위기']} | {row['분류']}**  
            [{row['뉴스 제목']}]({row['링크']})  
            <span style='color:gray; font-size:13px;'>{row['시간']}</span>
            ---
            """,
            unsafe_allow_html=True
        )
else:
    st.warning("뉴스 데이터를 불러오지 못했습니다.")

# =========================
# 간단 시장 브리핑
# =========================
st.subheader("📝 자동 시장 브리핑")

briefing = f"""
현재 시장 상태는 **{market_status}** 입니다.

- QQQ 변동률: {qqq_change}%
- NVDA 변동률: {nvda_change}%
- VIX: {vix_price}
- 미국 10년물 금리: {tnx_price}
- 달러 인덱스: {dxy_price}
- 반도체 ETF(SMH): {smh_change}%

해석: {market_comment}
"""

st.markdown(briefing)

# =========================
# 갱신 시각
# =========================
st.caption(
    f"마지막 갱신 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)