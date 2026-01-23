
import sys
import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from models import RawMarketData, MarketDataDaily, DividendFact, SplitFact
from etl_service import ETLService
from sqlmodel import Session, select
from symbol_utils import get_canonical_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_CASES = [
    # US
    {"symbol": "AAPL", "market": "US", "name": "Apple", "type": "dividend"},
    {"symbol": "NVDA", "market": "US", "name": "Nvidia", "type": "split"},
    # HK
    {"symbol": "0700.HK", "market": "HK", "name": "Tencent", "type": "dividend"},
    {"symbol": "0005.HK", "market": "HK", "name": "HSBC", "type": "dividend"},
    # CN
    {"symbol": "600309.SS", "market": "CN", "name": "Wanhua", "type": "dividend"},
    {"symbol": "600030.SS", "market": "CN", "name": "CITIC", "type": "dividend"},
]

def fetch_and_process(symbol, market):
    print(f"\n{'='*50}")
    print(f"Testing {symbol} ({market})")
    print(f"{'='*50}")

    # 1. Fetch from yfinance (max history to catch events)
    # Using auto_adjust=False to get raw data + events
    print("📥 Fetching raw data (auto_adjust=False)...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="5y", auto_adjust=False) # 5 years is enough for recent verification

    if df.empty:
        print("❌ No data fetched")
        return

    # 2. Check columns
    print(f"📊 Columns: {df.columns.tolist()}")
    if 'Dividends' in df.columns:
        div_count = df[df['Dividends'] > 0].shape[0]
        print(f"💰 Found {div_count} dividend events in raw dataframe")
    
    if 'Stock Splits' in df.columns:
        split_count = df[df['Stock Splits'] > 0].shape[0]
        print(f"🔪 Found {split_count} split events in raw dataframe")

    # 3. Simulate Data Fetcher processing
    records = df.reset_index().to_dict(orient='records')
    # Renaming happens in data_fetcher usually, but here we simulate payload creation
    # We need to mimick what data_fetcher does: rename keys
    clean_records = []
    for r in records:
        new_r = {}
        # Date handling
        for k, v in r.items():
            if k in ['Date', 'Datetime']:
                new_r['timestamp'] = v.strftime('%Y-%m-%d')
            elif k == 'Open': new_r['open'] = v
            elif k == 'High': new_r['high'] = v
            elif k == 'Low': new_r['low'] = v
            elif k == 'Close': new_r['close'] = v
            elif k == 'Volume': new_r['volume'] = v
            elif k == 'Dividends': new_r['dividends'] = v
            elif k == 'Stock Splits': new_r['stock_splits'] = v
        clean_records.append(new_r)

    # 4. Save to RawMarketData (Test Mode)
    import json
    payload = json.dumps(clean_records)
    
    with Session(engine) as session:
        raw = RawMarketData(
            symbol=symbol,
            market=market,
            source="test_script",
            period="5y",
            fetch_time=datetime.now(),
            payload=payload,
            processed=False
        )
        session.add(raw)
        session.commit()
        session.refresh(raw)
        raw_id = raw.id
        print(f"💾 Saved RawMarketData ID: {raw_id}")

    # 5. Run ETL
    print("⚙️ Running ETL...")
    ETLService.process_raw_data(raw_id)

    # 6. Verify Results
    canonical_id, _ = get_canonical_id(symbol, market)
    with Session(engine) as session:
        # Check Dividends
        divs = session.exec(select(DividendFact).where(DividendFact.asset_id == canonical_id)).all()
        print(f"✅ DB Dividend Count: {len(divs)}")
        if divs:
            print(f"   Last 3: {[f'{d.ex_date}: {d.cash_dividend}' for d in divs[:3]]}")

        # Check Splits
        splits = session.exec(select(SplitFact).where(SplitFact.asset_id == canonical_id)).all()
        print(f"✅ DB Split Count: {len(splits)}")
        if splits:
            print(f"   Events: {[f'{s.effective_date}: {s.split_factor}' for s in splits]}")

def main():
    print("🚀 Starting Corporate Actions Extraction Test")
    
    for case in TEST_CASES:
        try:
            fetch_and_process(case['symbol'], case['market'])
        except Exception as e:
            print(f"❌ Error testing {case['symbol']}: {e}")

if __name__ == "__main__":
    main()
