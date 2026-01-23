
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

def test_fetch(symbol, market_name):
    print(f"\nTesting {market_name}: {symbol}...")
    try:
        df = yf.download(symbol, period="1mo", progress=False)
        if not df.empty:
            last_date = df.index[-1].strftime('%Y-%m-%d')
            print(f"✅ SUCCESS: {len(df)} records. Last: {last_date}")
            print(df.tail(2))
        else:
            print("❌ FAILED: No data returned")
    except Exception as e:
        print(f"❌ ERROR: {e}")

# HK Stocks & Indices
test_fetch("0700.HK", "HK Stock (Tencent)")
test_fetch("^HSI", "HK Index (Hang Seng)")
test_fetch("^HSTECH", "HK Index (Tech)")  # Often problematic

# CN Stocks (A-share)
test_fetch("600519.SS", "CN Stock (Moutai - Shanghai)")
test_fetch("000858.SZ", "CN Stock (Wuliangye - Shenzhen)")

# CN Indices
test_fetch("000001.SS", "CN Index (Shanghai Composite)")
test_fetch("399001.SZ", "CN Index (Shenzhen Component)")
