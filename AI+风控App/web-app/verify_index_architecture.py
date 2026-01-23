"""
完整验证Index表架构
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session, select
from models import Index, Watchlist, MarketDataDaily, MarketSnapshot

print("="*70)
print("Index表架构完整验证")
print("="*70)

with Session(engine) as session:
    # 1. Index表
    print("\n1️⃣  Index表（指数）")
    print("-"*70)
    indices = session.exec(select(Index)).all()
    print(f"总计: {len(indices)} 个指数\n")
    for idx in indices:
        print(f"   📊 {idx.symbol:15s} ({idx.market}) - {idx.name}")
    
    # 2. Watchlist表
    print("\n2️⃣  Watchlist表（自选股）")
    print("-"*70)
    watchlist = session.exec(select(Watchlist)).all()
    print(f"总计: {len(watchlist)} 个股票\n")
    for item in watchlist:
        print(f"   📈 {item.symbol:15s} ({item.market}) - {item.name or item.symbol}")
    
    # 3. 合并统计
    print("\n3️⃣  需要更新的总符号数")
    print("-"*70)
    total = len(indices) + len(watchlist)
    print(f"   指数: {len(indices)}")
    print(f"   股票: {len(watchlist)}")
    print(f"   总计: {total}")
    
    # 4. 数据完整性检查
    print("\n4️⃣  数据完整性检查")
    print("-"*70)
    
    all_symbols = [(idx.symbol, idx.market, '指数') for idx in indices] + \
                  [(w.symbol, w.market, '股票') for w in watchlist]
    
    for symbol, market, type_name in all_symbols:
        # 检查MarketDataDaily
        daily_count = session.exec(
            select(MarketDataDaily).where(
                MarketDataDaily.symbol == symbol,
                MarketDataDaily.market == market
            )
        ).all()
        
        # 检查MarketSnapshot
        snapshot = session.exec(
            select(MarketSnapshot).where(
                MarketSnapshot.symbol == symbol,
                MarketSnapshot.market == market
            )
        ).first()
        
        status_daily = f"{len(daily_count)}条" if daily_count else "❌无数据"
        status_snapshot = "✅" if snapshot else "❌"
        
        print(f"   {symbol:15s} ({market}) [{type_name}]")
        print(f"      历史: {status_daily:10s} | 快照: {status_snapshot}")

print("\n" + "="*70)
print("✅ 验证完成！")
print("="*70)
