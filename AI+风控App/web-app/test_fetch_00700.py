
from fetch_valuation_history import fetch_hk_dividend_yield
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily
import logging

logging.basicConfig(level=logging.INFO)

def fix_00700():
    symbol = "HK:STOCK:00700"
    print(f"Fetching yield for {symbol}...")
    
    div = fetch_hk_dividend_yield(symbol)
    print(f"Result: {div}")
    
    if div is not None:
        with Session(engine) as session:
            record = session.exec(
                select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol
                ).order_by(MarketDataDaily.timestamp.desc())
            ).first()
            
            if record:
                print(f"Updating record {record.timestamp} from {record.dividend_yield} to {div}")
                record.dividend_yield = div
                session.add(record)
                session.commit()
                print("Done.")
            else:
                print("No record found.")

if __name__ == "__main__":
    fix_00700()
