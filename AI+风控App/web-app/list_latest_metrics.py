
import sys
import os
from sqlmodel import Session, select, col
from tabulate import tabulate  # assumes tabulate is installed or I'll use simple format
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from database import engine
from models import Watchlist, MarketDataDaily

# Mock logging to avoid clutter
logging.basicConfig(level=logging.ERROR)

def list_metrics():
    with Session(engine) as session:
        # Get all stocks from Watchlist
        assets = session.exec(select(Watchlist)).all()
        
        # Filter for Stocks (exclude Index/ETF/Crypto/Fund/Trust if possible)
        # Assuming convention matches previous scripts
        stocks = []
        for a in assets:
            if any(x in a.symbol for x in [':INDEX:', ':ETF:', ':CRYPTO:', ':TRUST:', ':FUND:']):
                continue
            stocks.append(a)
            
        print(f"📉 Found {len(stocks)} Individual Stocks in Watchlist.")
        
        results = []
        for stock in stocks:
            # Get latest daily record
            rec = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == stock.symbol)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()
            
            if rec:
                pe_ttm = f"{rec.pe_ttm:.2f}" if rec.pe_ttm is not None else "-"
                pe = f"{rec.pe:.2f}" if rec.pe is not None else "-"
                ts = rec.timestamp
                close = f"{rec.close:.2f}"
            else:
                pe_ttm = "-"
                pe = "-"
                ts = "N/A"
                close = "-"
            
            results.append([stock.symbol, stock.name or "", close, pe_ttm, pe, ts])
            
        # Sort by Symbol or Market
        results.sort(key=lambda x: x[0])
        
        # Print Table
        headers = ["Symbol", "Name", "Close", "PE (TTM)", "PE (Static)", "Timestamp"]
        
        # Simple formatting without tabulate dependency if risk of missing lib, 
        # but environment usually has standard libs. 
        # I'll use a simple format function just in case.
        print(f"{'Symbol':<20} | {'Name':<15} | {'Close':>10} | {'PE (TTM)':>10} | {'PE (St)':>10} | {'Timestamp':<20}")
        print("-" * 100)
        for r in results:
            sym = r[0] if len(r[0]) < 20 else r[0][:17]+"..."
            name = (r[1] or "") if len(r[1] or "") < 15 else (r[1] or "")[:12]+"..."
            print(f"{sym:<20} | {name:<15} | {r[2]:>10} | {r[3]:>10} | {r[4]:>10} | {r[5]:<20}")

if __name__ == "__main__":
    list_metrics()
