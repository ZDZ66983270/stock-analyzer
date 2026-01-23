
import sys
import time
from datetime import datetime
from sqlmodel import Session, select

sys.path.insert(0, 'backend')
from database import engine
from models import Watchlist
from daily_incremental_update import fetch_and_save_unified
from advanced_metrics import update_all_metrics

# HK ETFs to add
HK_ETFS = {
    "2800.HK": "盈富基金 Tracker Fund of Hong Kong",
    "3033.HK": "南方恒生科技 CSOP Hang Seng TECH Index ETF"
}

print("🚀 Adding HK ETFs to Watchlist...")

with Session(engine) as session:
    added_count = 0
    
    for symbol, name in HK_ETFS.items():
        # Check if exists
        exists = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).first()
        
        if not exists:
            print(f"➕ Adding {symbol} ({name})...")
            new_item = Watchlist(
                symbol=symbol,
                market="HK",
                name=name,
                added_at=datetime.now()
            )
            session.add(new_item)
            added_count += 1
        else:
            print(f"ℹ️  {symbol} already in watchlist.")
    
    session.commit()

print(f"\n✅ Added {added_count} new ETFs")

print("\n🔄 Downloading Historical Data...")
for symbol in HK_ETFS.keys():
    print(f"   Fetching {symbol}...", end=" ")
    if fetch_and_save_unified(symbol, "HK"):
        print("✅")
    else:
        print("❌")
    time.sleep(1)

print("\n📊 Updating Advanced Metrics...")
try:
    update_all_metrics()
    print("✅ Metrics Updated")
except Exception as e:
    print(f"⚠️ Failed: {e}")

print("\n🎉 HK ETFs Import Complete!")
