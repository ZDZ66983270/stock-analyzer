
import akshare as ak
import pandas as pd
import yfinance as yf

symbol = "09988"
print(f"Checking volume for {symbol}.hk...")

try:
    # 1. AkShare Minute
    print("--- AkShare Minute (Period='1') ---")
    df_min = ak.stock_hk_hist_min_em(symbol=symbol, period='1')
    if not df_min.empty:
        latest = df_min.iloc[-1]
        vol = latest['成交量']
        print(f"Latest Min Row Time: {latest['时间']}")
        print(f"Raw Volume: {vol}")
        print(f"Is this Shares? {vol}")
    else:
        print("AkShare Min Empty")
except Exception as e:
    print(f"AkShare Error: {e}")

try:
    # 2. AkShare Daily
    print("\n--- AkShare Daily ---")
    df_day = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
    if not df_day.empty:
        latest_day = df_day.iloc[-1]
        print(f"Latest Day: {latest_day['date']}") # Check column names first
        print(f"Raw Volume: {latest_day['volume']}")
    else:
        print("AkShare Daily Empty")
except Exception as e:
    print(f"AkShare Daily Error: {e}")

try:
    # 3. Yahoo Finance
    print("\n--- Yahoo Finance (9988.HK) ---")
    t = yf.Ticker("9988.HK")
    info = t.info
    print(f"Info Volume: {info.get('volume')}")
    print(f"Info RegularMarketVolume: {info.get('regularMarketVolume')}")
    
    hist = t.history(period='1d')
    if not hist.empty:
        print(f"History Volume: {hist.iloc[-1]['Volume']}")
except Exception as e:
    print(f"Yahoo Error: {e}")
