
import sys
from sqlmodel import Session, select, desc
from backend.database import engine
from backend.models import MarketSnapshot, MarketDataDaily, Watchlist
import pandas as pd

def list_stock_yields():
    print("# 📊 个股股息率一览表 (Stock Dividend Yields)\n")
    
    with Session(engine) as session:
        watchlist = session.exec(select(Watchlist)).all()
        name_map = {w.symbol: w.name for w in watchlist}
        
        # Filter for STOCKS only
        stock_symbols = [
            w.symbol for w in watchlist 
            if ':STOCK:' in w.symbol
            # Double check to exclude weird ones if any
            and not ':INDEX:' in w.symbol
            and not ':ETF:' in w.symbol
            and not ':CRYPTO:' in w.symbol
        ]
        
        # Pre-fetch snapshot
        snapshots = session.exec(select(MarketSnapshot).where(MarketSnapshot.symbol.in_(stock_symbols))).all()
        snap_dict = {s.symbol: s for s in snapshots}
        
        data = []
        for symbol in sorted(stock_symbols):
            name = name_map.get(symbol, "Unknown")
            market = symbol.split(':')[0]
            
            dy = None
            date_str = ""
            
            # 1. Snapshot
            snap = snap_dict.get(symbol)
            if snap and snap.dividend_yield is not None:
                dy = snap.dividend_yield
                date_str = str(snap.updated_at)[:10]
            else:
                # 2. Latest Daily
                daily = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == symbol)
                    .order_by(desc(MarketDataDaily.timestamp))
                    .limit(1)
                ).first()
                if daily and daily.dividend_yield is not None:
                    dy = daily.dividend_yield
                    date_str = str(daily.timestamp)[:10]
            
            if dy is not None:
                dy_str = f"{dy:.2f}%"
            else:
                dy_str = "-"
                
            data.append({
                "Market": market,
                "Symbol": symbol,
                "Name": name,
                "Div Yield": dy_str,
                "Date": date_str
            })
            
        df = pd.DataFrame(data)
        if df.empty:
            print("No stock data found.")
            return

        # Group by Market and print
        for market in sorted(df['Market'].unique()):
            print(f"## {market} Market")
            m_df = df[df['Market'] == market]
            print(m_df.to_markdown(index=False))
            print("\n")

if __name__ == "__main__":
    list_stock_yields()
