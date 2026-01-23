import sys
import logging
sys.path.append('backend')
# Consistent imports via 'backend' in path
from data_fetcher import fetch_latest_data
from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily, MarketSnapshot
from symbol_utils import get_canonical_id
import time

# Configure logging to see DataFetcher output
logging.basicConfig(level=logging.INFO)


def check_stock_pe(symbol, market):
    print(f"\n{'='*60}")
    print(f"🧪 Testing {symbol} ({market}) fetch with Source PE")
    print(f"{'='*60}")
    
    # 1. Fetch Data (Force Refresh to trigger API)
    print("🚀 Fetching latest data (Force Refresh)...")
    data = fetch_latest_data(symbol, market, force_refresh=True)
    
    if not data:
        print("❌ Fetch failed (None returned)")
        return
    
    print(f"📝 Returned Data: Price={data.get('price')}, PE={data.get('pe')}, Date={data.get('date')}")
    
    if data.get('pe') is None:
         print("❌ PE is Missing in API response!")
    else:
         print(f"✅ PE found in API response: {data.get('pe')}")

    # Wait for async ETL (if any, though current implementation calls ETL synchronously in saving pipeline for simplicity of this check)
    # in data_fetcher.py: self._save_to_raw_pipeline calls ETLService.process_raw_data immediately.
    
    # 2. Check Database Storage
    canonical_id, target_market = get_canonical_id(symbol, market)
    print(f"🔎 Checking DB for {canonical_id}...")
    
    with Session(engine) as session:
        # Check Daily
        daily = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == canonical_id)
            .order_by(MarketDataDaily.timestamp.desc())
            .limit(1)
        ).first()
        
        if daily:
            print(f"📦 DB Daily Record: Date={daily.timestamp}, Close={daily.close}, PE={daily.pe}, EPS={daily.eps}")
            if daily.pe == data.get('pe'):
                 print("✅ DB Daily PE matches Source PE!")
            else:
                 print(f"⚠️ DB Daily PE ({daily.pe}) != Source PE ({data.get('pe')})")
        else:
            print("❌ No Daily record found in DB!")

        # Check Snapshot
        snap = session.exec(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == canonical_id)
        ).first()
        if snap:
             print(f"📸 Snapshot Record: Price={snap.price}, PE={snap.pe}")
        else:
             print("❌ No Snapshot record found!")

if __name__ == "__main__":
    # Test US (Using yfinance)
    check_stock_pe("AAPL", "US")
    
    # Test CN (Using AkShare)
    # check_stock_pe("600030", "CN") 
    # Note: 600030 might be closed or slow, but let's try
    check_stock_pe("CN:STOCK:600030", "CN")
