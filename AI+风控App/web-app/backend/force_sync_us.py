from sqlmodel import create_engine, Session, select
from models import Watchlist, MarketData
from data_fetcher import DataFetcher
from datetime import datetime, timedelta
import asyncio

import os
print("DB Path:", os.path.abspath("database.db"))
engine = create_engine("sqlite:///database.db")

async def force_sync_us():
    fetcher = DataFetcher()
    with Session(engine) as session:
        # Sync ALL Watchlist Items
        stmt = select(Watchlist)
        items = session.exec(stmt).all()
        
        
        # Add Indices to Sync List
        class SyncItem:
            def __init__(self, s, m): self.symbol=s; self.market=m
        
        indices = [
            SyncItem('^DJI', 'US'),
            SyncItem('^IXIC', 'US'),
            SyncItem('^GSPC', 'US')
        ]
        
        all_items = list(items) + indices
        print(f"Syncing {len(all_items)} items (Watchlist + Indices)...")
        
        for item in all_items:
            symbol = item.symbol
            market = item.market
            print(f"Syncing {symbol} ({market})...")
            
            try:
                # Call DataFetcher
                latest = await asyncio.to_thread(fetcher.fetch_latest_data, symbol, market, force_refresh=True)
                
                if latest:
                    print(f"  -> Got Data: Price={latest.get('price')}, Date={latest.get('date')}")
                    
                    # Update DB
                    stmt_md = select(MarketData).where(
                        MarketData.symbol == symbol,
                        MarketData.period == '1d'
                    ).order_by(MarketData.date.desc())
                    existing_md = session.exec(stmt_md).first()
                    
                    if existing_md:
                        existing_md.date = latest['date']
                        existing_md.close = latest['close']
                        existing_md.updated_at = datetime.now()
                        # Also update open/high/low if available
                        if latest.get('open'): existing_md.open = latest['open']
                        if latest.get('high'): existing_md.high = latest['high']
                        if latest.get('low'): existing_md.low = latest['low']
                        if latest.get('volume'): existing_md.volume = latest['volume']
                        if latest.get('dividend_yield'): existing_md.dividend_yield = latest['dividend_yield']
                        if latest.get('pe'): existing_md.pe = latest['pe']
                        
                        session.add(existing_md)
                        session.commit()
                        print(f"  -> Updated DB record for {symbol}")
                    else:
                        # Create new record
                        new_md = MarketData(
                            symbol=symbol,
                            market=market,
                            period='1d',
                            date=latest['date'],
                            close=latest['close'],
                            volume=latest.get('volume', 0),
                            open=latest.get('open', 0.0),
                            high=latest.get('high', 0.0),
                            low=latest.get('low', 0.0),
                            dividend_yield=latest.get('dividend_yield'),
                            pe=latest.get('pe'),
                            updated_at=datetime.now()
                        )
                        session.add(new_md)
                        session.commit()
                        print(f"  -> Created New DB record for {symbol}")
                    
                    # ---------------------------------------------------------
                    # Inject Yesterday's Record (using prev_close) for accurate Change%
                    # ---------------------------------------------------------
                    if latest.get('prev_close') and latest.get('date'):
                        try:
                            # 1. Parse Current Date
                            date_str = latest['date']
                            is_us = "美东" in date_str
                            clean_date = date_str.replace(" 美东", "").strip()
                            # Try parsing YYYY-MM-DD HH:mm or YYYY-MM-DD
                            try:
                                curr_dt = datetime.strptime(clean_date, "%Y-%m-%d %H:%M")
                            except:
                                try:
                                    curr_dt = datetime.strptime(clean_date, "%Y-%m-%d")
                                except:
                                    curr_dt = None
                            
                            if curr_dt:
                                # 2. Calculate "Previous" Date (Simple -1 day, or skip weekend)
                                # Improved: If Monday(0), Prev is Friday(-3). Else -1.
                                offset = 3 if curr_dt.weekday() == 0 else 1
                                prev_dt = curr_dt - timedelta(days=offset)
                                
                                # Re-format date string
                                if is_us:
                                    prev_date_str = f"{prev_dt.strftime('%Y-%m-%d')} 16:00 美东"
                                else:
                                    prev_date_str = prev_dt.strftime('%Y-%m-%d 15:00') # Default CN close
                                    if market == "HK": prev_date_str = prev_dt.strftime('%Y-%m-%d 16:00')

                                # 3. Check DB
                                stmt_prev = select(MarketData).where(
                                    MarketData.symbol == symbol,
                                    MarketData.period == '1d',
                                    MarketData.date == prev_date_str
                                )
                                existing_prev = session.exec(stmt_prev).first()
                                
                                if not existing_prev:
                                    # Create "Ghost" Previous Record
                                    ghost_md = MarketData(
                                        symbol=symbol,
                                        market=market,
                                        period='1d',
                                        date=prev_date_str,
                                        close=latest['prev_close'],
                                        price=latest['prev_close'], 
                                        open=latest['prev_close'], # Placeholder
                                        high=latest['prev_close'],
                                        low=latest['prev_close'],
                                        volume=0, # Unknown
                                        updated_at=datetime.now()
                                    )
                                    session.add(ghost_md)
                                    session.commit()
                                    print(f"  -> Injected Prev Close Record for {symbol} ({prev_date_str})")
                        except Exception as e:
                            print(f"  -> Failed to inject prev record: {e}")

                else:
                    print(f"  -> FAILED to fetch {symbol}")
            except Exception as e:
                print(f"  -> ERROR syncing {symbol}: {e}")
        
    print("Force Sync All Complete.")

if __name__ == "__main__":
    asyncio.run(force_sync_us())
