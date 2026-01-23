import sys
import logging
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist, MarketDataDaily

# Disable logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

def list_stocks_only():
    print(f"\n{'='*95}")
    print(f"📊 个股最新行情与估值 (Stocks Only)")
    print(f"{'='*95}")
    print(f"{'Symbol':<18} | {'Name':<10} | {'Market':<6} | {'Date':<10} | {'Close':<8} | {'PE (TTM)':<8} | {'EPS':<8} | {'Updated At'}")
    print("-" * 95)

    with Session(engine) as session:
        # Get all stocks (filter by symbol convention)
        watchlist_items = session.exec(select(Watchlist).order_by(Watchlist.market, Watchlist.symbol)).all()
        
        count = 0
        for item in watchlist_items:
            # Simple heuristic for Stocks: contains 'STOCK' or is purely numeric (though canonical ids usually have type)
            if ':STOCK:' not in item.symbol:
                continue
                
            latest = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == item.symbol)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()
            
            if latest:
                ts_str = latest.timestamp[:10] if isinstance(latest.timestamp, str) else latest.timestamp.strftime('%Y-%m-%d')
                pe_str = f"{latest.pe:.2f}" if latest.pe else "-"
                eps_str = f"{latest.eps:.2f}" if latest.eps else "-"
                close_str = f"{latest.close:.2f}"
                updated_str = str(latest.updated_at)[11:19] if latest.updated_at else ""
                
                print(f"{item.symbol:<18} | {item.name:<10} | {item.market:<6} | {ts_str:<10} | {close_str:<8} | {pe_str:<8} | {eps_str:<8} | {updated_str}")
                count += 1
            else:
                print(f"{item.symbol:<18} | {item.name:<10} | {item.market:<6} | {'No Data':<10} | {'-':<8} | {'-':<8} | {'-':<8} |")

    print("-" * 95)
    print(f"Total Stocks: {count}")
    print(f"{'='*95}\n")

if __name__ == "__main__":
    list_stocks_only()
