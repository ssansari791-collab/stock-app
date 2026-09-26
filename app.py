import streamlit as st

# पेज की सेटिंग
st.set_page_config(page_title="TickStock", layout="wide")

# कम्पलीट कोड (विश्लेषण बिंदु, पिवट पॉइंट, एडवांस सर्च और ट्रेडिंगव्यू चार्ट के साथ)
st.markdown("""
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
            font-family: Arial, sans-serif;
        }
        .header {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #ffffff;
        }
        .analysis-box {
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }
        .analysis-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #ffcc00;
        }
        .analysis-text {
            font-size: 14px;
            margin-bottom: 8px;
            color: #e0e0e0;
        }
        .search-container {
            position: relative;
            width: 100%;
            max-width: 450px;
            margin-bottom: 20px;
        }
        #stockSearch {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            background-color: #1e1e1e;
            color: #fff;
            border: 1px solid #333;
            border-radius: 6px;
            box-sizing: border-box;
            outline: none;
        }
        .suggestions-list {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-top: none;
            max-height: 220px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            border-radius: 0 0 6px 6px;
        }
        .suggestion-item {
            padding: 12px;
            cursor: pointer;
            border-bottom: 1px solid #2a2a2a;
            color: #fff;
        }
        .suggestion-item:hover {
            background-color: #2c2c2c;
        }
        .section-title {
            font-size: 18px;
            margin: 15px 0 10px 0;
            color: #e0e0e0;
            font-weight: bold;
        }
        #tradingview-container {
            width: 100%;
            height: 500px;
            background-color: #1e1e1e;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #333;
        }
    </style>

    <div class="header">TickStock</div>

    <!-- त्वरित विश्लेषण बिंदु और पिवट पॉइंट सेक्शन -->
    <div class="analysis-box">
        <div class="analysis-title">📝 त्वरित विश्लेषण बिंदु</div>
        <div class="analysis-text">🚀 शेयर का भाव पिवट पॉइंट (₹ 125.15) से ऊपर है, जो मजबूती दिखा सकता है।</div>
        <div class="analysis-text">📉 पिछले दिन की तुलना में बाजार के रुझान का निरीक्षण किया गया है।</div>
    </div>

    <!-- एडवांस सर्च बार -->
    <div class="search-container">
        <input type="text" id="stockSearch" placeholder="स्टॉक का नाम या सिंबल सर्च करें (जैसे: RELIANCE, TCS)..." autocomplete="off">
        <div id="suggestionsList" class="suggestions-list"></div>
    </div>

    <div class="section-title" id="chartTitle">📊 ट्रेडिंगव्यू रियल-टाइम चार्ट (NSE:TEXRAIL)</div>

    <!-- ट्रेडिंगव्यू चार्ट कंटेनर -->
    <div id="tradingview-container">
        <div id="tradingview_widget" style="height:100%;width:100%"></div>
    </div>

    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script>
        const stockDatabase = [
            { name: "Reliance Industries Ltd", symbol: "BSE:RELIANCE" },
            { name: "Tata Consultancy Services Ltd", symbol: "NSE:TCS" },
            { name: "Apple Inc", symbol: "NASDAQ:AAPL" },
            { name: "Texmaco Rail & Engineering Ltd", symbol: "NSE:TEXRAIL" },
            { name: "State Bank of India", symbol: "NSE:SBIN" },
            { name: "Infosys Ltd", symbol: "NSE:INFY" },
            { name: "Ashoka Buildcon Ltd", symbol: "NSE:ASHOKA" },
            { name: "Marine Electricals India Ltd", symbol: "NSE:MARINE" },
            { name: "Redington Ltd", symbol: "NSE:REDINGTON" }
        ];

        const searchInput = document.getElementById('stockSearch');
        const suggestionsList = document.getElementById('suggestionsList');
        const chartTitle = document.getElementById('chartTitle');

        function loadTradingViewChart(symbol) {
            document.getElementById('tradingview_widget').innerHTML = "";
            
            new TradingView.widget({
                "width": "100%",
                "height": "100%",
                "symbol": symbol,
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "in",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "container_id": "tradingview_widget"
            });
            
            chartTitle.innerText = `📊 ट्रेडिंगव्यू रियल-टाइम चार्ट (${symbol})`;
        }

        // डिफ़ॉल्ट चार्ट लोड करें
        loadTradingViewChart("NSE:TEXRAIL");

        // सर्च इनपुट और सजेशन लॉजिक
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            suggestionsList.innerHTML = '';
            
            if (query.length === 0) {
                suggestionsList.style.display = 'none';
                return;
            }

            const filteredStocks = stockDatabase.filter(stock => 
                stock.name.toLowerCase().includes(query) || stock.symbol.toLowerCase().includes(query)
            );

            if (filteredStocks.length > 0) {
                suggestionsList.style.display = 'block';
                filteredStocks.forEach(stock => {
                    const item = document.createElement('div');
                    item.classList.add('suggestion-item');
                    item.innerHTML = `<strong>${stock.name}</strong> <span style="color: #888; font-size: 12px;">(${stock.symbol})</span>`;
                    
                    item.addEventListener('click', function() {
                        searchInput.value = stock.name;
                        suggestionsList.style.display = 'none';
                        loadTradingViewChart(stock.symbol);
                    });
                    
                    suggestionsList.appendChild(item);
                });
            } else {
                suggestionsList.style.display = 'none';
            }
        });

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                suggestionsList.style.display = 'none';
            }
        });
    </script>
""", unsafe_allow_html=True)
