import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import json
st.set_page_config(page_title="TickStox", layout="wide")

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
                
                if symbol.endswith('.NS') or symbol.endswith('.BO') or exchange in ['NSI', 'BSE', 'NSE']:
                    stock_options.append({
                        'display': f"{short_name} ({symbol})",
                        'symbol': symbol
                    })
            return stock_options
    except:
        return []

# ==================== मुख्य स्क्रीन पर स्मार्ट श्रेणियां और सर्च (Main Screen Smart Screener & Search) ====================
st.markdown("### 🔍 स्मार्ट स्टॉक श्रेणियां और सर्च (Smart Screener & Search)")

col_cat1, col_cat2 = st.columns(2)

with col_cat1:
    category_choice = st.selectbox(
        "लोकप्रिय थीम / श्रेणियां चुनें:", 
        [
            "--- अपनी पसंद का स्टॉक टाइप करें ---", 
            "🔥 हाई P/E / मोमेंटम (High P/E & Momentum)", 
            "🏛️ मजबूत फंडामेंटल (Strong Fundamentals)", 
            "💰 उच्च लाभांश वाले (High Dividend Yield)"
        ]
    )

# हाई P/E और मोमेंटम वाले लोकप्रिय शेयरों की व्यापक सूची
screener_stocks = {
    "🔥 हाई P/E / मोमेंटम (High P/E & Momentum)": [
        "TRENT.NS", "ZOMATO.NS", "DIXON.NS", "POLYCAB.NS", "PERSISTENT.NS", "MUTHOOTFIN.NS", 
        "HAL.NS", "BEL.NS", "CHOLAFIN.NS", "TATACOMM.NS", "LODHA.NS", "MOTHERSON.NS",
        "SRF.NS", "DLF.NS", "APOLLOHOSP.NS", "INDIGO.NS", "PIIND.NS", "NAUKRI.NS",
        "RVNL.NS", "JWL.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "IRFC.NS", "KPITTECH.NS"
    ],
    "🏛️ मजबूत फंडामेंटल (Strong Fundamentals)": [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "LT.NS", 
        "ICICIBANK.NS", "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS", "KOTAKBANK.NS",
        "AXISBANK.NS", "SUNPHARMA.NS", "TITAN.NS", "ASIANPAINT.NS", "MARUTI.NS"
    ],
    "💰 उच्च लाभांश वाले (High Dividend Yield)": [
        "COALINDIA.NS", "VEDL.NS", "ONGC.NS", "IOC.NS", "POWERGRID.NS", "NTPC.NS", 
        "BPCL.NS", "HINDPETRO.NS", "GAIL.NS", "ITC.NS", "HCLTECH.NS", "PETRONET.NS", "NHPC.NS"
    ]
}

default_query = "RELIANCE"
with col_cat2:
    if category_choice != "--- अपनी पसंद का स्टॉक टाइप करें ---":
        selected_category_list = screener_stocks[category_choice]
        display_names = [s.replace(".NS", "") for s in selected_category_list]
        chosen_cat_display = st.selectbox("या सूची से सीधा चुनें:", display_names)
        default_query = chosen_cat_display

# User Input Search Box
user_query = st.text_input("🔍 शेयर का नाम या कंपनी टाइप करें (उदा. Trent, Zomato, Reliance):", default_query)

selected_symbol = "RELIANCE.NS"

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
                st.warning(f"🔔 **कॉर्पोरेट अपडेट अलर्ट ({selected_symbol}):** इस स्टॉक से जुड़े आगामी इवेंट्स (जैसे अर्निंग्स रिजल्ट या डिविडेंड तारीख) नज़दीक हैं।")
            elif isinstance(calendar, dict) and len(calendar) > 0:
                st.warning(f"🔔 **कॉर्पोरेट अपडेट अलर्ट ({selected_symbol}):** आगामी वित्तीय परिणाम संभावित हैं।")
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

        # ==================== फंडामेंटल और वित्तीय प्रदर्शन ====================
        st.divider()
        st.markdown("### 🏢 फंडामेंटल डेटा और वित्तीय प्रदर्शन (Financial Results Summary)")
        try:
            info = stock.info
            market_cap = info.get('marketCap', 'N/A')
            if market_cap != 'N/A':
                market_cap_cr = market_cap / 10000000  
                market_cap_str = f"₹{market_cap_cr:,.2f} Cr"
            else:
                market_cap_str = "उपलब्ध नहीं"

            pe_ratio = info.get('trailingPE', 'N/A')
            pb_ratio = info.get('priceToBook', 'N/A')
            eps = info.get('trailingEps', 'N/A')
            div_yield = info.get('dividendYield', None)
            div_yield_str = f"{div_yield * 100:.2f}%" if div_yield else "N/A"
            high_52 = info.get('fiftyTwoWeekHigh', 'N/A')
            low_52 = info.get('fiftyTwoWeekLow', 'N/A')

            f1, f2, f3, f4 = st.columns(4)
            f1.metric("मार्केट कैप (Market Cap)", market_cap_str)
            f2.metric("पीई रेश्यो (P/E Ratio)", f"{pe_ratio}" if pe_ratio == 'N/A' else f"{pe_ratio:.2f}")
            f3.metric("पीबी रेश्यो (P/B Ratio)", f"{pb_ratio}" if pb_ratio == 'N/A' else f"{pb_ratio:.2f}")
            f4.metric("ईपीएस (EPS)", f"{eps}" if eps == 'N/A' else f"₹{eps:.2f}")

            f5, f6, f7 = st.columns(3)
            f5.metric("डिविडेंड यील्ड", div_yield_str)
            f6.metric("52 वीक हाई (High)", f"₹{high_52}" if high_52 == 'N/A' else f"₹{high_52:.2f}")
            f7.metric("52 वीक लो (Low)", f"₹{low_52}" if low_52 == 'N/A' else f"₹{low_52:.2f}")

            financials = stock.financials
            if financials is not None and not financials.empty:
                st.markdown("#### 📄 वार्षिक वित्तीय प्रदर्शन का निचोड़ (Annual Financials)")
                rev_row = [col for col in financials.index if 'Total Revenue' in col or 'Revenue' in col]
                net_row = [col for col in financials.index if 'Net Income' in col]
                
                summary_df = pd.DataFrame()
                if rev_row:
                    summary_df.loc['कुल रेवेन्यू (Revenue)'] = financials.loc[rev_row[0]]
                if net_row:
                    summary_df.loc['शुद्ध लाभ (Net Income)'] = financials.loc[net_row[0]]
                
                if not summary_df.empty:
                    st.dataframe(summary_df.iloc[:, :3] / 10000000)
                    st.caption("* नोट: आंकड़े करोड़ (Cr) में प्रदर्शित किए गए हैं।")

        except Exception as fund_err:
            st.info("वित्तीय परिणाम लोड करने में असमर्थ।")

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
