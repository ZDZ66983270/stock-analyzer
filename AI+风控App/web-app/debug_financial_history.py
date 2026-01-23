
import yfinance as yf
import pandas as pd

def check_history():
    symbol = "AAPL"
    print(f"Fetching history for {symbol}...")
    ticker = yf.Ticker(symbol)
    
    print("\n--- Financials (Income Statement) ---")
    fin = ticker.financials
    print(fin.head())
    print("Columns (Dates):", fin.columns)

    print("\n--- Balance Sheet ---")
    bs = ticker.balance_sheet
    print(bs.head())
    print("Columns (Dates):", bs.columns)

if __name__ == "__main__":
    check_history()
