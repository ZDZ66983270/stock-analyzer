
import sys
import os
from sqlmodel import Session, select
from backend.database import engine, db_path
from backend.models import Watchlist, MarketSnapshot, MarketDataDaily

def debug_symbols():
    print(f"🔌 Database Path: {db_path}")
    
    with Session(engine) as session:
        target = "000300"
        print(f"\n🔍 Searching for *{target}* in all tables...")
        
        # 1. Watchlist
        w_res = session.exec(select(Watchlist).where(Watchlist.symbol.like(f'%{target}%'))).all()
        for i in w_res:
            print(f"   [Watchlist] Found: {i.symbol} (ID: {i.id})")
            
        # 2. MarketSnapshot
        s_res = session.exec(select(MarketSnapshot).where(MarketSnapshot.symbol.like(f'%{target}%'))).all()
        for i in s_res:
            print(f"   [Snapshot]  Found: {i.symbol} (ID: {i.id})")
            
        # 3. MarketDataDaily (Limit 5)
        d_res = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol.like(f'%{target}%')).limit(5)).all()
        for i in d_res:
            print(f"   [Daily]     Found: {i.symbol} (ID: {i.id})")

        print("\n🔍 Checking for exact 'CN:STOCK:000300'...")
        stock_w = session.exec(select(Watchlist).where(Watchlist.symbol == "CN:STOCK:000300")).first()
        if stock_w: print("   !!! Found in Watchlist !!!")
        
        stock_s = session.exec(select(MarketSnapshot).where(MarketSnapshot.symbol == "CN:STOCK:000300")).first()
        if stock_s: print("   !!! Found in Snapshot !!!")

if __name__ == "__main__":
    debug_symbols()
