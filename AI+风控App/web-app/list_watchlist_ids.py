import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist

def list_ids():
    with Session(engine) as session:
        items = session.exec(select(Watchlist).order_by(Watchlist.market, Watchlist.symbol)).all()
        
        print("="*60)
        print(f"📋 Watchlist Canonical IDs (Total: {len(items)})")
        print("="*60)
        print(f"{'Canonical ID':<30} | {'Name':<20} | {'Market'}")
        print("-" * 60)
        
        for item in items:
            name = item.name if item.name else ""
            print(f"{item.symbol:<30} | {name:<20} | {item.market}")
            
        print("="*60)

if __name__ == "__main__":
    list_ids()
