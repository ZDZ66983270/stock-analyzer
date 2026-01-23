
from data_fetcher import DataFetcher
import logging

# Setup Logging to see what's happening
logging.basicConfig(level=logging.INFO)

def debug_sync():
    print("--- Starting Debug Sync of Indices ---")
    
    target_indices = [
        {"symbol": "^DJI", "market": "US"},
        {"symbol": "^NDX", "market": "US"},
        {"symbol": "SPY", "market": "US"},
        {"symbol": "800000", "market": "HK"},
        {"symbol": "800700", "market": "HK"},
        # {"symbol": "000001.SS", "market": "CN"} # Skip CN to verify US first
    ]
    
    fetcher = DataFetcher()
    
    for item in target_indices:
        symbol = item['symbol']
        market = item['market']
        print(f"\nFetching {symbol} ({market})...")
        try:
            # Emulate the call in the route
            data = fetcher.fetch_latest_data(symbol, market, force_refresh=True)
            print(f"Success: {data.get('price') if data else 'None'}")
        except Exception as e:
            print(f"FAILED {symbol}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_sync()
