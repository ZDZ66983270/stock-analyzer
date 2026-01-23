
from sqlmodel import create_engine, Session, select
from models import MarketDataDaily, MarketDataMinute
from datetime import datetime

# Setup DB
engine = create_engine("sqlite:///database.db")

def migrate_data():
    mappings = [
        {'old': '800700', 'new': 'HSTECH', 'market': 'HK'},
        {'old': '800000', 'new': 'HSI', 'market': 'HK'},
        # Add others if needed
    ]
    
    with Session(engine) as session:
        for m in mappings:
            old_sym = m['old']
            new_sym = m['new']
            mkt = m['market']
            
            print(f"Migrating {old_sym} -> {new_sym} ({mkt})...")
            
            # 1. Migrate Daily Data
            stmt_daily = select(MarketDataDaily).where(MarketDataDaily.symbol == old_sym, MarketDataDaily.market == mkt)
            daily_records = session.exec(stmt_daily).all()
            
            count_daily = 0
            for r in daily_records:
                # Check if new record exists to avoid unique constraint if any
                # Actually, duplicate dates might exist if we already ran something.
                # Let's just update the symbol! Faster and keeps ID.
                # But wait, if partial new data exists, we might have clashes?
                # Assume new symbol is empty as checked before.
                r.symbol = new_sym
                session.add(r)
                count_daily += 1
                
            print(f"  - Updated {count_daily} daily records.")

            # 2. Migrate Minute Data
            stmt_min = select(MarketDataMinute).where(MarketDataMinute.symbol == old_sym, MarketDataMinute.market == mkt)
            min_records = session.exec(stmt_min).all()
            
            count_min = 0
            for r in min_records:
                r.symbol = new_sym
                session.add(r)
                count_min += 1
                
            print(f"  - Updated {count_min} minute records.")
        
        session.commit()
        print("Migration committed.")

if __name__ == "__main__":
    migrate_data()
