import akshare as ak
import pandas as pd
import os
import time

print("Testing EastMoney HK Spot (stock_hk_spot_em)...")

max_retries = 3
for i in range(max_retries):
    try:
        print(f"Attempt {i+1}/{max_retries}...")
        # EastMoney usually returns all ~2600 stocks
        df = ak.stock_hk_spot_em()
        
        if df is None or df.empty:
            raise ValueError("Empty dataframe returned")
            
        print(f"Success! Fetched {len(df)} rows.")
        # print("Columns:", df.columns.tolist())
        
        # Check for Alibaba (09988)
        # EM code usually be '09988'
        if '代码' in df.columns:
            alibaba = df[df['代码'].astype(str) == '09988']
        elif 'symbol' in df.columns:
            alibaba = df[df['symbol'].astype(str) == '09988']
        else:
            alibaba = pd.DataFrame()
            
        if not alibaba.empty:
            print("Found Alibaba at index", alibaba.index[0])
            
        # Save to CSV
        save_path = os.path.join(os.path.dirname(__file__), "market_data_library", "snapshot_hk.csv")
        df.to_csv(save_path, index=False)
        print(f"\nSaved FULL snapshot to {save_path}")
        break # Success, exit loop
        
    except Exception as e:
        print(f"Error on attempt {i+1}: {e}")
        time.sleep(2)
else:
    print("All attempts failed.")
