
import sys
import os
from sqlmodel import Session, select
from sqlalchemy import text

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import engine
from backend.models import MarketDataDaily

def inspect_duplicates(symbol):
    with Session(engine) as session:
        print(f"--- Records for {symbol} (Last 10) ---")
        stmt = select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(10)
        rows = session.exec(stmt).all()
        for r in rows:
            print(f"ID: {r.id}, TS: {r.timestamp}, Close: {r.close}, PE: {r.pe_ttm}")

if __name__ == "__main__":
    inspect_duplicates("US:STOCK:NVDA")
