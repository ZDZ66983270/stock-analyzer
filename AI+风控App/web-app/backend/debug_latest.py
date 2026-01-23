import sys
import os
# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from data_fetcher import DataFetcher
import json

def test_fetch():
    fetcher = DataFetcher()
    
    # Test CN
    print("--- Testing CN (600036.sh) ---")
    data_cn = fetcher.fetch_latest_data("600036.sh", "CN")
    print(f"CN Result: {json.dumps(data_cn, indent=2, ensure_ascii=False)}")

    # Test US (if applicable, e.g. TSLA or AAPL)
    print("\n--- Testing US (TSLA) ---")
    try:
        data_us = fetcher.fetch_latest_data("TSLA", "US")
        print(f"US Result: {json.dumps(data_us, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"US Fetch Error: {e}")

if __name__ == "__main__":
    test_fetch()
