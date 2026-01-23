
from sqlmodel import create_engine, Session, select
from models import MarketDataMinute
from datetime import datetime

# Setup DB
engine = create_engine("sqlite:///database.db")

def check_minute_vol():
    # Check 09988.hk minute data (Alibaba)
    target_sym = '09988.hk' 
    
    with Session(engine) as session:
        # Get latest 10 minute records
        stmt = select(MarketDataMinute).where(MarketDataMinute.symbol == target_sym).order_by(MarketDataMinute.date.desc()).limit(10)
        results = session.exec(stmt).all()
        
        print(f"=== Minute Data for {target_sym} ===")
        if not results:
            print("No minute data found.")
            return

        total_vol_today = 0
        latest_date = results[0].date.date()
        
        for r in results:
            print(f"Time: {r.date} | Close: {r.close} | Vol: {r.volume}")
            
if __name__ == "__main__":
    check_minute_vol()
