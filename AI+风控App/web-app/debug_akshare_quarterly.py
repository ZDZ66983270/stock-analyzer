
import akshare as ak
import pandas as pd

def test_lrb():
    symbol = "601919"
    print(f"📊 Testing ak.stock_lrb_em(symbol='{symbol}') ...")
    
    try:
        # stock_lrb_em: A股-个股-利润表
        # usually returns historical reports
        df = ak.stock_lrb_em(symbol=symbol)
        
        if df is None or df.empty:
            print("❌ No data returned.")
            return
            
        print(f"✅ Data returned: {len(df)} rows")
        print("\nColumns:", df.columns.tolist())
        
        # Check dates and key metric (Net Profit)
        # 'REPORT_DATE' or similar?
        # 'NETPROFIT' or '净利润'?
        
        # Print first few rows to see structure
        print("\n📋 First 5 rows:")
        print(df.head().to_string())
        
        # Identify key columns for Net Profit
        # usually '净利润' or similar
        print("\n🔍 Checking for Net Profit columns:")
        for col in df.columns:
            if '净利润' in col:
                print(f"  - {col}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_lrb()
