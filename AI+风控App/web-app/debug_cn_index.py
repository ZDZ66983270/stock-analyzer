import yfinance as yf

def test_cn_index():
    print("--- Testing 000001.SS (Should be Shanghai Index ~3300) ---")
    t1 = yf.Ticker("000001.SS")
    hist1 = t1.history(period="1d")
    print(hist1)
    if not hist1.empty:
        print(f"000001.SS Close: {hist1['Close'].iloc[-1]}")

    print("\n--- Testing 000001.SZ (Should be Ping An Bank ~11.6) ---")
    t2 = yf.Ticker("000001.SZ")
    hist2 = t2.history(period="1d")
    print(hist2)
    if not hist2.empty:
        print(f"000001.SZ Close: {hist2['Close'].iloc[-1]}")

    print("\n--- Testing ^SSEC (Standard Yahoo Shanghai Index) ---")
    t3 = yf.Ticker("^SSEC")
    hist3 = t3.history(period="1d")
    print(hist3)
    if not hist3.empty:
        print(f"^SSEC Close: {hist3['Close'].iloc[-1]}")

if __name__ == "__main__":
    test_cn_index()
