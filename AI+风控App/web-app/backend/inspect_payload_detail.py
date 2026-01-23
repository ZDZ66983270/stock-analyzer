
import json
from sqlmodel import Session, select
from database import engine
from models import RawMarketData
import pandas as pd

def inspect_raw_payload(raw_id):
    with Session(engine) as session:
        record = session.get(RawMarketData, raw_id)
        if not record:
            print(f"Record {raw_id} not found")
            return
            
        print(f"--- ID: {record.id} ---")
        print(f"Symbol: {record.symbol}")
        print(f"Fetch Time: {record.fetch_time}")
        
        try:
            payload = json.loads(record.payload)
            data = payload
            if isinstance(payload, dict) and 'data' in payload:
                data = payload['data']
            
            df = pd.DataFrame(data)
            print("\nLast 3 Rows:")
            print(df.tail(3))
            
            # Check for today's date
            today_str = "2026-01-14"
            today_rows = df[df['timestamp'].astype(str).str.contains(today_str)]
            
            print(f"\nRows matching {today_str}:")
            if not today_rows.empty:
                print(today_rows)
                # print specific columns if they exist
                cols = ['timestamp', 'close', 'open', 'high', 'low', 'volume']
                available_cols = [c for c in cols if c in df.columns]
                print("\nDetailed Columns:")
                print(today_rows[available_cols])
            else:
                print("No rows found for today.")
                
        except Exception as e:
            print(f"Error parsing payload: {e}")

if __name__ == "__main__":
    inspect_raw_payload(162)
