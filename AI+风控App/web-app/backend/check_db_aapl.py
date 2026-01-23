from sqlmodel import Session, select
from database import engine
from models import MarketData

def check_aapl():
    with Session(engine) as session:
        # Check standard AAPL.OQ or just AAPL
        stmt = select(MarketData).where(MarketData.symbol.like("%AAPL%")).order_by(MarketData.date.desc())
        results = session.exec(stmt).all()
        
        print(f"Found {len(results)} records for AAPL:")
        for res in results:
            print(f"ID: {res.id} | Period: {res.period} | Date: {res.date} | Close: {res.close} | Change: {res.change} | PctChange: {res.pct_change} | UpdatedAt: {res.updated_at}")

if __name__ == "__main__":
    check_aapl()
