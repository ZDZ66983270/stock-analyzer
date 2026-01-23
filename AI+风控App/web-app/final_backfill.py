
import sys
import os
import json
import time
import yfinance as yf
from datetime import datetime
from sqlmodel import Session

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from models import RawMarketData
from etl_service import ETLService

TARGETS = [
    {"symbol": "BAC", "market": "US"},
    {"symbol": "META", "market": "US"},
    {"symbol": "BTC", "market": "US"},
    {"symbol": "SGOV", "market": "US"}
]

def backfill():
    print("🚀 Starting final history backfill for new assets...")
    
    for target in TARGETS:
        symbol = target["symbol"]
        market = target["market"]
        print(f"🔄 Fetching 10y history for {symbol}...")
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="10y", interval="1d", auto_adjust=True)
            
            if df.empty:
                print(f"⚠️ No data found for {symbol}")
                continue
                
            df = df.reset_index()
            # Rename columns to match ETL filter
            df = df.rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Convert to ISO strings for RawMarketData payload
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            records = df.to_dict(orient='records')
            
            payload = {
                "symbol": symbol,
                "market": market,
                "source": "yfinance_backfill",
                "data": records
            }
            
            # Save to Raw
            with Session(engine) as session:
                raw_record = RawMarketData(
                    symbol=symbol,
                    market=market,
                    source="yfinance",
                    period="1d",
                    fetch_time=datetime.now(),
                    payload=json.dumps(payload),
                    processed=False
                )
                session.add(raw_record)
                session.commit()
                session.refresh(raw_record)
                raw_id = raw_record.id
            
            print(f"⚡ Raw ID {raw_id} created. Triggering ETL...")
            ETLService.process_raw_data(raw_id)
            print(f"✅ {symbol} backfill complete.")
            
        except Exception as e:
            print(f"❌ Error for {symbol}: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    backfill()
