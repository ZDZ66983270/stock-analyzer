
import logging
from data_fetcher import DataFetcher
import pandas as pd
import akshare as ak

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def diagnose_indices_detailed():
    print("=== Diagnosing HK Indices Data Sources ===")
    fetcher = DataFetcher()
    
    targets = [
        {"symbol": "800000", "market": "HK", "name": "Hang Seng Index"},
        {"symbol": "800700", "market": "HK", "name": "Hang Seng Tech"}
    ]
    
    for item in targets:
        symbol = item['symbol']
        market = item['market']
        name = item['name']
        print(f"\n\n--- Testing {name} ({symbol}) ---")

        # 1. Yahoo Finance Fallback (Direct)
        print("\n[Test 1] Yahoo Finance Fallback (_fetch_fallback_yfinance)")
        try:
            # We pass the internal symbol (e.g. 800700.hk) and let the method handle mapping
            sym_input = f"{symbol}.hk"
            print(f"Input: {sym_input}")
            df_yf = fetcher._fetch_fallback_yfinance(sym_input, "HK")
            if df_yf is not None and not df_yf.empty:
                print("Yahoo Result (Last 2 rows):")
                print(df_yf.tail(2))
            else:
                print("Yahoo Result: Empty or None")
        except Exception as e:
            print(f"Yahoo Fallback Failed: {e}")

        # 2. Full Fetch with Force Refresh
        print("\n[Test 2] Full Fetch (fetch_latest_data, force_refresh=True)")
        try:
            res = fetcher.fetch_latest_data(symbol, market, force_refresh=True)
            print(f"Final Result: {res}")
        except Exception as e:
            print(f"Full Fetch Failed: {e}")

if __name__ == "__main__":
    diagnose_indices_detailed()
