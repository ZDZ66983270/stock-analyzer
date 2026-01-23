
import akshare as ak
import pandas as pd
import sys
sys.path.append('backend')
from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily
from datetime import datetime

def fetch_and_save_hstech():
    print("Fetching HSTECH from AkShare (Sina)...")
    try:
        # 尝试使用新浪源
        df = ak.stock_hk_index_daily_sina(symbol="HSTECH")
        print(f"✅ Fetched {len(df)} records")
        print(df.head())
        print(df.tail())
        
        # Mapping: date -> timestamp, close -> close, etc.
        # columns: date, open, high, low, close, volume
        # Sina output columns vary, let's inspect
        
        if df.empty:
            print("❌ Empty dataframe")
            return

        with Session(engine) as session:
            count = 0
            for _, row in df.iterrows():
                try:
                    # date format: "2020-07-27"
                    date_str = str(row['date'])
                    timestamp_str = f"{date_str} 16:00:00"
                    
                    # Check exist
                    record = session.exec(
                        select(MarketDataDaily).where(
                            MarketDataDaily.symbol == "HSTECH",
                            MarketDataDaily.market == "HK",
                            MarketDataDaily.timestamp == timestamp_str
                        )
                    ).first()
                    
                    if not record:
                        record = MarketDataDaily(
                            symbol="HSTECH",
                            market="HK",
                            timestamp=timestamp_str,
                            open=float(row['open']),
                            high=float(row['high']),
                            low=float(row['low']),
                            close=float(row['close']),
                            volume=int(row['volume']) if 'volume' in row else 0,
                            updated_at=datetime.utcnow()
                        )
                        session.add(record)
                        count += 1
                    else:
                        # Update if needed
                        record.close = float(row['close'])
                        record.open = float(row['open'])
                        record.high = float(row['high'])
                        record.low = float(row['low'])
                        record.volume = int(row['volume']) if 'volume' in row else 0
                        session.add(record)
                        
                except Exception as e:
                    print(f"Error row {row}: {e}")
                    continue
            session.commit()
            print(f"✅ Saved/Updated {count} records for HSTECH")

    except Exception as e:
        print(f"❌ Failed to fetch AkShare HSTECH: {e}")

if __name__ == "__main__":
    fetch_and_save_hstech()
