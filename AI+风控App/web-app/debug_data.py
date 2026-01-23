
import sys
import os
from sqlmodel import Session, select
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine
from models import MarketDataDaily, DividendFact, FinancialFundamentals, Watchlist

def debug_hk_dividend():
    print("\n🔎 Debugging HK Dividend (Target: HK:STOCK:00700)")
    print("-" * 60)
    with Session(engine) as session:
        # 1. Check DividendFact
        divs = session.exec(
            select(DividendFact)
            .where(DividendFact.asset_id == "HK:STOCK:00700")
            .order_by(DividendFact.ex_date.desc())
            .limit(5)
        ).all()
        
        print("Latest 5 DividendFacts:")
        for d in divs:
            print(f"  ExDate: {d.ex_date}, Cash: {d.cash_dividend}, Currency: {d.currency}")
            
        # 2. Check MarketDataDaily
        daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == "HK:STOCK:00700")
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if daily:
            print(f"\nLatest MarketDataDaily:")
            print(f"  Date: {daily.timestamp}")
            print(f"  Close: {daily.close}")
            print(f"  DivYield (DB Value): {daily.dividend_yield}")
            if daily.dividend_yield:
                print(f"  DivYield (Percentage): {daily.dividend_yield * 100:.4f}%")
        else:
            print("\nNo MarketDataDaily found.")

def debug_cn_metrics():
    print("\n🔎 Debugging CN Metrics (Target: CN:STOCK:600030 中信证券)")
    print("-" * 60)
    with Session(engine) as session:
        # 1. Check Financials
        funds = session.exec(
            select(FinancialFundamentals)
            .where(FinancialFundamentals.symbol == "CN:STOCK:600030")
            .order_by(FinancialFundamentals.as_of_date.desc())
            .limit(3)
        ).all()
        
        print("Latest 3 Financials:")
        if funds:
            for f in funds:
                print(f"  Date: {f.as_of_date}, NetIncome: {f.net_income_ttm}, Source: {f.data_source}")
        else:
            print("  No FinancialFundamentals found!")
            
        # 2. Check DividendFact
        divs = session.exec(
            select(DividendFact)
            .where(DividendFact.asset_id == "CN:STOCK:600030")
        ).all()
        print(f"\nTotal DividendFacts found: {len(divs)}")
        
        # 3. Check MarketDataDaily
        daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == "CN:STOCK:600030")
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if daily:
            print(f"\nLatest MarketDataDaily:")
            print(f"  Date: {daily.timestamp}")
            print(f"  Close: {daily.close}")
            print(f"  PE: {daily.pe}")
            print(f"  DivYield: {daily.dividend_yield}")
            print(f"  MarketCap: {daily.market_cap}")

if __name__ == "__main__":
    debug_hk_dividend()
    debug_cn_metrics()
