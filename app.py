import streamlit as st
import pandas as pd
import requests
from io import StringIO

# --- 1. पैकेज इंस्टॉल करने का जुगाड़ ---
try:
    import plotly.graph_objects as go
    import yfinance as yf
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly", "yfinance"])
    import plotly.graph_objects as go
    import yfinance as yf

st.set_page_config(page_title="TickStox Pro", layout="wide")

# --- 2. पूरे मार्केट (NSE) की सभी स्टॉक्स की लिस्ट ---
@st.cache_data(ttl=86400) 
def get_halal_nse_symbols():
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            
            # बैंकिंग, ब्याज और फाइनेंस सेक्टर को हटाने के लिए सटीक शब्द
            HARAM_KEYWORDS = [
                'BANK', 'FINANCE', 'NBFC', 'CAPITAL', 'FINSERV', 'MUTHOOT', 
                'BAJAJFIN', 'SHRIRAMFIN', 'INSURANCE', 'LIFE', 'GIC', 'LIC', 
                'HOUSING', 'LOAN', 'CREDIT', 'FINCORP', 'AMC', 'SECURITIES', 'BROKING'
            ]
            
            symbols = []
            for sym in df['SYMBOL'].tolist():
                sym_str = str(sym).strip().upper()
                if not any(kw in sym_str for kw in HARAM_KEYWORDS):
                    symbols.append(sym_str + '.NS')
            return symbols
        else:
            return []
    except:
        return []

# --- 3. न्यूज़ चेक करने का फंक्शन ---
def get_news_and_sentiment(ticker):
    NEGATIVE_KEYWORDS = ['loss', 'fraud', 'penalty', 'downgrade', 'resign', 'sebi', 'probe', 'fall', 'decline', 'debt', 'warning', 'slump']
    try:
        news_list = ticker.news
        if not news_list: return "🟢 कोई नेगेटिव खबर नहीं है।", []
        sentiment = "🟢 सामान्य/पॉजिटिव"
        headlines = []
        for news in news_list[:3]:
            title = news.get('title', '')
            headlines.append(title)
            title_lower = title.lower()
            for kw in NEGATIVE_KEYWORDS:
                if kw in title_lower:
                    sentiment = f"🔴 बुरी खबर (Bad News): {title[:40]}..."
                    break
        return sentiment, headlines
    except:
        return "⚪ न्यूज़ उपलब्ध नहीं", []

# --- 4. ऑप्शन A: सामान्य स्कैनर (ऑल-टाइम हाई के पास) ---
def analyze_normal_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5y")
        if df.empty or len(df) < 200: return None

        current_price = df['Close'].iloc[-1]
        if current_price < 20: return None

        all_time_high = df['High'].max()
        if current_price < (all_time_high * 0.85): return None

        prev_high = df['High'].iloc[-2]
        avg_volume = df['Volume'].iloc[-20:].mean()
        current_volume = df['Volume'].iloc[-1]

        status, color, details = "", "grey", ""
        
        if current_price > prev_high and current_volume > (avg_volume * 1.2):
            status = "🔥 ताजा ब्रेकआउट"
            color = "#00FF00"
            details = "स्टॉक ने पिछले हाई को तोड़ दिया है।"
        elif prev_high < current_price <= (prev_high * 1.02):
            status = "🎯 रीटेस्ट ज़ोन में"
            color = "#FFA500"
            details = "स्टॉक ब्रेकआउट के बाद वापस सपोर्ट पर है।"
        elif df['Close'].iloc[-1] > df['Open'].iloc[-1] and df['Low'].iloc[-1] <= (all_time_high * 0.99):
            status = "✅ रीटेस्ट कन्फर्म"
            color = "#00BFFF"
            details = "स्टॉक ने सपोर्ट लिया है और हरी कैंडल बनाई है।"
        elif current_price < prev_high and current_price < df['Open'].iloc[-1]:
            status = "❌ रीटेस्ट फेल"
            color = "#FF0000"
            details = "स्टॉक वापस पुराने लेवल के नीचे चला गया है।"
        else:
            status = "📊 हाई के पास"
            color = "grey"
            details = "स्टॉक हाई के पास है।"

        news_sentiment, headlines = get_news_and_sentiment(ticker)
        chart_df = df[-250:] 

        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": all_time_high,
            "Status": status, "Color": color, "Details": details, "News": news_sentiment,
            "Headlines": headlines, "ChartData": chart_df, "Type": "Normal"
        }
    except:
        return None

