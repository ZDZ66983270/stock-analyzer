import akshare as ak
import pandas as pd
import time
import os

def fetch_snapshots():
    print("=== Starting Full Market Snapshot Fetch ===")
    
    # 1. CN (A-Shares)
    print("\n1. Fetching CN (A-Shares) Spot Data...")
    try:
        start = time.time()
        df_cn = ak.stock_zh_a_spot_em()
        elapsed = time.time() - start
        
        # Save
        df_cn.to_csv("snapshot_cn.csv", index=False)
        print(f"   > Done in {elapsed:.2f}s. Saved {len(df_cn)} rows to snapshot_cn.csv")
    except Exception as e:
        print(f"   > CN Failed: {e}")

    # 2. HK (HK Stocks)
    print("\n2. Fetching HK Spot Data...")
    try:
        start = time.time()
        df_hk = ak.stock_hk_spot_em()
        elapsed = time.time() - start
        
        # Save
        df_hk.to_csv("snapshot_hk.csv", index=False)
        print(f"   > Done in {elapsed:.2f}s. Saved {len(df_hk)} rows to snapshot_hk.csv")
    except Exception as e:
        print(f"   > HK Failed: {e}")

    # 3. US (US Stocks)
    print("\n3. Fetching US Spot Data (EastMoney)...")
    try:
        start = time.time()
        df_us = ak.stock_us_spot_em()
        elapsed = time.time() - start
        
        # Clean Codes (105.AAPL -> AAPL)
        print("   > Cleaning US Codes (Stripping 105/106 prefixes)...")
        def clean_us_code(code):
            code_str = str(code)
            if '.' in code_str:
                return code_str.split('.')[-1]
            return code_str
        
        if '代码' in df_us.columns:
            df_us['clean_symbol'] = df_us['代码'].apply(clean_us_code)
        
        # Save
        df_us.to_csv("snapshot_us.csv", index=False)
        print(f"   > Done in {elapsed:.2f}s. Saved {len(df_us)} rows to snapshot_us.csv")
        
        # Verify a few targets
        targets = ['AAPL', 'TSLA', 'BABA', 'NVDA']
        print(f"   > Verifying targets in US snapshot: {targets}")
        match = df_us[df_us['clean_symbol'].isin(targets)]
        if not match.empty:
            print(match[['代码', '名称', '最新价', '涨跌幅']])
            
    except Exception as e:
        print(f"   > US Failed: {e}")

    print("\n=== All Snapshots Complete ===")

if __name__ == "__main__":
    fetch_snapshots()
