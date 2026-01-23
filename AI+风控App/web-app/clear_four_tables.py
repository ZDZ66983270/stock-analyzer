"""
清空四个表：Watchlist, RawMarketData, MarketSnapshot, MarketDataDaily
保留其他表（Index等）不变
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session, select
from models import Watchlist, RawMarketData, MarketSnapshot, MarketDataDaily

print("="*60)
print("清空四个表的数据")
print("="*60)
print("\n⚠️  将要清空以下表:")
print("   1. Watchlist (自选股)")
print("   2. RawMarketData (原始数据)")
print("   3. MarketSnapshot (快照数据)")
print("   4. MarketDataDaily (历史数据)")
print("\n✅ 保留以下表:")
print("   - Index (指数配置)")
print("   - 其他所有表")
print("="*60)

with Session(engine) as session:
    # 1. 清空 Watchlist
    print("\n📋 清空 Watchlist...")
    count_watchlist = session.exec(select(Watchlist)).all()
    print(f"   当前记录数: {len(count_watchlist)}")
    
    if len(count_watchlist) > 0:
        print("   以下股票将被删除:")
        for item in count_watchlist:
            print(f"      - {item.symbol} ({item.market}): {item.name or item.symbol}")
    
    session.query(Watchlist).delete()
    session.commit()
    print("   ✅ Watchlist 已清空")
    
    # 2. 清空 RawMarketData
    print("\n📦 清空 RawMarketData...")
    count_raw = session.exec(select(RawMarketData)).all()
    print(f"   当前记录数: {len(count_raw)}")
    
    session.query(RawMarketData).delete()
    session.commit()
    print("   ✅ RawMarketData 已清空")
    
    # 3. 清空 MarketSnapshot
    print("\n📸 清空 MarketSnapshot...")
    count_snapshot = session.exec(select(MarketSnapshot)).all()
    print(f"   当前记录数: {len(count_snapshot)}")
    
    session.query(MarketSnapshot).delete()
    session.commit()
    print("   ✅ MarketSnapshot 已清空")
    
    # 4. 清空 MarketDataDaily
    print("\n📊 清空 MarketDataDaily...")
    count_daily = session.exec(select(MarketDataDaily)).all()
    print(f"   当前记录数: {len(count_daily)}")
    
    session.query(MarketDataDaily).delete()
    session.commit()
    print("   ✅ MarketDataDaily 已清空")

print("\n" + "="*60)
print("🎉 清空完成！")
print("="*60)
print("\n📊 清空统计:")
print(f"   - Watchlist: {len(count_watchlist)} 条记录已删除")
print(f"   - RawMarketData: {len(count_raw)} 条记录已删除")
print(f"   - MarketSnapshot: {len(count_snapshot)} 条记录已删除")
print(f"   - MarketDataDaily: {len(count_daily)} 条记录已删除")
print("\n✅ Index表和其他表保持不变")

# 验证Index表未被影响
print("\n" + "="*60)
print("验证Index表")
print("="*60)
from models import Index
with Session(engine) as session:
    indices = session.exec(select(Index)).all()
    print(f"Index表记录数: {len(indices)} (应该是6个)")
    for idx in indices:
        print(f"   - {idx.symbol} ({idx.market}): {idx.name}")
