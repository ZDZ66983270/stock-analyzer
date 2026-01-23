import sys
import os
sys.path.append(os.getcwd())
from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily, Watchlist

def dump_db():
    try:
        with Session(engine) as session:
            # Get all watchlist items
            wl = session.exec(select(Watchlist)).all()
            print(f"Watchlist: {[w.symbol for w in wl]}")
            
            for item in wl:
                # Get latest 1d data
                latest = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == item.symbol, MarketDataDaily.market == item.market)
                ).first()
                
                if latest:
                    price_str = f"{latest.close}" if latest.close is not None else "None"
                    # change_str = f"{latest.change}" if latest.change is not None else "None" # removed from obj
                    vol_str = f"{latest.volume}" if latest.volume is not None else "None"
                    date_str = f"{latest.date}"
                    
                    print(f"Symbol: {item.symbol:<12} | Price: {price_str:<10} | Vol: {vol_str:<12} | Time: {date_str}")
                else:
                    print(f"Symbol: {item.symbol:<12} | NO 1d DATA (Checking ID...)")
    except Exception as e:
        print(f"Error dumping DB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    dump_db()
