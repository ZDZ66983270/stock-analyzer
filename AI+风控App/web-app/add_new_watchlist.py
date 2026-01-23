"""
Add new stocks, ETFs, and indices to watchlist with historical data download.
"""

import sys
import time
import json
import yfinance as yf
from datetime import datetime
from sqlmodel import Session, select

sys.path.insert(0, 'backend')
from database import engine
from models import Watchlist, Index, RawMarketData
from daily_incremental_update import get_yfinance_symbol, fetch_and_save_unified
from etl_service import ETLService
from advanced_metrics import update_all_metrics

# New items to add
NEW_ITEMS = {
    # CN Stocks
    "600536.SH": {"name": "中国软件", "market": "CN", "type": "stock"},
    
    # HK Stocks
    "00700.HK": {"name": "腾讯控股", "market": "HK", "type": "stock"},
    
    # CN ETFs
    "512800.SH": {"name": "银行ETF", "market": "CN", "type": "etf"},
    "159852.SZ": {"name": "软件ETF", "market": "CN", "type": "etf"},
    "516020.SH": {"name": "化工ETF", "market": "CN", "type": "etf"},
    "159662.SZ": {"name": "交运ETF", "market": "CN", "type": "etf"},
    "159751.SZ": {"name": "港股科技ETF", "market": "CN", "type": "etf"},
    "513190.SH": {"name": "港股通金融ETF", "market": "CN", "type": "etf"},
    
    # CN Indices
    "000300.SH": {"name": "沪深300指数", "market": "CN", "type": "index"},
    "000905.SH": {"name": "中证500指数", "market": "CN", "type": "index"},
    "000016.SH": {"name": "上证50指数", "market": "CN", "type": "index"},
    
    # HK Indices
    "HSCEI": {"name": "恒生中国企业指数", "market": "HK", "type": "index"},
    "HSCCI": {"name": "恒生沪深港通指数", "market": "HK", "type": "index"},
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

def add_to_watchlist_or_index(symbol, name, market, item_type):
    """Add item to Watchlist or Index table."""
    with Session(engine) as session:
        if item_type == "index":
            # Add to Index table
            exists = session.exec(select(Index).where(Index.symbol == symbol)).first()
            if not exists:
                print(f"   ➕ Adding to Index: {symbol} ({name})")
                new_item = Index(
                    symbol=symbol,
                    market=market,
                    name=name,
                    added_at=datetime.now()
                )
                session.add(new_item)
                session.commit()
                return True
            else:
                print(f"   ℹ️  {symbol} already in Index table.")
                return False
        else:
            # Add to Watchlist table (stocks and ETFs)
            exists = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).first()
            if not exists:
                print(f"   ➕ Adding to Watchlist: {symbol} ({name})")
                new_item = Watchlist(
                    symbol=symbol,
                    market=market,
                    name=name,
                    added_at=datetime.now()
                )
                session.add(new_item)
                session.commit()
                return True
            else:
                print(f"   ℹ️  {symbol} already in Watchlist.")
                return False

def download_historical_data(symbol, market, item_type):
    """Download 10-year historical data."""
    print(f"\n📥 Downloading history for {symbol}...")
    
    # Get Yahoo Finance symbol
    yf_symbol = get_yfinance_symbol(symbol, market)
    print(f"   Using yfinance symbol: {yf_symbol}")
    
    try:
        # Fetch 10-year history
        ticker = yf.Ticker(yf_symbol)
        history = ticker.history(period="10y")
        
        if history.empty:
            print("   ⚠️ No historical data found.")
            return False
        
        # Format payload
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
        
        # Save to RawMarketData
        raw_id = save_payload_to_db(symbol, market, "yfinance", payload, period="1d")
        print(f"   💾 Saved {len(data_list)} records (Raw ID: {raw_id})")
        
        # Process ETL
        ETLService.process_raw_data(raw_id)
        print("   ✅ ETL processing complete.")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return False

def update_latest_data(symbol, market):
    """Update today's latest market data."""
    print(f"🔄 Updating latest data for {symbol}...")
    try:
        # Use the data fetcher to get latest data
        fetch_and_save_unified(symbol, market)
        print(f"   ✅ Latest data updated.")
    except Exception as e:
        print(f"   ⚠️ Failed to update latest: {e}")

def main():
    print("=" * 60)
    print("🚀 Adding New Watchlist Items")
    print("=" * 60)
    
    # Step 1: Add all items to Watchlist/Index tables
    print("\n📋 Step 1: Adding to Watchlist/Index Tables...")
    added_count = 0
    for symbol, info in NEW_ITEMS.items():
        if add_to_watchlist_or_index(symbol, info["name"], info["market"], info["type"]):
            added_count += 1
    
    print(f"\n✅ Added {added_count} new items.")
    
    # Step 2: Download historical data
    print("\n📊 Step 2: Downloading Historical Data...")
    for symbol, info in NEW_ITEMS.items():
        download_historical_data(symbol, info["market"], info["type"])
        time.sleep(0.5)  # Rate limiting
    
    # Step 3: Update today's latest data for CN and HK markets
    print("\n📈 Step 3: Updating Today's Market Data (CN/HK)...")
    for symbol, info in NEW_ITEMS.items():
        if info["market"] in ["CN", "HK"]:
            update_latest_data(symbol, info["market"])
            time.sleep(0.3)
    
    # Step 4: Update advanced metrics
    print("\n🔢 Step 4: Updating Advanced Metrics...")
    try:
        update_all_metrics()
        print("✅ Metrics updated successfully.")
    except Exception as e:
        print(f"⚠️ Metrics update failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 All Operations Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
