import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import urllib.request
import json
import streamlit.components.v1 as components

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="TickStock | Stock Analysis Portal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Badges & Layout
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .badge-good { background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
    .badge-warning { background-color: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
    .badge-danger { background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
    .disclaimer-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 12px; margin-top: 20px; font-size: 0.85rem; color: #664d03; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS: LIVE SEARCH & DATA
# ==========================================
@st.cache_data(ttl=3600)
def fetch_stock_suggestions(query):
    """Live search suggestions from Yahoo Finance."""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={encoded_query}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            quotes = data.get('quotes', [])
            stock_options = []
            for q in quotes:
                symbol = q.get('symbol', '')
                short_name = q.get('shortname', q.get('longname', symbol))
                # Prioritize Indian exchanges (.NS / .BO) or general symbols
                if symbol.endswith('.NS') or symbol.endswith('.BO') or len(symbol) < 6:
                    stock_options.append({
                        'display': f"{short_name} ({symbol})",
                        'symbol': symbol
                    })
            return stock_options
    except Exception:
        return []

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        hist = stock.history(period="6mo")
        return stock, info, hist
    except Exception:
        return None, {}, pd.DataFrame()

def calculate_pivot_points(hist):
    if hist.empty or len(hist) < 2:
        return {}
    last_row = hist.iloc[-2]
    high, low, close = last_row['High'], last_row['Low'], last_row['Close']
    pivot = (high + low + close) / 3
    return {
        "Pivot": round(pivot, 2),
        "Resistance 1 (R1)": round((2 * pivot) - low, 2),
        "Support 1 (S1)": round((2 * pivot) - high, 2),
        "Resistance 2 (R2)": round(pivot + (high - low), 2),
        "Support 2 (S2)": round(pivot - (high - low), 2),
        "Resistance 3 (R3)": round(high + 2 * (pivot - low), 2),
        "Support 3 (S3)": round(low - 2 * (high - pivot), 2),
    }

def render_tradingview_chart(symbol):
    tv_symbol = symbol if ":" in symbol else f"NSE:{symbol.replace('.NS', '')}"
    widget_html = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%">
      <div id="tradingview_chart" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": "600",
        "symbol": "{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "light",
        "style": "1",
        "locale": "in",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "details": true,
        "hotlist": true,
        "calendar": true,
        "studies": [
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies",
          "BB@tv-basicstudies",
          "SuperTrend@tv-basicstudies"
        ],
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(widget_html, height=610, scrolling=False)

def get_smart_badge(metric_name, value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A", "badge-warning"
    if metric_name == "P/E Ratio":
        return (f"{value} (Attractive)", "badge-good") if value < 15 else ((f"{value} (High)", "badge-danger") if value > 35 else (f"{value} (Fair)", "badge-warning"))
    elif metric_name == "ROE":
        v = value * 100 if value < 1 else value
        return (f"{v:.2f}% (Healthy)", "badge-good") if v > 15 else (f"{v:.2f}% (Low)", "badge-danger")
    elif metric_name == "Debt to Equity":
        return (f"{value:.2f} (Safe)", "badge-good") if value < 0.5 else (f"{value:.2f} (High Risk)", "badge-danger")
    return str(value), "badge-warning"

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("📊 TickStock Portal")
st.sidebar.markdown("---")
app_mode = st.sidebar.radio("Navigation", ["Dashboard & Technicals", "Fundamental Analysis", "Stock Scanners"])
st.sidebar.markdown("---")

# Global Stock Search in Sidebar
user_query = st.sidebar.text_input("🔍 शेयर का नाम टाइप करें (जैसे: RELIANCE, TCS):", "RELIANCE.NS")
selected_ticker = user_query.upper().strip()

if len(user_query.strip()) >= 2:
    suggestions = fetch_stock_suggestions(user_query)
    if suggestions:
        options_map = {item['display']: item['symbol'] for item in suggestions}
        chosen_display = st.sidebar.selectbox("मिलते-जुले शेयर्स की सूची:", list(options_map.keys()))
        selected_ticker = options_map[chosen_display]

stock_obj, info, hist_data = fetch_stock_data(selected_ticker)

# ==========================================
# MAIN VIEWS
# ==========================================
if app_mode == "Dashboard & Technicals":
    st.title("📈 TickStock: Interactive Chart & Technicals")
    st.subheader(f"विश्लेषण: {info.get('longName', selected_ticker)} ({selected_ticker})")
    
    c1, c2, c3, c4 = st.columns(4)
    cp = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    with c1: st.metric("वर्तमान भाव (Current Price)", f"₹ {cp}" if cp != 'N/A' else 'N/A')
    with c2: st.metric("52-सप्ताह का उच्च (High)", f"₹ {info.get('fiftyTwoWeekHigh', 'N/A')}")
    with c3: st.metric("52-सप्ताह का निम्न (Low)", f"₹ {info.get('fiftyTwoWeekLow', 'N/A')}")
    with c4: st.metric("मार्केट कैप (Market Cap)", f"₹ {info.get('marketCap', 0):,}" if info.get('marketCap') else 'N/A')

    st.markdown("---")
    st.markdown("### 📊 ट्रेडिंगव्यू लाइव चार्ट (RSI, MACD, Moving Averages)")
    st.info("💡 नीचे दिए गए चार्ट के अंदर से आप टाइमफ्रेम (1M, 5M, 1D, 1W) और इंडिकेटर बदल सकते हैं।")
    render_tradingview_chart(selected_ticker)
    
    st.markdown("---")
    st.markdown("### 📐 सपोर्ट और रेजिस्टेंस लेवल्स (Pivot Points)")
    pivots = calculate_pivot_points(hist_data)
    if pivots:
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            st.markdown(f"**पिवट पॉइंट (P):** `{pivots.get('Pivot')}`")
            st.markdown(f"**सपोर्ट 1 (S1):** `{pivots.get('Support 1 (S1)')}`")
        with pc2:
            st.markdown(f"**रेजिस्टेंस 1 (R1):** `{pivots.get('Resistance 1 (R1)')}`")
            st.markdown(f"**सपोर्ट 2 (S2):** `{pivots.get('Support 2 (S2)')}`")
        with pc3:
            st.markdown(f"**रेजिस्टेंस 2 (R2):** `{pivots.get('Resistance 2 (R2)')}`")
            st.markdown(f"**सपोर्ट 3 (S3):** `{pivots.get('Support 3 (S3)')}`")

elif app_mode == "Fundamental Analysis":
    st.title("📑 फंडामेंटल एनालिसिस और हेल्थ इंडिकेटर्स")
    st.subheader(f"{info.get('longName', selected_ticker)} ({selected_ticker})")
    
    pe = info.get('trailingPE', info.get('forwardPE', None))
    roe = info.get('returnOnEquity', None)
    roce = info.get('returnOnCapitalEmployed', None)
    debt = info.get('debtToEquity', None)
    eps = info.get('trailingEps', None)
    
    metrics = [
        ("Market Capitalization", f"₹ {info.get('marketCap', 0):,}" if info.get('marketCap') else "N/A", "badge-warning", "कंपनी का कुल बाजार मूल्य"),
        ("P/E Ratio", get_smart_badge("P/E Ratio", pe)[0], get_smart_badge("P/E Ratio", pe)[1], "अर्निंग्स के मुकाबले शेयर का भाव"),
        ("Return on Equity (ROE)", get_smart_badge("ROE", roe)[0], get_smart_badge("ROE", roe)[1], "इक्विटी पर मिलने वाला रिटर्न (>15% अच्छा)"),
        ("Debt to Equity", get_smart_badge("Debt to Equity", debt)[0], get_smart_badge("Debt to Equity", debt)[1], "कंपनी पर कर्ज का स्तर (<0.5 सुरक्षित)"),
        ("Earnings Per Share (EPS)", f"₹ {eps:.2f}" if eps else "N/A", "badge-warning", "प्रति शेयर मुनाफा")
    ]
    
    for m, val, status, hint in metrics:
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1: st.markdown(f"**{m}**")
        with col2: st.markdown(f'<span class="{status}">{val}</span>', unsafe_allow_html=True)
        with col3: st.caption(hint)
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)

elif app_mode == "Stock Scanners":
    st.title("🔍 स्टॉक स्कैनर और स्क्रीनर")
    st.write("बाजार के चुनिंदा शेयरों को फिल्टर करके बेहतरीन विकल्प ढूंढें।")
    
    scanner_type = st.selectbox("स्कैनर रणनीति चुनें:", [
        "ब्रेकआउट / 52-वीक हाई के करीब शेयर्स",
        "अंडरवैल्यूड शेयर्स (कम P/E + हाई ROE)",
        "लो डेट (कम कर्ज वाली कंपनियां)"
    ])
    
    sample_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "SBIN.NS", "TATAMOTORS.NS"]
    
    if st.button("स्कैन शुरू करें", type="primary"):
        with st.spinner("स्कैनिंग जारी है..."):
            res = []
            for sym in sample_stocks:
                _, inf, _ = fetch_stock_data(sym)
                price = inf.get('currentPrice', inf.get('regularMarketPrice', 0))
                h52 = inf.get('fiftyTwoWeekHigh', 0)
                pe = inf.get('trailingPE', 20)
                roe = inf.get('returnOnEquity', 0)
                if roe and roe < 1: roe *= 100
                de = inf.get('debtToEquity', 1)
                
                match = False
                if "52-वीक" in scanner_type and price and h52 and price >= 0.90 * h52: match = True
                elif "अंडरवैल्यूड" in scanner_type and pe and pe < 25 and roe and roe > 12: match = True
                elif "लो डेट" in scanner_type and de is not None and de < 0.5: match = True
                
                if match:
                    res.append({"Symbol": sym, "Name": inf.get('longName', sym), "Price": price, "P/E": round(pe, 2) if pe else 'N/A', "ROE %": round(roe, 2) if roe else 'N/A'})
            
            if res:
                st.success(f"{len(res)} शेयर्स मिले!")
                st.dataframe(pd.DataFrame(res), use_container_width=True)
            else:
                st.info("वर्तमान फिल्टर के आधार पर कोई स्टॉक नहीं मिला।")

# ==========================================
# SEBI COMPLIANCE & LEGAL DISCLAIMER FOOTER
# ==========================================
st.markdown("---")
st.markdown("""
<div class="disclaimer-box">
  <b>⚠️ कानूनी और अनुपालन सूचना (Legal & Compliance Disclaimer):</b><br>
  TickStock पोर्टल केवल शैक्षणिक और सूचना के उद्देश्य से वित्तीय डेटा और चार्ट प्रदान करता है। 
  हम <b>SEBI-रजिस्टर्ड रिसर्च एनालिस्ट या निवेश सलाहकार नहीं हैं</b>। यहाँ दी गई किसी भी जानकारी को खरीद/बिक्री की सीधी सलाह न समझा जाए। 
  शेयर बाजार में निवेश बाजार जोखिमों के अधीन है। किसी भी निवेश से पहले अपने प्रमाणित वित्तीय सलाहकार से सलाह जरूर लें।
</div>
""", unsafe_allow_html=True)

st.markdown("<p style='text-align: center; color: gray; font-size: 0.8rem;'>© 2026 TickStock Portal. All rights reserved.</p>", unsafe_allow_html=True)
