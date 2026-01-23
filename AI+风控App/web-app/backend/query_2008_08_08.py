#!/usr/bin/env python3
"""
查询US市场2008年8月8日的数据
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily

def query_2008_08_08():
    """查询2008年8月8日的US市场数据"""
    
    print("=" * 100)
    print("US市场 2008年8月8日 数据")
    print("=" * 100)
    
    with Session(engine) as session:
        # 查询2008-08-08的所有US记录
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.market == 'US')
            .where(MarketDataDaily.date.like('2008-08-08%'))
        ).all()
        
        if not records:
            print("\n⚠️  未找到2008年8月8日的US市场数据")
            
            # 查找最接近的日期
            print("\n查找2008年8月附近的数据...")
            nearby = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.market == 'US')
                .where(MarketDataDaily.date.like('2008-08%'))
                .order_by(MarketDataDaily.date.asc())
                .limit(10)
            ).all()
            
            if nearby:
                print(f"\n找到 {len(nearby)} 条2008年8月的记录:")
                print(f"\n{'Symbol':<10} {'日期':<20} {'收盘价':<12} {'涨跌额':<12} {'涨跌幅':<12}")
                print("-" * 100)
                for r in nearby:
                    symbol = r.symbol
                    date = r.date
                    close = f"{r.close:.2f}" if r.close else "N/A"
                    change = f"{r.change:.2f}" if r.change is not None else "N/A"
                    pct_change = f"{r.pct_change:.2f}%" if r.pct_change is not None else "N/A"
                    print(f"{symbol:<10} {date:<20} {close:<12} {change:<12} {pct_change:<12}")
            else:
                print("\n⚠️  未找到2008年8月的任何US市场数据")
        else:
            print(f"\n找到 {len(records)} 条记录:")
            print(f"\n{'Symbol':<10} {'日期':<20} {'收盘价':<12} {'涨跌额':<12} {'涨跌幅':<12}")
            print("-" * 100)
            
            for r in records:
                symbol = r.symbol
                date = r.date
                close = f"{r.close:.2f}" if r.close else "N/A"
                change = f"{r.change:.2f}" if r.change is not None else "N/A"
                pct_change = f"{r.pct_change:.2f}%" if r.pct_change is not None else "N/A"
                
                print(f"{symbol:<10} {date:<20} {close:<12} {change:<12} {pct_change:<12}")

if __name__ == "__main__":
    try:
        query_2008_08_08()
        print("\n" + "=" * 100)
        print("✅ 查询完成")
        print("=" * 100)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
