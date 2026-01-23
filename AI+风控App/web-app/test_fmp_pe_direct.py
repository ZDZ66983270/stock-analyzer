
import requests
import pandas as pd
import sys

# Fixed API Key from codebase
API_KEY = "yytaAKONtPbR5cBcx9azLeqlovaWDRQm"
SYMBOL = "AAPL"

def test_daily_pe_ttm():
    """测试每日滚动 PE (TTM) 接口"""
    print(f"\n🚀 Testing Daily PE TTM for {SYMBOL}...")
    url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{SYMBOL}?limit=365&apikey={API_KEY}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            df = pd.DataFrame(data)
            # FMP TTM PE field is usually peRatioTTM
            if 'peRatioTTM' in df.columns:
                print("✅ Data fetched successfully:")
                print(df[['date', 'peRatioTTM']].head())
            else:
                 print("⚠️ Data fetched but 'peRatioTTM' column missing. Columns:", df.columns)
                 print(df.head())
        else:
            print("❌ No data returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_daily_pe_standard():
    """测试每日/每季 PE 接口"""
    print(f"\n🚀 Testing Standard PE for {SYMBOL}...")
    url = f"https://financialmodelingprep.com/api/v3/ratios/{SYMBOL}?limit=365&apikey={API_KEY}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            df = pd.DataFrame(data)
            # Standard ratio field is priceEarningsRatio
            if 'priceEarningsRatio' in df.columns:
                print("✅ Data fetched successfully:")
                print(df[['date', 'priceEarningsRatio']].head())
            else:
                 print("⚠️ Data fetched but 'priceEarningsRatio' column missing. Columns:", df.columns)
        else:
            print("❌ No data returned")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_daily_pe_ttm()
    test_daily_pe_standard()
