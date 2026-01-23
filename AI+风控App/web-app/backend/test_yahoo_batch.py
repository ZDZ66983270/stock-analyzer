
import yfinance as yf

def test_yahoo_batch():
    # Test batch fetch for HK stocks
    tickers = ["0700.HK", "09988.HK", "03690.HK"] # Tencent, Alibaba, Meituan
    print(f"Testing Batch Fetch for {tickers} (1m interval)...")
    
    try:
        # Batch download
        data = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False)
        
        if data is None or data.empty:
            print("FAILED: Empty result.")
            return

        print(f"SUCCESS: Result Shape: {data.shape}")
        
        # Check structure
        # If batch, columns might be MultiIndex
        print("Columns Level 0:", data.columns.get_level_values(0).unique())
        
        for t in tickers:
            try:
                # Access individual ticker data
                # Structure depends on yfinance version/group_by
                # Usually data[Ticker] or data[(Price, Ticker)]
                sub = data[t]
                print(f"\n[{t}] Rows: {len(sub)}")
                print(sub.head(2))
            except Exception as e:
                print(f"Failed to access {t}: {e}")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_yahoo_batch()
