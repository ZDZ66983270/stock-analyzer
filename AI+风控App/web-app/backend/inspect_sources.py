import asyncio
from data_fetcher import DataFetcher
import pandas as pd
import akshare as ak
import yfinance as yf

# Force pandas display
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

async def inspect():
    f = DataFetcher()
    
    print("=== 1. AkShare US (AAPL) ===")
    try:
        df = f.fetch_us_daily_data("105.aapl")
        if df is not None and not df.empty:
            print("Columns:", df.columns.tolist())
            print(df.tail(2))
        else:
            print("Empty/None")
    except Exception as e: print(e)

    print("\n=== 2. AkShare HK (00700) ===")
    try:
        df = f.fetch_hk_daily_data("00700.hk")
        if df is not None and not df.empty:
            print("Columns:", df.columns.tolist())
            print(df.tail(2))
        else:
            print("Empty/None")
    except Exception as e: print(e)

    print("\n=== 3. AkShare CN (600519) ===")
    try:
        df = f.fetch_cn_daily_data("600519.sh")
        if df is not None and not df.empty:
            print("Columns:", df.columns.tolist())
            print(df.tail(2))
        else:
            print("Empty/None")
    except Exception as e: print(e)

    print("\n=== 4. Yahoo Finance Fallback (AAPL) ===")
    try:
        df = f._fetch_fallback_yfinance("AAPL", "US")
        if df is not None and not df.empty:
            print("Columns:", df.columns.tolist())
            print(df.tail(2))
        else:
            print("Empty/None")
    except Exception as e: print(e)

if __name__ == "__main__":
    asyncio.run(inspect())
