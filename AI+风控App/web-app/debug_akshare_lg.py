
import akshare as ak
import pandas as pd
import datetime

def debug_lg_indicator(symbol):
    print(f"Fetching LG indicator data for {symbol}...")
    try:
        # This function returns historical daily valuation data
        df = ak.stock_a_indicator_lg(symbol=symbol)
        print("Columns:", df.columns.tolist() if df is not None else "None")
        
        if df is not None and not df.empty:
            # Sort by date descending to get latest
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date', ascending=False)
            
            print("\nLatest 5 rows:")
            print(df.head())
            
            # Check for dividend yield column (usually 'dv_ratio' or 'dv_ttm')
            # Columns are typically: trade_date, pe, pe_ttm, pb, ps, dv_ratio, dv_ttm
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_lg_indicator("600030")
