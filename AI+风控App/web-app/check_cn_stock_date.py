import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily

def check_stock_date():
    with Session(engine) as session:
        symbol = "CN:STOCK:600030"
        print(f"Checking {symbol} in database...")
        latest = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if latest:
            print(f"Latest Record: Date={latest.timestamp}, Close={latest.close}, UpdatedAt={latest.updated_at}")
        else:
            print("No data found.")

if __name__ == "__main__":
    check_stock_date()
