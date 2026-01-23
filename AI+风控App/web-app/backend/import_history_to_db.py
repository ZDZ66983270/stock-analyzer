
import os
import csv
import pandas as pd
from datetime import datetime
from sqlmodel import Session, select
from database import engine
from models import MarketData

LIBRARY_DIR = os.path.join(os.path.dirname(__file__), 'market_data_library')

def parse_date(date_val):
    # Handle various date formats
    # AkShare often returns YYYY-MM-DD or datetime objects
    s = str(date_val)
    try:
        if ' ' in s: s = s.split(' ')[0]
        return s
    except:
        return s

def import_csv(file_path):
    print(f"Importing {file_path}...")
    try:
        df = pd.read_csv(file_path)
        # Determine symbol from filename: history_SYMBOL.csv
        filename = os.path.basename(file_path)
        symbol = filename.replace('history_', '').replace('.csv', '')
        
        # Determine Market
        market = 'US'
        if symbol.endswith('.HK') or symbol.isdigit(): market = 'HK'
        if symbol.endswith('.SS') or symbol.endswith('.SZ') or symbol.startswith('sh') or symbol.startswith('sz'): market = 'CN'
        # Special case for indices in our library
        if symbol in ['800000', '800700']: market = 'HK'
        if symbol in ['000001.SS']: market = 'CN'
        
        records = []
        with Session(engine) as session:
            # Check existing count to avoid duplicate huge imports
            existing_count = session.exec(select(MarketData).where(MarketData.symbol == symbol)).all()
            if len(existing_count) > 100:
                print(f"  [!] Symbol {symbol} already has {len(existing_count)} records. Skipping.")
                return

            for _, row in df.iterrows():
                # Map columns (Flexible mapping for AkShare generic outputs)
                # Common headers: date/日期, open/开盘, close/收盘, high/最高, low/最低, volume/成交量
                
                date_str = str(row.get('date') or row.get('日期') or row.get('Time') or row.get('时间'))
                date_str = parse_date(date_str)
                
                try:
                    price = float(row.get('close') or row.get('收盘') or 0)
                    if price == 0: continue
                    
                    md = MarketData(
                        symbol=symbol,
                        market=market,
                        period='1d',
                        date=date_str,
                        open=float(row.get('open') or row.get('开盘') or 0),
                        high=float(row.get('high') or row.get('最高') or 0),
                        low=float(row.get('low') or row.get('最低') or 0),
                        close=price,
                        volume=int(row.get('volume') or row.get('成交量') or 0),
                        updated_at=datetime.now()
                    )
                    session.add(md)
                except Exception as row_err:
                    pass # Skip bad rows
            
            session.commit()
            print(f"  [V] Imported {symbol} to DB.")

    except Exception as e:
        print(f"  [X] Failed {file_path}: {e}")

def main():
    if not os.path.exists(LIBRARY_DIR):
        print("Library dir not found")
        return
        
    files = [f for f in os.listdir(LIBRARY_DIR) if f.startswith('history_') and f.endswith('.csv')]
    print(f"Found {len(files)} history files.")
    
    for f in files:
        import_csv(os.path.join(LIBRARY_DIR, f))

if __name__ == "__main__":
    main()
