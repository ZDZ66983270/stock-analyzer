
import sys
from sqlmodel import Session, select, func
from backend.database import engine
from backend.models import FinancialFundamentals, Watchlist

def check_counts():
    print("📊 Checking Quarterly Financials Data...")
    with Session(engine) as session:
        # 1. Total Quarterly Records
        q_count = session.exec(select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.report_type == 'quarterly')).one()
        a_count = session.exec(select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.report_type == 'annual')).one()
        
        print(f"   ✅ Total Quarterly Records: {q_count}")
        print(f"   ✅ Total Annual Records:    {a_count}")
        
        # 2. Breakdown by Market
        # Join with Watchlist to get market
        # This might be slow if table is huge, but fine for now
        print("\n   🔍 Breakdown by Market (Quarterly):")
        
        # Get all quarterly symbols first
        q_symbols = session.exec(select(FinancialFundamentals.symbol).where(FinancialFundamentals.report_type == 'quarterly').distinct()).all()
        
        market_counts = {'US': 0, 'HK': 0, 'CN': 0}
        
        for sym in q_symbols:
            # Check market from watchlist (cache this in real app)
            w = session.exec(select(Watchlist).where(Watchlist.symbol == sym)).first()
            if w and w.market in market_counts:
                market_counts[w.market] += 1
                
        for m, c in market_counts.items():
            print(f"      - {m}: {c} stocks have quarterly data")

if __name__ == "__main__":
    check_counts()
