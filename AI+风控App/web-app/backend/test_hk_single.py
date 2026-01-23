import akshare as ak
import yfinance as yf
import pandas as pd
import time

SYMBOL_AK = "09988"
SYMBOL_YF = "9988.HK"

print("--- Testing AkShare Single Daily ---")
try:
    start = time.time()
    # EastMoney single stock history
    df = ak.stock_hk_daily(symbol=SYMBOL_AK, adjust="qfq")
    print(f"AkShare Time: {time.time()-start:.2f}s")
    if not df.empty:
        print(f"Latest Date: {df.iloc[-1]['date']}")
        print(f"Latest Close: {df.iloc[-1]['close']}")
    else:
        print("AkShare returned empty.")
except Exception as e:
    print(f"AkShare Error: {e}")

print("\n--- Testing YFinance Single Quote ---")
try:
    start = time.time()
    ticker = yf.Ticker(SYMBOL_YF)
    # fast info
    info = ticker.fast_info
    print(f"YFinance Time: {time.time()-start:.2f}s")
    print(f"Last Price: {info.last_price}")
    # print(f"Previous Close: {info.previous_close}")
except Exception as e:
    print(f"YFinance Error: {e}")
