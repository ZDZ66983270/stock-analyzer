
import logging
from data_fetcher import DataFetcher
import pandas as pd
import akshare as ak

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def diagnose_800700_detailed():
    print("=== Diagnosing 800700 (Hang Seng Tech Index) Data Sources ===")
    fetcher = DataFetcher()
    symbol = "800700"
    market = "HK"
    
    # 1. AkShare Minute Data
    print("\n--- 1. Testing AkShare Minute Data (fetch_hk_min_data) ---")
    try:
        # Note: fetch_hk_min_data logic might try yfinance first if configured?
        # Let's see what the method does by calling it.
        df_min = fetcher.fetch_hk_min_data(symbol, period='1')
        if df_min is not None and not df_min.empty:
            print("AkShare Minute Result (Last 2 rows):")
            print(df_min.tail(2))
        else:
            print("AkShare Minute Result: Empty or None")
    except Exception as e:
        print(f"AkShare Minute Failed: {e}")

    # 2. AkShare Daily Data
    print("\n--- 2. Testing AkShare Daily Data (fetch_hk_daily_data) ---")
    try:
        df_daily = fetcher.fetch_hk_daily_data(symbol)
        if df_daily is not None and not df_daily.empty:
            print("AkShare Daily Result (Last 2 rows):")
            print(df_daily.tail(2))
        else:
            print("AkShare Daily Result: Empty or None")
    except Exception as e:
        print(f"AkShare Daily Failed: {e}")

    # 3. Yahoo Finance Fallback
    print("\n--- 3. Testing Yahoo Finance Fallback (_fetch_fallback_yfinance) ---")
    try:
        # Pass .hk extension as expected by generic logic, or just raw symbol
        # Logic in method: symbol.replace('.hk', '')
        sym_input = "800700.hk" 
        df_yf = fetcher._fetch_fallback_yfinance(sym_input, "HK")
        if df_yf is not None and not df_yf.empty:
            print("Yahoo Result (Last 2 rows):")
            print(df_yf.tail(2))
        else:
            print("Yahoo Result: Empty or None")
    except Exception as e:
        print(f"Yahoo Fallback Failed: {e}")

    # 4. Sina Method (Direct Raw Call if possible)
    # The snippet didn't show fetch_from_sina, maybe it was removed or I missed it.
    # But let's check fetch_latest_data logs when we force refresh.

    # 5. Full Fetch with Force Refresh
    print("\n--- 4. Full Fetch (Force Refresh = True) ---")
    try:
        res = fetcher.fetch_latest_data(symbol, market, force_refresh=True)
        print(f"Final Result: {res}")
    except Exception as e:
        print(f"Full Fetch Failed: {e}")

if __name__ == "__main__":
    diagnose_800700_detailed()
