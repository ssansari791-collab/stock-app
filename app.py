import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

        # ==================== फंडामेंटल डेटा ====================
        
        st.divider()

        st.markdown("### 🏢 फंडामेंटल डेटा (Fundamentals)")
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

        except Exception as fund_err:
            st.info("फंडामेंटल डेटा लोड करने में असमर्थ।")

        st.divider()

        # ==================== प्रोफेशनल कैंडलस्टिक चार्ट (इंडिकेटर के साथ) ====================
        
        st.markdown(f"### 📈 {selected_symbol} - प्रो कैंडलस्टिक चार्ट (Candlestick & Indicator)")
        
        try:
            # 20 Period Simple Moving Average (SMA) जोड़ रहे हैं
            df['SMA20'] = df['Close'].rolling(window=20).mean()

            # सबप्लॉट: ऊपर कैंडलस्टिक चार्ट, नीचे वॉल्यूम बार चार्ट
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # 1. Candlestick Trace
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Candles',
                increasing_line_color='#26a69a', 
                decreasing_line_color='#ef5350'
            ), row=1, col=1)

            # 2. Moving Average Trace (SMA 20)
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA20'], 
                line=dict(color='#ff9800', width=1.5), 
                name='SMA 20'
            ), row=1, col=1)

            # 3. Volume Bar Trace
            colors = ['#26a69a' if row['Close'] >= row['Open'] else '#ef5350' for index, row in df.iterrows()]
            fig.add_trace(go.Bar(
                x=df.index, y=df['Volume'], 
                marker_color=colors, 
                name='Volume'
            ), row=2, col=1)

            # Layout Styling (Dark Theme match)
            fig.update_layout(
                template='plotly_dark',
                height=550,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_rangeslider_visible=False,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as chart_err:
            st.line_chart(df['Close'])

except Exception as e:
    st.error(f"डेटा प्रोसेस करने में त्रुटि: {e}")
