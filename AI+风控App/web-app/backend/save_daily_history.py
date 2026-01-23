import akshare as ak
import pandas as pd
import os

def save_daily():
    symbol = "AAPL"
    print(f"--- Fetching & Saving History for {symbol} ---")
    
    # Fetch QFQ
    try:
        df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
        filename = f"history_us_{symbol}.csv"
        df.to_csv(filename, index=True) # Date is index usually? let's check. 
        # In the previous output "date" was a column? 
        # The example output shows date as index? 
        # "date open high..."
        # Let's save index=True just in case, or reset index if needed. 
        # Pandas usually handles it.
        print(f"Saved {len(df)} rows to {filename}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    save_daily()
