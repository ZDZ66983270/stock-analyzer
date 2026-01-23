
import sys
import os
from datetime import datetime
from sqlmodel import Session, select, func
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine
from models import MarketDataDaily, Watchlist, Index

def list_latest_pe():
    print(f"\n📊 最新 PE 数据概览 (Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 100)
    print(f"{'Symbol':<20} | {'Name':<15} | {'Market':<6} | {'Date':<10} | {'Close':>10} | {'PE':>10} | {'DivYield':>10}")
    print("-" * 100)

    with Session(engine) as session:
        # Get all watchlist items
        watchlist = session.exec(select(Watchlist)).all()
        indices = session.exec(select(Index)).all()
        all_assets = watchlist + indices
        
        # Sort by market and symbol
        all_assets.sort(key=lambda x: (x.market, x.symbol))

        for asset in all_assets:
            # Get latest daily record
            latest_daily = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == asset.symbol)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()

            if latest_daily:
                date_str = latest_daily.timestamp.split(' ')[0]
                pe_str = f"{latest_daily.pe:.2f}" if latest_daily.pe is not None else "N/A"
                dy_str = f"{latest_daily.dividend_yield*100:.2f}%" if latest_daily.dividend_yield is not None else "N/A"
                close_str = f"{latest_daily.close:.2f}"
                
                # Check formatting for name (truncate if too long for display)
                name_display = asset.name[:12] + "..." if len(asset.name) > 12 else asset.name
                
                print(f"{asset.symbol:<20} | {name_display:<15} | {asset.market:<6} | {date_str:<10} | {close_str:>10} | {pe_str:>10} | {dy_str:>10}")
            else:
                 print(f"{asset.symbol:<20} | {asset.name:<15} | {asset.market:<6} | {'No Data':<10} | {'-':>10} | {'-':>10} | {'-':>10}")

    print("=" * 100)

if __name__ == "__main__":
    list_latest_pe()
