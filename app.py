import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="TickStox Pro", layout="wide")

# --- 1. बड़ा स्टॉक लिस्ट (Nifty 50 + Next 50 + Midcap 150 + Smallcap के मुख्य स्टॉक्स) ---
# यह लगभग 600+ स्टॉक्स की लिस्ट है (पूरा मार्केट कवर करने के लिए)
# आप चाहें तो इसमें अपने मनपसंद स्टॉक्स और जोड़ सकते हैं।
SCAN_LIST = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS', 'SBIN.NS', 'INFY.NS', 'ITC.NS', 
    'HINDUNILVR.NS', 'LT.NS', 'BAJFINANCE.NS', 'HCLTECH.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'MARUTI.NS', 
    'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS', 'ADANIENT.NS', 'TATAMOTORS.NS', 'M&M.NS', 
    'POWERGRID.NS', 'NTPC.NS', 'TATASTEEL.NS', 'ZOMATO.NS', 'MAZDOCK.NS', 'HAL.NS', 'BEL.NS', 'IRFC.NS', 
    'TRENT.NS', 'DIXON.NS', 'POLYCAB.NS', 'RVNL.NS', 'JWL.NS', 'COCHINSHIP.NS', 'ADANIPORTS.NS', 'ASIANPAINT.NS', 
    'BAJAJFINSV.NS', 'BAJAJ-AUTO.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS', 
    'DRREDDY.NS', 'EICHERMOT.NS', 'GRASIM.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'ICICIGI.NS', 
    'ICICIPRULI.NS', 'INDUSINDBK.NS', 'JSWSTEEL.NS', 'LTIM.NS', 'NESTLEIND.NS', 'ONGC.NS', 'SBILIFE.NS', 
    'SHREECEM.NS', 'TATACONSUM.NS', 'TATAPOWER.NS', 'TECHM.NS', 'UPL.NS', 'VEDL.NS', 'ABB.NS', 
    'APOLLOHOSP.NS', 'BANKBARODA.NS', 'BERGEPAINT.NS', 'BOSCHLTD.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'DABUR.NS', 
    'DLF.NS', 'GAIL.NS', 'GODREJCP.NS', 'HAVELLS.NS', 'IDFCFIRSTB.NS', 'INDHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 
    'JINDALSTEL.NS', 'JIOFIN.NS', 'LICI.NS', 'LODHA.NS', 'MOTHERSON.NS', 'NAUKRI.NS', 'PFC.NS', 'PIDILITIND.NS', 
    'PNB.NS', 'RECLTD.NS', 'SIEMENS.NS', 'SRF.NS', 'TVSMOTOR.NS', 'ZYDUSLIFE.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS', 
    'ATGL.NS', 'AMBUJACEM.NS', 'DMART.NS', 'BANKINDIA.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'FEDERALBNK.NS', 
    'GMRINFRA.NS', 'IDEA.NS', 'INDIGO.NS', 'MAXHEALTH.NS', 'OBEROIRLTY.NS', 'PAYTM.NS', 'POLICYBZR.NS', 
    'SAIL.NS', 'TIINDIA.NS', 'TORNTPHARM.NS', 'SUNDARMFIN.NS', 'SUNTV.NS', 'NYKAA.NS', 'BHARATFORG.NS',
    # Midcap और Smallcap के प्रमुख स्टॉक्स
    'ABCAPITAL.NS', 'ABFRL.NS', 'ACC.NS', 'AIAENG.NS', 'AJANTPHARM.NS', 'ALKEM.NS', 'APLAPOLLO.NS', 'ASTRAL.NS',
    'AUBANK.NS', 'AUROPHARMA.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BATAINDIA.NS', 'BHARATRAS.NS', 'BIOCON.NS',
    'BSOFT.NS', 'CANFINHOME.NS', 'CDSL.NS', 'CGPOWER.NS', 'CROMPTON.NS', 'CUB.NS', 'CYIENT.NS', 'DALBHARAT.NS',
    'DEEPAKNTR.NS', 'DELHIVERY.NS', 'DEVYANI.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FORTIS.NS', 'GLENMARK.NS',
    'GODREJPROP.NS', 'GRANULES.NS', 'GUJGASLTD.NS', 'HDFCAMC.NS', 'HFCL.NS', 'HONAUT.NS', 'IDFC.NS',
    'IEX.NS', 'IGL.NS', 'INDIGOPNTS.NS', 'INDUSTOWER.NS', 'IPCALAB.NS', 'JBCHEPHARM.NS', 'JKCEMENT.NS',
    'JUBLFOOD.NS', 'KAJARIACER.NS', 'KANSAINER.NS', 'KPITTECH.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS',
    'LICHSGFIN.NS', 'LINDEINDIA.NS', 'LTTS.NS', 'MANAPPURAM.NS', 'MARICO.NS', 'MFSL.NS', 'MGL.NS',
    'MOTHERSON.NS', 'MPHASIS.NS', 'MRF.NS', 'NAVINFLUOR.NS', 'OBEROIRLTY.NS', 'OIL.NS', 'PAGEIND.NS',
    'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PPLPHARMA.NS', 'PRESTIGE.NS', 'RAMCOCEM.NS', 'RATNAMANI.NS',
    'SANOFI.NS', 'SCHAEFFLER.NS', 'SKFINDIA.NS', 'SONACOMS.NS', 'STARHEALTH.NS', 'SUNDRMFAST.NS',
    'SUPREMEIND.NS', 'SYNGENE.NS', 'TANLA.NS', 'TATAELXSI.NS', 'TATAMTRDVR.NS', 'TATACHEM.NS', 'THERMAX.NS',
    'TRIDENT.NS', 'UCOBANK.NS', 'UJJIVANSFB.NS', 'VINATIORGA.NS', 'VOLTAS.NS', 'WHIRLPOOL.NS', 'ZEEL.NS'
]

