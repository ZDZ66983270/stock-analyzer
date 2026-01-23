
from sqlmodel import Session, select
from backend.database import engine
from backend.models import RawMarketData
import json
import logging

logging.basicConfig(level=logging.INFO)

def inspect_payloads():
    ids = [88, 162]
    with Session(engine) as session:
        for rid in ids:
            rec = session.get(RawMarketData, rid)
            if not rec:
                print(f"Record {rid} not found")
                continue
                
            print(f"--- Record {rid} ---")
            print(f"Fetch Time: {rec.fetch_time}")
            print(f"Symbol: {rec.symbol} ({rec.market})")
            
            try:
                data = json.loads(rec.payload)
                # Handle wrapped
                if isinstance(data, dict) and 'data' in data:
                    data = data['data']
                
                if isinstance(data, list):
                    print(f"Data Points: {len(data)}")
                    if data:
                        last_item = data[-1]
                        print(f"LAST ITEM Raw Timestamp: {last_item.get('timestamp')}")
                        print(f"LAST ITEM Full: {last_item}")
                else:
                    print("Unknown payload structure")
            except Exception as e:
                print(f"Error parsing JSON: {e}")
            print("\n")

if __name__ == "__main__":
    inspect_payloads()
