from data_fetcher import DataFetcher
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

fetcher = DataFetcher()

symbols = [
    ("^DJI", "US"),
    ("^NDX", "US"),
    ("^SPX", "US"),
    ("000001.SS", "CN"),
    ("800000", "HK"),
    ("09988.hk", "HK"),
    ("00005.hk", "HK"),
    ("600309.sh", "CN"),
    ("TSLA", "US"),
    ("MSFT", "US")
]

print("--- Starting Manual Sync ---")
for symbol, market in symbols:
    print(f"\nFetching {symbol} ({market})...")
    try:
        data = fetcher.fetch_latest_data(symbol, market, force_refresh=True)
        print(f"Result for {symbol}: {data}")
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")

print("\n--- Sync Complete ---")
