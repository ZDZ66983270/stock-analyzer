
"""
Update Snapshots with Source PE (New Strategy)
Script to fetch the latest market data using the unified DataFetcher, 
specifically to populate the MarketSnapshot table with the Source PE values.
"""
import sys
import time
import logging

sys.path.append('backend')

from database import engine
from sqlmodel import Session, select
from models import Watchlist
from data_fetcher import DataFetcher
from etl_service import ETLService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SnapshotUpdate")

def update_snapshots():
    print("=" * 60)
    print("🚀 Updating Snapshots with Source PE (Fetch Latest)")
    print("=" * 60)
    
    with Session(engine) as session:
        watchlist = session.exec(select(Watchlist)).all()
        
    total = len(watchlist)
    print(f"📋 Found {total} symbols in Watchlist.")
    
    data_fetcher = DataFetcher()
    
    for idx, item in enumerate(watchlist, 1):
        print(f"\n[{idx}/{total}] Fetching {item.symbol} ({item.market})...")
        
        try:
            # 1. Fetch Latest Data (which includes Source PE)
            # Force fetch ensures we hit the APIs (yfinance/akshare)
            raw_data = data_fetcher.fetch_latest_data(item.symbol, item.market)
            
            if not raw_data:
                print(f"⚠️  No data returned for {item.symbol}")
                continue
                
            # 2. Extract PE for verification log
            pe_val = raw_data.get('pe')
            price = raw_data.get('kline', {}).get('close')
            
            # 3. Save to Raw Pipeline (Trigger ETL)
            # This will:
            #   a. Save RawMarketData
            #   b. Run ETLService.process_raw_data -> process_daily -> update_snapshot
            #   c. Prioritize 'pe' field in process_daily
            data_fetcher._save_to_raw_pipeline(item.symbol, item.market, raw_data, pe=pe_val)
            
            print(f"✅ Fetched & Queued: Price={price}, PE={pe_val}")
            
        except Exception as e:
            print(f"❌ Error fetching {item.symbol}: {e}")
            
        # Rate limit slightly to avoid spamming APIs too hard in sequence
        time.sleep(1)

    print("\n" + "=" * 60)
    print("🎉 Snapshot Update Complete!")
    print("=" * 60)

if __name__ == "__main__":
    update_snapshots()
