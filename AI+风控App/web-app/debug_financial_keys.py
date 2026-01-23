
import yfinance as yf

def check_keys():
    symbol = "AAPL"
    ticker = yf.Ticker(symbol)
    
    print(f"--- {symbol} Financials Keys ---")
    if not ticker.financials.empty:
        print(ticker.financials.index.tolist())
    else:
        print("Financials empty")

    print(f"\n--- {symbol} Balance Sheet Keys ---")
    if not ticker.balance_sheet.empty:
        print(ticker.balance_sheet.index.tolist())
    else:
        print("Balance Sheet empty")

if __name__ == "__main__":
    check_keys()
