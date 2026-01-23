import json
from sqlmodel import create_engine, Session, select
from backend.models import RawMarketData
import pandas as pd
import os
import sys

# Ensure backend modules can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    # Correct DB path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'database.db'))
    engine = create_engine(f"sqlite:///{db_path}")

    print(f"Querying {db_path}...")
    
    with Session(engine) as session:
        # Get all raw data, ordered by ID desc needed? 
        # Better: Get all, then sort in python to find latest per symbol
        stmt = select(RawMarketData).order_by(RawMarketData.id.desc())
        results = session.exec(stmt).all()
        
        latest_map = {}
        for row in results:
            if row.symbol not in latest_map:
                latest_map[row.symbol] = row
                
        # Group by market
        markets = {'US': [], 'CN': [], 'HK': []}
        
        print(f"\n{'Market':<6} {'Symbol':<10} {'Price':<10} {'Change':<10} {'Pct%':<8} {'Time (Raw)':<20} {'Source'}")
        print("-" * 80)
        
        for symbol, row in latest_map.items():
            market = row.market
            if market not in markets: markets[market] = []
            
            try:
                data = json.loads(row.payload)
                price = "N/A"
                change = "N/A"
                pct = "N/A"
                time_str = "N/A"
                
                # Logic to extract price depending on structure
                # This depends on how data_fetcher saves it.
                # Usually it's a list of dicts or a dict.
                
                item = None
                if isinstance(data, list) and len(data) > 0:
                    item = data[-1] # Assume last is latest
                elif isinstance(data, dict):
                    item = data
                
                if item:
                    # Generic extraction attempts
                    price = item.get('close') or item.get('price') or item.get('last_price')
                    
                    # Formatting
                    if price: price = f"{float(price):.2f}"
                    
                    # Time
                    time_str = item.get('date') or item.get('timestamp') or item.get('time')
                    
                    # Change? Raw data often DOESNT have change, only OHLC.
                    # We might calculate it if prev_close exists
                    c_val = item.get('change')
                    p_val = item.get('pct_change')
                    
                    if c_val is not None: change = f"{float(c_val):+.2f}"
                    if p_val is not None: pct = f"{float(p_val):+.2f}%"
                    
                print(f"{market:<6} {symbol:<10} {str(price):<10} {str(change):<10} {str(pct):<8} {str(time_str):<20} {row.source}")
                
            except Exception as e:
                print(f"{market:<6} {symbol:<10} ERROR PARSING: {e}")

if __name__ == "__main__":
    main()
