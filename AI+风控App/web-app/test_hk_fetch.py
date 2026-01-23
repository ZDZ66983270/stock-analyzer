"""测试HK指数数据获取和保存"""
import sys
sys.path.insert(0, 'backend')

from data_fetcher import DataFetcher
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fetcher = DataFetcher()

# 测试HK指数获取
print("\n=== Testing HSI ===")
result = fetcher.fetch_latest_data('HSI', 'HK', save_db=True)
if result:
    print(f"✅ HSI fetched:")
    print(f"  Price: {result.get('price')}")
    print(f"  Change: {result.get('change')}")
    print(f"  Pct Change: {result.get('pct_change')}%")
    print(f"  Prev Close: {result.get('prev_close')}")
    print(f"  Date: {result.get('date')}")
else:
    print("❌ Failed to fetch HSI")

print("\n=== Testing HSTECH ===")
result2 = fetcher.fetch_latest_data('HSTECH', 'HK', save_db=True)
if result2:
    print(f"✅ HSTECH fetched:")
    print(f"  Price: {result2.get('price')}")
    print(f"  Change: {result2.get('change')}")
    print(f"  Pct Change: {result2.get('pct_change')}%")
    print(f"  Prev Close: {result2.get('prev_close')}")
    print(f"  Date: {result2.get('date')}")
else:
    print("❌ Failed to fetch HSTECH")

print("\n=== Checking MarketSnapshot table ===")
from database import engine
from sqlmodel import Session, select
from models import MarketSnapshot

with Session(engine) as session:
    snapshots = session.exec(
        select(MarketSnapshot).where(MarketSnapshot.market == 'HK')
    ).all()
    
    for snap in snapshots:
        print(f"\n{snap.symbol}:")
        print(f"  Price: {snap.price}")
        print(f"  Change: {snap.change}")
        print(f"  Pct Change: {snap.pct_change}%")
        print(f"  Source: {snap.data_source}")
        print(f"  Updated: {snap.updated_at}")
