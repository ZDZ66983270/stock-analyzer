import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

# User Example:
# stock_hk_hist_min_em_df = ak.stock_hk_hist_min_em(symbol="01611", period='1', adjust='',
#                                                   start_date="2021-09-01 09:32:00",
#                                                   end_date="2021-09-07 18:32:00")

# Logic: Try 09988 (Alibaba)
symbol = "09988"
current_time = datetime.now()
start_time = (current_time - timedelta(days=5)).strftime("%Y-%m-%d 09:00:00")
end_time = current_time.strftime("%Y-%m-%d 16:00:00")

print(f"Testing stock_hk_hist_min_em for {symbol}...")
print(f"Time Range: {start_time} to {end_time}")

try:
    df = ak.stock_hk_hist_min_em(
        symbol=symbol, 
        period='1', 
        adjust='', 
        start_date=start_time, 
        end_date=end_time
    )
    
    if df is not None and not df.empty:
        print("Success!")
        print(df.tail())
        
        # Check latest price
        latest = df.iloc[-1]
        print(f"\nLatest Record Time: {latest['时间']}")
        print(f"Latest Price: {latest['最新价']}")
    else:
        print("Returned empty DataFrame.")
        
except Exception as e:
    print(f"Error: {e}")
