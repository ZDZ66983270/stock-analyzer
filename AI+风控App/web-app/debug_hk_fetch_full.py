import akshare as ak
import pandas as pd

def debug_hk_fetch(symbol):
    code = symbol.replace('.HK', '')
    print(f"Fetching {code}...")
    try:
        df = ak.stock_financial_hk_analysis_indicator_em(symbol=code, indicator="年度")
        if df is None or df.empty:
            print("Empty result")
            return
            
        print(f"Rows: {len(df)}")
        for _, row in df.iterrows():
             print(f"Time: {row.get('TIME')}, Holder Profit: {row.get('HOLDER_PROFIT')}")

    except Exception as e:
        print(f"Error: {e}")

debug_hk_fetch("00998.HK")
debug_hk_fetch("09988.HK")
debug_hk_fetch("00700.HK")
