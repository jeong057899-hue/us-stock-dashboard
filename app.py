import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from zoneinfo import ZoneInfo
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
.stApp {
    background: radial-gradient(circle at top left, #102033 0%, #080d16 45%, #05070d 100%);
    color: #f8fafc;
}

.block-container {
    padding-top: 1.1rem;
    padding-left: 1.6rem;
    padding-right: 1.6rem;
    max-width: 98vw !important;
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
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    min-height: 118px;
}

[data-testid="stMetricLabel"] {
    color: #cbd5e1;
    font-size: 0.82rem;
}

[data-testid="stMetricValue"] {
    font-size: 1.7rem;
    font-weight: 750;
}

[data-testid="stMetricDelta"] {
    font-size: 0.82rem;
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
    margin-bottom: 12px;
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
    min-height: 132px;
    max-height: 132px;
    overflow: hidden;
}

.news-card:hover {
    transform: translateY(-2px);
    transition: 0.2s;
    border-color: #38bdf8;
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
    margin-top: 8px;
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

.comment-row {
    border-bottom: 1px solid #26364c;
    padding: 9px 0;
}

.comment-title {
    font-weight: 800;
    font-size: 0.9rem;
}

.comment-desc {
    font-size: 0.82rem;
    color: #cbd5e1;
    line-height: 1.35;
    margin-top: 3px;
}

.comment-signal {
    font-size: 0.77rem;
    color: #38bdf8;
    margin-top: 3px;
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
# 시간
# =========================
def get_kst_now():
    return datetime.now(ZoneInfo("Asia/Seoul"))

# =========================
# Sidebar
# =========================
st.sidebar.title("⚙️ 설정")

auto_refresh = st.sidebar.checkbox("자동 갱신", value=False)
refresh_seconds = st.sidebar.selectbox("갱신 주기", [30, 60, 120, 300], index=1)

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh")

if st.sidebar.button("🔄 수동 새로고침", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

custom_symbol = st.sidebar.text_input(
    "🔎 티커 검색",
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
st.sidebar.info("무료 데이터 기반\n\nyfinance + Yahoo Finance RSS\n\n실시간 데이터는 지연될 수 있습니다.")
st.sidebar.caption(f"마지막 갱신\n{get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")

# =========================
# Tickers
# =========================
default_tickers = {
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
spy_price, spy_change = get_metric(df, "^GSPC")
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
    st.caption("성장주 · 나스닥100 · 반도체 · 금리 · 달러 · 원자재 · 뉴스 기반 실시간 시장 판단 시스템")

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
            template="plotly_dark",
            height=560,
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
# Real-time Comments
# =========================
st.markdown('<div class="panel-title">🧠 실시간 시장 코멘트</div>', unsafe_allow_html=True)

comments = []

if smh_change is not None:
    if smh_change >= 3:
        comments.append(("🟢 반도체 강세", "SMH가 강하게 상승 중입니다. AI/반도체 섹터 모멘텀이 우호적입니다.", "강세 관찰"))
    elif smh_change <= -2:
        comments.append(("🔴 반도체 약세", "SMH가 약세입니다. 성장주와 AI 관련주에 부담이 될 수 있습니다.", "주의"))
    else:
        comments.append(("🟡 반도체 중립", "반도체 섹터는 뚜렷한 방향성이 크지 않습니다.", "관망"))

if qqq_change is not None:
    if qqq_change >= 1.5:
        comments.append(("🟢 나스닥 강세", "QQQ가 강세입니다. 성장주 중심 위험선호가 나타나고 있습니다.", "강세 관찰"))
    elif qqq_change <= -1.5:
        comments.append(("🔴 나스닥 약세", "QQQ가 약세입니다. 성장주 비중 확대는 신중할 필요가 있습니다.", "리스크 경계"))
    else:
        comments.append(("🟡 나스닥 중립", "QQQ는 제한적 움직임입니다. 방향성 확인이 필요합니다.", "관망"))

if vix_price is not None:
    if vix_price >= 25:
        comments.append(("🔴 변동성 확대", "VIX가 높은 구간입니다. 시장 불안 심리가 커진 상태입니다.", "방어적 관망"))
    elif vix_price <= 18:
        comments.append(("🟢 변동성 안정", "VIX가 안정권입니다. 위험자산에 상대적으로 우호적인 환경입니다.", "우호적"))
    else:
        comments.append(("🟡 변동성 보통", "VIX는 중립 구간입니다. 급격한 공포 신호는 제한적입니다.", "관망"))

if tnx_change is not None:
    if tnx_change >= 1:
        comments.append(("🔴 금리 상승 부담", "10년물 금리가 상승 중입니다. 빅테크와 성장주 밸류에이션에 부담이 될 수 있습니다.", "주의"))
    elif tnx_change <= -1:
        comments.append(("🟢 금리 하락 우호", "10년물 금리가 하락 중입니다. 성장주에는 상대적으로 우호적입니다.", "우호적"))
    else:
        comments.append(("🟡 금리 중립", "금리 변화가 크지 않아 시장 영향은 제한적입니다.", "관망"))

if dxy_change is not None:
    if dxy_change >= 0.5:
        comments.append(("🔴 달러 강세", "달러 인덱스가 상승 중입니다. 위험자산과 신흥시장에는 부담 요인입니다.", "주의"))
    elif dxy_change <= -0.5:
        comments.append(("🟢 달러 약세", "달러가 약세입니다. 위험자산 선호에 우호적일 수 있습니다.", "우호적"))
    else:
        comments.append(("🟡 달러 중립", "달러 움직임은 제한적입니다.", "관망"))

strong_movers = df[
    (df["변동률(%)"].notna()) &
    (df["변동률(%)"].abs() >= 3)
].sort_values("변동률(%)", ascending=False)

if not strong_movers.empty:
    top_mover = strong_movers.iloc[0]
    comments.append((
        "🚨 급등락 종목 감지",
        f"{top_mover['이름']}({top_mover['티커']}) 변동률 {top_mover['변동률(%)']}% 감지.",
        "추적 필요"
    ))

comments = comments[:6]

comment_cols = st.columns(3)

for idx, (title, desc, signal) in enumerate(comments):
    with comment_cols[idx % 3]:
        st.markdown(
            f"""
            <div class="panel">
                <div class="comment-title">{title}</div>
                <div class="comment-desc">{desc}</div>
                <div class="comment-signal">판단: {signal}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# News
# =========================
news_title_col, news_btn_col = st.columns([5, 1])

with news_title_col:
    st.markdown('<div class="panel-title">📰 주요 시장 뉴스</div>', unsafe_allow_html=True)

with news_btn_col:
    if "show_all_news" not in st.session_state:
        st.session_state.show_all_news = False

    if st.button(
        "전체보기" if not st.session_state.show_all_news else "접기",
        use_container_width=True
    ):
        st.session_state.show_all_news = not st.session_state.show_all_news

news_df = get_market_news()
news_count = 8 if st.session_state.show_all_news else 4

if not news_df.empty:
    news_cols = st.columns(4)

    for idx, row in news_df.head(news_count).iterrows():
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

market_df = df.iloc[:13].copy()
stock_df = df.iloc[13:].copy()

with table_left:
    st.caption("지수 / 거시 / 선물 / 원자재 / 섹터")
    st.dataframe(
        market_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=430
    )

with table_right:
    st.caption("주요 관심 종목")
    st.dataframe(
        stock_df.style.map(color_change, subset=["변동률(%)"]),
        use_container_width=True,
        hide_index=True,
        height=430
    )

st.caption(f"마지막 갱신 시각: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")
st.caption("본 대시보드는 정보 제공 목적이며, 투자 조언이 아닙니다.")
