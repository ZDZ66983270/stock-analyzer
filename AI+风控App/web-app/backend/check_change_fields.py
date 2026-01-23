#!/usr/bin/env python3
"""
检查MarketDataDaily和MarketSnapshot表中涨跌额和涨跌幅字段的数据完整性
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select, func
from database import engine
from models import MarketDataDaily, MarketSnapshot

def check_daily_table():
    """检查MarketDataDaily表"""
    print("=" * 80)
    print("📊 MarketDataDaily 表 - 涨跌额/涨跌幅检查")
    print("=" * 80)
    
    with Session(engine) as session:
        # 总记录数
        total = session.exec(
            select(func.count(MarketDataDaily.id))
        ).one()
        
        # 有涨跌额的记录数
        has_change = session.exec(
            select(func.count(MarketDataDaily.id))
            .where(MarketDataDaily.change.isnot(None))
        ).one()
        
        # 有涨跌幅的记录数
        has_pct_change = session.exec(
            select(func.count(MarketDataDaily.id))
            .where(MarketDataDaily.pct_change.isnot(None))
        ).one()
        
        # 涨跌额为NULL的记录数
        null_change = total - has_change
        
        # 涨跌幅为NULL的记录数
        null_pct_change = total - has_pct_change
        
        print(f"\n总记录数: {total:,}")
        print(f"\n涨跌额 (change):")
        print(f"  有值: {has_change:,} ({has_change/total*100:.1f}%)")
        print(f"  NULL: {null_change:,} ({null_change/total*100:.1f}%)")
        
        print(f"\n涨跌幅 (pct_change):")
        print(f"  有值: {has_pct_change:,} ({has_pct_change/total*100:.1f}%)")
        print(f"  NULL: {null_pct_change:,} ({null_pct_change/total*100:.1f}%)")
        
        # 按市场统计
        print("\n" + "-" * 80)
        print("按市场统计:")
        print("-" * 80)
        
        for market in ['US', 'HK', 'CN']:
            market_total = session.exec(
                select(func.count(MarketDataDaily.id))
                .where(MarketDataDaily.market == market)
            ).one()
            
            market_has_change = session.exec(
                select(func.count(MarketDataDaily.id))
                .where(MarketDataDaily.market == market)
                .where(MarketDataDaily.change.isnot(None))
            ).one()
            
            market_has_pct = session.exec(
                select(func.count(MarketDataDaily.id))
                .where(MarketDataDaily.market == market)
                .where(MarketDataDaily.pct_change.isnot(None))
            ).one()
            
            if market_total > 0:
                print(f"\n{market} 市场:")
                print(f"  总记录: {market_total:,}")
                print(f"  涨跌额有值: {market_has_change:,} ({market_has_change/market_total*100:.1f}%)")
                print(f"  涨跌幅有值: {market_has_pct:,} ({market_has_pct/market_total*100:.1f}%)")
        
        # 查看一些NULL的样本
        print("\n" + "-" * 80)
        print("涨跌额为NULL的样本记录:")
        print("-" * 80)
        
        null_samples = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.change.is_(None))
            .limit(5)
        ).all()
        
        for record in null_samples:
            print(f"  {record.symbol} ({record.market}) - {record.date}")
            print(f"    close={record.close}, prev_close={record.prev_close}")
            print(f"    change={record.change}, pct_change={record.pct_change}")

def check_snapshot_table():
    """检查MarketSnapshot表"""
    print("\n\n")
    print("=" * 80)
    print("📸 MarketSnapshot 表 - 涨跌额/涨跌幅检查")
    print("=" * 80)
    
    with Session(engine) as session:
        # 总记录数
        total = session.exec(
            select(func.count(MarketSnapshot.id))
        ).one()
        
        # 有涨跌额的记录数
        has_change = session.exec(
            select(func.count(MarketSnapshot.id))
            .where(MarketSnapshot.change.isnot(None))
        ).one()
        
        # 有涨跌幅的记录数
        has_pct_change = session.exec(
            select(func.count(MarketSnapshot.id))
            .where(MarketSnapshot.pct_change.isnot(None))
        ).one()
        
        # 涨跌额为NULL的记录数
        null_change = total - has_change
        
        # 涨跌幅为NULL的记录数
        null_pct_change = total - has_pct_change
        
        print(f"\n总记录数: {total:,}")
        print(f"\n涨跌额 (change):")
        print(f"  有值: {has_change:,} ({has_change/total*100:.1f}%)")
        print(f"  NULL: {null_change:,} ({null_change/total*100:.1f}%)")
        
        print(f"\n涨跌幅 (pct_change):")
        print(f"  有值: {has_pct_change:,} ({has_pct_change/total*100:.1f}%)")
        print(f"  NULL: {null_pct_change:,} ({null_pct_change/total*100:.1f}%)")
        
        # 详细列表
        print("\n" + "-" * 80)
        print("所有快照详情:")
        print("-" * 80)
        
        snapshots = session.exec(
            select(MarketSnapshot)
            .order_by(MarketSnapshot.market, MarketSnapshot.symbol)
        ).all()
        
        for snap in snapshots:
            status = "✅" if snap.change is not None and snap.pct_change is not None else "❌"
            print(f"{status} {snap.symbol:15} ({snap.market})")
            print(f"   price={snap.price:.2f}, prev_close={snap.prev_close}")
            print(f"   change={snap.change}, pct_change={snap.pct_change}")

if __name__ == "__main__":
    try:
        check_daily_table()
        check_snapshot_table()
        print("\n" + "=" * 80)
        print("✅ 检查完成")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
