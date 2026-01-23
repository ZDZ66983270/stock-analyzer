
from backend.market_status import MarketStatus, is_market_open, get_market_time
from datetime import datetime
import pandas as pd

print(f"System Local Time: {datetime.now()}")

for market in ['CN', 'HK', 'US']:
    info = MarketStatus.get_market_status_info(market)
    print(f"--- {market} ---")
    print(f"Info: {info}")
    print(f"is_open: {is_market_open(market)}")
    
    now = get_market_time(market)
    print(f"Market Time: {now}")
    print(f"Market Date: {now.date()}")
    
    # Simulate the check in ETL
    market_today = now.date()
    market_should_be_open = is_market_open(market)
    
    # Simulate a row date of "today"
    row_date = pd.to_datetime("2026-01-14").date()
    
    if row_date == market_today and market_should_be_open:
        print(f"GUARD CHECK: SKIP Daily storage for {market} on {row_date} (Market is currently OPEN)")
    else:
        print(f"GUARD CHECK: PROCEED to storage (Risk of premature write!)")
