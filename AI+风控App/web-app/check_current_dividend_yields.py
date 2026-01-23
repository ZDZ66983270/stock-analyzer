
import sys
import os
from sqlmodel import Session, select, desc
from backend.database import engine
from backend.models import MarketSnapshot, StockInfo, MarketDataDaily, Watchlist
import pandas as pd

def check_dividend_yields():
    print("Fetching dividend yields from MarketSnapshot & MarketDataDaily...")
    
    with Session(engine) as session:
        # Get Watchlist for names (StockInfo might be empty)
        watchlist = session.exec(select(Watchlist)).all()
        name_map = {w.symbol: w.name for w in watchlist}
        market_map = {w.symbol: w.market for w in watchlist}
        
        # Get all snapshots
        snapshots = session.exec(select(MarketSnapshot)).all()
        
        # If snapshot is empty, fallback to Watchlist items to check if they have Daily data
        snapshot_symbols = {s.symbol for s in snapshots}
        watchlist_symbols = {w.symbol for w in watchlist}
        all_symbols = snapshot_symbols.union(watchlist_symbols)
        
        # Pre-fetch snapshots for fast lookup
        snap_dict = {s.symbol: s for s in snapshots}
        
        data = []
        for symbol in all_symbols:
            # Skip Indices if strictly requested (but keeping for now to see everything)
            # if ':INDEX:' in symbol: continue
            
            name = name_map.get(symbol, "Unknown")
            market = market_map.get(symbol, "Unknown")
            
            # 1. Try Snapshot
            dy = None
            source = "N/A"
            updated = "N/A"
            
            snap = snap_dict.get(symbol)
            if snap:
                market = snap.market # Trust snapshot market if available
                if snap.dividend_yield is not None:
                    dy = snap.dividend_yield
                    source = "Snapshot"
                    updated = snap.updated_at
            
            # 2. If missing in Snapshot, try Latest Daily
            if dy is None:
                latest_daily = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == symbol)
                    .order_by(desc(MarketDataDaily.timestamp))
                    .limit(1)
                ).first()
                
                if latest_daily:
                    if latest_daily.dividend_yield is not None:
                        dy = latest_daily.dividend_yield
                        source = "Daily (Latest)"
                        updated = latest_daily.timestamp
                    elif source == "N/A":
                        # If we found daily record but it has no yield, at least we found data
                        source = "Daily (No Yield)"
                        updated = latest_daily.timestamp
            
            # Formatting
            dy_str = f"{dy:.2f}%" if dy is not None else "MISSING"
            
            data.append({
                "Symbol": symbol,
                "Name": name,
                "Market": market,
                "Div Yield": dy_str,
                "Raw Val": dy,
                "Source": source,
                "Updated": str(updated)
            })
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            print("No data found (Snapshot & Watchlist empty).")
            return

        # Sort
        df.sort_values(by=['Market', 'Symbol'], inplace=True)
        
        # Print
        for market in sorted(df['Market'].unique()):
            print(f"\n=== {market} Market Dividend Yields ===")
            market_df = df[df['Market'] == market]
            
            print(market_df[['Symbol', 'Name', 'Div Yield', 'Source', 'Updated']].to_markdown(index=False))

if __name__ == "__main__":
    check_dividend_yields()
