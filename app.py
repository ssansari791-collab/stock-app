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
            
            # बैंकिंग और ब्याज आधारित कंपनियों को हटाना
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

# --- 4. "ट्रेडिंग रडार" लॉजिक (हर हाल में स्टॉक पकड़ेगा) ---
def analyze_radar_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5y")
        
        if df.empty or len(df) < 500: return None

        current_price = df['Close'].iloc[-1]
        if current_price < 30: return None

        # पिछले 2 साल का बड़ा रेजिस्टेंस निकालें (आखिरी 500 दिनों से पहले का)
        past_data = df.iloc[:-500] 
        if past_data.empty: return None
        resistance_level = past_data['High'].max()

        # शर्त: स्टॉक रेजिस्टेंस के पास हो (5% नीचे से 50% ऊपर तक) - ताकि कोई छूटे नहीं
        if not (resistance_level * 0.95 <= current_price <= resistance_level * 1.50):
            return None 

        status, color, details = "", "grey", ""
        is_green_candle = df['Close'].iloc[-1] > df['Open'].iloc[-1]
        
        # --- कैटेगरी तय करना ---
        if current_price <= resistance_level * 1.02:
            # रेजिस्टेंस के बिल्कुल पास या थोड़ा ऊपर
            if is_green_candle:
                status = "✅ रीटेस्ट कन्फर्म (ग्रीन कैंडल)"
                color = "#00BFFF"
                details = f"स्टॉक ने ₹{resistance_level:.2f} का रेजिस्टेंस तोड़ा है और अब हरी कैंडल बना रहा है।"
            else:
                status = "🔥 ताजा ब्रेकआउट / रीटेस्ट ज़ोन"
                color = "#00FF00"
                details = f"स्टॉक ने ₹{resistance_level:.2f} का रेजिस्टेंस तोड़ा है और अभी उसी के पास है।"
                
        elif resistance_level * 1.02 < current_price <= resistance_level * 1.15:
            # रेजिस्टेंस से 2% से 15% ऊपर (पहला टारगेट दे रहा है)
            status = "🚀 टारगेट हिट (ऊपर निकल गया)"
            color = "#FFA500"
            details = f"स्टॉक ₹{resistance_level:.2f} का रेजिस्टेंस तोड़कर ऊपर निकल चुका है। यह पहला टारगेट दे रहा है।"
            
        else:
            # रेजिस्टेंस से 15% से ज्यादा ऊपर (काफी ऊपर जा चुका है)
            status = "🎯 रीटेस्ट का इंतज़ार (काफी ऊपर है)"
            color = "#FF0000"
            details = f"स्टॉक ₹{resistance_level:.2f} के रेजिस्टेंस से काफी ऊपर जा चुका है। अगर यह वापस रेजिस्टेंस लाइन पर आए, तो एंट्री मिल सकती है।"

        # वॉल्यूम चेक (बहुत कम वॉल्यूम वाले फेक स्टॉक्स हटा दें)
        avg_volume = df['Volume'].iloc[-20:].mean()
        if df['Volume'].iloc[-1] < (avg_volume * 0.2):
            return None 

        news_sentiment, headlines = get_news_and_sentiment(ticker)
        chart_df = df[-500:] # चार्ट में 2 साल का डेटा दिखाएं

        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": resistance_level,
            "Status": status, "Color": color, "Details": details, "News": news_sentiment,
            "Headlines": headlines, "ChartData": chart_df
        }
    except:
        return None

# --- 5. मुख्य UI ---
st.title("⚡ TickStox Pro - अल्टीमेट ट्रेडिंग रडार")
st.info("🎯 यह रडार पूरे मार्केट से वो सारे स्टॉक्स दिखाता है जिन्होंने 2 साल का रेजिस्टेंस तोड़ा है—चाहे वो अभी टूटा हो, ऊपर निकल गया हो, या रीटेस्ट कर रहा हो।")

if st.button("🚀 पूरे मार्केट का रडार ऑन करें", use_container_width=True):
    with st.spinner("NSE की पूरी लिस्ट लोड हो रही है..."):
        scan_list = get_halal_nse_symbols()
        
    if not scan_list:
        st.error("NSE की लिस्ट लोड नहीं हो पाई। कृपया दोबारा कोशिश करें।")
    else:
        st.success(f"कुल {len(scan_list)} स्टॉक्स स्कैन किए जा रहे हैं... (इसमें 5-10 मिनट लग सकते हैं)")
        
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty() 
        
        for i, stock in enumerate(scan_list):
            res = analyze_radar_stock(stock)
            if res:
                results.append(res)
            
            if i % 50 == 0 or i == len(scan_list) - 1:
                progress = (i + 1) / len(scan_list)
                progress_bar.progress(progress)
                status_text.text(f"स्कैन हो रहा है: {i+1} / {len(scan_list)} (मिले: {len(results)})")
                
        progress_bar.empty()
        status_text.empty()

        if not results:
            st.warning("आज आपकी शर्तों पर कोई स्टॉक नहीं मिला।")
        else:
            # स्टॉक्स को स्टेटस के हिसाब से क्रम में लगाएं (सबसे बेस्ट सबसे ऊपर)
            results = sorted(results, key=lambda x: 0 if "✅" in x['Status'] else (1 if "🔥" in x['Status'] else (2 if "🚀" in x['Status'] else 3)))
            
            st.success(f"कुल {len(results)} स्टॉक्स आपके रडार पर हैं:")
            
            for r in results:
                expander_title = f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"
                
                with st.expander(expander_title):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                        st.markdown(f"**रेजिस्टेंस लेवल:** ₹{r['Level']:.2f}")
                        st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                        st.info(f"**विश्लेषण:** {r['Details']}")
                        
                        # नाम कॉपी करने का बॉक्स
                        st.text_input("📋 नाम कॉपी करें:", value=r['Stock'], key=f"copy_{r['Stock']}")
                        
                    with col2:
                        st.markdown("**📰 ताज़ा न्यूज़:**")
                        st.write(r['News'])
                        for h in r['Headlines'][:2]:
                            st.write(f"- {h}")
                            
                    st.markdown("**📈 चार्ट (रेजिस्टेंस लाइन के साथ):**")
                    
                    # चार्ट बनाना
                    fig = go.Figure(data=[go.Candlestick(
                        x=r['ChartData'].index,
                        open=r['ChartData']['Open'], high=r['ChartData']['High'],
                        low=r['ChartData']['Low'], close=r['ChartData']['Close'],
                        increasing_line_color='green', decreasing_line_color='red'
                    )])
                    
                    # चार्ट पर ब्लू लाइन खींचना
                    fig.add_hline(y=r['Level'], line_dash="dash", line_color="blue", annotation_text="पुराना रेजिस्टेंस (अब सपोर्ट)")
                    
                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=450,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                    )
                    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.info("🛡️ **अस्वीकरण:** यह जानकारी सिर्फ शैक्षिक उद्देश्य के लिए है।")
