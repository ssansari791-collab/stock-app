import streamlit as st
import pandas as pd
import requests
from io import StringIO

# --- 1. पैकेज इंस्टॉल करने का जुगाड़ ---
try:
    import plotly.graph_objects as go
    import plotly.express as px
    import yfinance as yf
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly", "yfinance"])
    import plotly.graph_objects as go
    import plotly.express as px
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

# --- 4. इंडिकेटर्स (RSI, MACD, EMA, MFI, और Money Flow Value) ---
def calculate_indicators(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # EMA 20
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # MFI (Money Flow Index)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    
    positive_flow_sum = positive_flow.rolling(window=14).sum()
    negative_flow_sum = negative_flow.rolling(window=14).sum()
    
    money_ratio = positive_flow_sum / negative_flow_sum
    df['MFI'] = 100 - (100 / (1 + money_ratio))
    df['MFI'] = df['MFI'].fillna(50) 
    
    # Money Flow Value (अंदाजा लगाने के लिए कि कितना पैसा मूव हुआ)
    df['Flow_Value'] = df['Volume'] * df['Close']
    
    return df

# --- 5. स्टॉक एनालिसिस ---
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
        current_mfi = df['MFI'].iloc[-1] 
        
        # पिछले हफ्ते का कुल ट्रेडिंग वैल्यू (करोड़ों में)
        last_week_flow = df['Flow_Value'].iloc[-1] / 10000000 # 1 Crore = 10 Million
        
        if current_price < 30: return None

        past_data = df.iloc[:-50] 
        if past_data.empty: return None
        resistance_level = past_data['High'].max()

        was_above_resistance = df['High'].iloc[-50:].max() > resistance_level

        avg_volume = df['Volume'].iloc[-10:].mean()
        if df['Volume'].iloc[-1] < (avg_volume * 0.1): return None 

        is_green_candle = df['Close'].iloc[-1] > df['Open'].iloc[-1]
        
        t1 = resistance_level * 1.15 
        t2 = resistance_level * 1.30 
        t3 = resistance_level * 1.50 

        status, color, category = "", "grey", ""
        
        if was_above_resistance and current_price < resistance_level:
            status = "❌ ब्रेकडाउन (रीटेस्ट फेल)"
            color = "#FF0000"
            category = "Breakdown"
            
        elif resistance_level * 0.95 <= current_price <= resistance_level * 1.20:
            if current_price <= resistance_level * 1.05:
                if is_green_candle and current_rsi > 50 and current_macd > current_signal:
                    status = "✅ रीटेस्ट कन्फर्म (सेफ एंट्री)"
                    color = "#00BFFF"
                else:
                    status = "🎯 रीटेस्ट ज़ोन में"
                    color = "#FFA500"
            else:
                if current_rsi > 55: 
                    status = "🔥 मजबूत मोमेंटम (ऊपर निकला)"
                    color = "#00FF00"
                else:
                    category = "" 
            if category != "":
                category = "Retest"
            
        elif current_price > resistance_level * 1.20:
            if current_price >= t3:
                status = "🚀 तीसरा टारगेट पार (T3)"
            elif current_price >= t2:
                status = "🚀 दूसरा टारगेट पार (T2)"
            else:
                status = "🚀 पहला टारगेट पार (T1)"
            color = "#FF1493"
            category = "Targets"

        if category == "":
            if current_mfi >= 60:
                status = "🟢 सिर्फ पैसा आ रहा है (Inflow)"
                color = "#00FF00"
                category = "InflowOnly"
            elif current_mfi <= 40:
                status = "🔴 पैसा निकल रहा है (Outflow)"
                color = "#FF0000"
                category = "OutflowOnly"
            else:
                return None 

        is_pure_breakout = (current_price > resistance_level) and (current_rsi > 50) and (current_macd > current_signal)

        news_sentiment, headlines = get_news_and_sentiment(ticker)
        chart_df = df[-150:] 

        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": resistance_level,
            "Status": status, "Color": color, "News": news_sentiment,
            "Headlines": headlines, "ChartData": chart_df, "Category": category,
            "RSI": round(current_rsi, 2), "EMA_Val": current_ema, "MFI": round(current_mfi, 2),
            "Flow_Value_Cr": round(last_week_flow, 2), # करोड़ों में वैल्यू
            "T1": t1, "T2": t2, "T3": t3, "Is_Pure_Breakout": is_pure_breakout
        }
    except:
        return None

# --- 6. मुख्य UI ---
st.title("⚡ TickStox Pro - रियल टारगेट रडार")
st.info("🎯 यह रडार 2 साल का रेजिस्टेंस तोड़ने वाले स्टॉक्स के साथ-साथ **स्मार्ट मनी (Money Flow)** को भी ट्रैक करता है।")

