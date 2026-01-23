
import sys
import os
import pandas as pd
from datetime import datetime
from sqlmodel import Session, select
sys.path.append(os.path.abspath('web-app/backend'))
from database import engine
from models import MarketDataDaily
from data_fetcher_base import DataFetcher

def force_fetch():
    symbol = "0P00014FO3"
    db_symbol = "US:UTRUST:0P00014FO3"
    market = "US"
    
    print(f"Force fetching {symbol}...")
    fetcher = DataFetcher()
    df = fetcher.fetch_us_daily_data(symbol, period='2y')
    
    if df is None or df.empty:
        print("No data fetched.")
        return

    print(f"Fetched {len(df)} rows.")
    print(f"Columns: {df.columns.tolist()}")
    
    # Map columns to standard
    col_map = {
        'Open': ['Open', 'open', '开盘'],
        'High': ['High', 'high', '最高'],
        'Low': ['Low', 'low', '最低'],
        'Close': ['Close', 'close', '收盘'],
        'Volume': ['Volume', 'volume', '成交量'],
        'Date': ['Date', 'date', '时间', 'timestamp']
    }
    
    def get_col(name):
        for candidate in col_map[name]:
            if candidate in df.columns:
                return df[candidate]
        return pd.Series([None]*len(df), index=df.index)

    # Use map
    open_s = get_col('Open')
    close_s = get_col('Close')
    
    # Fill Open with Close if missing (fixing the initial issue)
    # Note: If 'Open' column is missing entirely, get_col returns Series of None.
    # We need to assign it back to dataframe to safe access
    
    # Construct a clean DF for iteration
    clean_df = pd.DataFrame()
    clean_df['Date'] = get_col('Date')
    clean_df['Close'] = get_col('Close')
    clean_df['Open'] = get_col('Open').fillna(clean_df['Close']).fillna(0.0)
    clean_df['High'] = get_col('High').fillna(clean_df['Close']).fillna(0.0)
    clean_df['Low'] = get_col('Low').fillna(clean_df['Close']).fillna(0.0)
    clean_df['Volume'] = get_col('Volume').fillna(0)
    
    print(f"Cleaned DF Head:\n{clean_df.head()}")
    
    # Save
    with Session(engine) as session:
        count = 0
        for _, row in clean_df.iterrows():
            date_val = str(row['Date'])
            
            # Upsert logic (simplified)
            # Delete existing for this date? Or just ignore? 
            # Let's delete to be sure we overwrite old partial data if any
            # Actually, just insert.
            
            # Check exist
            exist = session.exec(select(MarketDataDaily).where(
                MarketDataDaily.symbol == db_symbol,
                MarketDataDaily.timestamp == date_val
            )).first()
            
            if exist: continue
            
            rec = MarketDataDaily(
                symbol=db_symbol,
                market=market,
                timestamp=date_val,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=int(row['Volume']),
                updated_at=datetime.now()
            )
            session.add(rec)
            count += 1
        session.commit()
        print(f"Saved {count} new records.")

if __name__ == "__main__":
    force_fetch()
