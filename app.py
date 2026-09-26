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

st.markdown("""
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    section[data-testid="stSidebar"] { display: none !important; }
    
    .main { background-color: #0b0f19; color: #f8fafc; padding-top: 0px !important; }
    .stApp { background-color: #0b0f19; }
    
    /* Groww Style Top Bar */
    .groww-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        margin-bottom: 15px;
    }
    
    /* Groww Style Banner Card */
    .groww-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    
    .metric-card {
        background-color: #161e2e;
        border: 1px solid #26334d;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        margin-bottom: 12px;
    }
    
    .stock-card {
        background-color: #161e2e;
        border: 1px solid #26334d;
        padding: 14px;
        border-radius: 12px;
        text-align: center;
        transition: 0.2s;
    }
    .stock-card:hover {
        border-color: #00d09c;
    }
    
    .badge-good { background-color: #065f46; color: #34d399; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-warning { background-color: #78350f; color: #fbbf24; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    .badge-danger { background-color: #7f1d1d; color: #f87171; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
    
    .disclaimer-box {
        background-color: #161e2e;
        border-left: 4px solid #00d09c;
        padding: 15px;
        border-radius: 8px;
        margin-top: 30px;
        font-size: 0.82rem;
        color: #94a3b8;
    }
    
    h1, h2, h3, h4 { color: #f8fafc !important; }
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
    <div class="tradingview-widget-container" style="height:500px;width:100%">
      <div id="tradingview_chart" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": "500",
        "symbol": "{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "in",
        "toolbar_bg": "#161e2e",
        "enable_publishing": false,
        "allow_symbol_change": false,
        "details": false,
        "hotlist": false,
        "calendar": false,
        "studies": [
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies",
          "SuperTrend@tv-basicstudies"
        ],
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(widget_html, height=510, scrolling=False)

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
# GROWW STYLE TOP BAR
# ==========================================
col_logo, col_search_icon, col_profile = st.columns([6, 1, 1])

with col_logo:
    st.markdown("<h3 style='margin:0; color:#00d09c;'>🟢 TickStock</h3>", unsafe_allow_html=True)

with col_profile:
    with st.popover("👤"):
        st.write("### यूजर प्रोफाइल")
        uploaded_file = st.file_uploader("फोटो लगाएं", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None:
            st.success("फोटो अपडेट हो गई!")
        st.markdown("---")
        st.markdown("🛠️ **सेटिंग्स**")
        st.markdown("👤 **स्टेटस:** गेस्ट यूजर")
        if st.button("शेयर ऐप"):
            st.success("लिंक कॉपी हो गया है!")

st.markdown("<h4 style='margin: 5px 0 15px 0; color: #94a3b8; font-size: 1rem;'>Welcome, User 👋</h4>", unsafe_allow_html=True)

# ==========================================
# GROWW STYLE TABS (Explore, Dashboard, etc.)
# ==========================================
app_mode = st.radio(
    "Navigation", 
    ["📈 Explore (लाइव चार्ट)", "📑 Dashboard (फंडामेंटल)", "🔍 Scanners (स्कैनर)"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# ==========================================
# SEARCH SECTION (Groww Style Banner)
# ==========================================
st.markdown("""
<div class="groww-banner">
  <h3 style="margin-top:0; color:#f8fafc;">Smart Stock Analysis & Insights</h3>
  <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:15px;">Search any stock or pick from popular choices below to get started instantly.</p>
</div>
""", unsafe_allow_html=True)

col_s1, col_s2 = st.columns(2)
with col_s1:
    popular_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "TATAMOTORS.NS", "MARINE.NS"]
    selected_ticker = st.selectbox("🔍 लोकप्रिय शेयर चुनें (Popular Stocks)", popular_stocks)
with col_s2:
    custom_input = st.text_input("या शेयर का टिकर लिखें (Custom Ticker)", placeholder="e.g. ZOMATO.NS, TATAPOWER.NS")

ticker_symbol = custom_input.upper().strip() if custom_input else selected_ticker

st.markdown("---")

info, hist_data = fetch_stock_data(ticker_symbol)

# ==========================================
# MAIN VIEWS
# ==========================================

if "Explore" in app_mode:
    st.subheader(f"विश्लेषण (Analyzing): {info.get('longName', ticker_symbol)}")
    curr_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><span style='color:#94a3b8; font-size:0.85rem;'>लाइव भाव (Price)</span><h3 style='margin:5px 0 0 0; color:#00d09c;'>₹ {curr_price}</h3></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><span style='color:#94a3b8; font-size:0.85rem;'>52W हाई (High)</span><h3 style='margin:5px 0 0 0;'>₹ {info.get('fiftyTwoWeekHigh', 'N/A')}</h3></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><span style='color:#94a3b8; font-size:0.85rem;'>52W लो (Low)</span><h3 style='margin:5px 0 0 0;'>₹ {info.get('fiftyTwoWeekLow', 'N/A')}</h3></div>", unsafe_allow_html=True)
    with c4:
        mcap = info.get('marketCap', 0)
        mcap_str = f"₹ {mcap:,}" if mcap else "N/A"
        st.markdown(f"<div class='metric-card'><span style='color:#94a3b8; font-size:0.85rem;'>मार्केट कैप</span><h3 style='margin:5px 0 0 0;'>{mcap_str}</h3></div>", unsafe_allow_html=True)

    st.markdown("### 📊 ट्रेडिंगव्यू रियल-टाइम चार्ट")
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

elif "Dashboard" in app_mode:
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

elif "Scanners" in app_mode:
    st.subheader("🔍 स्मार्ट स्टॉक स्कैनर")
    strategy = st.selectbox("फिल्टर चुनें", ["ब्रेकआउट / 52-वीक हाई के करीब", "कम कर्ज वाली कंपनियां"])
    
    if st.button("स्कैन शुरू करें", type="primary"):
        universe = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "SBIN.NS"]
        res = []
        for s in universe:
            try:
                inf = yf.Ticker(s).info
                price = inf.get('currentPrice', 0)
                h52 = inf.get('fiftyTwoWeekHigh', 0)
                if strategy == "ब्रेकआउट / 52-वीक हाई के करीब" and price >= 0.90 * h52:
                    res.append({"Symbol": s, "Name": inf.get('longName'), "Price": price, "52W High": h52})
            except:
                pass
        if res:
            st.dataframe(pd.DataFrame(res), use_container_width=True)
        else:
            st.info("वर्तमान में इस फिल्टर से मेल खाते शेयर नहीं मिले।")

# ==========================================
# DISCLAIMER FOOTER
# ==========================================
st.markdown("""
<div class="disclaimer-box">
  <b>⚠️ कानूनी सूचना (Disclaimer):</b> TickStock केवल शैक्षिक और सूचना के उद्देश्य से बनाया गया पोर्टल है। हम SEBI-पंजीकृत सलाहकार नहीं हैं। निवेश करने से पहले अपने वित्तीय सलाहकार से सलाह जरूर लें।
</div>
""", unsafe_allow_html=True)
