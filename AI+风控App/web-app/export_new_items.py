"""
Export newly added watchlist items and their latest market snapshots to CSV.
"""

import sys
import os
import pandas as pd
from datetime import datetime
from sqlmodel import Session, select

sys.path.insert(0, 'backend')
from database import engine
from models import Watchlist, Index, MarketSnapshot

OUTPUT_DIR = "outports"
WATCHLIST_FILE = os.path.join(OUTPUT_DIR, "new_watchlist_items.csv")
SNAPSHOT_FILE = os.path.join(OUTPUT_DIR, "new_items_market_snapshot.csv")

# New items we just added
NEW_SYMBOLS = [
    "600536.SH", "00700.HK", "512800.SH", "159852.SZ", "516020.SH", 
    "159662.SZ", "159751.SZ", "513190.SH", "000300.SH", "000905.SH", 
    "000016.SH", "HSCEI", "HSCCI"
]

def export_data():
    print("🚀 Starting CSV export of newly added items...")
    
    # Ensure directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    with Session(engine) as session:
        # 1. Export Watchlist + Index items
        print("\n📋 Exporting Watchlist and Index items...")
        watchlist_data = []
        
        # Get from Watchlist
        watchlist_query = select(Watchlist).where(Watchlist.symbol.in_(NEW_SYMBOLS))
        watchlist_items = session.exec(watchlist_query).all()
        for item in watchlist_items:
            watchlist_data.append({
                'symbol': item.symbol,
                'name': item.name,
                'market': item.market,
                'type': 'stock/etf',
                'added_at': item.added_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Get from Index
        index_query = select(Index).where(Index.symbol.in_(NEW_SYMBOLS))
        index_items = session.exec(index_query).all()
        for item in index_items:
            watchlist_data.append({
                'symbol': item.symbol,
                'name': item.name,
                'market': item.market,
                'type': 'index',
                'added_at': item.added_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        if watchlist_data:
            df_watchlist = pd.DataFrame(watchlist_data)
            df_watchlist = df_watchlist.sort_values('symbol')
            df_watchlist.to_csv(WATCHLIST_FILE, index=False, encoding='utf-8-sig')
            print(f"   ✅ Exported {len(df_watchlist)} items to {WATCHLIST_FILE}")
        else:
            print("   ⚠️ No watchlist items found.")
        
        # 2. Export Market Snapshots
        print("\n📊 Exporting Market Snapshots...")
        snapshot_query = select(MarketSnapshot).where(MarketSnapshot.symbol.in_(NEW_SYMBOLS))
        snapshots = session.exec(snapshot_query).all()
        
        if snapshots:
            snapshot_data = []
            for snap in snapshots:
                snapshot_data.append({
                    'symbol': snap.symbol,
                    'market': snap.market,
                    'price': round(snap.price, 2) if snap.price else None,
                    'open': round(snap.open, 2) if snap.open else None,
                    'high': round(snap.high, 2) if snap.high else None,
                    'low': round(snap.low, 2) if snap.low else None,
                    'prev_close': round(snap.prev_close, 2) if snap.prev_close else None,
                    'change': round(snap.change, 2) if snap.change else None,
                    'pct_change': round(snap.pct_change, 3) if snap.pct_change else None,
                    'volume': snap.volume,
                    'turnover': round(snap.turnover, 2) if snap.turnover else None,
                    'pe': round(snap.pe, 2) if snap.pe else None,
                    'pb': round(snap.pb, 2) if snap.pb else None,
                    'ps': round(snap.ps, 2) if snap.ps else None,
                    'dividend_yield': round(snap.dividend_yield, 4) if snap.dividend_yield else None,
                    'market_cap': round(snap.market_cap / 100000000, 2) if snap.market_cap else None,  # Convert to 亿
                    'timestamp': snap.timestamp,
                    'data_source': snap.data_source,
                    'updated_at': snap.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            df_snapshot = pd.DataFrame(snapshot_data)
            df_snapshot = df_snapshot.sort_values('symbol')
            
            # Rename columns to Chinese
            df_snapshot.columns = [
                '代码', '市场', '最新价', '开盘', '最高', '最低', '昨收', 
                '涨跌额', '涨跌幅(%)', '成交量', '成交额', 'PE', 'PB', 'PS', 
                '股息率(%)', '总市值(亿)', '时间戳', '数据源', '更新时间'
            ]
            
            df_snapshot.to_csv(SNAPSHOT_FILE, index=False, encoding='utf-8-sig')
            print(f"   ✅ Exported {len(df_snapshot)} snapshots to {SNAPSHOT_FILE}")
        else:
            print("   ⚠️ No market snapshot data found.")
    
    print("\n" + "=" * 60)
    print("🎉 CSV Export Complete!")
    print("=" * 60)
    print(f"Files created:")
    print(f"  - {WATCHLIST_FILE}")
    print(f"  - {SNAPSHOT_FILE}")

if __name__ == "__main__":
    export_data()
