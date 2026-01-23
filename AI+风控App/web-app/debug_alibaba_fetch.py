
import yfinance as yf
import pandas as pd

def check_alibaba():
    symbol = "09988.HK"
    print(f"Fetching {symbol} from yfinance...")
    
    ticker = yf.Ticker(symbol)
    # Fetch recent history (last 5 days)
    history = ticker.history(period="5d")
    
    print("\nRecent Data:")
    print(history.tail())
    
    if not history.empty:
        last_row = history.iloc[-1]
        print(f"\nLatest Date: {last_row.name}")
        print(f"Close: {last_row['Close']}")
        print(f"Volume: {last_row['Volume']}")

if __name__ == "__main__":
    check_alibaba()
