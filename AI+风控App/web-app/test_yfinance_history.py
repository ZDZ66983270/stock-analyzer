import yfinance as yf
import pandas as pd

def check_history(symbol):
    print(f"Checking {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        
        # Check Annual
        print("\n--- Annual Financials ---")
        fin = ticker.financials
        if not fin.empty:
            print(f"Columns (Dates): {len(fin.columns)}")
            print(fin.columns)
        else:
            print("Empty financials")

        # Check Balance Sheet
        print("\n--- Balance Sheet ---")
        bs = ticker.balance_sheet
        if not bs.empty:
            print(f"Columns (Dates): {len(bs.columns)}")
            print(bs.columns)
            
        # Check Cashflow
        print("\n--- Cashflow ---")
        cf = ticker.cashflow
        if not cf.empty:
            print(f"Columns (Dates): {len(cf.columns)}")
            print(cf.columns)

    except Exception as e:
        print(f"Error: {e}")

print("Checking US Stock (AAPL)")
check_history("AAPL")

print("\nChecking CN Stock (600519.SS)")
check_history("600519.SS")
