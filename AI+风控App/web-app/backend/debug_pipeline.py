from data_fetcher import DataFetcher
import sys
import pandas as pd
import json

def debug_fetch(symbol, market):
    print(f"\n========== DEBUG PIPELINE: {symbol} ({market}) ==========")
    
    fetcher = DataFetcher()
    
    # 1. AkShare RAW
    print(f"\n[1] AkShare Raw Fetch:")
    try:
        if market == "US":
            ak_symbol = fetcher.to_akshare_us_symbol(symbol)
            print(f"    AkShare Symbol: {ak_symbol}")
            if not symbol.startswith('^'):
                df = fetcher.fetch_us_min_data(ak_symbol)
            else:
                print("    Skipping AkShare for Index (Starts with ^)")
                df = None
        elif market == "CN":
            df = fetcher.fetch_cn_min_data(symbol)
        elif market == "HK":
            df = fetcher.fetch_hk_min_data(symbol)
        else:
            df = None
            
        if df is not None and not df.empty:
            print("    -> SUCCESS. Last row:")
            print(df.iloc[-1].to_dict())
        else:
            print("    -> EMPTY or FAILED.")
    except Exception as e:
        print(f"    -> EXCEPTION: {e}")

    # 2. Yahoo RAW
    print(f"\n[2] Yahoo Raw Fetch (Indicators + Price):")
    try:
        yf_data = fetcher.fetch_yahoo_indicators(symbol)
        print("    -> RAW Result:")
        print(json.dumps(yf_data, indent=4, default=str))
    except Exception as e:
        print(f"    -> EXCEPTION: {e}")

    # 3. Merged Data (fetch_latest_data logic)
    print(f"\n[3] Merged 'fetch_latest_data' Result:")
    try:
        merged = fetcher.fetch_latest_data(symbol, market, force_refresh=True)
        print(json.dumps(merged, indent=4, default=str))
    except Exception as e:
        print(f"    -> EXCEPTION: {e}")
        
    print("\n========================================================")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_pipeline.py <symbol> <market>")
        print("Example: python debug_pipeline.py MSFT.OQ US")
    else:
        debug_fetch(sys.argv[1], sys.argv[2])
