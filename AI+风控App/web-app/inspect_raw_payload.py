
import sys
import os
import json
from sqlmodel import Session, select
from backend.database import engine
from backend.models import RawMarketData

def inspect_raw():
    with Session(engine) as session:
        # Get latest raw for AAPL
        raw = session.exec(select(RawMarketData).where(RawMarketData.symbol == "US:STOCK:AAPL").order_by(RawMarketData.fetch_time.desc()).limit(1)).first()
        if raw:
            print(f"Fetch Time: {raw.fetch_time}")
            print(f"Payload Preview: {raw.payload[:500]}")
            try:
                data = json.loads(raw.payload)
                if isinstance(data, list):
                    print("Structure: List")
                    if data:
                        print(f"Item 0 keys: {data[0].keys()}")
                elif isinstance(data, dict):
                    print(f"Structure: Dict keys: {data.keys()}")
            except Exception as e:
                print(f"JSON Parse Error: {e}")
        else:
            print("No raw data for AAPL")

if __name__ == "__main__":
    inspect_raw()
