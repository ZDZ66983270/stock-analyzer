import akshare as ak
import pandas as pd
import time
import os

def fetch_and_save():
    print("--- Fetching Sina US Data (Saving to sina_us_dump.csv) ---")
    start = time.time()
    try:
        df = ak.stock_us_spot()
        elapsed = time.time() - start
        print(f"Fetch finished in {elapsed:.2f}s")
        
        # Save
        csv_path = "sina_us_dump.csv"
        df.to_csv(csv_path, index=False)
        print(f"Saved {len(df)} rows to {csv_path}")
        
        # Show AAPL record
        targets = ['AAPL']
        match = df[df['symbol'].isin(targets)]
        if not match.empty:
            record = match.iloc[0].to_dict()
            print(f"\n--- AAPL Record (Raw) ---")
            for k, v in record.items():
                print(f"{k:<15}: {v}")
        else:
            print("AAPL not found in dump!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_save()
