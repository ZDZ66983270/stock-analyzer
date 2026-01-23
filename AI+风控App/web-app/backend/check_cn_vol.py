
import akshare as ak
import pandas as pd

symbol = "600536" 
print(f"Checking volume for {symbol} (China Software)...")

try:
    # 1. AkShare CN Minute
    # symbol needs full code? 600536
    print("--- AkShare CN Minute (Period='1') ---")
    df_min = ak.stock_zh_a_hist_min_em(symbol=symbol, period='1')
    if not df_min.empty:
        latest = df_min.iloc[-1]
        print(f"Latest Min Row Time: {latest['时间']}")
        print(f"Latest Min Volume: {latest['成交量']}")
        
        # Calculate Sum
        latest_date = pd.to_datetime(latest['时间']).date()
        df_min['时间'] = pd.to_datetime(df_min['时间'])
        day_df = df_min[df_min['时间'].dt.date == latest_date]
        total = day_df['成交量'].sum()
        print(f"Sum of Today's Minute Volumes: {total}")
    else:
        print("AkShare Min Empty")
except Exception as e:
    print(f"AkShare Min Error: {e}")

try:
    # 2. AkShare CN Daily
    print("\n--- AkShare CN Daily ---")
    df_day = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20241201", adjust="qfq")
    if not df_day.empty:
        latest_day = df_day.iloc[-1]
        print(f"Latest Day: {latest_day['日期']}") 
        print(f"Daily Volume: {latest_day['成交量']}")
        print(f"Is this Hands or Shares? (Usually Hands for A-share)")
    else:
        print("AkShare Daily Empty")
except Exception as e:
    print(f"AkShare Daily Error: {e}")
