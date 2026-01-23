
from sqlmodel import create_engine, Session, select
from models import MarketDataDaily
from datetime import datetime

# Setup DB
engine = create_engine("sqlite:///database.db")

def check_today():
    target_date_str = "2025-12-15"
    symbols = ['HSI', 'HSTECH', '000001.SS', '800000', '800700', 'hkHSI', 'hkHSTECH']
    
    with Session(engine) as session:
        print(f"=== Checking Data for {target_date_str} ===")
        for sym in symbols:
            # Check Daily
            stmt = select(MarketDataDaily).where(
                MarketDataDaily.symbol == sym
            ).order_by(MarketDataDaily.date.desc()).limit(1)
            
            rec = session.exec(stmt).first()
            
            if rec:
                print(f"Symbol: {sym:<10} | Date: {rec.date} | Close: {rec.close} | Change: {rec.change} | Pct: {rec.pct_change} | Market: {rec.market}")
                # Check if it matches today
                if str(rec.date).startswith(target_date_str):
                    print(f"  -> SUCCESS: Found today's data for {sym}")
                else:
                    print(f"  -> WARNING: Latest data is OLD ({rec.date})")
            else:
                print(f"Symbol: {sym:<10} | NO DATA FOUND")

if __name__ == "__main__":
    check_today()
