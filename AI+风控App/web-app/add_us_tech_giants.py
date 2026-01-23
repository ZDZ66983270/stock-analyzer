
import sys
import time
import json
import yfinance as yf
from datetime import datetime
from sqlmodel import Session, select

sys.path.insert(0, 'backend')
from database import engine
from models import Watchlist, RawMarketData
from etl_service import ETLService
from advanced_metrics import update_all_metrics

# New US Stocks
NEW_US_STOCKS = {
    "AAPL": "苹果 Apple",
    "GOOG": "谷歌C Google Class C",
    "TSM": "台积电 TSMC",
    "AMZN": "亚马逊 Amazon",
    "NVDA": "英伟达 Nvidia"
}

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

def add_and_backfill():
    print("🚀 Adding US Tech Giants to Watchlist...")
    
    with Session(engine) as session:
        added_count = 0
        for symbol, name in NEW_US_STOCKS.items():
            exists = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).first()
            if not exists:
                print(f"➕ Adding {symbol} ({name})...")
                new_item = Watchlist(
                    symbol=symbol,
                    market="US",
                    name=name,
                    added_at=datetime.now()
                )
                session.add(new_item)
                added_count += 1
            else:
                print(f"ℹ️  {symbol} already in watchlist.")
        session.commit()
    
    print(f"\n✅ Added {added_count} new stocks.")
    
    print("\n🔄 Backfilling 10-Year History...")
    for symbol in NEW_US_STOCKS.keys():
        print(f"\nProcessing {symbol}...", end=" ")
        
        # 1. Get Yahoo Symbol (US symbols are same)
        yf_symbol = symbol
        print(f"[{yf_symbol}]")
        
        try:
            # 2. Fetch History
            ticker = yf.Ticker(yf_symbol)
            history = ticker.history(period="10y")
            
            if history.empty:
                print("   ⚠️ No data found.")
                continue
            
            # 3. Format Payload (Normalize columns)
            history.reset_index(inplace=True)
            history.rename(columns={
                "Date": "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            }, inplace=True)
            
            history['timestamp'] = history['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            data_list = history.to_dict(orient='records')
            
            payload = {'source': 'yfinance_history', 'data': data_list}
            
            # 4. Save & ETL
            raw_id = save_payload_to_db(symbol, "US", "yfinance", payload, period="1d")
            print(f"   💾 Saved Raw ID: {raw_id}")
            
            ETLService.process_raw_data(raw_id)
            print("   ✅ ETL Complete.")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        time.sleep(1)

    print("\n📊 Updating Advanced Metrics (PE/PB)...")
    try:
        update_all_metrics()
        print("✅ Metrics Updated")
    except Exception as e:
        print(f"⚠️ Failed: {e}")

    print("\n🎉 US Tech Giants Import Complete!")

if __name__ == "__main__":
    add_and_backfill()
