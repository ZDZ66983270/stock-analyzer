
import sys
import os
from sqlmodel import Session, select, delete
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from models import MarketDataDaily
from market_status import get_market_time, is_market_open

def cleanup():
    print("🧹 Cleaning up unfinalized daily records...")
    
    with Session(engine) as session:
        count = 0
        for market in ['CN', 'HK', 'US']:
            market_now = get_market_time(market)
            today_str = market_now.strftime('%Y-%m-%d')
            is_open = is_market_open(market)
            
            if is_open:
                print(f"🔍 Market {market} is OPEN. Checking for records on {today_str}...")
                
                # Delete daily records for today in open markets
                stmt = delete(MarketDataDaily).where(
                    MarketDataDaily.market == market,
                    MarketDataDaily.timestamp.like(f"{today_str}%")
                )
                result = session.exec(stmt)
                count += result.rowcount
                print(f"🗑️ Deleted {result.rowcount} unfinalized records for {market}")
            else:
                print(f"✅ Market {market} is CLOSED or on weekend. Today's data (if any) is considered finalized.")
        
        session.commit()
        print(f"✨ Cleanup complete. Total records removed: {count}")

if __name__ == "__main__":
    cleanup()
