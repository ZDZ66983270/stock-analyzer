import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist
from collections import Counter

def list_types():
    with Session(engine) as session:
        items = session.exec(select(Watchlist)).all()
        
        types = []
        for item in items:
            parts = item.symbol.split(':')
            if len(parts) >= 2:
                types.append(parts[1])
            else:
                types.append("UNKNOWN")
                
        counter = Counter(types)
        
        print("="*40)
        print("📋 Watchlist Asset Categories")
        print("="*40)
        
        if not counter:
            print("No assets found.")
        else:
            for type_name, count in counter.most_common():
                print(f"  {type_name:<10}: {count} items")
        
        print("-" * 40)
        print(f"Total: {len(items)}")

if __name__ == "__main__":
    list_types()
