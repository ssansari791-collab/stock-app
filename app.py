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

# --- 4. इंडिकेटर्स (RSI, MACD, EMA) ---
def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    return df

# --- 5. स्टॉक एनालिसिस (रियल टारगेट कैलकुलेशन के साथ) ---
def analyze_weekly_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5y", interval="1wk")
        
        if df.empty or len(df) < 100: return None

        df = calculate_indicators(df)
        
        current_price = df['Close'].iloc[-1]
        current_rsi = df['RSI'].iloc[-1]
        current_macd = df['MACD'].iloc[-1]
        current_signal = df['MACD_Signal'].iloc[-1]
        current_ema = df['EMA_20'].iloc[-1]
        
        if current_price < 30: return None

        # 2 साल का रेजिस्टेंस (पुराना हाई)
        past_data = df.iloc[:-50] 
        if past_data.empty: return None
        resistance_level = past_data['High'].max()

        # क्या स्टॉक पहले रेजिस्टेंस तोड़ चुका है?
        was_above_resistance = df['High'].iloc[-50:].max() > resistance_level

        # वॉल्यूम चेक
        avg_volume = df['Volume'].iloc[-10:].mean()
        if df['Volume'].iloc[-1] < (avg_volume * 0.2): return None 

        is_green_candle = df['Close'].iloc[-1] > df['Open'].iloc[-1]
        
        # --- रियल टारगेट कैलकुलेशन ---
        # टारगेट तय करने का फॉर्मूला (रेजिस्टेंस के आधार पर)
        t1 = resistance_level * 1.15 # 15% ऊपर
        t2 = resistance_level * 1.30 # 30% ऊपर
        t3 = resistance_level * 1.50 # 50% ऊपर

        status, color, category = "", "grey", ""
        
        # 1. ब्रेकडाउन (पहले ऊपर गया था, अब वापस लाइन के नीचे)
        if was_above_resistance and current_price < resistance_level:
            status = "❌ ब्रेकडाउन (रीटेस्ट फेल)"
            color = "#FF0000"
            category = "Breakdown"
            
        # 2. ऊपर उड़ान (रियल टारगेट्स)
        elif current_price >= t1:
            if current_price >= t3:
                status = "🚀 तीसरा टारगेट पार (T3)"
            elif current_price >= t2:
                status = "🚀 दूसरा टारगेट पार (T2)"
            else:
                status = "🚀 पहला टारगेट पार (T1)"
            color = "#FF1493"
            category = "Sky High"
            
        # 3. रीटेस्ट ज़ोन (लाइन के 5% के अंदर)
        elif resistance_level * 0.95 <= current_price < t1:
            if is_green_candle and current_rsi > 50 and current_macd > current_signal:
                status = "✅ रीटेस्ट कन्फर्म (सेफ एंट्री)"
                color = "#00BFFF"
            else:
                status = "🎯 रीटेस्ट ज़ोन में"
                color = "#FFA500"
            category = "Retest"

        if category == "": return None

        news_sentiment, headlines = get_news_and_sentiment(ticker)
        chart_df = df[-150:] 

        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": resistance_level,
            "Status": status, "Color": color, "News": news_sentiment,
            "Headlines": headlines, "ChartData": chart_df, "Category": category,
            "RSI": round(current_rsi, 2), "EMA_Val": current_ema,
            "T1": t1, "T2": t2, "T3": t3 # टारगेट की वैल्यू भी साथ भेजें
        }
    except:
        return None

# --- 6. मुख्य UI ---
st.title("⚡ TickStox Pro - रियल टारगेट रडार")
st.info("🎯 यह रडार सिर्फ उन स्टॉक्स को दिखाता है जिन्होंने 2 साल का रेजिस्टेंस तोड़ा है और अब वो अपने असली टारगेट (T1, T2, T3) की तरफ बढ़ रहे हैं।")

filter_option = st.radio(
    "आपको कौन से स्टॉक्स देखने हैं?",
    ["सभी स्टॉक्स (All)", "✅ रीटेस्ट कन्फर्म", "🚀 पहला टारगेट (T1)", "🚀 दूसरा टारगेट (T2)", "🚀 तीसरा टारगेट (T3)", "❌ ब्रेकडाउन (Failed)"],
    horizontal=True
)

