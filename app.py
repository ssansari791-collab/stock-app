import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page Config
st.set_page_config(page_title="TickStock - प्रो स्टॉक स्कैनर", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stTextInput, .stSelectbox { color: black; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 TickStock")
st.markdown("### प्रो स्टॉक स्कैनर और टेक्निकल एनालाइजर")

# Navigation Menu
menu = st.sidebar.radio("मेनु चुनें (Navigation)", 
                        ["📊 लाइव चार्ट और टेक्निकल (Live Chart & Technicals)", 
                         "💡 फंडामेंटल हेल्थ (Fundamental Health)", 
                         "🔍 स्मार्ट स्कैनर (Smart Scanners)"])

# Common Popular Stocks for quick search fallback
popular_stocks = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "Tata Power": "TATAPOWER.NS",
    "HFCL": "HFCL.NS",
    "Zomato": "ZOMATO.NS",
    "Himadri": "HSCL.NS"
}

if menu == "📊 लाइव चार्ट और टेक्निकल (Live Chart & Technicals)":
    st.subheader("🔍 शेयर सर्च करें")
    user_input = st.text_input("शेयर का नाम या टिकर लिखें (उदाम. Reliance, TCS, Zomato, HFCL):", "RELIANCE.NS")
    
    # Handle search flexibly
    ticker_symbol = user_input.strip()
    if not ticker_symbol.endswith(".NS") and not ticker_symbol.endswith(".BO"):
        # Check if matches popular names loosely
        matched = False
        for name, sym in popular_stocks.items():
            if ticker_symbol.lower() in name.lower() or ticker_symbol.lower() in sym.lower():
                ticker_symbol = sym
                matched = True
                break
        if not matched:
            ticker_symbol = ticker_symbol.upper() + ".NS"

    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="5d")
        
        if df.empty:
            st.error("स्टॉक डेटा नहीं मिला। कृपया सही नाम या टिकर दर्ज करें।")
        else:
            latest = df.iloc[-1]
            prev_close = df.iloc[-2]['Close'] if len(df) > 1 else latest['Open']
            change = latest['Close'] - prev_close
            pct_change = (change / prev_close) * 100
            
            # Live Price & Metrics Box
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("लाइव प्राइस (Live Price)", f"₹{latest['Close']:.2f}", f"{pct_change:.2f}%")
            col2.metric("आज का हाई (High)", f"₹{latest['High']:.2f}")
            col3.metric("आज का लो (Low)", f"₹{latest['Low']:.2f}")
            col4.metric("वॉल्यूम (Volume)", f"{int(latest['Volume']):,}")
            
            st.markdown("---")
            
            # Support, Resistance & Pivot Points Calculation
            high = latest['High']
            low = latest['Low']
            close = latest['Close']
            
            pivot = (high + low + close) / 3
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            
            st.subheader("📊 पिवट पॉइंट्स और संकेत (Pivot Points & Signals)")
            p_col1, p_col2 = st.columns(2)
            
            with p_col1:
                st.write(f"**पिवट पॉइंट (Pivot):** ₹{pivot:.2f}")
                st.write(f"**सपोर्ट 1 (S1):** ₹{s1:.2f}")
                st.write(f"**सपोर्ट 2 (S2):** ₹{s2:.2f}")
                
            with p_col2:
                st.write(f"**रेजिस्टेंस 1 (R1):** ₹{r1:.2f}")
                st.write(f"**रेजिस्टेंस 2 (R2):** ₹{r2:.2f}")
                
            # Trend Signal based on Pivot
            if close > pivot:
                st.success("🟢 **संकेत:** स्टॉक पिवट पॉइंट से ऊपर ट्रेड कर रहा है। ऊपर जाने की संभावना (Bullish) मजबूत है।")
            else:
                st.error("🔴 **संकेत:** स्टॉक पिवट पॉइंट से नीचे है। सतर्क रहें,िि नीचे जाने का दबाव हो सकता है (Bearish)।")

            st.markdown("---")
            st.subheader("📉 ट्रेडिंगव्यू लाइव चार्ट (TradingView Chart)")
            
            # TradingView Widget Embed via HTML
            tv_symbol = ticker_symbol.replace(".NS", "")
            chart_html = f"""
            <div class="tradingview-widget-container" style="height:500px;width:100%">
              <div id="tradingview_chart" style="height:100%;width:100%"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget(
              {{
                "width": "100%",
                "height": 500,
                "symbol": "NSE:{tv_symbol}",
                "interval": "D",
                "timezone": "Asia/Kolkata",
                "theme": "dark",
                "style": "1",
                "locale": "in",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_chart"
              }});
              </script>
            </div>
            """
            st.components.v1.html(chart_html, height=520)

    except Exception as e:
        st.error(f"डेटा लोड करने में त्रुटि आई: {e}")

