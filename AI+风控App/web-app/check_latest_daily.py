import sys
sys.path.append('backend')
from sqlmodel import Session, select, func
from backend.database import engine
from backend.models import MarketDataDaily
import pandas as pd

def check_latest():
    with Session(engine) as session:
        print("="*80)
        print("🔍 checking Latest MarketDataDaily Records per Market")
        print("="*80)
        
        markets = ['CN', 'HK', 'US']
        
        for market in markets:
            print(f"\n📊 Market: {market}")
            # Get latest date for this market
            latest_date_query = select(func.max(MarketDataDaily.timestamp)).where(MarketDataDaily.market == market)
            latest_date = session.exec(latest_date_query).first()
            
            if not latest_date:
                print("   No data found.")
                continue
                
            print(f"   📅 Latest Timestamp: {latest_date}")
            
            # Fetch a few records from this date
            stmt = select(MarketDataDaily).where(
                MarketDataDaily.market == market,
                MarketDataDaily.timestamp == latest_date
            ).limit(5)
            
            results = session.exec(stmt).all()
            
            if not results:
                print("   (Data found but fetch failed? Strange.)")
                continue
                
            data = []
            for r in results:
                data.append({
                    "Symbol": r.symbol,
                    "Close": r.close,
                    "PE": r.pe,
                    "PE(TTM)": r.pe_ttm,
                    "PB": r.pb,
                    "Updated": r.updated_at
                })
            
            df = pd.DataFrame(data)
            print(df.to_string(index=False))
            print("-" * 60)

if __name__ == "__main__":
    check_latest()
