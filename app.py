<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TickStock</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #121212;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        .header {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        /* एडवांस सर्च बॉक्स स्टाइल */
        .search-container {
            position: relative;
            width: 100%;
            max-width: 400px;
            margin-bottom: 20px;
        }
        #stockSearch {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            background-color: #1e1e1e;
            color: #fff;
            border: 1px solid #333;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .suggestions-list {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-top: none;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
        .suggestion-item {
            padding: 10px 12px;
            cursor: pointer;
            border-bottom: 1px solid #2a2a2a;
        }
        .suggestion-item:hover {
            background-color: #2c2c2c;
        }
        .section-title {
            font-size: 18px;
            margin: 15px 0 10px 0;
            color: #e0e0e0;
        }
        /* ट्रेडिंगव्यू विजेट कंटेनर */
        #tradingview-container {
            width: 100%;
            height: 500px;
            background-color: #1e1e1e;
            border-radius: 8px;
            overflow: hidden;
        }
    </style>
</head>
<body>

    <div class="header">📈 TickStock - त्वरित विश्लेषण बिंदु</div>

    <!-- एडवांस सर्च बार -->
    <div class="search-container">
        <input type="text" id="stockSearch" placeholder="स्टॉक का नाम या सिंबल सर्च करें (जैसे: RELIANCE, TCS)..." autocomplete="off">
        <div id="suggestionsList" class="suggestions-list"></div>
    </div>

    <div class="section-title" id="chartTitle">ट्रेडिंगव्यू रियल-टाइम चार्ट (RELIANCE)</div>

    <!-- ट्रेडिंगव्यू विजेट के लिए डिव -->
    <div id="tradingview-container">
        <div class="tradingview-widget-container" style="height:100%;width:100%">
            <div id="tradingview_widget" style="height:100%;width:100%"></div>
        </div>
    </div>

    <!-- ट्रेडिंगव्यू की आधिकारिक स्क्रिप्ट -->
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script>
        // सैंपल स्टॉक डेटा (आप इसे अपने एपीआई या डेटाबेस से बदल सकते हैं)
        const stockDatabase = [
            { name: "Reliance Industries Ltd", symbol: "BSE:RELIANCE" },
            { name: "Tata Consultancy Services Ltd", symbol: "NSE:TCS" },
            { name: "Apple Inc", symbol: "NASDAQ:AAPL" },
            { name: "Texmaco Rail & Engineering Ltd", symbol: "NSE:TEXRAIL" },
            { name: "State Bank of India", symbol: "NSE:SBIN" },
            { name: "Infosys Ltd", symbol: "NSE:INFY" }
        ];

        const searchInput = document.getElementById('stockSearch');
        const suggestionsList = document.getElementById('suggestionsList');
        const chartTitle = document.getElementById('chartTitle');

        let currentWidget = null;

        // ट्रेडिंगव्यू चार्ट लोड करने का फंक्शन
        function loadTradingViewChart(symbol) {
            document.getElementById('tradingview_widget').innerHTML = ""; // पुराना चार्ट साफ़ करें
            
            currentWidget = new TradingView.widget({
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
            
            chartTitle.innerText = `ट्रेडिंगव्यू रियल-टाइम चार्ट (${symbol})`;
        }

        // शुरुआत में डिफ़ॉल्ट चार्ट लोड करें
        loadTradingViewChart("NSE:TEXRAIL");

        // सर्च इनपुट पर इवेंट लिसनर
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            suggestionsList.innerHTML = '';
            
            if (query.length === 0) {
                suggestionsList.style.display = 'none';
                return;
            }

            // स्टॉक फ़िल्टर करें
            const filteredStocks = stockDatabase.filter(stock => 
                stock.name.toLowerCase().includes(query) || stock.symbol.toLowerCase().includes(query)
            );

            if (filteredStocks.length > 0) {
                suggestionsList.style.display = 'block';
                filteredStocks.forEach(stock => {
                    const item = document.createElement('div');
                    item.classList.add('suggestion-item');
                    item.innerHTML = `<strong>${stock.name}</strong> <span style="color: #888; font-size: 12px;">(${stock.symbol})</span>`;
                    
                    // सजेशन पर क्लिक करने पर
                    item.addEventListener('click', function() {
                        searchInput.value = stock.name;
                        suggestionsList.style.display = 'none';
                        loadTradingViewChart(stock.symbol); // नया चार्ट लोड करें
                    });
                    
                    suggestionsList.appendChild(item);
                });
            } else {
                suggestionsList.style.display = 'none';
            }
        });

        // बाहर क्लिक करने पर सजेशन बॉक्स बंद हो जाए
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                suggestionsList.style.display = 'none';
            }
        });
    </script>
</body>
</html>

