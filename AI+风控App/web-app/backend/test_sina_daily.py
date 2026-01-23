import akshare as ak
import pandas as pd
import time

def test_daily():
    symbol = "AAPL"
    print(f"--- Testing Sina US Daily History for {symbol} ---")
    
    # 1. Unadjusted
    print("\n1. Fetching Unadjusted Data (adjust='') ...")
    start = time.time()
    try:
        df = ak.stock_us_daily(symbol=symbol, adjust="")
        elapsed = time.time() - start
        print(f"   > Done in {elapsed:.2f}s. Rows: {len(df)}")
        print("   > Last 5 rows:")
        print(df.tail())
    except Exception as e:
        print(f"   > Failed: {e}")

    # 2. QFQ (Forward Adjusted)
    print("\n2. Fetching QFQ Data (adjust='qfq') ...")
    start = time.time()
    try:
        df_qfq = ak.stock_us_daily(symbol=symbol, adjust="qfq")
        elapsed = time.time() - start
        print(f"   > Done in {elapsed:.2f}s. Rows: {len(df_qfq)}")
        print("   > Last 5 rows (Adjusted):")
        print(df_qfq.tail())
    except Exception as e:
        print(f"   > Failed: {e}")

if __name__ == "__main__":
    test_daily()
