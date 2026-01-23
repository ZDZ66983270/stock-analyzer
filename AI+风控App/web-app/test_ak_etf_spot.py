import akshare as ak
import pandas as pd

def check_etf_spot():
    print("Fetching ETF Spot Data...")
    try:
        df = ak.fund_etf_spot_em()
        if df is not None:
             print(f"Columns: {df.columns.tolist()}")
             # Check if 159915 is in it
             row = df[df['代码'] == '159915']
             if not row.empty:
                 print("Found 159915:")
                 print(row.T)
             else:
                 print("159915 not found in spot data")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_etf_spot()
