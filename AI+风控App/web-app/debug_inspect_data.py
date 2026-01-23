import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from backend.db import engine
from backend.models import RawMarketData, FinancialFundamentals, MarketDataDaily
import pandas as pd

def inspect_symbol(symbol):
    print(f"\n{'='*20} INSPECTING {symbol} {'='*20}")
    
    with Session(engine) as session:
        # 1. Check RawMarketData (Last 5)
        print("\n--- [RawMarketData] (Last 5) ---")
        raws = session.exec(select(RawMarketData).where(RawMarketData.symbol == symbol).order_by(RawMarketData.timestamp.desc()).limit(5)).all()
        if not raws:
            print("❌ No RawMarketData found.")
        else:
            for r in raws:
                print(f"Time: {r.timestamp}, Source: {r.source}, Status: {r.processing_status}, Size: {len(r.payload) if r.payload else 0} chars")

        # 2. Check FinancialFundamentals (Last 5)
        print("\n--- [FinancialFundamentals] (Last 5) ---")
        fins = session.exec(select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).order_by(FinancialFundamentals.as_of_date.desc()).limit(5)).all()
        if not fins:
            print("❌ No FinancialFundamentals found.")
        else:
            for f in fins:
                print(f"Date: {f.as_of_date}, Type: {f.report_type}, EPS: {f.eps}, Rev: {f.revenue_ttm}, NetInc: {f.net_income_ttm}")
        
        # 3. Check MarketDataDaily PE/PE_TTM (Last 5 Valid)
        print("\n--- [MarketDataDaily] (Last 5 PE/PE_TTM) ---")
        dailies = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(5)).all()
        if not dailies:
            print("❌ No MarketDataDaily found.")
        else:
            for d in dailies:
                print(f"Date: {d.timestamp}, PE: {d.pe}, PE_TTM: {d.pe_ttm}, Close: {d.close}")

if __name__ == "__main__":
    inspect_symbol("US:STOCK:TSM")
    inspect_symbol("HK:STOCK:00700")
