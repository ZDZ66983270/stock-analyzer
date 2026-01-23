import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketSnapshot

def check_snapshot_price():
    with Session(engine) as session:
        symbol = "CN:STOCK:600030"
        print(f"Checking Snapshot for {symbol}...")
        snapshot = session.exec(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == symbol)
        ).first()
        
        if snapshot:
            print(f"Snapshot Record: Price={snapshot.price}, UpdatedAt={snapshot.timestamp}")
        else:
            print("No snapshot found.")

if __name__ == "__main__":
    check_snapshot_price()
