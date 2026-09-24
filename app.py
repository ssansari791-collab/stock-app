import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import json

st.set_page_config <meta name="google-site-verification" content="1dTgqLUYMFbbmFPX2C6Us4vTdQFZ7uW4mZrRuA-xhT4" />
(page_title="TickStox", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📈TickStox</h1>", unsafe_allow_html=True)
st.write("---")

# Dynamic live search function connecting directly to Yahoo Finance database for Indian stocks
def fetch_stock_suggestions(query):
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={encoded_query}&quotesCount=15&newsCount=0&enableFuzzyQuery=true"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            quotes = data.get('quotes', [])
            
            stock_options = []
            for q in quotes:
                symbol = q.get('symbol', '')
                short_name = q.get('shortname', q.get('longname', symbol))
                exchange = q.get('exchange', '')
                
                # Filter for Indian markets (.NS for NSE, .BO for BSE or standard Indian exchanges)
                if symbol.endswith('.NS') or symbol.endswith('.BO') or exchange in ['NSI', 'BSE', 'NSE']:
                    stock_options.append({
                        'display': f"{short_name} ({symbol})",
                        'symbol': symbol
                    })
            return stock_options
    except:
        return []

# User Input Search Box
user_query = st.text_input("🔍 शेयर का नाम या कंपनी टाइप करें (उदा. Aegis, Tata, Marine, Reliance):", "RELIANCE")

selected_symbol = "RELIANCE.NS"

if user_query:
    clean_query = user_query.strip()
    
    # Live search from internet
    with st.spinner("🔍 इंटरनेट से शेयर खोजे जा रहे हैं..."):
        suggestions = fetch_stock_suggestions(clean_query)
    
    if suggestions:
        options_map = {item['display']: item['symbol'] for item in suggestions}
        chosen_display = st.selectbox("👇 मिलते-जुलते शेयरों की सूची (सूची से चुनें):", list(options_map.keys()))
        selected_symbol = options_map[chosen_display]
    else:
        # Direct fallback: if search API is busy, try formatting directly with .NS or .BO
        upper_q = clean_query.upper().replace(" ", "")
        if not upper_q.endswith(".NS") and not upper_q.endswith(".BO"):
            selected_symbol = upper_q + ".NS"
        else:
            selected_symbol = upper_q

st.write("---")

# Fetch and display live market data and pivot points
try:
    stock = yf.Ticker(selected_symbol)
    df = stock.history(period="6mo")
    
    if df.empty:
        # Try BSE (.BO) if NSE (.NS) fails
        if selected_symbol.endswith(".NS"):
            bse_symbol = selected_symbol.replace(".NS", ".BO")
            stock = yf.Ticker(bse_symbol)
            df = stock.history(period="6mo")
            if not df.empty:
                selected_symbol = bse_symbol
                
    if df.empty:
        st.error(f"❌ '{selected_symbol}' का डेटा नहीं मिला। कृपया कंपनी का नाम सही से लिखें।")
    else:
        latest = df.iloc[-1]
        prev_close = df.iloc[-2]['Close'] if len(df) > 1 else latest['Open']
        
        close_price = latest['Close']
        high_price = latest['High']
        low_price = latest['Low']
        open_price = latest['Open']
        volume = latest['Volume']
        
        change = close_price - prev_close
        change_pct = (change / prev_close) * 100
        
        # Pivot Points Calculation
        pivot = (high_price + low_price + close_price) / 3
        r1 = (2 * pivot) - low_price
        s1 = (2 * pivot) - high_price
        r2 = pivot + (high_price - low_price)
        s2 = pivot - (high_price - low_price)
        r3 = high_price + 2 * (pivot - low_price)
        s3 = low_price - 2 * (pivot - low_price)
        
        # Display Metrics
        st.subheader(f"📊 {selected_symbol} - बाजार सारांश")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("लाइव भाव (Close)", f"₹{close_price:.2f}", f"{change_pct:+.2f}%")
        m2.metric("आज का हाई (High)", f"₹{high_price:.2f}")
        m3.metric("आज का लो (Low)", f"₹{low_price:.2f}")
        m4.metric("वॉल्यूम (Volume)", f"{volume:,}")
        
        st.write("---")
        
        # Pivot Points Display
        st.markdown("### 🎯 सपोर्ट और रेजिस्टेंस लेवल्स (Pivot Points)")
        s_col, r_col = st.columns(2)
        
        with s_col:
            st.markdown("#### 🔵 सपोर्ट लेवल्स")
            st.write(f"**S1:** ₹{s1:.2f}")
            st.write(f"**S2:** ₹{s2:.2f}")
            st.write(f"**S3:** ₹{s3:.2f}")
            
        with r_col:
            st.markdown("#### 🟢 रेजिस्टेंस लेवल्स")
            st.write(f"**R1:** ₹{r1:.2f}")
            st.write(f"**R2:** ₹{r2:.2f}")
            st.write(f"**R3:** ₹{r3:.2f}")
            
        st.divider()
        
        # Quick Technical Analysis Insights
        st.markdown("### 📝 त्वरित विश्लेषण बिंदु")
        reasons = []
        if close_price > pivot:
            reasons.append(f"✅ शेयर का भाव आज के पिवट पॉइंट (₹{pivot:.2f}) से ऊपर ट्रेड कर रहा है, जो तेजी का संकेत हो सकता है।")
        else:
            reasons.append(f"⚠️ शेयर का भाव पिवट पॉइंट (₹{pivot:.2f}) से नीचे है, जो कमजोरी दिखा सकता है।")
            
        if close_price > prev_close:
            reasons.append("📈 पिछला दिन हरे निशान में बंद हुआ था।")
        else:
            reasons.append("📉 पिछले दिन की तुलना में गिरावट दर्ज की गई है।")
            
        for r in reasons:
            st.write(r)
            
except Exception as e:
    st.error(f"डेटा प्रोसेस करने में त्रुटि: {e}")
