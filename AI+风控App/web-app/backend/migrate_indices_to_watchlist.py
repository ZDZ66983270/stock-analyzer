import sys
import os
from datetime import datetime

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from sqlmodel import Session, select
from models import Watchlist, Index
from symbol_utils import get_canonical_id

def migrate():
    print("🚀 Starting migration: Index -> Watchlist")
    
    with Session(engine) as session:
        # 1. Fetch all indices
        indices = session.exec(select(Index)).all()
        print(f"📊 Found {len(indices)} indices in the Index table.")
        
        added_count = 0
        updated_count = 0
        
        for idx in indices:
            # 2. Get Canonical ID if not already there
            # Indices usually don't have suffixes in the Index table, but let's be safe
            symbol = idx.symbol
            if ':' not in symbol:
                canonical_id, market = get_canonical_id(symbol, idx.market, asset_type='INDEX')
            else:
                canonical_id = symbol
            
            # 3. Check if already in Watchlist
            existing_wl = session.exec(select(Watchlist).where(Watchlist.symbol == canonical_id)).first()
            
            if not existing_wl:
                # Add to Watchlist
                new_item = Watchlist(
                    symbol=canonical_id,
                    name=idx.name,
                    market=idx.market,
                    added_at=idx.added_at
                )
                session.add(new_item)
                added_count += 1
                print(f"✅ Added to Watchlist: {canonical_id} ({idx.name})")
            else:
                # Update existing name if needed
                if not existing_wl.name or existing_wl.name == existing_wl.symbol:
                    existing_wl.name = idx.name
                    session.add(existing_wl)
                    updated_count += 1
                    print(f"🔄 Updated Watchlist Name: {canonical_id} -> {idx.name}")
        
        session.commit()
        print("\n" + "="*50)
        print(f"🏁 Migration Completed:")
        print(f"✨ New Watchlist entries: {added_count}")
        print(f"📝 Updated Watchlist entries: {updated_count}")
        print("="*50)

if __name__ == "__main__":
    migrate()