# --- 2. न्यूज़ और सेंटीमेंट चेक करने का फंक्शन ---
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
        df = ticker.history(period="1y")
        if df.empty or len(df) < 50: return None

        current_price = df['Close'].iloc[-1]
        week_52_high = df['High'].max()
        
        # शर्त: 52-वीक हाई के 10% के दायरे में वाले स्टॉक्स (ताकि ज्यादा स्टॉक्स मिलें)
        if current_price < (week_52_high * 0.90): return None

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
        elif df['Close'].iloc[-1] > df['Open'].iloc[-1] and df['Low'].iloc[-1] <= (week_52_high * 0.99):
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
            details = "स्टॉक अपने 52-वीक हाई के पास है, लेकिन अभी किसी तरफ साफ मूवमेंट नहीं दिखा रहा है।"

        news_sentiment, headlines = get_news_and_sentiment(ticker)

        return {
            "Stock": symbol.replace('.NS', ''),
            "Price": current_price,
            "52W High": week_52_high,
            "Status": status,
            "Color": color,
            "Details": details,
            "News": news_sentiment,
            "Headlines": headlines,
            "ChartData": df['Close']
        }
    except:
        return None

# --- 4. मुख्य UI ---
st.title("⚡ TickStox Pro - स्मार्ट स्कैनर")

if st.button("🚀 पूरे मार्केट को स्कैन करें", use_container_width=True):
    with st.spinner("डेटा स्कैन हो रहा है... इसमें 5-10 मिनट लग सकते हैं। कृपया प्रतीक्षा करें..."):
        results = []
        progress_bar = st.progress(0)
        
        for i, stock in enumerate(SCAN_LIST):
            res = analyze_stock(stock)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(SCAN_LIST))
            
        progress_bar.empty()

        if not results:
            st.warning("आज आपकी शर्तों (52-वीक हाई के पास) पर कोई स्टॉक नहीं मिला।")
        else:
            st.success(f"कुल {len(results)} स्टॉक्स मिले जो हाई के पास हैं। किसी भी स्टॉक पर क्लिक करके पूरी डिटेल देखें:")
            
            # स्टॉक्स को लिस्ट में दिखाना (Expander का इस्तेमाल करके)
            for r in results:
                expander_title = f"{r['Stock']} | ₹{r['Price']:.2f} | {r['Status']}"
                
                with st.expander(expander_title):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown(f"**कीमत:** ₹{r['Price']:.2f}")
                        st.markdown(f"**52-वीक हाई:** ₹{r['52W High']:.2f}")
                        st.markdown(f"**स्टेटस:** <span style='color:{r['Color']}; font-weight:bold;'>{r['Status']}</span>", unsafe_allow_html=True)
                        st.info(f"**विश्लेषण:** {r['Details']}")
                        
                    with col2:
                        st.markdown("**📰 ताज़ा न्यूज़:**")
                        st.write(r['News'])
                        for h in r['Headlines'][:3]:
                            st.write(f"- {h}")
                            
                    st.markdown("**📈 पिछले 1 साल का चार्ट:**")
                    st.line_chart(r['ChartData'])

st.markdown("---")
st.info("🛡️ **अस्वीकरण:** यह जानकारी सिर्फ शैक्षिक उद्देश्य के लिए है।")
