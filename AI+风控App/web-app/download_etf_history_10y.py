
import sys
import json
import time
import yfinance as yf
from datetime import datetime
from sqlmodel import Session, select
import pandas as pd

# Add backend to path
sys.path.insert(0, 'backend')
from database import engine
from models import Watchlist, MarketDataDaily, RawMarketData
from etl_service import ETLService
from daily_incremental_update import get_yfinance_symbol

def save_payload_to_db(symbol, market, source, payload, period):
    with Session(engine) as session:
        raw_record = RawMarketData(
            source=source,
            symbol=symbol,
            market=market,
            period=period,
            fetch_time=datetime.now(),
            payload=json.dumps(payload),
            processed=False
        )
        session.add(raw_record)
        session.commit()
        session.refresh(raw_record)
        return raw_record.id

def download_and_process_history():
    print("🚀 Starting 10-Year History Backfill for All Watchlist Items...")
    
    with Session(engine) as session:
        # Get all watchlist items (Stocks & ETFs)
        watchlist_items = session.exec(select(Watchlist)).all()
        
        print(f"📊 Found {len(watchlist_items)} items in Watchlist.")
        
        for item in watchlist_items:
            # 从 Canonical ID 提取纯代码
            code = item.symbol.split(':')[-1] if ':' in item.symbol else item.symbol
            market = item.market
            name = item.name
            
            print(f"\n🔄 Processing {item.symbol} ({name})...")
            
            # 1. Convert symbol for Yahoo
            yf_symbol = get_yfinance_symbol(code, market)
            print(f"   🎯 Yahoo Symbol: {yf_symbol}")
            
            try:
                # 2. Fetch 10y History
                ticker = yf.Ticker(yf_symbol)
                history = ticker.history(period="10y")
                
                if history.empty:
                    print(f"   ⚠️ No data found for {item.symbol}")
                    continue
                
                print(f"   ✅ Downloaded {len(history)} rows.")
                
                # 3. Format Payload
                history.reset_index(inplace=True)
                
                # Standardize column names
                history.rename(columns={
                    "Date": "timestamp",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume"
                }, inplace=True)
                
                # Format timestamp
                history['timestamp'] = history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Convert to list of dicts (minimize size by selecting cols)
                data_list = history.to_dict(orient='records')
                
                # Wrap in dictionary (standardizing payload format)
                payload = {'source': 'yfinance_history', 'data': data_list}
                
                # 4. Save to RawMarketData
                # IMPORTANT: Use period='1d' so ETLService recognizes it as daily data and processes it.
                # The payload contains 10 years of data, but the interval is 1d.
                raw_id = save_payload_to_db(item.symbol, market, "yfinance", payload, period="1d")
                print(f"   💾 Saved Raw ID: {raw_id}")
                
                # 5. Trigger ETL
                print(f"   ⚙️ Triggering ETL...")
                try:
                    ETLService.process_raw_data(raw_id)
                    print(f"   ✅ ETL Complete.")
                except Exception as e:
                    print(f"   ❌ ETL Failed: {e}")
                    
            except Exception as e:
                print(f"   ❌ Download Failed: {e}")
                
            time.sleep(1) # Rate limit protection

    print("\n🎉 All Backfills Complete!")

if __name__ == "__main__":
    download_and_process_history()
