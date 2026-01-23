
import sys
import os
from datetime import datetime

# Adjust path to root to allow 'backend' imports
sys.path.append(os.getcwd())

from backend.database import engine, get_session
from backend.models import Watchlist, MarketDataDaily, MarketDataMinute
from sqlmodel import select, Session

def check_data():
    cn_open = False
    hk_open = False
    now = datetime.now()
    # Simple status check (approximate)
    if 9 <= now.hour < 15: cn_open = 'OPEN (Approx)' # Rough check
    if 9 <= now.hour < 16: hk_open = 'OPEN (Approx)'
    
    print(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    # We can't easily check 'status' without DataFetcher fully loaded, 
    # but let's just query the data as requested.
    
    with Session(engine) as session:
        # Get Watchlist
        watchlist = session.exec(select(Watchlist)).all()
        
        print("\n--- Latest Data for A/HK Shares ---")
        print(f"{'Symbol':<12} {'Market':<8} {'Price':<10} {'Timestamp':<25}")
        print("-" * 60)
        
        for item in watchlist:
            if item.market not in ['CN', 'HK']:
                continue
                
            # Check Daily
            daily = session.exec(select(MarketDataDaily).where(
                MarketDataDaily.symbol == item.symbol.upper()
            ).order_by(MarketDataDaily.date.desc()).limit(1)).first()
            
            # Check Minute
            minute = session.exec(select(MarketDataMinute).where(
                MarketDataMinute.symbol == item.symbol.upper()
            ).order_by(MarketDataMinute.date.desc()).limit(1)).first()
            
            # Decide best
            price = "N/A"
            ts = "N/A"
            
            # Prefer Minute data if it's from today, otherwise Daily
            if minute and str(minute.date).startswith(now.strftime('%Y-%m-%d')):
                 price = minute.close
                 ts = minute.date
            elif daily:
                 price = daily.close
                 # Format logic
                 d_str = str(daily.date)
                 if d_str.endswith('00:00:00'):
                      if item.market == 'CN': d_str = d_str.replace('00:00:00', '15:00:00')
                      elif item.market == 'HK': d_str = d_str.replace('00:00:00', '16:00:00')
                 ts = d_str
            
            print(f"{item.symbol:<12} {item.market:<8} {price:<10} {ts:<25}")

if __name__ == "__main__":
    check_data()
