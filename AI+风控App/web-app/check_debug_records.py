
import sys
import os
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily

def check_records():
    with Session(engine) as session:
        # Check AAPL latest 5
        print("--- AAPL Latest 5 ---")
        rows = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == "US:STOCK:AAPL").order_by(MarketDataDaily.timestamp.desc()).limit(5)).all()
        for r in rows:
            print(f"TS: {r.timestamp}, Close: {r.close}, ID: {r.id}")
            
        # Check HK:STOCK:00700 Latest 1 (for PE)
        print("\n--- HK:STOCK:00700 Latest ---")
        hk = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == "HK:STOCK:00700").order_by(MarketDataDaily.timestamp.desc()).limit(1)).first()
        if hk:
            print(f"TS: {hk.timestamp}, Close: {hk.close}, PE: {hk.pe_ttm}, EPS: {hk.eps}")

if __name__ == "__main__":
    check_records()
