import akshare as ak
import pandas as pd

pd.set_option('display.max_columns', None)

def inspect_cn_cols():
    print("Fetching CN financials (stock_yjbb_em) for 20241231...")
    try:
        # Note: stock_yjbb_em returns a summary table for ALL stocks for that date
        # It might be filtered or we look for a familiar symbol
        df = ak.stock_yjbb_em(date="20240930") # Use Q3 2024 as Dec might not be out
        
        if not df.empty:
            print("\n--- Columns ---")
            print(df.columns.tolist())
            print("\n--- First Row ---")
            print(df.iloc[0])
            
            # Check for a specific stock e.g. 600519
            target = df[df['股票代码'] == '600519']
            if not target.empty:
                print("\n--- 600519 Row ---")
                print(target.iloc[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_cn_cols()
