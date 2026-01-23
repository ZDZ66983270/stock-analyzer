import akshare as ak
import pandas as pd

def check_codes():
    targets = {
        "CN": ["600519", "600309"], # Moutai, Wanhua
        "HK": ["09988", "00005"],   # Ali, HSBC
        "US": ["TSLA", "AAPL", "NVDA", "MSFT", "BABA", "PDD"] # Tesla, Apple, Nvidia, Microsoft, Ali(US), PDD
    }
    
    print("--- 1. Checking CN (A-Shares) ---")
    try:
        df = ak.stock_zh_a_spot_em()
        # Find matches
        print(f"Total CN Rows: {len(df)}")
        for t in targets["CN"]:
            match = df[df['代码'].astype(str) == t]
            if not match.empty:
                print(f"Found {t}: Code='{match.iloc[0]['代码']}' Name='{match.iloc[0]['名称']}'")
            else:
                print(f"NOT FOUND: {t}")
    except Exception as e:
        print(f"CN Error: {e}")

    print("\n--- 2. Checking HK (HK Stocks) ---")
    try:
        df = ak.stock_hk_spot_em()
        print(f"Total HK Rows: {len(df)}")
        for t in targets["HK"]:
            # HK codes often 5 digits in EM?
            match = df[df['代码'].astype(str) == t]
            if not match.empty:
                print(f"Found {t}: Code='{match.iloc[0]['代码']}' Name='{match.iloc[0]['名称']}' Price={match.iloc[0]['最新价']}")
            else:
                print(f"NOT FOUND: {t}")
    except Exception as e:
        print(f"HK Error: {e}")

    print("\n--- 3. Checking US (US Stocks) ---")
    try:
        df = ak.stock_us_spot_em()
        print(f"Total US Rows: {len(df)}")
        # US codes in EM are like "105.TSLA"
        for t in targets["US"]:
            # Search by substring in Code OR Name
            # We want to see the PREFIX
            matches = df[df['代码'].astype(str).str.contains(t, case=False)]
            if not matches.empty:
                for _, row in matches.iterrows():
                    print(f"MATCH {t}: Code='{row['代码']}' Name='{row['名称']}' Price={row['最新价']}")
            else:
                print(f"NOT FOUND: {t}")
    except Exception as e:
        print(f"US Error: {e}")

if __name__ == "__main__":
    check_codes()
