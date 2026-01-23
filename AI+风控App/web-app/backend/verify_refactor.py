import sys
import os

# Ensure backend dir is in path
current_dir = os.getcwd()
if current_dir.endswith("backend"):
    sys.path.append(current_dir)
else:
    sys.path.append(os.path.join(current_dir, "web-app/backend"))

from data_fetcher import DataFetcher, normalize_symbol_db
from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily, MarketDataMinute

def verify():
    fetcher = DataFetcher()
    
    # Test 1: US Stock (TSLA.OQ -> TSLA)
    print("--- Testing US Stock (TSLA.OQ) ---")
    symbol_us = "TSLA.OQ" # Front end passes this
    
    try:
        fetcher.fetch_latest_data(symbol_us, "US", force_refresh=True)
        
        with Session(fetcher.engine) as session:
            # Check Daily
            db_sym = normalize_symbol_db(symbol_us, "US")
            print(f"Normalized Symbol: {db_sym}")
            
            daily = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == db_sym).order_by(MarketDataDaily.date.desc())).first()
            if daily:
                print(f"Daily Data Found: {daily.date} | Close: {daily.close} | Change: {daily.change} | Pct: {daily.pct_change}")
            else:
                print("ERROR: No Daily Data Found for TSLA")
                
            # Check Minute
            minute = session.exec(select(MarketDataMinute).where(MarketDataMinute.symbol == db_sym).order_by(MarketDataMinute.date.desc())).first()
            if minute:
                print(f"Minute Data Found: {minute.date} | Close: {minute.close}")
            else:
                print("WARNING: No Minute Data Found for TSLA (Market might be closed or fetch failed)")

    except Exception as e:
        print(f"US Test Failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: CN Stock (600519.SH -> 600519.SH)
    print("\n--- Testing CN Stock (600519.SH) ---")
    symbol_cn = "600519.SH"
    try:
        latest = fetcher.fetch_latest_data(symbol_cn, "CN", force_refresh=True)
        print(f"Fetch Result: {latest}")
        
        with Session(fetcher.engine) as session:
            db_sym = normalize_symbol_db(symbol_cn, "CN")
            print(f"Normalized Symbol: {db_sym}")
            
            daily = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == db_sym).order_by(MarketDataDaily.date.desc())).first()
            if daily:
                 print(f"Daily Data Found: {daily.date} | Close: {daily.close}")
            else:
                 print("ERROR: No Daily Data Found for 600519.SH")
    except Exception as e:
        print(f"CN Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