if st.button("🚀 स्कैन शुरू करें", use_container_width=True):
    with st.spinner("NSE की पूरी लिस्ट लोड हो रही है..."):
        scan_list = get_halal_nse_symbols()
        
    if not scan_list:
        st.error("NSE की लिस्ट लोड नहीं हो पाई।")
    else:
        st.success(f"कुल {len(scan_list)} स्टॉक्स स्कैन किए जा रहे हैं... (इसमें 5-10 मिनट लग सकते हैं)")
        
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty() 
        
        for i, stock in enumerate(scan_list):
            res = analyze_weekly_stock(stock)
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
            # फ़िल्टर लगाना
            if filter_option == "✅ रीटेस्ट कन्फर्म":
                results = [r for r in results if r['Category'] == 'Retest']
            elif filter_option == "🚀 पहला टारगेट (T1)":
                results = [r for r in results if "T1" in r['Status']]
            elif filter_option == "🚀 दूसरा टारगेट (T2)":
                results = [r for r in results if "T2" in r['Status']]
            elif filter_option == "🚀 तीसरा टारगेट (T3)":
                results = [r for r in results if "T3" in r['Status']]
            elif filter_option == "❌ ब्रेकडाउन (Failed)":
                results = [r for r in results if r['Category'] == 'Breakdown']

            if not results:
                st.warning("इस फ़िल्टर में कोई स्टॉक नहीं मिला।")
            else:
                # लिस्ट को स्टेटस के हिसाब से सजाएं (रीटेस्ट सबसे ऊपर)
                results = sorted(results, key=lambda x: 0 if "✅" in x['Status'] else (1 if "🚀" in x['Status'] else 2))
                st.success(f"कुल {len(results)} स्टॉक्स मिले:")
                
                for r in results:
                    expander_title = f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"
                    
                    with st.expander(expander_title):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                            st.markdown(f"**रेजिस्टेंस (सपोर्ट):** ₹{r['Level']:.2f}")
                            st.markdown(f"**Weekly RSI:** {r['RSI']}")
                            st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                            
                            # असली टारगेट दिखाएं
                            st.markdown("**🎯 टारगेट लेवल्स:**")
                            st.markdown(f"**T1:** ₹{r['T1']:.2f} | **T2:** ₹{r['T2']:.2f} | **T3:** ₹{r['T3']:.2f}")
                            
                            st.info(f"**न्यूज़:** {r['News']}")
                            st.text_input("📋 नाम कॉपी करें:", value=r['Stock'], key=f"copy_{r['Stock']}")
                            
                        with col2:
                            st.markdown("**📰 ताज़ा हेडलाइंस:**")
                            for h in r['Headlines'][:2]:
                                st.write(f"- {h}")
                                
                        st.markdown("**📈 साप्ताहिक (Weekly) चार्ट:**")
                        
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=r['ChartData'].index,
                            open=r['ChartData']['Open'], high=r['ChartData']['High'],
                            low=r['ChartData']['Low'], close=r['ChartData']['Close'],
                            increasing_line_color='green', decreasing_line_color='red',
                            name='Price'
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=r['ChartData'].index, y=r['ChartData']['EMA_20'],
                            line=dict(color='yellow', width=2), name='EMA 20'
                        ))
                        
                        # चार्ट पर सभी टारगेट लाइनें खींचें
                        fig.add_hline(y=r['Level'], line_dash="dash", line_color="blue", annotation_text="पुराना रेजिस्टेंस")
                        fig.add_hline(y=r['T1'], line_dash="dot", line_color="orange", annotation_text="Target 1")
                        fig.add_hline(y=r['T2'], line_dash="dot", line_color="purple", annotation_text="Target 2")
                        fig.add_hline(y=r['T3'], line_dash="dot", line_color="red", annotation_text="Target 3")
                        
                        fig.update_layout(
                            xaxis_rangeslider_visible=False,
                            height=450,
                            margin=dict(l=10, r=10, t=10, b=10),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            showlegend=True
                        )
                        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.info("🛡️ **अस्वीकरण:** यह जानकारी सिर्फ शैक्षिक उद्देश्य के लिए है।")
