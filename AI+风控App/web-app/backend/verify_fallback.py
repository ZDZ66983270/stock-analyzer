import os
import pandas as pd
from data_fetcher import DataFetcher

# Unset proxy to test fallback connectivity
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

def test_fallback():
    print("Initializing DataFetcher...")
    try:
        fetcher = DataFetcher()
    except Exception as e:
        print(f"CRITICAL: DataFetcher init failed: {e}")
        return

    # Test CN Fallback (China Merchants Bank)
    symbol_cn = "600036.sh"
    print(f"\n--- Testing Fallback for {symbol_cn} ---")
    try:
        # Force fallback by NOT using the public method (or we rely on it failing AkShare internally)
        # But to be sure, let's call the private method directly
        df = fetcher._fetch_fallback_yfinance(symbol_cn, "CN")
        if df.empty:
            print("Fallback returned EMPTY DataFrame")
        else:
            print(f"Fallback SUCCESS. Rows: {len(df)}")
            print("Columns:", df.columns.tolist())
            print(df.tail(1).to_dict('records'))
    except Exception as e:
        print(f"Fallback execution FAILED: {e}")

    # Test HK Fallback (COSCO)
    symbol_hk = "01919.hk"
    print(f"\n--- Testing Fallback for {symbol_hk} ---")
    try:
        df = fetcher._fetch_fallback_yfinance(symbol_hk, "HK")
        if df.empty:
            print("Fallback returned EMPTY DataFrame")
        else:
            print(f"Fallback SUCCESS. Rows: {len(df)}")
            print("Columns:", df.columns.tolist())
            print(df.tail(1).to_dict('records'))
    except Exception as e:
        print(f"Fallback execution FAILED: {e}")

if __name__ == "__main__":
    test_fallback()
