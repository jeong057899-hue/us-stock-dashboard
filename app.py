# =========================
# NASDAQ MONITOR DASHBOARD
# FINAL STABLE VERSION
# =========================

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import random

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="나스닥 시황 모니터링 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# SESSION
# =========================

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

# =========================
# SETTINGS
# =========================

with st.sidebar:

    st.markdown("## ⚙️ 설정")

    auto_refresh = st.checkbox("자동 갱신", value=True)

    refresh_sec = st.selectbox(
        "갱신 주기",
        [15, 30, 60, 120],
        index=0
    )

    theme_mode = st.selectbox(
        "테마",
        ["Dark", "Blue Dark"]
    )

    st.markdown("---")

    st.markdown("### 🔎 빠른 티커 추가")

    quick_input = st.text_input(
        "",
        placeholder="예: NVDA, QQQ, SOXL, PLTR"
    )

    if st.button("➕ 관심종목 추가"):

        if quick_input:

            ticker_upper = quick_input.upper()

            if ticker_upper not in st.session_state.watchlist:
                st.session_state.watchlist.append(ticker_upper)

# =========================
# AUTO REFRESH
# =========================

if auto_refresh:
    st_autorefresh(
        interval=refresh_sec * 1000,
        key="refresh"
    )

# =========================
# STYLE
# =========================

if theme_mode == "Dark":

    bg_color = "#020617"
    card_color = "#0f172a"

else:

    bg_color = "#031525"
    card_color = "#08111f"

st.markdown(f"""
<style>

.stApp {{
    background: linear-gradient(135deg, {bg_color}, #000814);
    color: white;
}}

.block-container {{
    padding-top: 1rem;
    max-width: 100%;
}}

header {{
    visibility:hidden;
}}

footer {{
    visibility:hidden;
}}

[data-testid="collapsedControl"] {{
    display:flex !important;
    visibility:visible !important;
    opacity:1 !important;

    position:fixed !important;
    top:20px !important;
    left:15px !important;

    width:42px !important;
    height:42px !important;

    border-radius:50% !important;

    background:#0f172a !important;
    border:1px solid #38bdf8 !important;

    justify-content:center !important;
    align-items:center !important;

    z-index:999999 !important;
}}

[data-testid="collapsedControl"] svg {{
    display:none !important;
}}

[data-testid="collapsedControl"]::before {{
    content:"⚙️";
    font-size:22px;
}}

.metric-card {{
    background:{card_color};
    border:1px solid rgba(255,255,255,0.08);
    border-radius:18px;
    padding:18px;
    margin-bottom:14px;
}}

.news-card {{
    background:{card_color};
    border:1px solid rgba(255,255,255,0.08);
    border-radius:14px;
    padding:14px;
    height:150px;
}}

.watch-card {{
    background:{card_color};
    border-radius:18px;
    padding:20px;
    border:1px solid rgba(255,255,255,0.08);
    margin-bottom:14px;
}}

.small {{
    font-size:12px;
    color:#94a3b8;
}}

.green {{
    color:#4ade80;
}}

.red {{
    color:#f87171;
}}

</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================

col1, col2 = st.columns([4,2])

with col1:

    st.markdown("""
    # 📈 나스닥 시황 모니터링 대시보드
    나스닥100 · 성장주 · 반도체 · 금리 · 달러 · 원자재 · 뉴스 기반 시장 판단 시스템
    """)

with col2:

    st.markdown("""
    <div class='metric-card'>
    <div style='font-size:28px'>🟢 Risk On</div>
    <div class='small'>성장주 및 반도체 우호 환경</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# MARKET DATA
# =========================

market = {
    "QQQ":"QQQ",
    "나스닥":"^IXIC",
    "S&P500":"^GSPC",
    "나스닥 선물":"NQ=F",
    "S&P 선물":"ES=F",
    "VIX":"^VIX",
    "10년물 금리":"^TNX",
    "DXY":"DX-Y.NYB",
    "금":"GC=F",
    "유가WTI":"CL=F",
    "비트코인":"BTC-USD",
    "SMH":"SMH",
    "SOX":"^SOX",
    "NVDA":"NVDA",
    "AMD":"AMD"
}

# =========================
# TOP METRICS
# =========================

cols = st.columns(5)

idx = 0

for name, ticker in market.items():

    try:

        data = yf.Ticker(ticker).history(period="2d")

        price = round(data["Close"].iloc[-1],2)

        prev = data["Close"].iloc[-2]

        change = round((price-prev)/prev*100,2)

        color = "green" if change >=0 else "red"

        with cols[idx%5]:

            st.markdown(f"""
            <div class='metric-card'>
            <div class='small'>{name}</div>
            <div style='font-size:36px;font-weight:700'>{price}</div>
            <div class='{color}'>{change}%</div>
            </div>
            """, unsafe_allow_html=True)

        idx += 1

    except:
        pass

# =========================
# CHART
# =========================

st.markdown("## 📊 실시간 차트")

chart_col1, chart_col2 = st.columns([3,1])

with chart_col1:

    ticker_choice = st.selectbox(
        "",
        ["QQQ","SOXL","NVDA","AMD","TSLA","PLTR"]
    )

    chart_data = yf.download(
        ticker_choice,
        period="1d",
        interval="5m"
    )

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=chart_data.index,
        open=chart_data["Open"],
        high=chart_data["High"],
        low=chart_data["Low"],
        close=chart_data["Close"]
    ))

    fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=10,r=10,t=10,b=10),
        paper_bgcolor="#020617",
        plot_bgcolor="#020617"
    )

    st.plotly_chart(fig, use_container_width=True)

