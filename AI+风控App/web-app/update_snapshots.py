
import sys
sys.path.append('backend')

from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily, MarketSnapshot, Watchlist, Index
from datetime import datetime

def update_snapshot(session, symbol, market):
    # Get latest daily
    latest_daily = session.exec(
        select(MarketDataDaily)
        .where(MarketDataDaily.symbol == symbol, MarketDataDaily.market == market)
        .order_by(MarketDataDaily.timestamp.desc())
        .limit(1)
    ).first()
    
    if not latest_daily:
        print(f"   No daily data for {symbol}")
        return

    # Prepare snapshot data
    snapshot_data = {
        'price': latest_daily.close,
        'open': latest_daily.open,
        'high': latest_daily.high,
        'low': latest_daily.low,
        'volume': latest_daily.volume,
        'change': latest_daily.change,
        'pct_change': latest_daily.pct_change,
        'prev_close': latest_daily.prev_close,
        'timestamp': latest_daily.timestamp, # Use standard timestamp
        'data_source': 'daily_close (backfill)',
        'updated_at': datetime.utcnow()
    }
    
    # Upsert
    snapshot = session.exec(
        select(MarketSnapshot)
        .where(MarketSnapshot.symbol == symbol, MarketSnapshot.market == market)
    ).first()
    
    if snapshot:
        for k, v in snapshot_data.items():
            setattr(snapshot, k, v)
    else:
        snapshot = MarketSnapshot(symbol=symbol, market=market, **snapshot_data)
        session.add(snapshot)
    
    print(f"✅ Updated Snapshot for {symbol}: {latest_daily.close}")

def main():
    print("Syncing MarketSnapshot from MarketDataDaily...")
    with Session(engine) as session:
        # Get all symbols
        watchlist = session.exec(select(Watchlist)).all()
        indices = session.exec(select(Index)).all()
        
        targets = []
        for i in indices: targets.append((i.symbol, i.market))
        for w in watchlist: targets.append((w.symbol, w.market))
        
        for s, m in targets:
            update_snapshot(session, s, m)
            
        session.commit()
    print("Snapshot Sync Complete.")

if __name__ == "__main__":
    main()
