import akshare as ak
import pandas as pd
import time
import os

def fetch_cn_history():
    symbol = "sh600309" # Wanhua Chemical
    print(f"--- Fetching Sina A-Share History for {symbol} (stock_zh_a_daily) ---")
    
    start_date = "19900101"
    end_date = "20251231"
    
    # Try QFQ (Forward Adjusted) as per practice
    print(f"Fetching QFQ data from {start_date} to {end_date}...")
    try:
        start = time.time()
        # Sina requires specific prefix like sh/sz
        df = ak.stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust="qfq")
        elapsed = time.time() - start
        
        filename = f"history_cn_{symbol}.csv"
        df.to_csv(filename, index=False)
        
        print(f"   > Done in {elapsed:.2f}s. Saved {len(df)} rows to {filename}")
        print("   > Last 5 rows:")
        print(df.tail())
        
    except Exception as e:
        print(f"   > Failed: {e}")

if __name__ == "__main__":
    fetch_cn_history()
