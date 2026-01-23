import sys
sys.path.append('backend')
from sqlmodel import Session, select, func
from backend.database import engine
from backend.models import Watchlist, FinancialFundamentals, MarketDataDaily

def check_status():
    with Session(engine) as session:
        wl_count = session.exec(select(func.count()).select_from(Watchlist)).one()
        ff_count = session.exec(select(func.count()).select_from(FinancialFundamentals)).one()
        md_count = session.exec(select(func.count()).select_from(MarketDataDaily)).one()
        
        print(f"Watchlist: {wl_count}")
        print(f"Financials: {ff_count}")
        print(f"MarketData: {md_count}")
        
        if wl_count > 0 and ff_count > 0 and md_count > 0:
            print("READY")
        else:
            print("NOT READY")

if __name__ == "__main__":
    check_status()
