from data_fetcher import DataFetcher
import logging

# Configure basic logging to complete stdout
logging.basicConfig(level=logging.INFO)

def test_fetch_hk():
    fetcher = DataFetcher()
    symbol = "09988.hk"
    print(f"Testing fetch for {symbol}...")
    
    # 1. Fetch Daily
    df = fetcher.fetch_hk_daily_data(symbol)
    print(f"Daily Data Result: {len(df) if df is not None else 'None'} rows")
    if df is not None and not df.empty:
        print(df.tail(1))
        
    # 2. Fetch Minute
    df_min = fetcher.fetch_hk_min_data(symbol)
    print(f"Minute Data Result: {len(df_min) if df_min is not None else 'None'} rows")
    
if __name__ == "__main__":
    test_fetch_hk()
