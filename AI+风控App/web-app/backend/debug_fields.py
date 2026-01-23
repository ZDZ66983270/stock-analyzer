import asyncio
from data_fetcher import DataFetcher
import json
import pandas as pd

async def debug_fields():
    f = DataFetcher()
    symbol = "AAPL"
    market = "US"
    
    print(f"--- Debugging {symbol} ({market}) ---")
    
    # 1. Test Daily Fallback Content
    print("\n1. Test Daily Fetch Structure:")
    us_sym = f.to_akshare_us_symbol(symbol)
    daily = f.fetch_us_daily_data(us_sym)
    if daily is not None and not daily.empty:
        print("Columns:", daily.columns.tolist())
        row = daily.iloc[-1]
        print("Last Row:")
        print(row)
        
        # Check calculation
        close = row['close']
        prev = daily.iloc[-2]['close'] if len(daily) > 1 else close
        calc_change = close - prev
        calc_pct = (calc_change / prev) * 100
        print(f"Calc Change: {calc_change}, Calc Pct: {calc_pct}%")
    else:
        print("Daily Fetch Failed/Empty")

    # 2. Test Yahoo Indicators
    print("\n2. Test Yahoo Indicators:")
    try:
        inds = f.fetch_yahoo_indicators(symbol)
        print(json.dumps(inds, indent=2))
    except Exception as e:
        print(f"Yahoo Failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_fields())
