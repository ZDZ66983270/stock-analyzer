import yfinance as yf

def test_hk_syms():
    # Test 5 digit
    sym5 = "00700.HK"
    print(f"Testing {sym5}...")
    try:
        f = yf.Ticker(sym5).financials
        if f.empty: print("Empty")
        else: print(f"Found {len(f.columns)} cols")
    except: print("Error")

    # Test 4 digit
    sym4 = "0700.HK"
    print(f"Testing {sym4}...")
    try:
        f = yf.Ticker(sym4).financials
        if f.empty: print("Empty")
        else: print(f"Found {len(f.columns)} cols")
    except: print("Error")

if __name__ == "__main__":
    test_hk_syms()
