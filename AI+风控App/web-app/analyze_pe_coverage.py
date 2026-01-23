from sqlmodel import Session, select, func, text
from backend.database import engine
from backend.models import MarketDataDaily, Watchlist

def analyze_coverage():
    print("="*60)
    print("📊 PE vs PE(TTM) Coverage Analysis (Stocks Only)")
    print("="*60)
    
    with Session(engine) as session:
        markets = ['CN', 'HK', 'US']
        
        print(f"{'Market':<6} | {'Total Stocks':<12} | {'Static PE %':<12} | {'TTM PE %':<12} | {'Details (Count)'}")
        print("-" * 75)
        
        for market in markets:
            # 1. Get Total Stocks count
            stmt_total = select(func.count(Watchlist.id)).where(
                Watchlist.market == market,
                Watchlist.symbol.like('%:STOCK:%')
            )
            total_stocks = session.exec(stmt_total).one()
            
            if total_stocks == 0:
                print(f"{market:<6} | {0:<12} | {'0.0%':<12} | {'0.0%':<12} | N/A")
                continue

            # 2. Get distinct stocks with valid PE (Static)
            sql_pe = text(f"""
                SELECT COUNT(DISTINCT symbol) 
                FROM marketdatadaily 
                WHERE market = '{market}' 
                  AND symbol LIKE '%:STOCK:%' 
                  AND pe IS NOT NULL
                  AND pe > 0
            """)
            pe_count = session.exec(sql_pe).one()[0]
            
            # 3. Get distinct stocks with valid PE (TTM)
            sql_pe_ttm = text(f"""
                SELECT COUNT(DISTINCT symbol) 
                FROM marketdatadaily 
                WHERE market = '{market}' 
                  AND symbol LIKE '%:STOCK:%' 
                  AND pe_ttm IS NOT NULL
                  AND pe_ttm > 0
            """)
            pe_ttm_count = session.exec(sql_pe_ttm).one()[0]
            
            # Calc Percentages
            pe_pct = (pe_count / total_stocks) * 100
            pe_ttm_pct = (pe_ttm_count / total_stocks) * 100
            
            print(f"{market:<6} | {total_stocks:<12} | {pe_pct:.1f}%{'':<7} | {pe_ttm_pct:.1f}%{'':<7} | Static: {pe_count}, TTM: {pe_ttm_count}")

if __name__ == "__main__":
    analyze_coverage()
