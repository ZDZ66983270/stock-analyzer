
import sys
import os
import time
from datetime import datetime
from sqlmodel import Session, select

# Add backend to path
sys.path.insert(0, 'backend')
from database import engine
from models import Watchlist

# Import fetch logic
from daily_incremental_update import fetch_and_save_unified
from advanced_metrics import update_all_metrics

# Proxy List Definitions
PROXIES = {
    # Anchors
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust",
    "DIA": "SPDR Dow Jones Industrial Average ETF Trust",
    
    # Sectors
    "XLK": "Technology Select Sector SPDR Fund",
    "XLF": "Financial Select Sector SPDR Fund",
    "XLV": "Health Care Select Sector SPDR Fund",
    "XLP": "Consumer Staples Select Sector SPDR Fund",
    "XLY": "Consumer Discretionary Select Sector SPDR Fund",
    "XLI": "Industrial Select Sector SPDR Fund",
    "XLE": "Energy Select Sector SPDR Fund",
    "XLB": "Materials Select Sector SPDR Fund",
    "XLU": "Utilities Select Sector SPDR Fund",
    "XLRE": "Real Estate Select Sector SPDR Fund",
    "XLC": "Communication Services Select Sector SPDR Fund",
    
    # Styles & Defensive
    "VUG": "Vanguard Growth ETF",
    "VTV": "Vanguard Value ETF",
    "VYM": "Vanguard High Dividend Yield ETF",
    "IWM": "iShares Russell 2000 ETF",
    "USMV": "iShares MSCI USA Min Vol Factor ETF",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "GLD": "SPDR Gold Shares"
}

def add_and_fetch_proxies():
    print("🚀 Starting Market Proxies Import...")
    
    with Session(engine) as session:
        added_count = 0
        existing_count = 0
        
        for symbol, name in PROXIES.items():
            # Check if exists
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
                existing_count += 1
                # Update name if needed? No, keep existing.
                print(f"ℹ️  {symbol} already in watchlist.")
        
        session.commit()
    
    print(f"\n📊 Import Summary: Added {added_count}, Existing {existing_count}")
    
    if added_count > 0 or existing_count > 0:
        print("\n🔄 Triggering Data Fetch for Proxies...")
        
        # We only fetch these specific symbols to save time, or we could run full update.
        # Let's fetch these specifically.
        
        success_list = []
        for symbol in PROXIES.keys():
            print(f"   Downloading {symbol}...", end=" ")
            if fetch_and_save_unified(symbol, "US"):
                print("✅")
                success_list.append(symbol)
                time.sleep(1) # Polite delay
            else:
                print("❌")
        
        if success_list:
            print("\n🔧 Triggering ETL Pipeline...")
            try:
                import run_etl
                run_etl.run_etl_pipeline()
            except Exception as e:
                print(f"⚠️ ETL Failed: {e}")
                
            print("\n📊 Updating Advanced Metrics (PE/PB)...")
            try:
                update_all_metrics()
            except Exception as e:
                print(f"⚠️ Metrics Update Failed: {e}")
                
    print("\n🎉 Market Proxies Import & Sync Complete!")

if __name__ == "__main__":
    add_and_fetch_proxies()
