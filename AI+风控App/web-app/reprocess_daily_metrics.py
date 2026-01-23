
import sys
sys.path.append('backend')

from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily, Watchlist, Index
import pandas as pd
from datetime import datetime

def reprocess_symbol(session, symbol, market):
    print(f"Processing {symbol} ({market})...")
    
    # Get all records sorted by time
    statement = select(MarketDataDaily).where(
        MarketDataDaily.symbol == symbol,
        MarketDataDaily.market == market
    ).order_by(MarketDataDaily.timestamp)
    
    records = list(session.exec(statement).all())
    
    if not records:
        print(f"   No records found.")
        return 0
        
    updated_count = 0
    last_close = None
    
    for record in records:
        changed = False
        
        # 1. Update prev_close
        if last_close is not None:
            if record.prev_close != last_close:
                record.prev_close = last_close
                changed = True
        
        # 2. Update change & pct_change
        if record.prev_close and record.close:
            expected_change = record.close - record.prev_close
            expected_pct = (expected_change / record.prev_close) * 100
            
            # Allow small float diff
            if record.change is None or abs(record.change - expected_change) > 0.0001:
                record.change = expected_change
                changed = True
                
            if record.pct_change is None or abs(record.pct_change - expected_pct) > 0.0001:
                record.pct_change = expected_pct
                changed = True
        
        if changed:
            record.updated_at = datetime.utcnow()
            session.add(record)
            updated_count += 1
            
        last_close = record.close
        
    return updated_count

def main():
    print("Starting Daily Data Reprocessing (ETL: Calc Change/Pct)...")
    
    with Session(engine) as session:
        # Get all symbols
        watchlist = session.exec(select(Watchlist)).all()
        indices = session.exec(select(Index)).all()
        
        all_targets = []
        for i in indices: all_targets.append((i.symbol, i.market))
        for w in watchlist: all_targets.append((w.symbol, w.market))
        
        total_updated = 0
        
        for symbol, market in all_targets:
            c = reprocess_symbol(session, symbol, market)
            total_updated += c
            
        session.commit()
        print(f"\nDone! Total updated records: {total_updated}")

if __name__ == "__main__":
    main()
