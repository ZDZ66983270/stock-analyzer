
import sys
sys.path.append('.')
import logging
from fetch_valuation_history import fetch_hk_valuation_baidu_direct
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_hk(symbol="00700"):
    print(f"Fetching valuation for {symbol}...")
    try:
        df = fetch_hk_valuation_baidu_direct(symbol, indicator="市盈率(TTM)")
        if df is not None and not df.empty:
            print(f"Data shape: {df.shape}")
            print(df.head(10))
            print("...")
            print(df.tail(20))
            
            # Check for specific dates
            print("\nChecking for specific dates:")
            check_dates = ['2026-01-12', '2026-01-09', '2026-01-08', '2025-12-30', '2025-12-31']
            for d in check_dates:
                # Assuming date col is string or date object
                # The output from previous tool shows it has a 'date' column
                # Let's normalize to string YYYY-MM-DD
                df['date_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                match = df[df['date_str'] == d]
                if not match.empty:
                    print(f"  ✅ Found {d}: {match.iloc[0]['value']}")
                else:
                    print(f"  ❌ Missing {d}")
        else:
            print("No data returned.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_hk()
