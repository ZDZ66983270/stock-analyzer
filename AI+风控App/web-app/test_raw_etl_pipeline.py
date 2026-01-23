"""
测试 RAW → ETL 数据管道
下载单个资产验证流程
"""

from download_full_history import download_full_history
from sqlmodel import Session, create_engine, select, text
from backend.models import RawMarketData, MarketDataDaily, MarketSnapshot

# 测试资产: 美股 AAPL
canonical_id = "US:STOCK:AAPL"
code = "AAPL"
market = "US"
asset_type = "STOCK"

print("=" * 80)
print("测试 RAW → ETL 数据管道")
print("=" * 80)
print(f"测试资产: {canonical_id}")
print()

# 1. 下载数据
print("Step 1: 下载数据...")
print("-" * 80)
saved = download_full_history(canonical_id, code, market, asset_type)
print(f"✅ 下载完成: {saved} 条记录")
print()

# 2. 验证数据流
print("Step 2: 验证数据流...")
print("-" * 80)

engine = create_engine('sqlite:///backend/database.db')

with Session(engine) as session:
    # 检查 RawMarketData
    raw_count = session.exec(
        text("SELECT COUNT(*) FROM rawmarketdata WHERE symbol = :symbol")
    .bindparams(symbol=canonical_id)).first()[0]
    print(f"✅ RawMarketData: {raw_count} 条记录")
    
    # 检查 processed 状态
    raw_processed = session.exec(
        text("SELECT COUNT(*) FROM rawmarketdata WHERE symbol = :symbol AND processed = 1")
        .bindparams(symbol=canonical_id)
    ).first()[0]
    print(f"   - 已处理: {raw_processed} 条")
    
    # 检查 MarketDataDaily
    daily_count = session.exec(
        text("SELECT COUNT(*) FROM marketdatadaily WHERE symbol = :symbol")
        .bindparams(symbol=canonical_id)
    ).first()[0]
    print(f"✅ MarketDataDaily: {daily_count:,} 条记录")
    
    # 检查日期范围
    if daily_count > 0:
        result = session.exec(
            text("SELECT MIN(timestamp), MAX(timestamp) FROM marketdatadaily WHERE symbol = :symbol")
            .bindparams(symbol=canonical_id)
        ).first()
        print(f"   - 日期范围: {result[0][:10]} 至 {result[1][:10]}")
    
    # 检查 MarketSnapshot
    snapshot_count = session.exec(
        text("SELECT COUNT(*) FROM marketsnapshot WHERE symbol = :symbol")
        .bindparams(symbol=canonical_id)
    ).first()[0]
    print(f"✅ MarketSnapshot: {snapshot_count} 条记录")
    
    # 检查快照详情
    if snapshot_count > 0:
        snapshot = session.exec(
            select(MarketSnapshot).where(MarketSnapshot.symbol == canonical_id)
        ).first()
        print(f"   - 最新价: {snapshot.price:.2f}")
        print(f"   - 涨跌幅: {snapshot.pct_change:+.2f}%")
        print(f"   - 成交量: {snapshot.volume:,}")

print()
print("=" * 80)
print("✅ 测试完成")
print("=" * 80)
