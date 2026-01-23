import akshare as ak
import pandas as pd
import os

print(f"AkShare Version: {ak.__version__}")
print("Testing Sina HK Spot (stock_hk_spot)...")

try:
    # Sina interface (No params according to docs)
    df = ak.stock_hk_spot()
    
    if df is not None and not df.empty:
        print(f"Success! Fetched {len(df)} rows.")
        print("Columns:", df.columns.tolist())
        print("First 5 rows:")
        print(df.head())
        
        # Save for inspection
        save_path = os.path.join(os.path.dirname(__file__), "market_data_library", "snapshot_hk_sina.csv")
        df.to_csv(save_path, index=False)
        print(f"Saved to {save_path}")
    else:
        print("Returned empty dataframe.")

except Exception as e:
    print(f"Error: {e}")
