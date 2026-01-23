"""
Fix missing historical data for CN indices using AkShare
yfinance doesn't support these indices, use AkShare instead
"""

import sys
import time
import json
import akshare as ak
import pandas as pd
from datetime import datetime
from sqlmodel import Session

sys.path.insert(0, 'backend')
from database import engine
from models import RawMarketData
from etl_service import ETLService

# Indices that need fixing - use AkShare codes
INDICES_TO_FIX = {
    "000016.SH": {"name": "上证50指数", "ak_code": "sh000016"},
    "000905.SH": {"name": "中证500指数", "ak_code": "sh000905"},
}

def save_payload_to_db(symbol, market, source, payload, period):
    """Save raw market data payload to database."""
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

def download_and_fix(symbol, info):
    """Download historical data using AkShare and process through ETL."""
    print(f"\n🔄 Fixing {symbol} ({info['name']})...")
    print(f"   Using AkShare code: {info['ak_code']}")
    
    try:
        # Fetch historical data from AkShare
        # ak.stock_zh_index_daily_em returns columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
        df = ak.stock_zh_index_daily_em(symbol=info['ak_code'])
        
        if df is None or df.empty:
            print("   ⚠️ No data returned from AkShare")
            return False
        
        print(f"   📊 Downloaded {len(df)} records")
        
        # AkShare returns: date, open, close, high, low, volume, amount
        # Rename to match our schema
        df.rename(columns={
            'date': 'timestamp',
            'amount': 'turnover'
            # open, high, low, close, volume already match
        }, inplace=True)
        
        # Select only needed columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Convert timestamp to string format (it's already date type from AkShare)
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d 15:00:00')  # CN indices close at 15:00
        
        data_list = df.to_dict(orient='records')
        
        payload = {'source': 'akshare_history', 'data': data_list}
        
        # Save to RawMarketData
        raw_id = save_payload_to_db(symbol, "CN", "akshare", payload, period="1d")
        print(f"   💾 Saved to RawMarketData (ID: {raw_id}, {len(data_list)} records)")
        
        # Process ETL
        print(f"   ⚙️ Running ETL...")
        ETLService.process_raw_data(raw_id)
        print(f"   ✅ ETL Complete")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🔧 Fixing Missing Index Historical Data (AkShare)")
    print("=" * 60)
    
    success_count = 0
    for symbol, info in INDICES_TO_FIX.items():
        if download_and_fix(symbol, info):
            success_count += 1
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"✅ Fixed {success_count}/{len(INDICES_TO_FIX)} indices")
    print("=" * 60)

if __name__ == "__main__":
    main()
