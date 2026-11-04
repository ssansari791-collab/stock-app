import streamlit as st
import pandas as pd
import requests
from io import StringIO

# --- जुगाड़: अगर सर्वर पर लाइब्रेरी नहीं है, तो खुद इंस्टॉल करने की कोशिश करेगा ---
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

# --- 1. पूरे मार्केट (NSE) की सभी स्टॉक्स की लिस्ट लोड करने का फंक्शन ---
@st.cache_data(ttl=86400) # 24 घंटे तक लिस्ट कैश (याद) रखेगा
def get_all_nse_symbols():
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            symbols = [str(sym).strip() + '.NS' for sym in df['SYMBOL'].tolist()]
            return symbols
        else:
            return []
    except:
        return []

# --- 2. न्यूज़ चेक करने का फंक्शन ---
def get_news_and_sentiment(ticker):
    NEGATIVE_KEYWORDS = ['loss', 'fraud', 'penalty', 'downgrade', 'resign', 'sebi', 'probe', 'fall', 'decline', 'debt', 'warning', 'slump']
    try:
        news_list = ticker.news
        if not news_list:
            return "🟢 कोई नेगेटिव खबर नहीं है।", []
            
        sentiment = "🟢 सामान्य/पॉजिटिव"
        headlines = []
        for news in news_list[:5]:
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

# --- 3. स्कैनर का मुख्य लॉजिक ---
def analyze_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5y")
        if df.empty or len(df) < 200: return None

        current_price = df['Close'].iloc[-1]
        
        # पेनी स्टॉक्स (₹20 से नीचे) को हटाने के लिए
        if current_price < 20: return None

        all_time_high = df['High'].max()
        
        # शर्त: 5 साल के All-Time High के 15% के दायरे में
        if current_price < (all_time_high * 0.85): return None

        prev_high = df['High'].iloc[-2]
        avg_volume = df['Volume'].iloc[-20:].mean()
        current_volume = df['Volume'].iloc[-1]

        status, color, details = "", "grey", ""
        
        if current_price > prev_high and current_volume > (avg_volume * 1.2):
            status = "🔥 ताजा ब्रेकआउट (Volume Spike)"
            color = "#00FF00"
            details = "स्टॉक ने पिछले हाई को तोड़ दिया है और वॉल्यूम भी तेज़ है। यहाँ एंट्री का अच्छा मौका हो सकता है।"
        elif prev_high < current_price <= (prev_high * 1.02):
            status = "🎯 रीटेस्ट ज़ोन में"
            color = "#FFA500"
            details = "स्टॉक ब्रेकआउट के बाद वापस अपने पुराने हाई (अब सपोर्ट) को टेस्ट कर रहा है। अगर यहाँ हरी कैंडल बने, तो एंट्री ली जा सकती है।"
        elif df['Close'].iloc[-1] > df['Open'].iloc[-1] and df['Low'].iloc[-1] <= (all_time_high * 0.99):
            status = "✅ रीटेस्ट कन्फर्म"
            color = "#00BFFF"
            details = "स्टॉक ने सपोर्ट ले लिया है और हरी कैंडल बना दी है। यह एक कन्फर्म एंट्री सिग्नल है।"
        elif current_price < prev_high and current_price < df['Open'].iloc[-1]:
            status = "❌ रीटेस्ट फेल / ब्रेकडाउन"
            color = "#FF0000"
            details = "स्टॉक ब्रेकआउट के बाद वापस पुराने लेवल के नीचे चला गया है। यह फेक ब्रेकआउट या ब्रेकडाउन है, यहाँ से बचें।"
        else:
            status = "📊 हाई के पास (Consolidating)"
            color = "grey"
            details = "स्टॉक अपने ऑल-टाइम हाई के पास है, लेकिन अभी किसी तरफ साफ मूवमेंट नहीं दिखा रहा है।"

        news_sentiment, headlines = get_news_and_sentiment(ticker)
        chart_df = df[-250:] 

        return {
            "Stock": symbol.replace('.NS', ''),
            "Price": current_price,
            "ATH": all_time_high,
            "Status": status,
            "Color": color,
            "Details": details,
            "News": news_sentiment,
            "Headlines": headlines,
            "ChartData": chart_df
        }
    except:
        return None

# --- 4. मुख्य UI ---
st.title("⚡ TickStox Pro - पूरा मार्केट स्कैनर")
st.warning("⚠️ ध्यान दें: यह स्कैनर NSE के सभी लिस्टेड स्टॉक्स को स्कैन करता है। इसमें 10-15 मिनट लग सकते हैं।")

if st.button("🚀 पूरे मार्केट को स्कैन करें", use_container_width=True):
    with st.spinner("NSE की पूरी लिस्ट लोड हो रही है..."):
        scan_list = get_all_nse_symbols()
        
    if not scan_list:
        st.error("NSE की लिस्ट लोड नहीं हो पाई। कृपया दोबारा कोशिश करें।")
    else:
        st.success(f"लिस्ट लोड हो गई! कुल {len(scan_list)} स्टॉक्स स्कैन किए जा रहे हैं...")
        
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty() 
        
        for i, stock in enumerate(scan_list):
            res = analyze_stock(stock)
            if res:
                results.append(res)
            
            if i % 50 == 0 or i == len(scan_list) - 1:
                progress = (i + 1) / len(scan_list)
                progress_bar.progress(progress)
                status_text.text(f"स्कैन हो रहा है: {i+1} / {len(scan_list)} स्टॉक्स (मिले: {len(results)})")
                
        progress_bar.empty()
        status_text.empty()

        if not results:
            st.warning("आज आपकी शर्तों पर कोई स्टॉक नहीं मिला।")
        else:
            st.success(f"कुल {len(results)} स्टॉक्स मिले जो हाई के पास हैं:")
            
            for r in results:
                expander_title = f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"
                
                with st.expander(expander_title):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                        st.markdown(f"**All-Time High:** ₹{r['ATH']:.2f}")
                        st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                        st.info(f"**विश्लेषण:** {r['Details']}")
                        
                    with col2:
                        st.markdown("**📰 ताज़ा न्यूज़:**")
                        st.write(r['News'])
                        for h in r['Headlines'][:3]:
                            st.write(f"- {h}")
                            
                    st.markdown("**📈 पिछले 1 साल का Candlestick चार्ट:**")
                    
                    fig = go.Figure(data=[go.Candlestick(
                        x=r['ChartData'].index,
                        open=r['ChartData']['Open'],
                        high=r['ChartData']['High'],
                        low=r['ChartData']['Low'],
                        close=r['ChartData']['Close'],
                        increasing_line_color='green', 
                        decreasing_line_color='red'
                    )])
                    
                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=400,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                    )
                    st.plotly_chart(fig, use_container_width=True)
