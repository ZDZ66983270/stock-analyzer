"""
清空指定的三个表：RawMarketData, Watchlist, MarketDataDaily
其他表（MarketSnapshot等）保持不变
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session, select
from models import RawMarketData, Watchlist, MarketDataDaily

print("🗑️  开始清空指定表...")
print("="*60)

with Session(engine) as session:
    # 1. 清空 RawMarketData
    print("\n📦 清空 RawMarketData...")
    count_raw = session.exec(select(RawMarketData)).all()
    print(f"   当前记录数: {len(count_raw)}")
    
    session.query(RawMarketData).delete()
    session.commit()
    print("   ✅ RawMarketData 已清空")
    
    # 2. 清空 Watchlist
    print("\n📋 清空 Watchlist...")
    count_watchlist = session.exec(select(Watchlist)).all()
    print(f"   当前记录数: {len(count_watchlist)}")
    
    if len(count_watchlist) > 0:
        print("   以下股票将被删除:")
        for item in count_watchlist:
            print(f"      - {item.symbol} ({item.market}): {item.name}")
    
    session.query(Watchlist).delete()
    session.commit()
    print("   ✅ Watchlist 已清空")
    
    # 3. 清空 MarketDataDaily
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
print(f"   - RawMarketData: {len(count_raw)} 条记录已删除")
print(f"   - Watchlist: {len(count_watchlist)} 条记录已删除")
print(f"   - MarketDataDaily: {len(count_daily)} 条记录已删除")
print("\n✅ 其他表（MarketSnapshot等）保持不变")
