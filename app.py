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

# --- 2. पूरे मार्केट (NSE) की सभी स्टॉक्स की लिस्ट (बैंकिंग हटाकर) ---
@st.cache_data(ttl=86400) 
def get_halal_nse_symbols():
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            
            # बैंकिंग, ब्याज और फाइनेंस सेक्टर को हटाने के लिए
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

# --- 4. RSI और MACD कैलकुलेट करने का फंक्शन (Weekly के लिए) ---
def calculate_indicators(df):
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

# --- 5. "साप्ताहिक (Weekly)" आसमान छूने वाले स्टॉक्स का लॉजिक ---
def analyze_sky_rocket_weekly(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        # 🚨 सबसे बड़ा बदलाव: अब हम '1wk' (Weekly) डेटा मंगवा रहे हैं
        df = ticker.history(period="5y", interval="1wk")
        
        if df.empty or len(df) < 100: return None

        # इंडिकेटर्स कैलकुलेट करें
        df = calculate_indicators(df)
        
        current_price = df['Close'].iloc[-1]
        current_rsi = df['RSI'].iloc[-1]
        current_macd = df['MACD'].iloc[-1]
        current_signal = df['MACD_Signal'].iloc[-1]
        
        if current_price < 30: return None

        # 🚨 RSI फिल्टर: RSI 50 से ऊपर होना चाहिए
        if current_rsi < 50:
            return None

        # 🚨 MACD फिल्टर: MACD लाइन सिग्नल लाइन के ऊपर होनी चाहिए (तेजी का मोमेंटम)
        if current_macd < current_signal:
            return None

        # 2-3 साल का बड़ा रेजिस्टेंस (पुराना हाई) निकालें
        # 5 साल में लगभग 250 हफ्ते होते हैं। हम आखिरी 50 हफ्ते (1 साल) छोड़कर बाकी डेटा से रेजिस्टेंस निकालेंगे
        past_data = df.iloc[:-50] 
        if past_data.empty: return None
        resistance_level = past_data['High'].max()

        # शर्त 1: स्टॉक का भाव उस रेजिस्टेंस से ऊपर हो (ब्रेकआउट हो चुका हो)
        if current_price <= resistance_level:
            return None 

        # शर्त 2 (सेफ्टी चेक): अगर स्टॉक रेजिस्टेंस से 25% से ज्यादा ऊपर उड़ चुका है, तो छोड़ दें
        if current_price > (resistance_level * 1.25):
            return None

        # कैटेगरी तय करना
        status, color, details, category = "", "grey", "", ""
        is_green_candle = df['Close'].iloc[-1] > df['Open'].iloc[-1]
        
        # 1. रीटेस्ट ज़ोन (लाइन के 7% के अंदर)
        if resistance_level * 0.93 <= current_price <= resistance_level * 1.07:
            if is_green_candle:
                status = "✅ रीटेस्ट कन्फर्म (Weekly Green)"
                color = "#00BFFF"
                details = f"स्टॉक ने ₹{resistance_level:.2f} का रेजिस्टेंस तोड़ा और वापस उसी पर आकर हफ्ते की हरी कैंडल बना रहा है। सबसे सेफ एंट्री।"
            else:
                status = "🎯 रीटेस्ट ज़ोन में"
                color = "#FFA500"
                details = f"स्टॉक ने ₹{resistance_level:.2f} का रेजिस्टेंस तोड़ा और अब उसी के पास है।"
            category = "Retest"
            
        # 2. टारगेट हिट (लाइन से 7% से 25% ऊपर)
        elif resistance_level * 1.07 < current_price <= resistance_level * 1.25:
            status = "🔥 नया ब्रेकआउट (Weekly)"
            color = "#00FF00"
            details = f"स्टॉक ने ₹{resistance_level:.2f} का बड़ा रेजिस्टेंस तोड़ लिया है और अब ऊपर की तरफ बढ़ रहा है।"
            category = "Fresh"

        # वॉल्यूम चेक (हफ्ते का औसत वॉल्यूम)
        avg_volume = df['Volume'].iloc[-10:].mean()
        if df['Volume'].iloc[-1] < (avg_volume * 0.2):
            return None 

        news_sentiment, headlines = get_news_and_sentiment(ticker)
        chart_df = df[-150:] # चार्ट में 3 साल का हफ्ते वार डेटा दिखाएं

        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": resistance_level,
            "Status": status, "Color": color, "Details": details, "News": news_sentiment,
            "Headlines": headlines, "ChartData": chart_df, "Category": category,
            "RSI": round(current_rsi, 2)
        }
    except:
        return None

