
import sys
import time
import json
import yfinance as yf
from datetime import datetime
from sqlmodel import Session, select

sys.path.insert(0, 'backend')
from database import engine
from models import Watchlist, RawMarketData
from daily_incremental_update import get_yfinance_symbol
from etl_service import ETLService
from advanced_metrics import update_all_metrics

# New ETFs
# 159851 -> SZSE -> .SZ
# 512880 -> SSE -> .SS (Yahoo uses .SS for Shanghai usually)
NEW_ETFS = {
    "159851.SZ": "金融科技ETF Fintech ETF",
    "512880.SS": "证券ETF Securities ETF"
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
    print("🚀 Adding New ETFs to Watchlist...")
    
    with Session(engine) as session:
        added_count = 0
        for symbol, name in NEW_ETFS.items():
            exists = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).first()
            if not exists:
                print(f"➕ Adding {symbol} ({name})...")
                new_item = Watchlist(
                    symbol=symbol,
                    market="CN",
                    name=name,
                    added_at=datetime.now()
                )
                session.add(new_item)
                added_count += 1
            else:
                print(f"ℹ️  {symbol} already in watchlist.")
        session.commit()
    
    print(f"\n✅ Added {added_count} new ETFs.")
    
    print("\n🔄 Backfilling 10-Year History...")
    for symbol in NEW_ETFS.keys():
        print(f"\nProcessing {symbol}...", end=" ")
        
        # 1. Get Yahoo Symbol
        # For CN, our util might expect .SH/.SZ or might just append SS/SZ.
        # Let's pass the full symbol with suffix to be safe or rely on logic.
        # If symbol has .SZ/.SS, get_yfinance_symbol should handle or we pass directly.
        # Let's trust get_yfinance_symbol logic or manual override.
        yf_symbol = get_yfinance_symbol(symbol, "CN")
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
            raw_id = save_payload_to_db(symbol, "CN", "yfinance", payload, period="1d")
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

    print("\n🎉 Specific ETFs Import Complete!")

if __name__ == "__main__":
    add_and_backfill()
