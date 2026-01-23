
import sys
import os
# Add current directory to path so we can import backend
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlmodel import Session, select, delete, text
from backend.database import engine
from backend.models import Watchlist, Index, MarketSnapshot, MarketDataDaily, FinancialFundamentals
from backend.symbol_utils import get_canonical_id

def migrate_ids():
    print("🚀 Starting Database Migration to Standard Canonical IDs (Optimized)...")
    
    with Session(engine) as session:
        # 1. Standardize Watchlist
        print("\nChecking Watchlist...")
        watchlist_items = session.exec(select(Watchlist)).all()
        for item in watchlist_items:
            asset_type = 'STOCK'
            if ':INDEX:' in item.symbol: asset_type = 'INDEX'
            elif ':ETF:' in item.symbol: asset_type = 'ETF'
            elif ':CRYPTO:' in item.symbol: asset_type = 'CRYPTO'
            raw_symbol = item.symbol.split(':')[-1]
            new_id, new_market = get_canonical_id(raw_symbol, item.market, asset_type)
            if item.symbol != new_id:
                print(f"   🔄 Watchlist: {item.symbol} -> {new_id}")
                existing = session.exec(select(Watchlist).where(Watchlist.symbol == new_id)).first()
                if existing:
                    session.delete(item)
                else:
                    item.symbol = new_id
                    item.market = new_market
                    session.add(item)
        session.commit()

        # 2. Standardize Index Table
        print("\nChecking Index Table...")
        index_items = session.exec(select(Index)).all()
        for item in index_items:
            market = item.symbol.split(':')[0] if ':' in item.symbol else item.market
            raw_symbol = item.symbol.split(':')[-1] if ':' in item.symbol else item.symbol
            new_id, new_market = get_canonical_id(raw_symbol, market, 'INDEX')
            if item.symbol != new_id:
                print(f"   🔄 Index: {item.symbol} -> {new_id}")
                existing = session.exec(select(Index).where(Index.symbol == new_id)).first()
                if existing:
                    session.delete(item)
                else:
                    item.symbol = new_id
                    item.market = new_market
                    session.add(item)
        session.commit()

        # 3. Clean FinancialFundamentals
        print("\nCleaning FinancialFundamentals...")
        # Remove anything with INDEX in symbol
        session.execute(text("DELETE FROM financialfundamentals WHERE symbol LIKE '%INDEX%'"))
        # Remove ambiguous ones
        session.execute(text("DELETE FROM financialfundamentals WHERE symbol IN ('000001', '000300')"))
        session.commit()

        # 4. Update MarketSnapshot and MarketDataDaily using RAW SQL for speed and to handle conflicts
        mapping = {
            "CRYPTO:CRYPTO:BTC": "WORLD:CRYPTO:BTC-USD",
            "US:INDEX:^DJI": "US:INDEX:DJI",
            "US:INDEX:^NDX": "US:INDEX:NDX",
            "US:INDEX:^SPX": "US:INDEX:SPX"
        }
        
        for old_id, new_id in mapping.items():
            print(f"\nProcessing {old_id} -> {new_id}...")
            new_market = "WORLD" if "WORLD" in new_id else old_id.split(':')[0]
            
            # Sub-task: MarketSnapshot
            # Delete if new one exists, then update old to new
            session.execute(text(f"DELETE FROM marketsnapshot WHERE symbol = :new_id AND market = :market"), {"new_id": new_id, "market": new_market})
            session.execute(text(f"UPDATE marketsnapshot SET symbol = :new_id, market = :market WHERE symbol = :old_id"), {"new_id": new_id, "market": new_market, "old_id": old_id})
            
            # Sub-task: MarketDataDaily
            # This is tricky due to (symbol, market, timestamp) unique key.
            # Strategy: 
            # 1. Delete records from old_id where (market, timestamp) already exists for new_id
            # 2. Update remaining old_id records to new_id
            
            # Step 1: Delete conflicts
            session.execute(text("""
                DELETE FROM marketdatadaily 
                WHERE symbol = :old_id 
                AND EXISTS (
                    SELECT 1 FROM marketdatadaily d2 
                    WHERE d2.symbol = :new_id 
                    AND d2.market = :market
                    AND d2.timestamp = marketdatadaily.timestamp
                )
            """), {"old_id": old_id, "new_id": new_id, "market": new_market})
            
            # Step 2: Update remaining
            session.execute(text("""
                UPDATE marketdatadaily 
                SET symbol = :new_id, market = :market 
                WHERE symbol = :old_id
            """), {"old_id": old_id, "new_id": new_id, "market": new_market})
            
            session.commit()

    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate_ids()
