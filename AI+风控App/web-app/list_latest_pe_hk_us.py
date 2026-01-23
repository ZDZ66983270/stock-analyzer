import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from sqlmodel import Session, select, func
from backend.database import engine
from backend.models import MarketDataDaily

def list_latest_pe():
    print(f"{'Symbol':<20} | {'Date':<12} | {'Close':<10} | {'PE':<10} | {'PE_TTM':<10}")
    print("-" * 75)
    
    with Session(engine) as session:
        # Get all HK and US symbols
        # Efficient strategy: group by symbol, max(timestamp)
        # SQLModel doesn't support complex group by easily, proceed with raw sql or per symbol
        
        # Method 1: Get all unique symbols for HK/US from Watchlist (or just distinct form daily)
        # Let's query distinct symbols from MarketDataDaily where market in ('HK', 'US')
        # Actually better to query Watchlist
        from backend.models import Watchlist
        # Case insensitive query manually or ensure enum
        assets = session.exec(select(Watchlist)).all()
        
        hk_count = 0
        us_count = 0
        
        output_lines = []
        header = f"{'Symbol':<20} | {'Date':<12} | {'Close':<10} | {'PE':<10} | {'PE_TTM':<10}"
        print(header)
        output_lines.append(header)
        output_lines.append("-" * 75)
        
        assets = sorted(assets, key=lambda x: x.symbol)

        for asset in assets:
            # Check market via symbol prefix (more reliable)
            if asset.symbol.startswith('HK:STOCK'):
                pass
            elif asset.symbol.startswith('US:STOCK'):
                pass
            else:
                continue

            # Get latest daily
            latest = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == asset.symbol)
                .order_by(MarketDataDaily.timestamp.desc())
                .limit(1)
            ).first()
            
            if latest:
                pe_str = f"{latest.pe:.2f}" if latest.pe else "-"
                pe_ttm_str = f"{latest.pe_ttm:.2f}" if latest.pe_ttm else "-"
                close_str = f"{latest.close:.2f}"
                date_str = str(latest.timestamp).split(' ')[0]
                
                line = f"{asset.symbol:<20} | {date_str:<12} | {close_str:<10} | {pe_str:<10} | {pe_ttm_str:<10}"
                print(line)
                output_lines.append(line)
                
                if asset.symbol.startswith('HK'): hk_count += 1
                if asset.symbol.startswith('US'): us_count += 1
            else:
                print(f"{asset.symbol:<20} | {'NO DATA':<12} | {'-':<10} | {'-':<10} | {'-':<10}")
        
        print(f"\nTotal HK: {hk_count}, Total US: {us_count}")
        
        with open('outputs/pe_check.txt', 'w') as f:
            f.write('\n'.join(output_lines))

if __name__ == "__main__":
    list_latest_pe()
