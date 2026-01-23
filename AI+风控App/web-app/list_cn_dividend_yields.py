import sys
sys.path.append('backend')
from backend.database import engine, Session
from backend.models import MarketDataDaily, Watchlist
from sqlmodel import select, col
from datetime import datetime

def list_cn_yields():
    with Session(engine) as session:
        # 1. Get all CN symbols from Watchlist to show names
        watchlist_items = session.exec(select(Watchlist).where(Watchlist.market == 'CN')).all()
        symbol_map = {item.symbol: item.name for item in watchlist_items}
        
        print(f"{'Symbol':<20} | {'Name':<15} | {'Date':<12} | {'Yield (%)':<10} | {'PE':<8} | {'PB':<8}")
        print("-" * 85)
        
        # 2. For each symbol, get the latest MarketDataDaily record
        # Optimization: We could use a group by query, but looping over watchlist is fine for small N.
        
        count = 0
        sorted_symbols = sorted(symbol_map.keys())
        
        for symbol in sorted_symbols:
            record = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == symbol)
                .where(MarketDataDaily.market == 'CN')
                .where(MarketDataDaily.dividend_yield != None)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()
            
            if record:
                name = symbol_map.get(symbol, "Unknown")
                # Format output
                date_str = record.timestamp.split()[0]
                dy_str = f"{record.dividend_yield:.2f}" if record.dividend_yield is not None else "-"
                pe_str = f"{record.pe:.2f}" if record.pe is not None else "-"
                pb_str = f"{record.pb:.2f}" if record.pb is not None else "-"
                
                print(f"{symbol:<20} | {name:<15} | {date_str:<12} | {dy_str:<10} | {pe_str:<8} | {pb_str:<8}")
                count += 1
            else:
                # Try to get record even without dividend_yield just to show PE/PB?
                # User asked specifically for Dividend Yields. 
                # If None, maybe just blank.
                pass
                
        print("-" * 85)
        print(f"Total: {count} records found.")

if __name__ == "__main__":
    list_cn_yields()
