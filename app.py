import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import json
st.set_page_config(page_title="TickStox", layout="wide")

# Custom CSS for clean UI look
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2a2e39;
    }
    </style>
""", unsafe_allow_html=True)

# 1. आपकी ओरिजिनल, सबसे दमदार लाइव सर्च फंक्शन (Original Live Search API)
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
                
                if symbol.endswith('.NS') or symbol.endswith('.BO') or exchange in ['NSI', 'BSE', 'NSE']:
                    stock_options.append({
                        'display': f"{short_name} ({symbol})",
                        'symbol': symbol
                    })
            return stock_options
    except:
        return []

st.markdown("### ⚡ TickStox - प्रोफेशनल स्टॉक एनालिटिक्स टर्मिनल")

# अलग से दिए गए हाई P/E और मजबूत फंडामेंटल स्टॉक्स के शॉर्टकट विकल्प (अलग सेक्शन)
st.markdown("#### 🔥 त्वरित श्रेणियां (Quick Screeners)")
screener_mode = st.radio(
    "मोड चुनें:",
    ["🔍 सामान्य लाइव सर्च (Live Search)", "🔥 हाई P/E / मोमेंटम स्टॉक सूची", "🏛️ मजबूत फंडामेंटल स्टॉक सूची"],
    horizontal=True
)

# यदि यूजर श्रेणियां चुने तो उनके लिए सुझाई गई सूचियां
preset_symbol = "RELIANCE.NS"
if screener_mode == "🔥 हाई P/E / मोमेंटम स्टॉक सूची":
    high_pe_list = ["TRENT.NS", "ZOMATO.NS", "DIXON.NS", "POLYCAB.NS", "HAL.NS", "BEL.NS", "RVNL.NS", "JWL.NS", "COCHINSHIP.NS"]
    chosen_preset = st.selectbox("चुनें (High P/E & Momentum):", high_pe_list)
    preset_symbol = chosen_preset
elif screener_mode == "🏛️ मजबूत फंडामेंटल स्टॉक सूची":
    strong_fund_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "LT.NS", "ICICIBANK.NS", "SBIN.NS"]
    chosen_preset = st.selectbox("चुनें (Strong Fundamentals):", strong_fund_list)
    preset_symbol = chosen_preset

# 2. ओरिजिनल और सबसे सटीक सर्च बॉक्स
user_query = st.text_input("🔍 शेयर का नाम या कंपनी टाइप करें (उदा. Zomato, Tata, Marine, Reliance):", preset_symbol.replace(".NS", ""))

selected_symbol = preset_symbol

if screener_mode == "🔍 सामान्य लाइव सर्च (Live Search)":
    if user_query:
        clean_query = user_query.strip()
        
        with st.spinner("🔍 इंटरनेट से शेयर खोजे जा रहे हैं..."):
            suggestions = fetch_stock_suggestions(clean_query)
        
        if suggestions:
            options_map = {item['display']: item['symbol'] for item in suggestions}
            chosen_display = st.selectbox("👇 मिलते-जुलते शेयरों की सूची (सूची से चुनें):", list(options_map.keys()))
            selected_symbol = options_map[chosen_display]
        else:
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
        if selected_symbol.endswith(".NS"):
            bse_symbol = selected_symbol.replace(".NS", ".BO")
            stock = yf.Ticker(bse_symbol)
            df = stock.history(period="6mo")
            if not df.empty:
                selected_symbol = bse_symbol
                
    if df.empty:
        st.error(f"❌ '{selected_symbol}' का डेटा नहीं मिला। कृपया कंपनी का नाम सही से लिखें।")
    else:
        # कॉर्पोरेट इवेंट्स अलर्ट
        try:
            calendar = stock.calendar
            if calendar is not None and not isinstance(calendar, dict) and not calendar.empty:
                st.warning(f"🔔 **कॉर्पोरेट अपडेट अलर्ट ({selected_symbol}):** आगामी वित्तीय परिणाम या इवेंट्स नज़दीक हैं।")
            elif isinstance(calendar, dict) and len(calendar) > 0:
                st.warning(f"🔔 **कॉर्पोरेट अपडेट अलर्ट ({selected_symbol}):** वित्तीय परिणाम संभावित हैं।")
        except:
            pass

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
        
        # Display Metrics (Market Summary)
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
            st.write(f"**S1:** ₹{s1:.2f} | **S2:** ₹{s2:.2f} | **S3:** ₹{s3:.2f}")
            
        with r_col:
            st.markdown("#### 🟢 रेजिस्टेंस लेवल्स")
            st.write(f"**R1:** ₹{r1:.2f} | **R2:** ₹{r2:.2f} | **R3:** ₹{r3:.2f}")
            
        st.divider()
        
        # Quick Technical Analysis Insights
        st.markdown("### 📝 त्वरित विश्लेषण बिंदु")
        if close_price > pivot:
            st.success(f"✅ शेयर का भाव आज के पिवट पॉइंट (₹{pivot:.2f}) से ऊपर ट्रेड कर रहा है (तेजी का संकेत)।")
        else:
            st.warning(f"⚠️ शेयर का भाव पिवट पॉइंट (₹{pivot:.2f}) से नीचे है (कमजोरी का संकेत)।")

        # ==================== फंडामेंटल डेटा, ROE, ROCE, CAGR और इंडस्ट्री P/E ====================
        st.divider()
        st.markdown("### 🏢 उन्नत फंडामेंटल और वित्तीय रेश्यो (Advanced Fundamentals)")
        try:
            info = stock.info
            market_cap = info.get('marketCap', 'N/A')
            market_cap_str = f"₹{market_cap / 10000000:,.2f} Cr" if market_cap != 'N/A' else "उपलब्ध नहीं"

            pe_ratio = info.get('trailingPE', 'N/A')
            pb_ratio = info.get('priceToBook', 'N/A')
            eps = info.get('trailingEps', 'N/A')
            div_yield = info.get('dividendYield', None)
            div_yield_str = f"{div_yield * 100:.2f}%" if div_yield else "N/A"
            
            roe = info.get('returnOnEquity', None)
            roe_str = f"{roe * 100:.2f}%" if roe else "N/A"
            
            roce = info.get('returnOnCapitalEmployed', None)
            roce_str = f"{roce * 100:.2f}%" if roce else "N/A"
            
            ind_pe = info.get('industryPE', 'N/A')
            high_52 = info.get('fiftyTwoWeekHigh', 'N/A')
            low_52 = info.get('fiftyTwoWeekLow', 'N/A')
            
            cagr_val = "N/A"
            if len(df) >= 252:
                start_p = df.iloc[0]['Close']
                end_p = df.iloc[-1]['Close']
                cagr_val = f"{(((end_p/start_p)**(1/0.5))-1)*100:.2f}%"

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("मार्केट कैप", market_cap_str)
            c2.metric("स्टॉक P/E", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else pe_ratio)
            c3.metric("इंडस्ट्री P/E", f"{ind_pe}" if ind_pe == 'N/A' else f"{ind_pe:.2f}")
            c4.metric("P/B रेश्यो", f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else pb_ratio)

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("ROE", roe_str)
            c6.metric("ROCE", roce_str)
            c7.metric("EPS", f"₹{eps:.2f}" if isinstance(eps, (int, float)) else eps)
            c8.metric("CAGR", cagr_val)

            c9, c10, c11 = st.columns(3)
            c9.metric("डिविडेंड यील्ड", div_yield_str)
            c10.metric("52 वीक हाई", f"₹{high_52}" if high_52 == 'N/A' else f"₹{high_52:.2f}")
            c11.metric("52 वीक लो", f"₹{low_52}" if low_52 == 'N/A' else f"₹{low_52:.2f}")

        except Exception as fund_err:
            st.info("फंडामेंटल डेटा लोड करने में असमर्थ।")

        # ==================== मूल्य और वॉल्यूम चार्ट ====================
        st.divider()
        st.markdown(f"### 📈 {selected_symbol} - मूल्य और वॉल्यूम चार्ट")
        
        chart_df = pd.DataFrame(index=df.index)
        chart_df['Close Price'] = df['Close']
        chart_df['SMA 20'] = df['Close'].rolling(window=20).mean()
        
        st.line_chart(chart_df)
        st.markdown("#### 📊 वॉल्यूम (Volume)")
        st.bar_chart(df['Volume'])

        # ==================== कानूनी अस्वीकरण (SEBI Disclaimer) ====================
        st.markdown("---")
        st.info("🛡️ **अस्वीकरण (Disclaimer):** यह ऍप्लिकेशन केवल शैक्षिक और सूचना के उद्देश्य (Educational Purpose) के लिए है। यह किसी भी प्रकार की SEBI पंजीकृत निवेश सलाह या स्टॉक टिप नहीं प्रदान करता है।")
            
except Exception as e:
    st.error(f"डेटा प्रोसेस करने में त्रुटि: {e}")
