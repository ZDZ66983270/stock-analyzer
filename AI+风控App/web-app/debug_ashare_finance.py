
import akshare as ak
import pandas as pd

def check_financial_indicator():
    print("Checking AkShare Financial Analysis Indicator for 600030...")
    try:
        # This is the main interface used for financial indicators in fetch_financials.py
        # typically returns annual report data
        df = ak.stock_financial_analysis_indicator(symbol="600030")
        
        if df is not None and not df.empty:
            print("Columns:", df.columns.tolist())
            print("\nLatest 5 rows:")
            print(df.head())
            
            # Check for dividend related columns
            div_cols = [c for c in df.columns if '股息' in c or '分红' in c]
            print("\nDividend Columns Found:", div_cols)
            
            if div_cols:
                print(df[['日期'] + div_cols].head())
        else:
            print("No data returned.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_financial_indicator()
