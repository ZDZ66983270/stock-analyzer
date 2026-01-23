
import akshare as ak
import pandas as pd
from datetime import datetime

def test_hk_1min():
    symbol = "00700"  # Tencent
    print(f"Testing 1-min fetch for {symbol} HK via AkShare/EastMoney...")
    
    try:
        # period='1' means 1-minute bars
        df = ak.stock_hk_hist_min_em(symbol=symbol, period='1')
        
        if df is None or df.empty:
            print("FAILED: Returned empty DataFrame.")
            return

        print(f"SUCCESS: Received {len(df)} rows.")
        print("Columns:", df.columns.tolist())
        print("First 5 rows:")
        print(df.head())
        print("Last 5 rows:")
        print(df.tail())
        
        # Check time interval
        if '时间' in df.columns:
            df['时间'] = pd.to_datetime(df['时间'])
            diffs = df['时间'].diff().dropna()
            print("\nTime Diffs (Mode):", diffs.mode()[0])
            
            
    except Exception as e:
        print(f"ERROR AkShare: {e}")
        
    print("\n--- Testing YFinance Fallback ---")
    try:
        import yfinance as yf
        yf_symbol = "0700.HK" # Yahoo format
        print(f"Fetching {yf_symbol} via YFinance...")
        data = yf.download(yf_symbol, period="1d", interval="1m", progress=False)
        
        if data is None or data.empty:
            print("FAILED YFinance: Empty result.")
        else:
            print(f"SUCCESS YFinance: Received {len(data)} rows.")
            print(data.head())
            print(data.tail())
    except Exception as ye:
        print(f"ERROR YFinance: {ye}")

if __name__ == "__main__":
    test_hk_1min()
