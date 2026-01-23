import akshare as ak
import pandas as pd

def test_fetch():
    symbol = "601998"
    print(f"Fetching daily data for {symbol}...")
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        if df is None or df.empty:
            print("DF is empty!")
        else:
            print(f"Fetched {len(df)} rows.")
            print(df.tail(2))
            # Check columns
            print("\nColumns:", df.columns.tolist())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch()
