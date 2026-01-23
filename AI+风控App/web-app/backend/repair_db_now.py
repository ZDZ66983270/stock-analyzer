import sys
import os
sys.path.append(os.getcwd())
from sqlmodel import Session, select
from database import engine
from models import Watchlist
from data_fetcher import DataFetcher
import logging

# Configure logging to print to stdout
logging.basicConfig(level=logging.INFO)

def repair():
    print("Starting Manual DB Repair...")
    fetcher = DataFetcher()
    
    with Session(engine) as session:
        wl = session.exec(select(Watchlist)).all()
        print(f"Found {len(wl)} items in watchlist.")
        
        for item in wl:
            print(f"--- Repairing {item.symbol} ({item.market}) ---")
            try:
                # We want to force the system to re-evaluate the data.
                # Since 'fetch_latest_data' checks freshness, we might need to trick it 
                # or rely on the "Change is 0/None" check to trigger the fallback.
                
                # Let's inspect what fetch_latest_data returns
                data = fetcher.fetch_latest_data(item.symbol, item.market)
                
                if data:
                    print(f"  > Result: Price={data.get('price')}, Change={data.get('change')}, Pct={data.get('pct_change')}")
                else:
                    print("  > Result: None")
                    
            except Exception as e:
                print(f"  > Error: {e}")
                import traceback
                traceback.print_exc()

    print("Repair Complete.")

if __name__ == "__main__":
    repair()
