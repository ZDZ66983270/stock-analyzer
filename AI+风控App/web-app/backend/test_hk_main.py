import akshare as ak
import pandas as pd
import os

print("Testing EastMoney HK Main Board Spot...")
try:
    # Try specific board interface
    df = ak.stock_hk_main_board_spot_em()
    print(f"Success! Fetched {len(df)} rows.")
    
    # Save if successful
    save_path = os.path.join(os.path.dirname(__file__), "market_data_library", "snapshot_hk_main.csv")
    df.to_csv(save_path, index=False)
    print(f"Saved to {save_path}")

except Exception as e:
    print(f"Error: {e}")
