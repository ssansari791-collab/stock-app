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

# --- 2. पूरे मार्केट (NSE) की लिस्ट (बैंकिंग हटाकर) ---
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

# --- 3. इंडिकेटर्स (RSI, MACD, EMA, MFI) ---
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

# --- 4. स्टॉक एनालिसिस ---
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

        # स्टेटस चेक
        is_breakdown = False
        is_target = False
        is_retest = False
        is_pure_breakout = False

        if was_above_resistance and current_price < resistance_level:
            is_breakdown = True
        elif resistance_level * 0.95 <= current_price <= resistance_level * 1.20:
            if current_price <= resistance_level * 1.05:
                if is_green_candle and current_rsi > 50 and current_macd > current_signal:
                    is_retest = True
            else:
                if current_rsi > 55: 
                    is_retest = True # मजबूत मोमेंटम
        elif current_price > resistance_level * 1.20:
            is_target = True
        
        if (current_price > resistance_level) and (current_rsi > 50) and (current_macd > current_signal):
            is_pure_breakout = True

        return {
            "Stock": symbol.replace('.NS', ''), "Price": current_price, "Level": resistance_level,
            "ChartData": df[-150:], "RSI": round(current_rsi, 2), "EMA_Val": current_ema, 
            "MFI": round(current_mfi, 2), "Flow_Value_Cr": round(last_week_flow, 2),
            "T1": t1, "T2": t2, "T3": t3,
            "Is_Breakdown": is_breakdown, "Is_Target": is_target, 
            "Is_Retest": is_retest, "Is_Pure_Breakout": is_pure_breakout
        }
    except:
        return None

# --- 5. मुख्य UI ---
st.title("⚡ TickStox Pro - प्रो डैशबोर्ड")

if st.button("🚀 पूरे मार्केट को स्कैन करें (5-10 मिनट)", use_container_width=True, type="primary"):
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
    
    # 6 शानदार टैब
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "✅ रीटेस्ट / मोमेंटम", 
        "🔥 सिर्फ ब्रेकआउट", 
        "🚀 ऊपर उड़ान (Targets)", 
        "❌ ब्रेकडाउन (Breakdown)",
        "🟢 पैसा आ रहा है (Inflow)",
        "🔴 पैसा निकल रहा है (Outflow)"
    ])

    # --- टैब 1: रीटेस्ट ---
    with tab1:
        data = sorted([r for r in results if r['Is_Retest']], key=lambda x: x['Price'], reverse=True)
        if not data: st.info("इस टैब में कोई स्टॉक नहीं मिला।")
        for r in data:
            st.markdown(f"**{r['Stock']}** | ₹{r['Price']:.2f} | MFI: {r['MFI']} | RSI: {r['RSI']} | Target 1: ₹{r['T1']:.2f}")

    # --- टैब 2: ब्रेकआउट ---
    with tab2:
        data = sorted([r for r in results if r['Is_Pure_Breakout']], key=lambda x: x['Price'], reverse=True)
        if not data: st.info("इस टैब में कोई स्टॉक नहीं मिला।")
        for r in data:
            st.markdown(f"**{r['Stock']}** | ₹{r['Price']:.2f} | MFI: {r['MFI']} | RSI: {r['RSI']}")

    # --- टैब 3: टारगेट ---
    with tab3:
        data = sorted([r for r in results if r['Is_Target']], key=lambda x: x['Price'], reverse=True)
        if not data: st.info("इस टैब में कोई स्टॉक नहीं मिला।")
        for r in data:
            st.markdown(f"**{r['Stock']}** | ₹{r['Price']:.2f} | T1: ₹{r['T1']:.2f} | T2: ₹{r['T2']:.2f}")

    # --- टैब 4: ब्रेकडाउन ---
    with tab4:
        data = sorted([r for r in results if r['Is_Breakdown']], key=lambda x: x['Price'], reverse=True)
        if not data: st.info("इस टैब में कोई स्टॉक नहीं मिला।")
        for r in data:
            st.markdown(f"**{r['Stock']}** | ₹{r['Price']:.2f} | MFI: {r['MFI']} | RSI: {r['RSI']}")

    # --- टैब 5: इनफ्लो (पैसा आ रहा है) ---
    with tab5:
        data = sorted([r for r in results if r['MFI'] >= 60], key=lambda x: x['Flow_Value_Cr'], reverse=True)
        if not data: 
            st.info("इस टैब में कोई स्टॉक नहीं मिला।")
        else:
            total_cr = sum([r['Flow_Value_Cr'] for r in data])
            st.metric("कुल इनफ्लो (पिछला हफ्ता)", f"₹{total_cr:,.2f} Cr")
            
            # टॉप 10 का ग्राफ
            top_10 = data[:10]
            fig = go.Figure(go.Bar(
                x=[r['Flow_Value_Cr'] for r in top_10],
                y=[r['Stock'] for r in top_10],
                orientation='h',
                marker_color='#00FF00',
                text=[f"₹{r['Flow_Value_Cr']:.1f} Cr" for r in top_10],
                textposition='auto',
            ))
            fig.update_layout(height=400, yaxis=dict(autorange="reversed"), title="टॉप 10 इनफ्लो स्टॉक्स")
            st.plotly_chart(fig, use_container_width=True)
            
            for r in data:
                st.markdown(f"**{r['Stock']}** | ₹{r['Price']:.2f} | **कुल कारोबार: ₹{r['Flow_Value_Cr']:.2f} Cr** | MFI: {r['MFI']}")

    # --- टैब 6: आउटफ्लो (पैसा निकल रहा है) ---
    with tab6:
        data = sorted([r for r in results if r['MFI'] <= 40], key=lambda x: x['Flow_Value_Cr'], reverse=True)
        if not data: 
            st.info("इस टैब में कोई स्टॉक नहीं मिला।")
        else:
            total_cr = sum([r['Flow_Value_Cr'] for r in data])
            st.metric("कुल आउटफ्लो (पिछला हफ्ता)", f"₹{total_cr:,.2f} Cr")
            
            # टॉप 10 का ग्राफ
            top_10 = data[:10]
            fig = go.Figure(go.Bar(
                x=[r['Flow_Value_Cr'] for r in top_10],
                y=[r['Stock'] for r in top_10],
                orientation='h',
                marker_color='#FF0000',
                text=[f"₹{r['Flow_Value_Cr']:.1f} Cr" for r in top_10],
                textposition='auto',
            ))
            fig.update_layout(height=400, yaxis=dict(autorange="reversed"), title="टॉप 10 आउटफ्लो स्टॉक्स")
            st.plotly_chart(fig, use_container_width=True)
            
            for r in data:
                st.markdown(f"**{r['Stock']}** | ₹{r['Price']:.2f} | **कुल कारोबार: ₹{r['Flow_Value_Cr']:.2f} Cr** | MFI: {r['MFI']}")
