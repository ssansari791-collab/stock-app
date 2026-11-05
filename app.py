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

# --- 2. कस्टम CSS (डिब्बों को सुंदर बनाने के लिए) ---
st.markdown("""
<style>
    .inflow-box {
        background-color: rgba(0, 255, 0, 0.1);
        border: 2px solid #00FF00;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        color: #00FF00;
        font-size: 24px;
        font-weight: bold;
        box-shadow: 0 0 10px #00FF00;
    }
    .outflow-box {
        background-color: rgba(255, 0, 0, 0.1);
        border: 2px solid #FF0000;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        color: #FF0000;
        font-size: 24px;
        font-weight: bold;
        box-shadow: 0 0 10px #FF0000;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. पूरे मार्केट (NSE) की लिस्ट (बैंकिंग हटाकर) ---
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

# --- 4. इंडिकेटर्स (RSI, MACD, EMA, MFI) ---
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
    
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)
    positive_flow_sum = positive_flow.rolling(window=14).sum()
    negative_flow_sum = negative_flow.rolling(window=14).sum()
    money_ratio = positive_flow_sum / negative_flow_sum
    df['MFI'] = 100 - (100 / (1 + money_ratio))
    df['MFI'] = df['MFI'].fillna(50) 
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
        last_week_flow = df['Flow_Value'].iloc[-1] / 10000000 
        
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
        
        # पुराना लॉजिक
        if was_above_resistance and current_price < resistance_level:
            status = "❌ ब्रेकडाउन"
            color = "#FF0000"
            category = "Breakdown"
        elif resistance_level * 0.95 <= current_price <= resistance_level * 1.20:
            if current_price <= resistance_level * 1.05:
                if is_green_candle and current_rsi > 50 and current_macd > current_signal:
                    status = "✅ रीटेस्ट कन्फर्म"
                    color = "#00BFFF"
                else:
                    status = "🎯 रीटेस्ट ज़ोन"
                    color = "#FFA500"
            else:
                if current_rsi > 55: 
                    status = "🔥 मजबूत मोमेंटम"
                    color = "#00FF00"
                else:
                    category = "" 
            if category != "":
                category = "Retest"
        elif current_price > resistance_level * 1.20:
            if current_price >= t3: status = "🚀 तीसरा टारगेट (T3)"
            elif current_price >= t2: status = "🚀 दूसरा टारगेट (T2)"
            else: status = "🚀 पहला टारगेट (T1)"
            color = "#FF1493"
            category = "Targets"

        # मनी फ्लो लॉजिक
        if category == "":
            if current_mfi >= 60:
                status = "🟢 पैसा आ रहा है"
                color = "#00FF00"
                category = "InflowOnly"
            elif current_mfi <= 40:
                status = "🔴 पैसा निकल रहा है"
                color = "#FF0000"
                category = "OutflowOnly"
            else:
                return None 

        is_pure_breakout = (current_price > resistance_level) and (current_rsi > 50) and (current_macd > current_signal)

        # न्यूज़ (स्कैन फास्ट करने के लिए इसे हल्का रखा है)
        news_status = "🟢 कोई बुरी खबर नहीं"
        headlines = []
        
        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": resistance_level,
            "Status": status, "Color": color, "News": news_status,
            "Headlines": headlines, "ChartData": df[-150:], "Category": category,
            "RSI": round(current_rsi, 2), "EMA_Val": current_ema, "MFI": round(current_mfi, 2),
            "Flow_Value_Cr": round(last_week_flow, 2),
            "T1": t1, "T2": t2, "T3": t3, "Is_Pure_Breakout": is_pure_breakout
        }
    except:
        return None

# --- 6. मुख्य UI ---
st.title("⚡ TickStox Pro - प्रो डैशबोर्ड")

# स्कैन बटन (डेटा को सेव करने के लिए Session State)
if st.button("🚀 पूरे मार्केट को स्कैन करें (5-10 मिनट)", use_container_width=True):
    with st.spinner("डेटा स्कैन हो रहा है... कृपया प्रतीक्षा करें..."):
        scan_list = get_halal_nse_symbols()
        results = []
        progress_bar = st.progress(0)
        
        for i, stock in enumerate(scan_list):
            res = analyze_weekly_stock(stock)
            if res: results.append(res)
            if i % 50 == 0 or i == len(scan_list) - 1:
                progress_bar.progress((i + 1) / len(scan_list))
                
        st.session_state['scan_results'] = results
        st.success(f"स्कैन पूरा हुआ! कुल {len(results)} स्टॉक्स मिले।")

# अगर डेटा स्कैन हो चुका है, तो UI दिखाएं
if 'scan_results' in st.session_state:
    results = st.session_state['scan_results']
    
    # 1. पुराने 4 टैब (रेडियो बटन)
    st.markdown("### 🔍 ब्रेकआउट और टारगेट स्कैनर")
    filter_option = st.radio(
        "टैब चुनें:",
        ["✅ रीटेस्ट / मोमेंटम", "🔥 सिर्फ ब्रेकआउट", "🚀 ऊपर उड़ान (Targets)", "❌ ब्रेकडाउन (Breakdown)"],
        horizontal=True
    )

    st.markdown("---")
    
    # 2. नया मनी फ्लो डैशबोर्ड (बड़े डिब्बे)
    st.markdown("### 💰 मनी फ्लो रडार (स्मार्ट मनी)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="inflow-box">🟢 पैसा आ रहा है (Inflow)</div>', unsafe_allow_html=True)
        btn_inflow = st.button("यहाँ क्लिक करें (Inflow)", use_container_width=True, type="primary")
    with col2:
        st.markdown('<div class="outflow-box">🔴 पैसा निकल रहा है (Outflow)</div>', unsafe_allow_html=True)
        btn_outflow = st.button("यहाँ क्लिक करें (Outflow)", use_container_width=True, type="secondary")

    st.markdown("---")

    # 3. डेटा दिखाने का लॉजिक
    display_data = []
    show_dashboard = False
    
    if btn_inflow:
        display_data = [r for r in results if r['MFI'] >= 60]
        display_data = sorted(display_data, key=lambda x: x['Flow_Value_Cr'], reverse=True)
        show_dashboard = True
        main_color = "#00FF00"
        title_text = "🟢 टॉप इनफ्लो स्टॉक्स"
    elif btn_outflow:
        display_data = [r for r in results if r['MFI'] <= 40]
        display_data = sorted(display_data, key=lambda x: x['Flow_Value_Cr'], reverse=True)
        show_dashboard = True
        main_color = "#FF0000"
        title_text = "🔴 टॉप आउटफ्लो स्टॉक्स"
    else:
        # अगर रेडियो बटन वाले टैब पर क्लिक किया है
        if filter_option == "✅ रीटेस्ट / मोमेंटम":
            display_data = sorted([r for r in results if r['Category'] == 'Retest'], key=lambda x: 0 if "✅" in x['Status'] else 1)
        elif filter_option == "🔥 सिर्फ ब्रेकआउट":
            display_data = sorted([r for r in results if r['Is_Pure_Breakout'] == True], key=lambda x: x['Price'], reverse=True)
        elif filter_option == "🚀 ऊपर उड़ान (Targets)":
            display_data = sorted([r for r in results if r['Category'] == 'Targets'], key=lambda x: 0 if "T1" in x['Status'] else 1)
        elif filter_option == "❌ ब्रेकडाउन (Breakdown)":
            display_data = [r for r in results if r['Category'] == 'Breakdown']

    if not display_data:
        st.warning("इस सेक्शन में कोई स्टॉक नहीं मिला।")
    else:
        # अगर मनी फ्लो बटन दबाया है, तो ग्राफ दिखाएं
        if show_dashboard:
            total_flow_cr = sum([r['Flow_Value_Cr'] for r in display_data])
            st.metric(label="कुल फंड मूवमेंट (पिछला हफ्ता)", value=f"₹{total_flow_cr:,.2f} Cr")
            
            top_stocks = display_data[:10]
            fig = go.Figure(go.Bar(
                x=[r['Flow_Value_Cr'] for r in top_stocks],
                y=[r['Stock'] for r in top_stocks],
                orientation='h',
                marker_color=main_color,
                text=[f"₹{val:.1f} Cr" for val in [r['Flow_Value_Cr'] for r in top_stocks]],
                textposition='auto',
            ))
            fig.update_layout(height=400, yaxis=dict(autorange="reversed"), title=title_text)
            st.plotly_chart(fig, use_container_width=True)
            
        # स्टॉक्स की लिस्ट
        for r in display_data:
            with st.expander(f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                    st.markdown(f"**MFI:** {r['MFI']} | **RSI:** {r['RSI']}")
                    st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**टारगेट:** T1: ₹{r['T1']:.2f} | T2: ₹{r['T2']:.2f}")
                
                fig = go.Figure(data=[go.Candlestick(x=r['ChartData'].index, open=r['ChartData']['Open'], high=r['ChartData']['High'], low=r['ChartData']['Low'], close=r['ChartData']['Close'], increasing_line_color='green', decreasing_line_color='red')])
                fig.add_hline(y=r['Level'], line_dash="dash", line_color="blue", annotation_text="रेजिस्टेंस")
                fig.update_layout(xaxis_rangeslider_visible=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
        
