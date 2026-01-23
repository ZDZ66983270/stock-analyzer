
import sys
from sqlmodel import Session, select
sys.path.append('backend')
from database import engine
from models import MarketSnapshot

def verify_snapshot_pe():
    print("="*60)
    print("📸 Verifying PE in MarketSnapshot Table")
    print("="*60)
    print(f"{'Symbol':<15} | {'Market':<6} | {'Price':<10} | {'PE':<10} | {'Updated At'}")
    print("-" * 65)
    
    with Session(engine) as session:
        snapshots = session.exec(select(MarketSnapshot)).all()
        
        has_pe_count = 0
        total = 0
        
        for s in snapshots:
            total += 1
            pe_display = f"{s.pe:.2f}" if s.pe is not None else "None"
            if s.pe is not None:
                has_pe_count += 1
                
            print(f"{s.symbol:<15} | {s.market:<6} | {s.price:<10.2f} | {pe_display:<10} | {s.updated_at}")
            
    print("-" * 65)
    print(f"Total Snapshots: {total}")
    print(f"With PE: {has_pe_count}")
    print(f"Missing PE: {total - has_pe_count}")
    print("="*60)

if __name__ == "__main__":
    verify_snapshot_pe()
