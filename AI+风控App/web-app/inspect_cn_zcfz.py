import akshare as ak
import pandas as pd

pd.set_option('display.max_columns', None)

def inspect_cn_zcfz():
    print("Fetching CN Balance Sheet (stock_zcfz_em) for 20240930...")
    try:
        # Try bulk fetch by date
        df = ak.stock_zcfz_em(date="20240930")
        
        if not df.empty:
            print("\n--- Columns ---")
            print(df.columns.tolist())
            print("\n--- First Row ---")
            print(df.iloc[0])
            
            # Check 600519
            target = df[df['股票代码'] == '600519']
            if not target.empty:
                print("\n--- 600519 Row ---")
                print(target.iloc[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_cn_zcfz()