filter_option = st.radio(
    "मुख्य मेनू चुनें:",
    ["✅ रीटेस्ट / मोमेंटम", "🔥 सिर्फ ब्रेकआउट", "🚀 ऊपर उड़ान (Targets)", "❌ ब्रेकडाउन (Breakdown)", "🟢 पैसा आ रहा है (Inflow)", "🔴 पैसा निकल रहा है (Outflow)"],
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
            # ==========================================
            # 🚨 नया डैशबोर्ड लुक (सिर्फ Inflow/Outflow के लिए)
            # ==========================================
            if filter_option in ["🟢 पैसा आ रहा है (Inflow)", "🔴 पैसा निकल रहा है (Outflow)"]:
                
                # डेटा फ़िल्टर करें
                if filter_option == "🟢 पैसा आ रहा है (Inflow)":
                    flow_data = [r for r in results if r['MFI'] >= 60]
                    flow_data = sorted(flow_data, key=lambda x: x['Flow_Value_Cr'], reverse=True)
                    main_color = "#00FF00"
                    title_text = "🟢 कुल पैसा आ रहा है (Inflow)"
                else:
                    flow_data = [r for r in results if r['MFI'] <= 40]
                    flow_data = sorted(flow_data, key=lambda x: x['Flow_Value_Cr'], reverse=True)
                    main_color = "#FF0000"
                    title_text = "🔴 कुल पैसा निकल रहा है (Outflow)"

                if not flow_data:
                    st.warning("इस टैब में कोई स्टॉक नहीं मिला।")
                else:
                    # 1. मीट्रिक्स (करोड़ों में टोटल वैल्यू)
                    total_flow_cr = sum([r['Flow_Value_Cr'] for r in flow_data])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="कुल फंड मूवमेंट (पिछला हफ्ता)", value=f"₹{total_flow_cr:,.2f} Cr", delta="हाई वॉल्यूम" if main_color == "#00FF00" else "-भारी बिकवाली", delta_color="normal" if main_color == "#00FF00" else "inverse")
                    with col2:
                        st.metric(label="कुल स्टॉक्स", value=f"{len(flow_data)}", delta="एक्टिव")

                    # 2. ग्राफिक्स (बार चार्ट)
                    st.markdown(f"#### 📊 {title_text} - टॉप 10 स्टॉक्स")
                    
                    # टॉप 10 निकालें
                    top_stocks = flow_data[:10]
                    stock_names = [r['Stock'] for r in top_stocks]
                    flow_values = [r['Flow_Value_Cr'] for r in top_stocks]
                    
                    fig = go.Figure(go.Bar(
                        x=flow_values,
                        y=stock_names,
                        orientation='h',
                        marker_color=main_color,
                        text=[f"₹{val:.1f} Cr" for val in flow_values],
                        textposition='auto',
                    ))
                    fig.update_layout(
                        height=400,
                        margin=dict(l=10, r=10, t=10, b=10),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        yaxis=dict(autorange="reversed") # सबसे ऊपर वाला सबसे बड़ा हो
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("---")
                    st.markdown("#### 📋 पूरी लिस्ट (क्लिक करके डिटेल देखें)")

            else:
                # बाकी टैब के लिए पुराना फ़िल्टर
                if filter_option == "✅ रीटेस्ट / मोमेंटम":
                    results = [r for r in results if r['Category'] == 'Retest']
                    results = sorted(results, key=lambda x: 0 if "✅" in x['Status'] else 1)
                elif filter_option == "🔥 सिर्फ ब्रेकआउट":
                    results = [r for r in results if r['Is_Pure_Breakout'] == True]
                    results = sorted(results, key=lambda x: x['Price'], reverse=True)
                elif filter_option == "🚀 ऊपर उड़ान (Targets)":
                    results = [r for r in results if r['Category'] == 'Targets']
                    results = sorted(results, key=lambda x: 0 if "T1" in x['Status'] else (1 if "T2" in x['Status'] else 2))
                elif filter_option == "❌ ब्रेकडाउन (Breakdown)":
                    results = [r for r in results if r['Category'] == 'Breakdown']

                if not results:
                    st.warning("इस टैब में कोई स्टॉक नहीं मिला।")
                else:
                    st.success(f"कुल {len(results)} स्टॉक्स मिले:")
                    
                    # स्टॉक कार्ड दिखाना
                    for r in results:
                        expander_title = f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"
                        
                        with st.expander(expander_title):
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                                st.markdown(f"**रेजिस्टेंस (सपोर्ट):** ₹{r['Level']:.2f}")
                                st.markdown(f"**Weekly RSI:** {r['RSI']}")
                                
                                mfi_color = "green" if r['MFI'] >= 60 else ("red" if r['MFI'] <= 40 else "orange")
                                st.markdown(f"**Weekly MFI (Money Flow):** <span style='color:{mfi_color}; font-weight:bold;'>{r['MFI']}</span>", unsafe_allow_html=True)
                                
                                st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                                
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
