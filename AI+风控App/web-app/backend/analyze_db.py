#!/usr/bin/env python3
"""
数据库数据分析脚本
分析MarketDataDaily和MarketSnapshot表的数据情况
"""

from sqlmodel import Session, select, func
from database import engine
from models import MarketDataDaily, MarketSnapshot
from datetime import datetime
import pandas as pd

def analyze_daily_data():
    """分析MarketDataDaily表"""
    print("=" * 80)
    print("📊 MarketDataDaily 表分析")
    print("=" * 80)
    
    with Session(engine) as session:
        # 1. 总记录数
        total_count = session.exec(
            select(func.count(MarketDataDaily.id))
        ).one()
        print(f"\n总记录数: {total_count:,}")
        
        # 2. 按symbol统计
        print("\n" + "=" * 80)
        print("📈 按股票/指数统计:")
        print("=" * 80)
        
        symbol_stats = session.exec(
            select(
                MarketDataDaily.symbol,
                MarketDataDaily.market,
                func.count(MarketDataDaily.id).label('count'),
                func.max(MarketDataDaily.timestamp).label('latest_date'),
                func.min(MarketDataDaily.timestamp).label('earliest_date')
            )
            .group_by(MarketDataDaily.symbol, MarketDataDaily.market)
            .order_by(MarketDataDaily.symbol)
        ).all()
        
        # 转换为DataFrame便于显示
        data = []
        for stat in symbol_stats:
            data.append({
                'Symbol': stat[0],
                'Market': stat[1],
                'Records': stat[2],
                'Latest': stat[3],
                'Earliest': stat[4]
            })
        
        df = pd.DataFrame(data)
        
        # 按市场分组显示
        for market in ['US', 'HK', 'CN']:
            market_df = df[df['Market'] == market]
            if not market_df.empty:
                print(f"\n{market} 市场:")
                print("-" * 80)
                for _, row in market_df.iterrows():
                    print(f"  {row['Symbol']:15} | 记录数: {row['Records']:6,} | "
                          f"最新: {row['Latest']} | 最早: {row['Earliest']}")
        
        # 3. 按市场统计
        print("\n" + "=" * 80)
        print("🌍 按市场统计:")
        print("=" * 80)
        
        market_stats = session.exec(
            select(
                MarketDataDaily.market,
                func.count(MarketDataDaily.id).label('count'),
                func.count(func.distinct(MarketDataDaily.symbol)).label('symbols')
            )
            .group_by(MarketDataDaily.market)
        ).all()
        
        for stat in market_stats:
            print(f"  {stat[0]:5} | 记录数: {stat[1]:8,} | 股票/指数数: {stat[2]:3}")

def analyze_snapshot_data():
    """分析MarketSnapshot表"""
    print("\n\n")
    print("=" * 80)
    print("📸 MarketSnapshot 表分析")
    print("=" * 80)
    
    with Session(engine) as session:
        # 1. 总记录数
        total_count = session.exec(
            select(func.count(MarketSnapshot.id))
        ).one()
        print(f"\n总记录数: {total_count:,}")
        
        # 2. 按symbol统计
        print("\n" + "=" * 80)
        print("📈 快照详情:")
        print("=" * 80)
        
        snapshots = session.exec(
            select(MarketSnapshot)
            .order_by(MarketSnapshot.market, MarketSnapshot.symbol)
        ).all()
        
        # 按市场分组
        data = {}
        for snap in snapshots:
            if snap.market not in data:
                data[snap.market] = []
            data[snap.market].append({
                'Symbol': snap.symbol,
                'Price': snap.price,
                'Change': snap.pct_change,
                'Timestamp': snap.timestamp,  # date → timestamp
                'Updated': snap.updated_at,
                'Source': snap.data_source
            })
        
        for market in ['US', 'HK', 'CN']:
            if market in data:
                print(f"\n{market} 市场:")
                print("-" * 80)
                for item in data[market]:
                    age = ""
                    if item['Updated']:
                        age_seconds = (datetime.now() - item['Updated']).total_seconds()
                        if age_seconds < 60:
                            age = f"{int(age_seconds)}秒前"
                        elif age_seconds < 3600:
                            age = f"{int(age_seconds/60)}分钟前"
                        else:
                            age = f"{int(age_seconds/3600)}小时前"
                    
                    print(f"  {item['Symbol']:15} | "
                          f"价格: {item['Price']:10.2f} | "
                          f"涨跌: {item['Change']:+6.2f}% | "
                          f"时间: {item['Timestamp']} | "
                          f"更新: {age:10} | "
                          f"来源: {item['Source']}")
        
        # 3. 按市场统计
        print("\n" + "=" * 80)
        print("🌍 按市场统计:")
        print("=" * 80)
        
        market_stats = session.exec(
            select(
                MarketSnapshot.market,
                func.count(MarketSnapshot.id).label('count')
            )
            .group_by(MarketSnapshot.market)
        ).all()
        
        for stat in market_stats:
            print(f"  {stat[0]:5} | 快照数: {stat[1]:3}")
        
        # 4. 数据新鲜度分析
        print("\n" + "=" * 80)
        print("⏰ 数据新鲜度:")
        print("=" * 80)
        
        now = datetime.now()
        fresh_count = 0
        stale_count = 0
        
        for snap in snapshots:
            if snap.updated_at:
                age_seconds = (now - snap.updated_at).total_seconds()
                if age_seconds < 3600:  # 1小时内
                    fresh_count += 1
                else:
                    stale_count += 1
        
        print(f"  新鲜数据 (<1小时): {fresh_count}")
        print(f"  过期数据 (>1小时): {stale_count}")

def main():
    """主函数"""
    print("\n")
    print("🔍 数据库数据分析")
    print(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        analyze_daily_data()
        analyze_snapshot_data()
        
        print("\n" + "=" * 80)
        print("✅ 分析完成")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n❌ 分析出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
