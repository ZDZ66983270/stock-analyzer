
import sys
import logging
from data_fetcher import DataFetcher

# Configure logging to show info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def diagnose_800700():
    print("=== Diagnosing 800700 (Hang Seng Tech Index) Data Sources ===")
    fetcher = DataFetcher()
    symbol = "800700"
    market = "HK"
    
    # 1. Sina (Method 1)
    print("\n--- 1. Testing Sina Source ---")
    try:
        sina_res = fetcher.fetch_from_sina(symbol, market)
        print(f"Sina Result: {sina_res}")
    except Exception as e:
        print(f"Sina Failed: {e}")

    # 2. Tencent/Smartbox (Method 2 - if applicable in fetcher)
    # Looking at data_fetcher.py source would define this, but generally it's hidden.
    # We will trust fetch_latest_data logic to try them.
    
    # 3. AkShare (if used)
    print("\n--- 2. Testing AkShare (Eastern Money) ---")
    try:
        # Assuming internal method name, checking generic fetch
        # Ideally we want to call the headers directly, but let's see what fetch_latest_data does with logging on.
        pass
    except:
        pass

    # Let's use the main entry point which likely tries multiple sources
    print("\n--- Full Fetch Workflow (with print traces) ---")
    result = fetcher.fetch_latest_data(symbol, market)
    print(f"\nFinal Combined Result: {result}")

if __name__ == "__main__":
    diagnose_800700()
