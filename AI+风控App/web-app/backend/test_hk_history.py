import akshare as ak
import pandas as pd
import time
import os

def fetch_hk_history():
    symbol = "09988" # Alibaba
    print(f"--- Fetching Sina HK History for {symbol} (stock_hk_daily) ---")
    
    # Try QFQ (Forward Adjusted)
    print(f"Fetching QFQ data for {symbol} ...")
    try:
        start = time.time()
        # HK interface: symbol must be 5 digits? '09988'. 
        df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
        elapsed = time.time() - start
        
        filename = f"history_hk_{symbol}.csv"
        df.to_csv(filename, index=False)
        
        print(f"   > Done in {elapsed:.2f}s. Saved {len(df)} rows to {filename}")
        print("   > Last 5 rows:")
        print(df.tail())
        
    except Exception as e:
        print(f"   > Failed: {e}")

if __name__ == "__main__":
    fetch_hk_history()
