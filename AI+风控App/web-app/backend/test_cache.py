from data_fetcher import DataFetcher
import logging
import sys

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

fetcher = DataFetcher()
symbol = "MSFT.OQ"
market = "US"

print(f"--- CALL 1: {symbol} (Market: {market}) ---")
data1 = fetcher.fetch_latest_data(symbol, market, force_refresh=False)
print("Data1 Date:", data1.get('date') if data1 else "None")

print(f"\n--- CALL 2: {symbol} (Should be CACHED) ---")
data2 = fetcher.fetch_latest_data(symbol, market, force_refresh=False)
print("Data2 Date:", data2.get('date') if data2 else "None")
