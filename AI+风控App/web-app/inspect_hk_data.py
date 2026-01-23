
import sys
import os
from sqlmodel import Session, select
import pandas as pd

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import engine
from backend.models import FinancialFundamentals, MarketDataDaily

def inspect(symbol):
    with Session(engine) as session:
        print(f"--- Inspecting {symbol} ---")
        
        # 1. Financials
        stmt = select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).order_by(FinancialFundamentals.as_of_date.desc()).limit(5)
        fins = session.exec(stmt).all()
        print("\n[Financials (Top 5)]")
        for f in fins:
            print(f"Date: {f.as_of_date}, ReportType: {f.report_type}, EPS: {f.eps}, NetIncome: {f.net_income_ttm}")
            
        # 2. Market Data
        stmt = select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(5)
        mkt = session.exec(stmt).all()
        print("\n[Market Data (Top 5)]")
        for m in mkt:
            print(f"Date: {m.timestamp}, Close: {m.close}, PE_TTM: {m.pe_ttm}, EPS_in_Daily: {m.eps}")

if __name__ == "__main__":
    inspect("HK:STOCK:00005")
