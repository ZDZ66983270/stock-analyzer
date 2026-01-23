
import yfinance as yf

def test_yahoo_hk_format():
    # Candidates for Alibaba (09988) and Tencent (00700) and Meituan (03690)
    candidates = [
        "9988.HK", "09988.HK", 
        "0700.HK", "00700.HK",
        "3690.HK", "03690.HK"
    ]
    
    print(f"Testing Yahoo fetch for: {candidates}")
    try:
        data = yf.download(candidates, period="1d", interval="1m", group_by='ticker', progress=False)
        
        # Check which columns exist (successfully fetched)
        if hasattr(data.columns, 'levels'):
            # MultiIndex
            found = data.columns.get_level_values(0).unique()
        else:
            found = data.columns
            
        print("\nSuccessfully fetched symbols:")
        print(found)
        
        # Explicitly check for Alibaba
        print("\nChecking Alibaba (9988 vs 09988):")
        if '9988.HK' in found: print("  9988.HK: FOUND")
        else: print("  9988.HK: MISSING")
            
        if '09988.HK' in found: print("  09988.HK: FOUND")
        else: print("  09988.HK: MISSING")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_yahoo_hk_format()