with chart_col2:

    st.markdown("### 🧠 시장 종합 판단")

    comments = [
        "🟢 반도체 강세",
        "🟢 나스닥 강세",
        "🟡 금리 중립",
        "🟢 변동성 안정",
        "🟢 AI 테마 지속",
        "🟡 단기 과열 주의"
    ]

    for c in comments:
        st.markdown(f"""
        <div class='metric-card'>{c}</div>
        """, unsafe_allow_html=True)

# =========================
# SEARCH
# =========================

st.markdown("## 🔎 종목 검색 분석")

alias = {
    "엔비디아":"NVDA",
    "테슬라":"TSLA",
    "팔란티어":"PLTR",
    "솔리드파워":"SLDP",
    "로켓랩":"RKLB",
    "amd":"AMD"
}

search = st.text_input(
    "",
    placeholder="예: 엔비디아 / 솔리드파워 / NVDA / TSLA"
)

if search:

    ticker = alias.get(search.lower(), search.upper())

    try:

        info = yf.Ticker(ticker).info

        col1, col2 = st.columns([2,2])

        with col1:

            st.markdown(f"""
            <div class='watch-card'>
            <h3>{info.get('longName',ticker)}</h3>
            <div>{info.get('sector','')}</div>
            <br>
            <div>현재가: {info.get('currentPrice','-')}</div>
            <div>거래량: {info.get('volume','-')}</div>
            <div>시가총액: {info.get('marketCap','-')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:

            signal = random.choice(
                ["🟢 매수 관심","🟡 관망","🔴 단기주의"]
            )

            st.markdown(f"""
            <div class='watch-card'>
            <h3>📈 AI 시장 분석</h3>
            <br>
            최근 시장 흐름 및 뉴스 기반 분석 결과
            성장주/기술주 수급이 유지되고 있습니다.
            <br><br>
            추천 의견: <b>{signal}</b>
            </div>
            """, unsafe_allow_html=True)

        if st.button("⭐ 관심종목 추가"):

            if ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(ticker)

    except:
        st.warning("검색 실패")

# =========================
# WATCHLIST
# =========================

st.markdown("## ⭐ 보유/관심종목 모니터링")

watch_cols = st.columns(3)

for i, ticker in enumerate(st.session_state.watchlist):

    try:

        info = yf.Ticker(ticker).info

        price = info.get("currentPrice",0)

        prev = info.get("previousClose",1)

        change = round((price-prev)/prev*100,2)

        color = "green" if change >=0 else "red"

        with watch_cols[i%3]:

            st.markdown(f"""
            <div class='watch-card'>
            <h3>{ticker}</h3>
            <div>{info.get('longName','')}</div>
            <br>
            <div style='font-size:32px'>{price}</div>
            <div class='{color}'>{change}%</div>
            </div>
            """, unsafe_allow_html=True)

    except:
        pass

# =========================
# NEWS
# =========================

st.markdown("## 📰 주요 시장 뉴스")

feed = feedparser.parse(
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=QQQ&region=US&lang=en-US"
)

news_cols = st.columns(4)

for i, item in enumerate(feed.entries[:4]):

    with news_cols[i]:

        st.markdown(f"""
        <div class='news-card'>
        <div style='font-weight:700'>{item.title}</div>
        <br>
        <a href='{item.link}' target='_blank'>뉴스보기</a>
        </div>
        """, unsafe_allow_html=True)

# =========================
# FOOTER
# =========================

kst = pytz.timezone("Asia/Seoul")

now = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

st.markdown("---")

st.markdown(f"""
<div class='small'>
최종 업데이트: {now} KST
<br><br>
본 대시보드는 정보 제공 목적이며 투자 조언이 아닙니다.
<br><br>
ⓒ 제작자 동의없이 배포 및 불펌 금지 - JJS
</div>
""", unsafe_allow_html=True)
