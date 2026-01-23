
import akshare as ak
import pandas as pd

def debug_spot():
    print("Fetching spot data (top 20 rows)...")
    try:
        # This returns data for ALL stocks, so it might take a few seconds
        df = ak.stock_zh_a_spot_em()
        print("Columns:", df.columns.tolist())
        
        # Filter for our test stocks
        test_codes = ['600030', '600519']
        result = df[df['代码'].isin(test_codes)]
        print("\nTest Stocks Data:")
        print(result[['代码', '名称', '最新价', '市盈率-动态', '市净率', '股息率']])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_spot()
