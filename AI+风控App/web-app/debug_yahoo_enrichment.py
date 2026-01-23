import sys
import os

# Ensure backend dir is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.data_fetcher import DataFetcher
import logging

# Setup logging to console
logging.basicConfig(level=logging.INFO)

def test_yahoo_fetch(symbol):
    print(f"--- Testing Yahoo Fetch for {symbol} ---")
    fetcher = DataFetcher()
    
    # 1. Test Fetch Method directly
    print("Calling fetch_yahoo_indicators...")
    data = fetcher.fetch_yahoo_indicators(symbol)
    
    print("\nResult:")
    if data:
        for k, v in data.items():
            print(f"  {k}: {v}")
    else:
        print("  [ERROR] No data returned (Empty dict)")

    # 2. Check specific keys needed for frontend
    needed = ['price', 'pe', 'dividend_yield', 'eps']
    print("\nChecking critical fields:")
    for k in needed:
        val = data.get(k)
        status = "OK" if val is not None else "MISSING"
        print(f"  {k}: {val} ({status})")

if __name__ == "__main__":
    # Test with the stock user showed in screenshot: 00998.hk
    test_yahoo_fetch("00998.hk")
