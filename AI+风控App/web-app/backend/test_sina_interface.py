import akshare as ak
import pandas as pd
import time

# Force full display
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def test_sina():
    print("--- Testing Sina US Spot Interface (Realtime) ---")
    try:
        df = ak.stock_us_spot()
        
        # Check specific symbols
        targets = ['AAPL', 'TSLA', 'MSFT', 'NVDA', 'BABA', 'PDD']
        print(f"\nScanning for: {targets}")
        
        if not match.empty:
            # Print FULL dictionary for the first match (AAPL)
            record = match.iloc[0].to_dict()
            print(f"\n--- 完整字段详情 (AAPL) ---")
            for k, v in record.items():
                print(f"{k:<15}: {v}")
        else:
            print("No targets found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sina()
