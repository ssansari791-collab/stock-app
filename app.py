
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

# ==========================================
# PAGE CONFIGURATION & PREMIUM CSS
# ==========================================
st.set_page_config(
    page_title="TickStock | Pro Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling for Professional App Look
st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stApp { background-color: #0f172a; }
    
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
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
# HELPER FUNCTIONS (FIXED CACHING)
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
          "SuperTrend@tv-basicstudies"
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
# SIDEBAR - CLEAN & PROFESSIONAL UI
# ==========================================
st.sidebar.markdown("## ⚡ TickStock Pro")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio("Navigation", ["📈 Live Chart & Technicals", "📑 Fundamental Health", "🔍 Smart Scanners"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Stock Search")
popular_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "TATAMOTORS.NS", "MARINE.NS"]
selected_ticker = st.sidebar.selectbox("Choose Popular Stock", popular_stocks)

custom_input = st.sidebar.text_input("Or enter Ticker (e.g. AAPL, RELIANCE.NS)")
ticker_symbol = custom_input.upper().strip() if custom_input else selected_ticker

info, hist_data = fetch_stock_data(ticker_symbol)

# ==========================================
# MAIN APP VIEWS
# ==========================================

if app_mode == "📈 Live Chart & Technicals":
    st.title("📈 Advanced Live Market Portal")
    comp_name = info.get('longName', ticker_symbol)
    curr_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><h4>Stock</h4><h3>{comp_name}</h3></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h4>Live Price</h4><h3>₹ {curr_price}</h3></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h4>52W High</h4><h3>₹ {info.get('fiftyTwoWeekHigh', 'N/A')}</h3></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><h4>52W Low</h4><h3>₹ {info.get('fiftyTwoWeekLow', 'N/A')}</h3></div>", unsafe_allow_html=True)

    st.markdown("### 📊 TradingView Real-Time Pro Chart")
    render_tradingview_chart(ticker_symbol)
    
    st.markdown("### 📐 Dynamic Support & Resistance (Pivot Points)")
    pivots = calculate_pivot_points(hist_data)
    if pivots:
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(f"<div class='metric-card'><b>Pivot Point:</b> {pivots['Pivot']}<br><b>Resistance 1:</b> {pivots['R1']}<br><b>Support 1:</b> {pivots['S1']}</div>", unsafe_allow_html=True)
        with p2:
            st.markdown(f"<div class='metric-card'><b>Resistance 2:</b> {pivots['R2']}<br><b>Support 2:</b> {pivots['S2']}</div>", unsafe_allow_html=True)
        with p3:
            st.markdown(f"<div class='metric-card'><b>Resistance 3:</b> {pivots['R3']}<br><b>Support 3:</b> {pivots['S3']}</div>", unsafe_allow_html=True)

elif app_mode == "📑 Fundamental Health":
    st.title("📑 Fundamental Analysis & Smart Health")
    st.subheader(info.get('longName', ticker_symbol))
    
    pe = info.get('trailingPE', None)
    roe = info.get('returnOnEquity', None)
    de = info.get('debtToEquity', None)
    mcap = info.get('marketCap', None)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='metric-card'><b>Market Cap:</b> ₹ {mcap:,}</div>" if mcap else "<div class='metric-card'><b>Market Cap:</b> N/A</div>", unsafe_allow_html=True)
        pe_val, pe_badge = get_smart_badge("P/E Ratio", pe)
        st.markdown(f"<div class='metric-card'><b>P/E Ratio:</b> <span class='{pe_badge}'>{pe_val}</span></div>", unsafe_allow_html=True)
    with col2:
        roe_val, roe_badge = get_smart_badge("ROE", roe)
        st.markdown(f"<div class='metric-card'><b>Return on Equity (ROE):</b> <span class='{roe_badge}'>{roe_val}</span></div>", unsafe_allow_html=True)
        de_val, de_badge = get_smart_badge("Debt to Equity", de)
        st.markdown(f"<div class='metric-card'><b>Debt to Equity:</b> <span class='{de_badge}'>{de_val}</span></div>", unsafe_allow_html=True)

elif app_mode == "🔍 Smart Scanners":
    st.title("🔍 Pro Stock Scanners")
    strategy = st.selectbox("Select Screening Filter", ["Breakout / Near 52-Week High", "Undervalued (Low P/E + High ROE)", "Low Debt Companies"])
    
    if st.button("Run Instant Scan", type="primary"):
        universe = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "SBIN.NS"]
        res = []
        for s in universe:
            try:
                inf = yf.Ticker(s).info
                price = inf.get('currentPrice', 0)
                h52 = inf.get('fiftyTwoWeekHigh', 0)
                if strategy == "Breakout / Near 52-Week High" and price >= 0.90 * h52:
                    res.append({"Symbol": s, "Name": inf.get('longName'), "Price": price, "52W High": h52})
            except:
                pass
        if res:
            st.dataframe(pd.DataFrame(res), use_container_width=True)
        else:
            st.info("No matching stocks found in current scan batch.")

# ==========================================
# DISCLAIMER FOOTER
# ==========================================
st.markdown("""
<div class="disclaimer-box">
  <b>⚠️ Legal Notice:</b> TickStock is an educational and informational analytics portal. We are <b>not a SEBI-registered research analyst or investment advisor</b>. Consult a certified financial expert before investing.
</div>
""", unsafe_allow_html=True)

