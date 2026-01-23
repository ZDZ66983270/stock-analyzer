from sqlmodel import Session, select
from backend.database import engine
from backend.models import RawMarketData
import json

def check_raw_data():
    symbol = "CN:STOCK:601919"
    with Session(engine) as session:
        # Get latest RawMarketData for this symbol
        stmt = select(RawMarketData).where(RawMarketData.symbol == symbol).order_by(RawMarketData.fetch_time.desc()).limit(3)
        records = session.exec(stmt).all()
        
        print(f"Found {len(records)} raw records for {symbol}")
        
        for r in records:
            print(f"\nID: {r.id}, Created: {r.fetch_time}, Processed: {r.processed}")
            try:
                payload = json.loads(r.payload)
                data = payload.get('data', []) if isinstance(payload, dict) else payload
                if isinstance(data, list) and data:
                    last_item = data[-1]
                    print(f"  Last Data Point: {last_item.get('timestamp')}, Close: {last_item.get('close')}")
                else:
                    print(f"  Data is empty or invalid format: {type(data)}")
            except Exception as e:
                print(f"  Error parsing payload: {e}")

if __name__ == "__main__":
    check_raw_data()