# --- 5. ऑप्शन B: मल्टी-ईयर रेजिस्टेंस ब्रेकआउट स्कैनर (आपका पसंदीदा) ---
def analyze_breakout_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5y")
        if df.empty or len(df) < 500: return None

        current_price = df['Close'].iloc[-1]
        if current_price < 30: return None

        # 2-3 साल का पुराना रेजिस्टेंस निकालें (आखिरी 100 दिन छोड़कर)
        past_data = df.iloc[:-100] 
        if past_data.empty: return None
        resistance_level = past_data['High'].max()

        # शर्त: स्टॉक रेजिस्टेंस तोड़ चुका हो और रीटेस्ट ज़ोन (5% के अंदर) में हो
        if current_price <= resistance_level or current_price > (resistance_level * 1.10):
            return None 

        status, color, details = "", "grey", ""
        
        if df['Close'].iloc[-1] > df['Open'].iloc[-1]:
            status = "✅ रीटेस्ट कन्फर्म (ग्रीन कैंडल)"
            color = "#00BFFF"
            details = f"स्टॉक ने ₹{resistance_level:.2f} का बड़ा रेजिस्टेंस तोड़ा है और अब हरी कैंडल बना रहा है।"
        else:
            status = "🎯 रीटेस्ट ज़ोन में"
            color = "#FFA500"
            details = f"स्टॉक ने ₹{resistance_level:.2f} का रेजिस्टेंस तोड़ा है और अब उसी के पास है।"

        news_sentiment, headlines = get_news_and_sentiment(ticker)
        chart_df = df[-300:] 

        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": resistance_level,
            "Status": status, "Color": color, "Details": details, "News": news_sentiment,
            "Headlines": headlines, "ChartData": chart_df, "Type": "Breakout"
        }
    except:
        return None

# --- 6. मुख्य UI ---
st.title("⚡ TickStox Pro - स्मार्ट स्कैनर")

# UI में दो बटन
col1, col2 = st.columns(2)

with col1:
    btn_normal = st.button("🔍 सभी स्टॉक्स स्कैन करें (नार्मल)", use_container_width=True)
with col2:
    btn_breakout = st.button("🎯 2 साल का रेजिस्टेंस तोड़ने वाले स्टॉक्स", use_container_width=True)

# अगर नार्मल बटन दबाया
if btn_normal:
    with st.spinner("डेटा लोड हो रहा है..."):
        scan_list = get_halal_nse_symbols()
    if scan_list:
        st.success(f"कुल {len(scan_list)} स्टॉक्स स्कैन हो रहे हैं...")
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty() 
        
        for i, stock in enumerate(scan_list):
            res = analyze_normal_stock(stock)
            if res: results.append(res)
            if i % 50 == 0 or i == len(scan_list) - 1:
                progress_bar.progress((i + 1) / len(scan_list))
                status_text.text(f"स्कैन हो रहा है: {i+1} / {len(scan_list)} (मिले: {len(results)})")
                
        progress_bar.empty(); status_text.empty()
        st.session_state['results'] = results
        st.session_state['type'] = 'Normal'

# अगर ब्रेकआउट बटन दबाया
if btn_breakout:
    with st.spinner("डेटा लोड हो रहा है..."):
        scan_list = get_halal_nse_symbols()
    if scan_list:
        st.success(f"कुल {len(scan_list)} स्टॉक्स स्कैन हो रहे हैं (सिर्फ बेस्ट ब्रेकआउट के लिए)...")
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty() 
        
        for i, stock in enumerate(scan_list):
            res = analyze_breakout_stock(stock)
            if res: results.append(res)
            if i % 50 == 0 or i == len(scan_list) - 1:
                progress_bar.progress((i + 1) / len(scan_list))
                status_text.text(f"स्कैन हो रहा है: {i+1} / {len(scan_list)} (मिले: {len(results)})")
                
        progress_bar.empty(); status_text.empty()
        st.session_state['results'] = results
        st.session_state['type'] = 'Breakout'

# --- 7. रिजल्ट दिखाना ---
if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']
    scan_type = st.session_state['type']
    
    if scan_type == 'Breakout':
        st.info(f"कुल {len(results)} बेहतरीन स्टॉक्स मिले जिन्होंने 2-3 साल का रेजिस्टेंस तोड़कर रीटेस्ट किया है:")
    else:
        st.info(f"कुल {len(results)} स्टॉक्स मिले जो हाई के पास हैं:")

    for r in results:
        expander_title = f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"
        with st.expander(expander_title):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                if scan_type == 'Breakout':
                    st.markdown(f"**पुराना रेजिस्टेंस (अब सपोर्ट):** ₹{r['Level']:.2f}")
                else:
                    st.markdown(f"**All-Time High:** ₹{r['Level']:.2f}")
                st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                st.info(f"**विश्लेषण:** {r['Details']}")
                st.text_input("📋 नाम कॉपी करें:", value=r['Stock'], key=f"copy_{r['Stock']}")
                
            with col2:
                st.markdown("**📰 ताज़ा न्यूज़:**")
                st.write(r['News'])
                for h in r['Headlines'][:2]:
                    st.write(f"- {h}")
                    
            st.markdown("**📈 चार्ट:**")
            fig = go.Figure(data=[go.Candlestick(
                x=r['ChartData'].index,
                open=r['ChartData']['Open'], high=r['ChartData']['High'],
                low=r['ChartData']['Low'], close=r['ChartData']['Close'],
                increasing_line_color='green', decreasing_line_color='red'
            )])
            
            if scan_type == 'Breakout':
                # चार्ट पर रेजिस्टेंस लाइन खींचना
                fig.add_hline(y=r['Level'], line_dash="dash", line_color="blue", annotation_text="पुराना रेजिस्टेंस")
            
            fig.update_layout(
                xaxis_rangeslider_visible=False, height=450,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.info("🛡️ **अस्वीकरण:** यह जानकारी सिर्फ शैक्षिक उद्देश्य के लिए है।")
