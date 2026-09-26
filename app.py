import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="TickStock | Pro Stock Analysis",
    page_icon="📈",
    layout="wide"
)

# CSS to hide sidebar and style the clean top-to-bottom UI
st.markdown("""
    <style>
    [data-testid="stSidebar"], section[data-testid="stSidebar"], div[data-testid="collapsedControl"] {
        display: none !important;
        width: 0px !important;
    }
    
    .main { background-color: #0f172a; color: #f8fafc; }
    .stApp { background-color: #0f172a; }
    
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
    }
    
    .badge-good { background-color: #065f46; color: #34d399; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-warning { background-color: #78350f; color: #fbbf24; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-danger { background-color: #7f1d1d; color: #f87171; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    
    .disclaimer-box {
        background-color: #1e293b;
        border-left: 4px solid #f59e0b;
        padding: 15px;
        border-radius: 8px;
        margin-top: 30px;
        font-size: 0.82rem;
        color: #94a3b8;
    }
    
    h1, h2, h3 { color: #f8fafc !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        hist = stock.history(period="6mo")
        return info, hist
    except Exception as e:
        return {}, pd.DataFrame()

def calculate_pivot_points(hist):
    if hist.empty or len(hist) < 2:
        return {}
    last_row = hist.iloc[-2]
    high, low, close = last_row['High'], last_row['Low'], last_row['Close']
    pivot = (high + low + close) / 3
    return {
        "Pivot": round(pivot, 2),
        "R1": round((2 * pivot) - low, 2),
        "S1": round((2 * pivot) - high, 2),
        "R2": round(pivot + (high - low), 2),
        "S2": round(pivot - (high - low), 2),
        "R3": round(high + 2 * (pivot - low), 2),
        "S3": round(low - 2 * (high - high), 2),
    }

def render_tradingview_chart(symbol):
    clean_sym = symbol.replace(".NS", "").upper()
    tv_symbol = f"NSE:{clean_sym}"
    
    widget_html = f"""
    <div class="tradingview-widget-container" style="height:550px;width:100%">
      <div id="tradingview_chart" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": "550",
        "symbol": "{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "in",
        "toolbar_bg": "#1e293b",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "details": false,
        "hotlist": false,
        "calendar": false,
        "studies": [
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies",
          "SuperTrend@tv-basicstudies",
          "BB@tv-basicstudies"
        ],
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(widget_html, height=560, scrolling=False)

def get_smart_badge(metric_name, value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A", "badge-warning"
    if metric_name == "P/E Ratio":
        if value < 15: return f"{value:.2f} (Attractive)", "badge-good"
        elif 15 <= value <= 30: return f"{value:.2f} (Fair)", "badge-warning"
        else: return f"{value:.2f} (High)", "badge-danger"
    elif metric_name == "ROE":
        v = value * 100 if value < 1 else value
        if v > 15: return f"{v:.2f}% (Healthy)", "badge-good"
        elif v >= 10: return f"{v:.2f}% (Moderate)", "badge-warning"
        else: return f"{v:.2f}% (Low)", "badge-danger"
    elif metric_name == "Debt to Equity":
        if value < 0.5: return f"{value:.2f} (Safe)", "badge-good"
        elif value <= 1.5: return f"{value:.2f} (Moderate)", "badge-warning"
        else: return f"{value:.2f} (High Risk)", "badge-danger"
    return str(value), "badge-warning"

# ==========================================
# TOP-TO-BOTTOM LAYOUT
# ==========================================
st.markdown("## ⚡ TickStock Pro Portal")
st.markdown("---")

col_s1, col_s2 = st.columns(2)
with col_s1:
    popular_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "TATAMOTORS.NS", "SBIN.NS", "MARINE.NS"]
    selected_ticker = st.selectbox("🔍 लोकप्रिय शेयर चुनें (Popular Stock)", popular_stocks)
with col_s2:
    custom_input = st.text_input("या शेयर का टिकर लिखें (Custom Ticker)", placeholder="e.g. RELIANCE.NS")

ticker_symbol = custom_input.upper().strip() if custom_input else selected_ticker

st.markdown("---")

app_mode = st.radio(
    "मेनु चुनें (Navigation)", 
    ["📈 लाइव चार्ट और टेक्निकल (Live Chart & Technicals)", "📑 फंडामेंटल हेल्थ (Fundamental Health)", "🔍 स्मार्ट स्कैनर (Smart Scanners)"], 
    horizontal=True
)

st.markdown("---")

info, hist_data = fetch_stock_data(ticker_symbol)

# ==========================================
# MAIN VIEWS
# ==========================================

if app_mode == "📈 लाइव चार्ट और टेक्निकल (Live Chart & Technicals)":
    st.subheader(f"विश्लेषण (Analyzing): {info.get('longName', ticker_symbol)}")
    curr_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><h4>लाइव भाव (Price)</h4><h3>₹ {curr_price}</h3></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h4>52W हाई (High)</h4><h3>₹ {info.get('fiftyTwoWeekHigh', 'N/A')}</h3></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h4>52W लो (Low)</h4><h3>₹ {info.get('fiftyTwoWeekLow', 'N/A')}</h3></div>", unsafe_allow_html=True)
    with c4:
        mcap = info.get('marketCap', 0)
        st.markdown(f"<div class='metric-card'><h4>मार्केट कैप</h4><h3>₹ {mcap:,}</h3></div>" if mcap else "<div class='metric-card'><h4>मार्केट कैप</h4><h3>N/A</h3></div>", unsafe_allow_html=True)

    st.markdown("### 📊 ट्रेडिंगव्यू एडवांस्ड लाइव चार्ट")
    render_tradingview_chart(ticker_symbol)
    
    st.markdown("### 📐 सपोर्ट और रेजिस्टेंस (Pivot Points)")
    pivots = calculate_pivot_points(hist_data)
    if pivots:
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(f"<div class='metric-card'><b>पिवट (Pivot):</b> {pivots['Pivot']}<br><b>सपोर्ट 1:</b> {pivots['S1']}</div>", unsafe_allow_html=True)
        with p2:
            st.markdown(f"<div class='metric-card'><b>रेजिस्टेंस 1:</b> {pivots['R1']}<br><b>सपोर्ट 2:</b> {pivots['S2']}</div>", unsafe_allow_html=True)
        with p3:
            st.markdown(f"<div class='metric-card'><b>रेजिस्टेंस 2:</b> {pivots['R2']}<br><b>रेजिस्टेंस 3:</b> {pivots['R3']}</div>", unsafe_allow_html=True)

elif app_mode == "📑 फंडामेंटल हेल्थ (Fundamental Health)":
    st.subheader(f"कंपनी की वित्तीय सेहत: {info.get('longName', ticker_symbol)}")
    
    pe = info.get('trailingPE', None)
    roe = info.get('returnOnEquity', None)
    de = info.get('debtToEquity', None)
    
    fc1, fc2 = st.columns(2)
    with fc1:
        pe_val, pe_badge = get_smart_badge("P/E Ratio", pe)
        st.markdown(f"<div class='metric-card'><b>P/E रेश्यो:</b> <span class='{pe_badge}'>{pe_val}</span></div>", unsafe_allow_html=True)
    with fc2:
        roe_val, roe_badge = get_smart_badge("ROE", roe)
        st.markdown(f"<div class='metric-card'><b>ROE (रिटर्न ऑन इक्विटी):</b> <span class='{roe_badge}'>{roe_val}</span></div>", unsafe_allow_html=True)
        
    de_val, de_badge = get_smart_badge("Debt to Equity", de)
    st.markdown(f"<div class='metric-card'><b>डेट टू इक्विटी (कर्ज):</b> <span class='{de_badge}'>{de_val}</span></div>", unsafe_allow_html=True)

elif app_mode == "🔍 स्मार्ट स्कैनर (Smart Scanners)":
    st.subheader("🔍 प्रो स्टॉक स्कैनर और फिल्टर")
    
    strategy = st.selectbox(
        "स्कैनिंग रणनीति चुनें (Select Strategy)", 
        [
            "ब्रेकआउट / 52-वीक हाई के करीब (Breakout Stocks)", 
            "कम कर्ज वाली कंपनियां (Low Debt Companies)", 
            "अंडरवैल्यूड स्टॉक्स - कम P/E + हाई ROE (Undervalued Stocks)",
            "हाई ग्रोथ / मजबूत रिटर्न वाली कंपनियां (High Growth)"
        ]
    )
    
    # Custom search bar inside scanner to search specific stock directly
    scan_search = st.text_input("या विशेष स्टॉक सर्च करें (Search Stock in Scanner)", placeholder="e.g. TCS.NS, INFY.NS")

    if st.button("🚀 स्कैन शुरू करें (Run Scan)", type="primary"):
        # Expanded stock universe for reliable scanning results
        universe = [
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", 
            "TATAMOTORS.NS", "SBIN.NS", "ICICIBANK.NS", "BHARTIARTL.NS", 
            "LICI.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "SUNPHARMA.NS"
        ]
        
        if scan_search:
            universe = [scan_search.upper().strip()]

        with st.spinner("बाजार से डेटा स्कैन किया जा रहा है... कृपया प्रतीक्षा करें"):
            res = []
            for s in universe:
                try:
                    inf = yf.Ticker(s).info
                    name = inf.get('longName', s)
                    price = inf.get('currentPrice', inf.get('regularMarketPrice', 0))
                    h52 = inf.get('fiftyTwoWeekHigh', 0)
                    pe = inf.get('trailingPE', 30)
                    roe = inf.get('returnOnEquity', 0)
                    if roe and roe < 1: roe = roe * 100
                    de = inf.get('debtToEquity', 1)
                    if de is None: de = 0

                    match = False
                    if strategy == "ब्रेकआउट / 52-वीक हाई के करीब (Breakout Stocks)":
                        if h52 and price and (price >= 0.85 * h52):
                            match = True
                    elif strategy == "कम कर्ज वाली कंपनियां (Low Debt Companies)":
                        if de < 0.8:
                            match = True
                    elif strategy == "अंडरवैल्यूड स्टॉक्स - कम P/E + हाई ROE (Undervalued Stocks)":
                        if pe and pe < 25 and roe and roe > 10:
                            match = True
                    elif strategy == "हाई ग्रोथ / मजबूत रिटर्न वाली कंपनियां (High Growth)":
                        if roe and roe > 15:
                            match = True

                    if match:
                        res.append({
                            "टिकर (Symbol)": s,
                            "कंपनी का नाम (Company)": name,
                            "भाव (Price)": price,
                            "P/E": round(pe, 2) if pe else 'N/A',
                            "ROE (%)": round(roe, 2) if roe else 'N/A',
                            "कर्ज (Debt/Eq)": round(de, 2) if de is not None else 'N/A',
                            "52W हाई": h52
                        })
                except Exception:
                    continue

            if res:
                st.success(f"कुल {len(res)} शेयर इस शर्त को पूरा करते हैं!")
                st.dataframe(pd.DataFrame(res), use_container_width=True)
            else:
                st.info("वर्तमान में इस फिल्टर से मेल खाते शेयर नहीं मिले। कृपया दूसरा फिल्टर या स्टॉक आज़माएं।")

# ==========================================
# DISCLAIMER FOOTER
# ==========================================
st.markdown("""
<div class="disclaimer-box">
  <b>⚠️ कानूनी सूचना (Disclaimer):</b> TickStock केवल शैक्षिक और सूचना के उद्देश्य से बनाया गया पोर्टल है। हम SEBI-पंजीकृत सलाहकार नहीं हैं। निवेश करने से पहले अपने वित्तीय सलाहकार से सलाह जरूर लें।
</div>
""", unsafe_allow_html=True)
