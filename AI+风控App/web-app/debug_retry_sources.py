
import akshare as ak
import pandas as pd
import datetime

def test_lg_indicator_retry():
    print("\n" + "="*50)
    print("🔄 Retrying ak.stock_a_indicator_lg with prefixes...")
    print("="*50)
    
    # Try different formats
    symbols = ["600030", "sh600030", "000001", "sz000001"]
    
    for sym in symbols:
        try:
            print(f"\nTesting symbol: {sym}")
            df = ak.stock_a_indicator_lg(symbol=sym)
            if df is not None and not df.empty:
                print("✅ Success!")
                print("Columns:", df.columns.tolist())
                print(df.tail(2))
                return # Found working format
            else:
                print("Returned None/Empty")
        except Exception as e:
            print(f"Error: {e}")

def test_user_suggestion():
    print("\n" + "="*50)
    print("🔄 Testing user suggestion: news_trade_notify_dividend_baidu")
    print("="*50)
    
    try:
        # User example uses future date 20251126? Let's use a known recent date.
        # e.g., 2024-11-07 as mentioned in description, or today.
        # Find a recent trading day.
        today = datetime.datetime.now().strftime("%Y%m%d")
        print(f"Testing date: {today}")
        
        df = ak.news_trade_notify_dividend_baidu(date=today)
        print(df)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_lg_indicator_retry()
    test_user_suggestion()
