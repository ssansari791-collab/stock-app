import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import json
import urllib.parse

st.set_page_config(page_title="TickStox Pro", layout="wide")

# --- 1. सुरक्षित सर्च फंक्शन ---
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
                    stock_options.append({'display': f"{short_name} ({symbol})", 'symbol': symbol})
            return stock_options
    except:
        return []

# --- 2. ब्रेकआउट और रीटेस्ट स्कैनर का लॉजिक ---
def check_breakout_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty or len(df) < 50: return None

        current_price = df['Close'].iloc[-1]
        week_52_high = df['High'].max()
        
        # शर्त 1: स्टॉक 52-वीक हाई के 5% के दायरे में हो (खुले आसमान के पास)
        if current_price < (week_52_high * 0.95): return None

        prev_high = df['High'].iloc[-2]
        avg_volume = df['Volume'].iloc[-20:].mean()
        current_volume = df['Volume'].iloc[-1]

        # शर्त 2: स्टेटस चेक करना
        status, color = "", "grey"
        
        if current_price > prev_high and current_volume > (avg_volume * 1.2):
            status = "🔥 ताजा ब्रेकआउट (Volume Spike)"
            color = "green"
        elif prev_high < current_price <= (prev_high * 1.02):
            status = "🎯 रीटेस्ट ज़ोन में (Near Old High)"
            color = "orange"
        elif df['Close'].iloc[-1] > df['Open'].iloc[-1] and df['Low'].iloc[-1] <= (week_52_high * 0.99):
            status = "✅ रीटेस्ट कन्फर्म (Green Candle)"
            color = "blue"
        elif current_price < prev_high and current_price < df['Open'].iloc[-1]:
            status = "❌ रीटेस्ट फेल / फेक ब्रेकआउट"
            color = "red"
        else:
            status = "📊 हाई के पास (Consolidating)"
            color = "grey"

        # शर्त 3: बैड न्यूज़ चेक करना
        NEGATIVE_KEYWORDS = ['loss', 'fraud', 'penalty', 'downgrade', 'resign', 'sebi', 'probe', 'fall', 'decline', 'debt']
        news_list = ticker.news
        news_status = "🟢 No Bad News"
        
        if news_list:
            for news in news_list[:3]:
                title = news.get('title', '').lower()
                for keyword in NEGATIVE_KEYWORDS:
                    if keyword in title:
                        news_status = f"🔴 BAD NEWS: {news['title'][:30]}..."
                        break

        return {
            "Stock": symbol.replace('.NS', ''),
            "Price": f"₹{current_price:.2f}",
            "52W High": f"₹{week_52_high:.2f}",
            "Status": status,
            "News": news_status,
            "Color": color
        }
    except:
        return None

# --- 3. मुख्य UI ---
st.markdown("### ⚡ TickStox Pro - प्रोफेशनल स्टॉक एनालिटिक्स")

screener_mode = st.radio(
    "🔍 मोड चुनें:",
    ["🔥 स्मार्ट ब्रेकआउट स्कैनर (नया)", "सामान्य लाइव सर्च (Manual)", "🏛️ मजबूत फंडामेंटल स्टॉक"],
    horizontal=True
)

# स्कैनर के लिए स्टॉक्स की लिस्ट
SCAN_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS',
    'SBIN.NS', 'INFY.NS', 'ITC.NS', 'HINDUNILVR.NS', 'LT.NS',
    'BAJFINANCE.NS', 'HCLTECH.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'MARUTI.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ADANIENT.NS',
    'TATAMOTORS.NS', 'M&M.NS', 'POWERGRID.NS', 'NTPC.NS', 'TATASTEEL.NS',
    'ZOMATO.NS', 'MAZDOCK.NS', 'HAL.NS', 'BEL.NS', 'IRFC.NS', 'TRENT.NS'
]

