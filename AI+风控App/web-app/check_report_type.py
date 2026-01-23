
import sys
import os
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals

def check_type():
    with Session(engine) as session:
        rows = session.exec(select(FinancialFundamentals.report_type).where(FinancialFundamentals.symbol == "US:STOCK:AMZN").distinct()).all()
        print(f"Distinct Report Types: {rows}")
        
        # Dump few rows
        rows = session.exec(select(FinancialFundamentals.as_of_date, FinancialFundamentals.report_type).where(FinancialFundamentals.symbol == "US:STOCK:AMZN").limit(5)).all()
        for r in rows:
            print(r)

if __name__ == "__main__":
    check_type()
