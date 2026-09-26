import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="TickStock - शेयर बाज़ार विश्लेषण",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .metric-card {
        background-color: #1e222d;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2a2e39;
        margin-bottom: 10px;
    }
    .stSelectbox label, .stTextInput label, .stRadio label {
        color: #d1d4dc !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Robust Indian Stock Symbol Resolver (Mapping + Fallback)
# ---------------------------------------------------------
POPULAR_SYMBOL_MAP = {
    "HIMADRI": "HSCL",
    "HIMADRI SPECIALITY": "HSCL",
    "TEXMACO": "TEXRAIL",
    "TEXMACO RAIL": "TEXRAIL",
    "TEXMACO INFRA": "TEXINFRA",
    "RELIANCE": "RELIANCE",
    "TCS": "TCS",
    "ZOMATO": "ZOMATO",
    "HDFCBANK": "HDFCBANK",
    "INFY": "INFY",
    "TATAMOTORS": "TATAMOTORS",
    "TATASTEEL": "TATASTEEL",
    "SBIN": "SBIN",
    "BHARTIARTL": "BHARTIARTL",
    "ITC": "ITC",
    "REFEX": "REFEX",
    "ADANIENT": "ADANIENT",
    "SUZLON": "SUZLON"
}

@st.cache_data(ttl=86400)
def search_symbol(query):
    query_clean = query.strip().upper()
    
    # 1. Direct/Partial Match in Dictionary
    if query_clean in POPULAR_SYMBOL_MAP:
        base_symbol = POPULAR_SYMBOL_MAP[query_clean]
        return f"{base_symbol}.NS", base_symbol
    
    for key, val in POPULAR_SYMBOL_MAP.items():
        if key in query_clean:
            return f"{val}.NS", val

    # 2. Yahoo Finance Search API Fallback
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_clean}&quotesCount=5"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            for q in quotes:
                symbol = q.get('symbol', '')
                if symbol.endswith('.NS') or symbol.endswith('.BO'):
                    tradingview_sym = symbol.replace('.NS', '').replace('.BO', '')
                    return symbol, tradingview_sym
    except Exception:
        pass

    # 3. Default formatting
    clean_sym = query_clean.replace('.NS', '').replace('.BO', '')
    return f"{clean_sym}.NS", clean_sym

# Helper function to fetch stock data safely
@st.cache_data(ttl=300)
def fetch_stock_data(yf_symbol):
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        history = ticker.history(period="1y")
        if history.empty:
            alt_symbol = yf_symbol.replace('.NS', '.BO')
            ticker = yf.Ticker(alt_symbol)
            history = ticker.history(period="1y")
            info = ticker.info
            if not history.empty:
                yf_symbol = alt_symbol

        return ticker, info, history, yf_symbol
    except Exception:
        return None, {}, pd.DataFrame(), yf_symbol

# ---------------------------------------------------------
# Sidebar & Navigation
# ---------------------------------------------------------
st.title("📈 TickStock - शेयर बाज़ार विश्लेषण")

st.markdown("### 🔍 शेयर का नाम या टिकर लिखें")
user_input = st.text_input(
    "उदाहरण: Himadri, Reliance, TCS, Texmaco, Zomato",
    value="Himadri",
    key="stock_search_input"
)

yf_symbol, tv_symbol = search_symbol(user_input)

st.markdown("### 📌 मेनू चुनें (Navigation)")
nav_option = st.radio(
    "Navigation Options",
    options=[
        "📈 लाइव चार्ट और टेक्निकल (Live Chart & Technicals)",
        "📊 फंडामेंटल हेल्थ (Fundamental Health)",
        "🔍 स्मार्ट स्कैनर (Smart Scanners)"
    ],
    label_visibility="collapsed"
)

ticker_obj, stock_info, hist_df, resolved_yf_symbol = fetch_stock_data(yf_symbol)

