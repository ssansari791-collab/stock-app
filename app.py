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
    
    .main { background-color: #0f172a; color: #f8fafc; padding-top: 0px !important; }
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
# UNIVERSAL SMART TICKER RESOLVER
# ==========================================
def resolve_ticker(user_input):
    clean = user_input.upper().strip()
    if not clean:
        return "RELIANCE.NS"
        
    mapping = {
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "HDFC": "HDFCBANK.NS",
        "HDFCBANK": "HDFCBANK.NS",
        "ITC": "ITC.NS",
        "SBIN": "SBIN.NS",
        "TATAMOTORS": "TATAMOTORS.NS",
        "ZOMATO": "ZOMATO.NS",
        "HFCL": "HFCL.NS",
        "SUZLON": "SUZLON.NS",
        "MARINE": "MARINE.NS",
        "JUPITER": "JUPITERWAG.NS",
        "RAMASTEEL": "RAMASTEEL.NS",
        "TEXRAIL": "TEXRAIL.NS",
        "BODAL": "BODALCHEM.NS",
        "TATAPOWER": "TATAPOWER.NS",
        "ADANIENT": "ADANIENT.NS"
    }
    
    if clean in mapping:
        return mapping[clean]
        
    if ".NS" in clean or ".BO" in clean:
        return clean
        
    formatted = clean.replace(" ", "")
    return f"{formatted}.NS"

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

def render_tradingview_chart(ticker_symbol):
    clean_sym = ticker_symbol.replace(".NS", "").replace(".BO", "").upper()
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
    components.html(widget_html, height=510, scrolling=False)

def get_smart_badge(metric_name, value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A", "badge-warning"
    if metric_name == "P/E Ratio":
        if value < 15: return f"{value:.2f} (Attractive)", "badge-good"
        elif 15 <= value <= 30: return f"{value:.2f} (Fair)", "badge-warning"
        else: return f"{value:.2f} (High Growth / P/E)", "badge-danger"
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
# CORNER-TO-CORNER TOP BAR (LOGO & SETTINGS)
# ==========================================
header_c1, header_c2 = st.columns([8, 1])

with header_c1:
    st.markdown("<h3 style='margin:0; padding:0; color:#38bdf8;'>🟢 TickStock</h3>", unsafe_allow_html=True)

with header_c2:
    with st.popover("⚙️"):
        st.write("### यूजर प्रोफाइल")
        uploaded_file = st.file_uploader("फोटो लगाएं", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None:
            st.success("फोटो अपडेट हो गई!")
        st.markdown("---")
        st.markdown("🛠️ **सेटिंग्स**")
        st.markdown("👤 **स्टेटस:** गेस्ट यूजर")
        if st.button("शेयर ऐप"):
            st.success("लिंक कॉपी हो गया है!")

st.markdown("<h4 style='margin: 10px 0 10px 0; color: #f8fafc;'>Welcome, User 👋</h4>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# UNIVERSAL FREE-TEXT SEARCH BAR
# ==========================================
search_query = st.text_input("🔍 कोई भी शेयर सर्च करें (उदा. Ramasteel, Reliance, Zomato, Tata, Suzlon):", value="RELIANCE")
ticker_symbol = resolve_ticker(search_query)

st.markdown("---")

# ==========================================
# NAVIGATION TABS
# ==========================================
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
    st.subheader(f"📊 {ticker_symbol} - बाजार सारांश")
    
    curr_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    day_high = info.get('dayHigh', 'N/A')
    day_low = info.get('dayLow', 'N/A')
    volume = info.get('volume', 'N/A')
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><h4>ताजा भाव (Close)</h4><h3>₹ {curr_price}</h3></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h4>आज का हाई (High)</h4><h3>₹ {day_high}</h3></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h4>आज का लो (Low)</h4><h3>₹ {day_low}</h3></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-card'><h4>वॉल्यूम (Volume)</h4><h3>{volume:,}</h3></div>" if isinstance(volume, (int, float)) else f"<div class='metric-card'><h4>वॉल्यूम</h4><h3>{volume}</h3></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Support & Resistance Section
    st.markdown("### 🎯 सपोर्ट और रेजिस्टेंस लेवल्स (Pivot Points)")
    pivots = calculate_pivot_points(hist_data)
    
    if pivots:
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.markdown("#### 🔵 सपोर्ट लेवल्स")
            st.markdown(f"**S1:** ₹ {pivots['S1']}")
            st.markdown(f"**S2:** ₹ {pivots['S2']}")
            st.markdown(f"**S3:** ₹ {pivots['S3']}")
        with p_col2:
            st.markdown("#### 🟢 रेजिस्टेंस लेवल्स")
            st.markdown(f"**R1:** ₹ {pivots['R1']}")
            st.markdown(f"**R2:** ₹ {pivots['R2']}")
            st.markdown(f"**R3:** ₹ {pivots['R3']}")
            
        # Quick Analysis Insights
        st.markdown("---")
        st.markdown("### 📝 त्वरित विश्लेषण बिंदु")
        if isinstance(curr_price, (int, float)):
            if curr_price < pivots['Pivot']:
                st.markdown(f"⚠️ शेयर का भाव पिवट पॉइंट (₹ {pivots['Pivot']}) से नीचे है, जो कमजोरी दिखा सकता है।")
            else:
                st.markdown(f"🚀 शेयर का भाव पिवट पॉइंट (₹ {pivots['Pivot']}) से ऊपर है, जो मजबूती दिखा सकता है।")
        st.markdown("📉 पिछले दिन की तुलना में बाजार के रुझान का निरीक्षण किया गया है।")

    st.markdown("---")
    st.markdown(f"### 📊 ट्रेडिंगव्यू रियल-टाइम चार्ट ({ticker_symbol})")
    render_tradingview_chart(ticker_symbol)

elif app_mode == "📑 फंडामेंटल हेल्थ (Fundamental Health)":
    st.subheader(f"📑 फंडामेंटल एनालिसिस: {info.get('longName', ticker_symbol)}")
    
    pe = info.get('trailingPE', info.get('forwardPE', None))
    pb = info.get('priceToBook', None)
    roe = info.get('returnOnEquity', None)
    roce = info.get('returnOnCapitalEmployed', None)
    eps = info.get('trailingEps', None)
    de = info.get('debtToEquity', None)
    mcap = info.get('marketCap', None)
    div_yield = info.get('dividendYield', None)
    if div_yield: div_yield = div_yield * 100

    metrics_list = [
        {"Metric": "Market Capitalization", "Val": f"₹ {mcap:,}" if mcap else "N/A", "Badge": "badge-warning", "Hint": "कंपनी का कुल बाजार मूल्यांकन"},
        {"Metric": "P/E Ratio", "Val": get_smart_badge("P/E Ratio", pe)[0], "Badge": get_smart_badge("P/E Ratio", pe)[1], "Hint": "प्रति शेयर आय के मुकाबले मूल्य (<15 आकर्षक, >30 हाई ग्रोथ)"},
        {"Metric": "P/B Ratio", "Val": f"{pb:.2f}" if pb else "N/A", "Badge": "badge-warning", "Hint": "बुक वैल्यू के मुकाबले कीमत"},
        {"Metric": "ROE", "Val": get_smart_badge("ROE", roe)[0], "Badge": get_smart_badge("ROE", roe)[1], "Hint": "इक्विटी पर रिटर्न (>15% स्वास्थ्यवध)"},
        {"Metric": "ROCE", "Val": get_smart_badge("ROCE", roce)[0], "Badge": get_smart_badge("ROCE", roce)[1], "Hint": "नियोजित पूंजी पर रिटर्न (>15% मजबूत)"},
        {"Metric": "EPS", "Val": f"₹ {eps:.2f}" if eps else "N/A", "Badge": "badge-warning", "Hint": "प्रति शेयर कमाई"},
        {"Metric": "Debt to Equity", "Val": get_smart_badge("Debt to Equity", de)[0], "Badge": get_smart_badge("Debt to Equity", de)[1], "Hint": "वित्तीय जोखिम और कर्ज (<0.5 सुरक्षित)"},
        {"Metric": "Dividend Yield", "Val": f"{div_yield:.2f}%" if div_yield else "N/A", "Badge": "badge-warning", "Hint": "वार्षिक लाभांश रिटर्न"}
    ]

    for m in metrics_list:
        col_m1, col_m2, col_m3 = st.columns([2, 2, 3])
        with col_m1:
            st.markdown(f"**{m['Metric']}**")
        with col_m2:
            st.markdown(f"<span class='{m['Badge']}'>{m['Val']}</span>", unsafe_allow_html=True)
        with col_m3:
            st.caption(m['Hint'])
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)

elif app_mode == "🔍 स्मार्ट स्कैनर (Smart Scanners)":
    st.subheader("🔍 प्रो स्टॉक स्कैनर और स्क्रीनर्स")
    strategy = st.selectbox(
        "स्कैनिंग रणनीति चुनें",
        [
            "ब्रेकआउट / 52-वीक हाई के करीब",
            "अंडरवैल्यूड (कम P/E + उच्च ROE)",
            "हाई ग्रोथ / हाई P/E स्टॉक्स (High P/E & Growth)",
            "कम कर्ज वाली सुरक्षित कंपनियां"
        ]
    )
    
    if st.button("स्कैन रन करें", type="primary"):
        with st.spinner("बाजार के शेयरों को स्कैन किया जा रहा है..."):
            universe = [
                "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", 
                "SBIN.NS", "TATAMOTORS.NS", "ZOMATO.NS", "HFCL.NS", "SUZLON.NS", 
                "JUPITERWAG.NS", "RAMASTEEL.NS", "TEXRAIL.NS", "BODALCHEM.NS", 
                "TRENT.NS", "DIXON.NS", "POLYCAB.NS", "KAYNES.NS", "ADANIENT.NS"
            ]
            res = []
            for s in universe:
                try:
                    inf = yf.Ticker(s).info
                    price = inf.get('currentPrice', inf.get('regularMarketPrice', 0))
                    h52 = inf.get('fiftyTwoWeekHigh', 0)
                    pe = inf.get('trailingPE', inf.get('forwardPE', 0))
                    roe = inf.get('returnOnEquity', 0)
                    if roe and roe < 1: roe = roe * 100
                    de = inf.get('debtToEquity', 1)
                    
                    match = False
                    if strategy == "ब्रेकआउट / 52-वीक हाई के करीब" and price and h52 and price >= 0.90 * h52:
                        match = True
                    elif strategy == "अंडरवैल्यूड (कम P/E + उच्च ROE)" and pe and 0 < pe < 25 and roe and roe > 12:
                        match = True
                    elif strategy == "हाई ग्रोथ / हाई P/E स्टॉक्स (High P/E & Growth)" and pe and pe > 30:
                        match = True
                    elif strategy == "कम कर्ज वाली सुरक्षित कंपनियां" and de is not None and de < 0.5:
                        match = True
                        
                    if match:
                        res.append({
                            "Symbol": s,
                            "Company": inf.get('longName', s),
                            "Price (₹)": price,
                            "P/E": round(pe, 2) if pe else 'N/A',
                            "ROE (%)": round(roe, 2) if roe else 'N/A',
                            "Debt/Eq": round(de, 2) if de else 'N/A'
                        })
                except:
                    continue
            if res:
                st.success(f"{len(res)} शेयर मिले जो इस फिल्टर से मेल खाते हैं!")
                st.dataframe(pd.DataFrame(res), use_container_width=True)
            else:
                st.info("वर्तमान बैच में इस शर्त से मेल खाने वाला कोई शेयर नहीं मिला।")

# ==========================================
# LEGAL DISCLAIMER FOOTER
# ==========================================
st.markdown("""
<div class="disclaimer-box">
  <b>⚠️ कानूनी सूचना (Disclaimer):</b> TickStock केवल शैक्षिक और सूचना के उद्देश्य से बनाया गया पोर्टल है। हम SEBI-पंजीकृत सलाहकार नहीं हैं। निवेश करने से पहले अपने वित्तीय सलाहकार से सलाह जरूर लें।
</div>
""", unsafe_allow_html=True)
