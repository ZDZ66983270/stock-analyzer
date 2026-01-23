
import yfinance as yf
import pandas as pd

symbol = "0P00014FO3"
print(f"Checking {symbol}...")
try:
    t = yf.Ticker(symbol)
    hist = t.history(period="1y")
    print(f"\nHistory Head:\n{hist.head()}")
    print(f"\nHistory Tail:\n{hist.tail()}")
    print("\nChecking for NaNs:")
    print(hist.isna().sum())
    
    # Check if a specific row has NaN open
    if not hist.empty:
        last_row = hist.iloc[-1]
        print(f"\nLast Row: {last_row}")
except Exception as e:
    print(f"Error: {e}")
