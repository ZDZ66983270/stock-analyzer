
import akshare as ak
import pandas as pd

def debug_cn_dividend(symbol):
    print(f"Testing symbol: {symbol}")
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        print("Columns:", df.columns.tolist() if df is not None else "None")
        print("Data:\n", df)
        
        # Check specifically for dividend related fields
        if df is not None:
            div_rows = df[df['item'].str.contains('股息', na=False)]
            print("\nDividend related rows:")
            print(div_rows)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with CITIC Securities (600030) and Kweichow Moutai (600519) just in case
    debug_cn_dividend("600030")
    print("-" * 50)
    debug_cn_dividend("600519")
