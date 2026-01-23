
import requests
import json
import os

# Note: 'demo' key usually only works for 'IBM', 'TSCO.LON', 'SHOP.TRT' etc.
# To test HK/CN, we likely need a real key.
API_KEY = os.environ.get("AV_API_KEY", "072YUEUXAYVA6AUF") 

def test_av(symbol, function="GLOBAL_QUOTE"):
    print(f"\n>>> Testing {symbol} with function={function}...")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": API_KEY
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        # Check for Errors
        if "Error Message" in data:
            print(f"❌ Error: {data['Error Message']}")
            return False
        if "Information" in data:
            print(f"⚠️ Limit/Info: {data['Information']}")
            return False
        
        # Check Success based on function
        if function == "GLOBAL_QUOTE":
            quote = data.get("Global Quote", {})
            if quote:
                print(f"✅ Success! Price: {quote.get('05. price')} (Date: {quote.get('07. latest trading day')})")
                return True
            else:
                print(f"❌ Empty Quote: {data}")
                return False
                
        elif function == "TIME_SERIES_DAILY":
            ts = data.get("Time Series (Daily)", {})
            if ts:
                dates = list(ts.keys())
                print(f"✅ Success! Fetched {len(dates)} days. Latest: {dates[0]} -> {ts[dates[0]]['4. close']}")
                return True
            else:
                print(f"❌ Empty TimeSeries: {data}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print(f"Using API KEY: {API_KEY}")
    
    # 1. US Market (IBM - Should work with demo)
    print("\n--- 1. US Market (IBM) ---")
    test_av("IBM", "GLOBAL_QUOTE")
    
    # 2. HK Market (Tencent 0700.HK)
    print("\n--- 2. HK Market (0700.HK) ---")
    test_av("0700.HK", "GLOBAL_QUOTE")
    
    # 3. CN Market (Moutai 600519.SH)
    print("\n--- 3. CN Market (600519.SH) ---")
    test_av("600519.SH", "GLOBAL_QUOTE")