# ---------------------------------------------------------
# PAGE 1: LIVE CHART & TECHNICALS
# ---------------------------------------------------------
if "लाइव चार्ट और टेक्निकल" in nav_option:
    st.subheader(f"📊 {tv_symbol} - बाज़ार सारांश")

    if not hist_df.empty:
        curr_price = stock_info.get('regularMarketPrice') or hist_df['Close'].iloc[-1]
        prev_close = stock_info.get('regularMarketPreviousClose') or (hist_df['Close'].iloc[-2] if len(hist_df)>1 else curr_price)
        day_high = stock_info.get('dayHigh') or hist_df['High'].iloc[-1]
        day_low = stock_info.get('dayLow') or hist_df['Low'].iloc[-1]
        price_change = curr_price - prev_close
        pct_change = (price_change / prev_close) * 100

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ताज़ा भाव (Close)", f"₹{curr_price:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
        with col2:
            st.metric("आज का हाई (High)", f"₹{day_high:.2f}")
        with col3:
            st.metric("आज का लो (Low)", f"₹{day_low:.2f}")

        # Support & Resistance (Pivot Levels)
        pivot = (day_high + day_low + curr_price) / 3
        r1 = (2 * pivot) - day_low
        s1 = (2 * pivot) - day_high
        r2 = pivot + (day_high - day_low)
        s2 = pivot - (day_high - day_low)

        st.markdown("---")
        st.subheader("🎯 सपोर्ट और रेजिस्टेंस (Pivot Levels)")
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("रेजिस्टेंस 2 (R2)", f"₹{r2:.2f}")
        sc2.metric("रेजिस्टेंस 1 (R1)", f"₹{r1:.2f}")
        sc3.metric("सपोर्ट 1 (S1)", f"₹{s1:.2f}")
        sc4.metric("सपोर्ट 2 (S2)", f"₹{s2:.2f}")

    else:
        st.warning(f"⚠️ {user_input} का डेटा प्राप्त नहीं हो सका। कृपया सही नाम दर्ज करें।")

    st.markdown("---")
    st.subheader(f"📉 ट्रेडिंगव्यू रियल-टाइम चार्ट (NSE:{tv_symbol})")

    tv_widget_html = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%;">
      <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "NSE:{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "in",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart",
        "studies": [
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies"
        ]
      }});
      </script>
    </div>
    """
    components.html(tv_widget_html, height=620)

# ---------------------------------------------------------
# PAGE 2: FUNDAMENTAL HEALTH
# ---------------------------------------------------------
elif "फंडामेंटल हेल्थ" in nav_option:
    st.subheader(f"📑 {tv_symbol} - फंडामेंटल और वित्तीय हेल्थ")

    if stock_info and len(stock_info) > 5:
        col1, col2, col3, col4 = st.columns(4)
        
        pe_ratio = stock_info.get('trailingPE', 'N/A')
        pb_ratio = stock_info.get('priceToBook', 'N/A')
        roe = stock_info.get('returnOnEquity', 'N/A')
        debt_to_equity = stock_info.get('debtToEquity', 'N/A')
        market_cap = stock_info.get('marketCap', 0)
        
        roe_str = f"{roe*100:.2f}%" if isinstance(roe, (int, float)) else "N/A"
        mcap_cr = f"₹{market_cap/1e7:.2f} Cr" if market_cap else "N/A"

        col1.metric("मार्केट कैप (Market Cap)", mcap_cr)
        col2.metric("P/E अनुपात (PE Ratio)", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else pe_ratio)
        col3.metric("P/B अनुपात (PB Ratio)", f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else pb_ratio)
        col4.metric("ROE (%)", roe_str)

        st.markdown("---")
        st.markdown("### 📊 विस्तृत वित्तीय मेट्रिक्स")
        ratios_data = {
            "मेट्रिक (Metric)": ["डेब्ट टू इक्विटी (Debt/Equity)", "डिविडेंड यील्ड (Dividend Yield)", "प्रॉफिट मार्जिन (Profit Margin)", "52-हफ़्ते का हाई", "52-हफ़्ते का लो"],
            "मान (Value)": [
                f"{debt_to_equity}" if debt_to_equity != 'N/A' else "कम / नगण्य",
                f"{(stock_info.get('dividendYield', 0) or 0)*100:.2f}%",
                f"{(stock_info.get('profitMargins', 0) or 0)*100:.2f}%",
                f"₹{stock_info.get('fiftyTwoWeekHigh', 'N/A')}",
                f"₹{stock_info.get('fiftyTwoWeekLow', 'N/A')}"
            ]
        }
        st.table(pd.DataFrame(ratios_data))

        st.markdown("### 🏢 कंपनी परिचय")
        st.write(stock_info.get('longBusinessSummary', 'कंपनी की जानकारी उपलब्ध नहीं है।'))
    else:
        st.error(f"❌ {tv_symbol} के फंडामेंटल डेटा लोड नहीं हो पाए।")

# ---------------------------------------------------------
# PAGE 3: SMART SCANNERS
# ---------------------------------------------------------
elif "स्मार्ट स्कैनर" in nav_option:
    st.subheader("🔍 प्रो स्टॉक स्कैनर और स्क्रीनर्स")

    scan_strategy = st.selectbox(
        "स्कैनिंग रणनीति चुनें",
        options=[
            "ब्रेकआउट / 52-वीक हाई के करीब",
            "अंडरवैल्यूड (कम P/E + उच्च ROE)",
            "हाई ग्रोथ / हाई P/E स्टॉक्स (High P/E & Growth)",
            "कम कर्ज वाली सुरक्षित कंपनियां"
        ]
    )

    st.markdown("---")
    st.markdown(f"#### 🎯 परिणाम: **{scan_strategy}**")

    WATCHLIST = ["HSCL.NS", "TEXRAIL.NS", "RELIANCE.NS", "TCS.NS", "ZOMATO.NS", "INFY.NS", "REFEX.NS", "SUZLON.NS"]
    scanner_results = []
    
    with st.spinner("स्कैनिंग जारी है..."):
        for sym in WATCHLIST:
            try:
                t = yf.Ticker(sym)
                inf = t.info
                hist = t.history(period="1y")
                if hist.empty:
                    continue

                c_price = hist['Close'].iloc[-1]
                high_52 = inf.get('fiftyTwoWeekHigh') or hist['High'].max()
                pe = inf.get('trailingPE', 999)
                roe = (inf.get('returnOnEquity') or 0) * 100
                debt_eq = inf.get('debtToEquity', 100)
                clean_name = sym.replace('.NS', '')

                if scan_strategy == "ब्रेकआउट / 52-वीक हाई के करीब":
                    if c_price >= high_52 * 0.90:
                        scanner_results.append({
                            "शेयर (Symbol)": clean_name,
                            "करंट प्राइस": f"₹{c_price:.2f}",
                            "52W High": f"₹{high_52:.2f}",
                            "दूरी (%)": f"{((high_52 - c_price)/high_52)*100:.1f}% नीचे",
                            "सिग्नल": "🔥 ब्रेकआउट के करीब"
                        })

                elif scan_strategy == "अंडरवैल्यूड (कम P/E + उच्च ROE)":
                    if pe < 30 and roe > 12:
                        scanner_results.append({
                            "शेयर (Symbol)": clean_name,
                            "करंट प्राइस": f"₹{c_price:.2f}",
                            "P/E Ratio": f"{pe:.2f}",
                            "ROE (%)": f"{roe:.1f}%",
                            "सिग्नल": "✅ वैल्यू स्टॉक"
                        })

                elif scan_strategy == "हाई ग्रोथ / हाई P/E स्टॉक्स (High P/E & Growth)":
                    if pe >= 30:
                        scanner_results.append({
                            "शेयर (Symbol)": clean_name,
                            "करंट प्राइस": f"₹{c_price:.2f}",
                            "P/E Ratio": f"{pe:.2f}",
                            "सिग्नल": "🚀 हाई मोमेंटम"
                        })

                elif scan_strategy == "कम कर्ज वाली सुरक्षित कंपनियां":
                    if debt_eq < 50:
                        scanner_results.append({
                            "शेयर (Symbol)": clean_name,
                            "करंट प्राइस": f"₹{c_price:.2f}",
                            "Debt/Equity": f"{debt_eq:.2f}",
                            "सिग्नल": "🛡️ कम रिस्क"
                        })
            except Exception:
                continue

    if scanner_results:
        st.dataframe(pd.DataFrame(scanner_results), use_container_width=True)
    else:
        st.info("इस फ़िल्टर मानदंड के अनुसार वर्तमान में कोई शेयर मैच नहीं हुआ।")

st.markdown("---")
st.caption("⚠️ **अस्वीकरण:** यह ऐप केवल शैक्षणिक और अध्ययन उद्देश्यों के लिए है।")
        
