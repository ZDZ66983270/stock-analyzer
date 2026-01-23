
import sys
import os
from datetime import datetime
import pytz

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.database import engine
from backend.models import Watchlist, MarketDataDaily, MarketDataMinute
from sqlmodel import Session, select
from backend.data_fetcher import DataFetcher

def check_status():
    fetcher = DataFetcher(log_dir="backend/logs_debug")
    
    cn_status = fetcher.check_market_status("CN")
    hk_status = fetcher.check_market_status("HK")
    
    print(f"Current Time: {datetime.now()}")
    print(f"A-Share (CN) Status: {'OPEN' if cn_status else 'CLOSED'}")
    print(f"HK Stock (HK) Status: {'OPEN' if hk_status else 'CLOSED'}")
    
    with Session(engine) as session:
        # Get Watchlist
        watchlist = session.exec(select(Watchlist)).all()
        
        print("\n--- Latest Data for Watchlist (CN/HK) ---")
        print(f"{'Symbol':<12} {'Market':<8} {'Price':<10} {'Timestamp':<25} {'Source'}")
        print("-" * 70)
        
        for item in watchlist:
            if item.market not in ['CN', 'HK']:
                continue
                
            # Check Daily
            daily = session.exec(select(MarketDataDaily).where(
                MarketDataDaily.symbol == item.symbol
            ).order_by(MarketDataDaily.date.desc()).limit(1)).first()
            
            # Check Minute (for today)
            minute = session.exec(select(MarketDataMinute).where(
                MarketDataMinute.symbol == item.symbol
            ).order_by(MarketDataMinute.date.desc()).limit(1)).first()
            
            latest = None
            source = "None"
            
            if minute:
                latest = minute
                source = "Minute"
                # If minute is older than daily (unlikely if today), prefer daily? 
                # Actually minute is usually finer.
                if daily and daily.date > minute.date: # String comparison works for ISO format
                    latest = daily
                    source = "Daily"
            elif daily:
                latest = daily
                source = "Daily"
            
            price = latest.close if latest else "N/A"
            ts = latest.date if latest else "N/A"
            
            print(f"{item.symbol:<12} {item.market:<8} {price:<10} {ts:<25} {source}")

if __name__ == "__main__":
    check_status()
