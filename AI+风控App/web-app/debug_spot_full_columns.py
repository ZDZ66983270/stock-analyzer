
import akshare as ak
import pandas as pd

def check_spot_columns():
    print("Checking A-share spot columns (stock_zh_a_spot_em)...")
    try:
        # Fetching a small subset is not natively supported, so we fetch all and take head
        df_a = ak.stock_zh_a_spot_em()
        print("A-share Columns:", df_a.columns.tolist())
        print("First row:", df_a.iloc[0].to_dict())
        
        # Check for '股息' in columns
        div_cols = [c for c in df_a.columns if '股息' in c]
        print("A-share Dividend Columns found:", div_cols)
        
        if div_cols:
             print("\nSample Data for Dividend Columns:")
             print(df_a[['代码', '名称'] + div_cols].head())

    except Exception as e:
        print(f"A-share Error: {e}")

    print("\n" + "="*50 + "\n")

    print("Checking HK-share spot columns (stock_hk_spot_em)...")
    try:
        df_hk = ak.stock_hk_spot_em()
        print("HK-share Columns:", df_hk.columns.tolist())
        
        # Check for '股息' in columns
        div_cols_hk = [c for c in df_hk.columns if '股息' in c]
        print("HK-share Dividend Columns found:", div_cols_hk)
        
        if div_cols_hk:
             print("\nSample Data for Dividend Columns:")
             print(df_hk[['symbol', 'name'] + div_cols_hk].head())

    except Exception as e:
        print(f"HK-share Error: {e}")

if __name__ == "__main__":
    check_spot_columns()
