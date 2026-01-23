import akshare as ak
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def inspect_hk():
    print("Fetching HK financials for 00700...")
    try:
        df = ak.stock_financial_hk_analysis_indicator_em(symbol="00700", indicator="年度")
        if not df.empty:
            print("\n--- Columns ---")
            print(df.columns.tolist())
            print("\n--- First Row ---")
            print(df.iloc[0])
    except Exception as e:
        print(e)
    
    print("\n--- FINAL COLUMNS LIST ---")
    try:
         df = ak.stock_financial_hk_analysis_indicator_em(symbol="00700", indicator="年度")
         print(df.columns.tolist())
    except: pass

if __name__ == "__main__":
    inspect_hk()
