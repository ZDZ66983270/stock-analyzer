
import yfinance as yf

symbols = ["^NDX", "^IXIC"]
print("Testing Yahoo Finance Symbols:")
for s in symbols:
    print(f"\nTesting {s}...")
    try:
        ticker = yf.Ticker(s)
        hist = ticker.history(period="5d")
        if not hist.empty:
            print(f"✅ {s}: Found {len(hist)} records. Last close: {hist['Close'].iloc[-1]}")
            info = ticker.info
            print(f"   Name: {info.get('shortName')} / {info.get('longName')}")
        else:
            print(f"❌ {s}: No data")
    except Exception as e:
        print(f"❌ {s}: Error {e}")
