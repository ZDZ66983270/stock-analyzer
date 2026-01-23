import sys
import os
sys.path.append('web-app') # Ensure backend imports work
from sqlmodel import Session, select, func, col
from backend.database import engine
from backend.models import MarketDataDaily, FinancialFundamentals, Watchlist

def verify_data():
    with Session(engine) as session:
        print("="*60)
        print("🔍 DATABASE VERIFICATION REPORT")
        print("="*60)

        # 1. PE TTM Check (MarketDataDaily)
        print("\n[1] PE TTM (MarketDataDaily) Coverage")
        print("-" * 60)
        # Select stocks that are in Watchlist (to avoid checking removed assets)
        stocks = session.exec(select(Watchlist).where(Watchlist.market.in_(['US', 'HK', 'CN']))).all()
        stock_symbols = [s.symbol for s in stocks]
        
        # Check overall stats
        total_daily = session.exec(select(func.count(MarketDataDaily.id))).one()
        total_pe_ttm = session.exec(select(func.count(MarketDataDaily.id)).where(MarketDataDaily.pe_ttm != None)).one()
        
        print(f"Total Daily Records: {total_daily}")
        print(f"Records with PE_TTM: {total_pe_ttm} ({total_pe_ttm/total_daily*100:.1f}%)" if total_daily > 0 else "Records: 0")

        # Sample Check for Key Assets (NVDA, TSLA, 00700, 600519)
        sample_symbols = ['US:STOCK:NVDA', 'US:STOCK:TSLA', 'HK:STOCK:00700', 'CN:STOCK:600519']
        # Also check some from the user's current fetch if possible (BCAT?) - User logs showed trusts, maybe skip trusts for PE
        
        print(f"\n{'Symbol':<20} | {'Count PEm':<10} | {'Latest Date':<20} | {'Latest PE_TTM':<15}")
        print("-" * 75)
        
        for sym in sample_symbols:
            # Check if symbol exists in DB (fuzzy match for ease)
            # Actually simpler to query exact
            recs = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == sym)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()
            
            count = session.exec(
                select(func.count(MarketDataDaily.id))
                .where(MarketDataDaily.symbol == sym)
                .where(MarketDataDaily.pe_ttm != None)
            ).one()
            
            latest_date = recs.timestamp if recs else "N/A"
            latest_val = f"{recs.pe_ttm:.2f}" if recs and recs.pe_ttm is not None else "None"
            
            print(f"{sym:<20} | {count:<10} | {latest_date:<20} | {latest_val:<15}")

        # 2. Financials Completeness (FinancialFundamentals)
        print("\n\n[2] Financials Completeness (EPS, NetIncome, DividendAmount)")
        print("-" * 60)
        
        total_fin = session.exec(select(func.count(FinancialFundamentals.id))).one()
        with_eps = session.exec(select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.eps != None)).one()
        with_ni = session.exec(select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.net_income_ttm != None)).one()
        with_div = session.exec(select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.dividend_amount != None)).one()
        
        print(f"Total Financial Reports: {total_fin}")
        print(f"With EPS:              {with_eps:<5} ({with_eps/total_fin*100:.1f}%)")
        print(f"With Net Income:       {with_ni:<5} ({with_ni/total_fin*100:.1f}%)")
        print(f"With Dividend Amt:     {with_div:<5} ({with_div/total_fin*100:.1f}%)")
        
        print("\nSample Data (Latest 5 Reports with Dividend Amount):")
        print(f"{'Symbol':<15} | {'Date':<10} | {'Type':<6} | {'EPS':<8} | {'NetIncome(M)':<12} | {'DivAmount(M)':<12}")
        print("-" * 80)
        
        samples = session.exec(
            select(FinancialFundamentals)
            .where(FinancialFundamentals.dividend_amount != None)
            .order_by(FinancialFundamentals.created_at.desc())
            .limit(10)
        ).all()
        
        for s in samples:
            ni_str = f"{s.net_income_ttm/1e6:.1f}" if s.net_income_ttm else "None"
            div_str = f"{s.dividend_amount/1e6:.1f}" if s.dividend_amount is not None else "None"
            eps_str = f"{s.eps:.2f}" if s.eps is not None else "None"
            print(f"{s.symbol.split(':')[-1]:<15} | {s.as_of_date:<10} | {s.report_type[:4]:<6} | {eps_str:<8} | {ni_str:<12} | {div_str:<12}")

if __name__ == "__main__":
    verify_data()
