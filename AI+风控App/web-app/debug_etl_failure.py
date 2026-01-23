
import sys
sys.path.insert(0, 'backend')
import pandas as pd
import json
from database import engine
from sqlmodel import Session, select
from models import RawMarketData

def debug_id(raw_id):
    print(f"🔍 Debugging RawMarketData ID: {raw_id}")
    with Session(engine) as session:
        record = session.get(RawMarketData, raw_id)
        if not record:
            print("Record not found")
            return
            
        print(f"Symbol: {record.symbol}")
        print(f"Payload snippet: {record.payload[:100]}...")
        
        try:
            data_list = json.loads(record.payload)
            print(f"Data list type: {type(data_list)}")
            if len(data_list) > 0:
                print(f"First item keys: {data_list[0].keys()}")
                
            df = pd.DataFrame(data_list)
            print("DataFrame Columns:", df.columns.tolist())
            
            if 'timestamp' in df.columns:
                print("✅ 'timestamp' column exists.")
            else:
                print("❌ 'timestamp' column MISSING!")
                
        except Exception as e:
            print(f"Error parsing: {e}")

if __name__ == "__main__":
    debug_id(28)