elif menu == "💡 फंडामेंटल हेल्थ (Fundamental Health)":
    st.subheader("🏢 फंडामेंटल हेल्थ और वित्तीय जानकारी")
    f_input = st.text_input("कंपनी का टिकर दर्ज करें (उदा. RELIAS, TCS):", "RELIANCE.NS")
    try:
        comp = yf.Ticker(f_input.upper() if ".NS" in f_input else f_input.upper() + ".NS")
        info = comp.info
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**कंपनी का नाम:** {info.get('longName', 'N/A')}")
            frames = info.get('marketCap', 'N/A')
            st.write(f"**मार्केट कैप (Market Cap):** {frames:,}" if isinstance(frames, int) else f"**मार्केट कैप:** {frames}")
            st.write(f"**पी/ई रेश्यो (P/E Ratio):** {info.get('trailingPE', 'N/A')}")
        with col2:
            st.write(f"**डिविडेंड यील्ड (Dividend Yield):** {info.get('dividendYield', 0)*100 if info.get('dividendYield') else 'N/A'}%")
            st.write(f"**52 वीक हाई:** {info.get('fiftyTwoWeekHigh', 'N/A')}")
            st.write(f"**52 वीक लो:** {info.get('fiftyTwoWeekLow', 'N/A')}")
            
    except Exception as e:
        st.warning("फंडामेंटल विवरण प्राप्त करने में असफल।")

elif menu == "🔍 स्मार्ट स्कैनर (Smart Scanners)":
    st.subheader("🚀 प्रो स्टॉक स्कैनर और स्क्रीनर्स")
    scanner_type = st.selectbox("स्कैनिंग रणनीति चुनें", [
        "हाई ग्रोथ / हाई पी स्टॉक्स (High P/E & Growth)",
        "ब्रेकआउट / 52-वीक हाई के करीब",
        "अंडरवैैल्यूड (कम P/E + उच्च ROE)",
        "कम कर्ज वाली सुरक्षित कंपनियां"
    ])
    
    st.markdown(f"**चयनित रणनीति:** `{scanner_type}`")
    
    # Sample scanner results dataframe matching your layout
    scanner_data = {
        "Symbol": ["HFCL.NS", "TATAPOWER.NS", "RELIANCE.NS", "ZOMATO.NS", "HSCL.NS"],
        "Company": ["HFCL Limited", "The Tata Power Company", "Reliance Industries", "Zomato Limited", "Himadri Speciality"],
        "Sector": ["Telecom", "Power", "Conglomerate", "Consumer Services", "Chemicals"],
        "Status": ["Breakout Active", "High Growth", "Strong Support", "High Volume", "Undervalued"]
    }
    
    df_scan = pd.DataFrame(scanner_data)
    st.dataframe(df_scan, use_container_width=True)

# Footer Disclaimer
st.markdown("---")
st.markdown("⚠️ **कानूनी सूचना (Disclaimer):** TickStock केवल शैक्षिक और सूचना के उद्देश्य से बनाया गया पोर्टल है। हम SEBI-पंजीकृत सलाहकार नहीं हैं। निवेश करने से पहले अपने वित्तीय सलाहकार से सलाह ज़रूर लें[span_2](start_span)[span_2](end_span)[span_3](start_span)[span_3](end_span)।")
            
