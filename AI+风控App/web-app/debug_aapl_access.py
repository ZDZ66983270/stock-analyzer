
import yfinance as yf
import pandas as pd
import datetime

def debug_access():
    symbol = "AAPL"
    ticker = yf.Ticker(symbol)
    
    inc = ticker.financials
    
    print("--- Indices ---")
    if 'Total Revenue' in inc.index:
        print("'Total Revenue' FOUND in index")
    else:
        print("'Total Revenue' NOT in index")

    col = inc.columns[0]
    print(f"\n--- Column 0: {col} (Type: {type(col)}) ---")
    
    print("\n--- Access Attempt 1: .loc[key, col] ---")
    try:
        val = inc.loc['Total Revenue', col]
        print(f"Value: {val}")
        print(f"Type: {type(val)}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Access Attempt 2: .loc[key][col] ---")
    try:
        val = inc.loc['Total Revenue'][col]
        print(f"Value: {val}")
    except Exception as e:
        print(f"Error: {e}")
        
    print("\n--- Rows with 'Revenue' ---")
    for idx in inc.index:
        if 'Revenue' in str(idx):
            print(f"Key: '{idx}' -> Val: {inc.loc[idx, col]}")

if __name__ == "__main__":
    debug_access()
