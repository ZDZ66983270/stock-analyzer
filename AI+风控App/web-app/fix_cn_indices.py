
import sys
from sqlmodel import Session, select
sys.path.append('backend')
from database import engine
from models import MarketSnapshot
from data_fetcher import fetch_latest_data
import time

def fix_cn_indices():
    print("🔧 Fixing CN Indices in MarketSnapshot...")
    
    with Session(engine) as session:
        # 1. Find all CN Indices
        indices = session.exec(
            select(MarketSnapshot)
            .where(MarketSnapshot.market == 'CN')
            .where(MarketSnapshot.symbol.contains('INDEX'))
        ).all()
        
        print(f"Found {len(indices)} CN Indices to fix.")
        
        # 2. Delete them to force fresh fetch and clear bad data
        for idx in indices:
            print(f"🗑️ Deleting corrupted snapshot: {idx.symbol} (Price: {idx.price})")
            session.delete(idx)
        session.commit()
        print("✅ Deleted corrupted snapshots.")

    # 3. Re-fetch
    # List of common CN indices to re-add/update
    # We can get them from Watchlist, but for now let's manually trigger the ones we saw.
    # Actually, running update_snapshots_with_pe.py again is better if cache is gone.
    # But let's do 000001 and 000300 explicitly here to verify.
    
    target_indices = ['CN:INDEX:000001', 'CN:INDEX:000300']
    
    print("\n🔄 Re-fetching correct data...")
    for symbol in target_indices:
        print(f"Fetching {symbol}...")
        # Force refresh to be sure, though cache is gone so it should fetch anyway.
        data = fetch_latest_data(symbol, 'CN', force_refresh=True) 
        if data:
            print(f"✅ Fixed {symbol}: Price={data.get('price')}, PE={data.get('pe')}")
        else:
            print(f"❌ Failed to fetch {symbol}")
        time.sleep(1)

if __name__ == "__main__":
    fix_cn_indices()
