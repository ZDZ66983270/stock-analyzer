import yfinance as yf
import pandas as pd

def check_quarterly(symbol):
    print(f"Checking {symbol} Quarterly...")
    try:
        ticker = yf.Ticker(symbol)
        
        # Check Quarterly Financials
        print("\n--- Quarterly Financials ---")
        q_fin = ticker.quarterly_financials
        if not q_fin.empty:
            print(f"Columns (Dates): {len(q_fin.columns)}")
            print(q_fin.columns)
        else:
            print("Empty quarterly financials")

    except Exception as e:
        print(f"Error: {e}")

print("Checking US Stock (AAPL)")
check_quarterly("AAPL")
