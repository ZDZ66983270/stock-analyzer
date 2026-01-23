
import sys
import os
from sqlmodel import Session, select
import logging

# Silence logs
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import engine
from backend.models import FinancialFundamentals

def inspect(symbol):
    with Session(engine) as session:
        print(f"--- FINS for {symbol} ---")
        stmt = select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).order_by(FinancialFundamentals.as_of_date.desc())
        fins = session.exec(stmt).all()
        if not fins:
            print("No records found.")
        for f in fins:
            print(f"Date: {f.as_of_date}, EPS: {f.eps}, Src: {f.data_source}")

if __name__ == "__main__":
    inspect("HK:STOCK:00005")
