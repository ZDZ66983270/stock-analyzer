import akshare as ak
import pandas as pd
import os
from datetime import datetime

# Setup
SYMBOL = "09988"
NAME = "Alibaba-HK"
PERIOD = "1" # 1 min
ADJUST = "qfq"

print(f"Fetching 1-min history for {NAME} ({SYMBOL})...")

try:
    # stock_hk_hist_min_em returns recent 5 days for 1-min
    # Note: start_date/end_date params in user docs might be optional or specific format
    # The user example: start_date="2021-09-01 09:32:00"
    # We will try to fetch default (recent) first.
    
    # Calculate a recent start date if needed, but docs say "Default returns all data" (limited to 5 days for 1min?)
    # User doc: "其中 1 分钟数据返回近 5 个交易日数据" -> Implicit limit.
    
    df = ak.stock_hk_hist_min_em(
        symbol=SYMBOL, 
        period=PERIOD, 
        adjust=ADJUST,
        start_date="2024-01-01 09:00:00", # Try a wide range, API will clip
        end_date="2222-01-01 16:00:00"
    )
    
    if df is not None and not df.empty:
        print(f"Success! Fetched {len(df)} rows.")
        print(df.head())
        print(df.tail())
        
        # Save
        filename = f"history_hk_{SYMBOL}_1min.csv"
        save_path = os.path.join(os.path.dirname(__file__), "market_data_library", filename)
        df.to_csv(save_path, index=False)
        print(f"Saved to {save_path}")
    else:
        print("No data returned.")

except Exception as e:
    print(f"Error: {e}")