# --- 6. मुख्य UI ---
st.title("⚡ TickStox Pro - साप्ताहिक (Weekly) ब्रेकआउट स्कैनर")
st.info("🎯 यह स्कैनर पूरे मार्केट को **हफ्ते (Weekly)** के हिसाब से स्कैन करता है। सिर्फ वही स्टॉक्स आएंगे जो 2-3 साल का रेजिस्टेंस तोड़ चुके हैं, जिनका **Weekly RSI 50+** है और **MACD तेजी** में है।")

# फ़िल्टर ऑप्शन
filter_option = st.radio(
    "आपको कौन से स्टॉक्स देखने हैं?",
    ["सभी स्टॉक्स (All)", "🔥 नया ब्रेकआउट (Fresh Breakout)", "✅ रीटेस्ट कन्फर्म (Safe Entry)"],
    horizontal=True
)

if st.button("🚀 मेरे लिए बेस्ट स्टॉक्स खोजो", use_container_width=True):
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
            res = analyze_sky_rocket_weekly(stock)
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
            # रिजल्ट्स को फ़िल्टर करना
            if filter_option == "🔥 नया ब्रेकआउट (Fresh Breakout)":
                results = [r for r in results if r['Category'] == 'Fresh']
            elif filter_option == "✅ रीटेस्ट कन्फर्म (Safe Entry)":
                results = [r for r in results if r['Category'] == 'Retest']

            if not results:
                st.warning("इस फ़िल्टर में कोई स्टॉक नहीं मिला। कृपया 'सभी स्टॉक्स' चुनकर देखें।")
            else:
                # कन्फर्म वाले स्टॉक्स सबसे ऊपर
                results = sorted(results, key=lambda x: 0 if "✅" in x['Status'] else (1 if "🔥" in x['Status'] else 2))
                st.success(f"कुल {len(results)} शानदार स्टॉक्स मिले:")
                
                for r in results:
                    expander_title = f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"
                    
                    with st.expander(expander_title):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                            st.markdown(f"**रेजिस्टेंस लेवल:** ₹{r['Level']:.2f}")
                            st.markdown(f"**Weekly RSI:** {r['RSI']}")
                            st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                            st.info(f"**विश्लेषण:** {r['Details']}")
                            
                            # नाम कॉपी करने का बॉक्स
                            st.text_input("📋 नाम कॉपी करें:", value=r['Stock'], key=f"copy_{r['Stock']}")
                            
                        with col2:
                            st.markdown("**📰 ताज़ा न्यूज़:**")
                            st.write(r['News'])
                            for h in r['Headlines'][:2]:
                                st.write(f"- {h}")
                                
                        st.markdown("**📈 साप्ताहिक (Weekly) चार्ट (रेजिस्टेंस लाइन के साथ):**")
                        
                        # चार्ट बनाना (अब यह हफ्ते वाला चार्ट दिखाएगा)
                        fig = go.Figure(data=[go.Candlestick(
                            x=r['ChartData'].index,
                            open=r['ChartData']['Open'], high=r['ChartData']['High'],
                            low=r['ChartData']['Low'], close=r['ChartData']['Close'],
                            increasing_line_color='green', decreasing_line_color='red'
                        )])
                        
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