if screener_mode == "🔥 स्मार्ट ब्रेकआउट स्कैनर (नया)":
    st.info("यह स्कैनर सिर्फ उन स्टॉक्स को ढूंढता है जो अपने 52-वीक हाई के 5% के दायरे में हैं (जहाँ ऊपर कोई रेजिस्टेंस नहीं है)।")
    
    if st.button("🚀 स्कैन शुरू करें", use_container_width=True):
        with st.spinner("डेटा स्कैन हो रहा है... इसमें 30-40 सेकंड लग सकते हैं..."):
            results = []
            for stock in SCAN_LIST:
                res = check_breakout_stock(stock)
                if res:
                    results.append(res)
            
            if not results:
                st.warning("आज आपकी शर्तों पर कोई स्टॉक नहीं मिला।")
            else:
                for r in results:
                    card_color = r['Color']
                    st.markdown(f"""
                    <div style="border-left: 5px solid {card_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px; background-color: #1e1e1e; color: white;">
                        <h4 style="margin:0; color: {card_color};">{r['Stock']} | {r['Price']}</h4>
                        <p style="margin:5px 0;">52W High: {r['52W High']} | Status: <b>{r['Status']}</b></p>
                        <p style="margin:0; font-size: 14px;">{r['News']}</p>
                    </div>
                    """, unsafe_allow_html=True)

elif screener_mode == "🏛️ मजबूत फंडामेंटल स्टॉक":
    strong_fund_list = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ITC.NS", "LT.NS", "ICICIBANK.NS", "SBIN.NS"]
    chosen_preset = st.selectbox("मजबूत फंडामेंटल स्टॉक चुनें:", strong_fund_list)
    selected_symbol = chosen_preset
else:
    # सामान्य सर्च
    user_query = st.text_input("🔍 शेयर का नाम टाइप करें (उदा. Zomato, Tata):", "RELIANCE")
    selected_symbol = "RELIANCE.NS"
    if user_query:
        suggestions = fetch_stock_suggestions(user_query.strip())
        if suggestions:
            options_map = {item['display']: item['symbol'] for item in suggestions}
            chosen_display = st.selectbox("👇 स्टॉक चुनें:", list(options_map.keys()))
            selected_symbol = options_map[chosen_display]

# --- 4. सामान्य सर्च वाला पुराना डेटा (यह सिर्फ तब दिखेगा जब स्कैनर नहीं चुना हो) ---
if screener_mode != "🔥 स्मार्ट ब्रेकआउट स्कैनर (नया)":
    st.write("---")
    try:
        stock = yf.Ticker(selected_symbol)
        df = stock.history(period="6mo")
        
        if df.empty:
            st.error(f"❌ '{selected_symbol}' का डेटा नहीं मिला।")
        else:
            latest = df.iloc[-1]
            prev_close = df.iloc[-2]['Close'] if len(df) > 1 else latest['Open']
            
            close_price = latest['Close']
            high_price = latest['High']
            low_price = latest['Low']
            
            change = close_price - prev_close
            change_pct = (change / prev_close) * 100
            
            # पिवट पॉइंट्स
            pivot = (high_price + low_price + close_price) / 3
            r1 = (2 * pivot) - low_price
            s1 = (2 * pivot) - high_price
            
            st.subheader(f"📊 {selected_symbol} - बाजार सारांश")
            m1, m2, m3 = st.columns(3)
            m1.metric("लाइव भाव (Close)", f"₹{close_price:.2f}", f"{change_pct:+.2f}%")
            m2.metric("आज का हाई", f"₹{high_price:.2f}")
            m3.metric("आज का लो", f"₹{low_price:.2f}")
            
            st.markdown(f"**🎯 पिवट पॉइंट (Pivot): ₹{pivot:.2f}**")
            s_col, r_col = st.columns(2)
            with s_col:
                st.write(f"🔵 सपोर्ट (S1): ₹{s1:.2f}")
            with r_col:
                st.write(f"🟢 रेजिस्टेंस (R1): ₹{r1:.2f}")
                
            st.markdown("#### 📈 चार्ट (Price & Volume)")
            chart_df = pd.DataFrame(index=df.index)
            chart_df['Close Price'] = df['Close']
            st.line_chart(chart_df)
            
    except Exception as e:
        st.error(f"डेटा प्रोसेस करने में त्रुटि: {e}")

st.markdown("---")
st.info("🛡️ **अस्वीकरण:** यह ऐप सिर्फ शैक्षिक उद्देश्य के लिए है।")
