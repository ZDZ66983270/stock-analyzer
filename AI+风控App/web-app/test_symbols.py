
import yfinance as yf

symbols = ["^HSTECH", "HSTECH.HK", "000001.SS", "000001.SZ"]

print("Testing Yahoo Finance Symbols:")
for s in symbols:
    print(f"\nTesting {s}...")
    try:
        ticker = yf.Ticker(s)
        hist = ticker.history(period="5d")
        if not hist.empty:
            print(f"✅ {s}: Found {len(hist)} records")
        else:
            print(f"❌ {s}: No data")
    except Exception as e:
        print(f"❌ {s}: Error {e}")
