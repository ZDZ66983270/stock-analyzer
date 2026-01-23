#!/usr/bin/env python3
"""
查询六大指数的最新日线数据
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily
from symbols_config import INDEX_LIST

def get_latest_index_data():
    """获取六大指数的最新日线数据"""
    
    print("=" * 100)
    print("六大指数最新日线数据")
    print("=" * 100)
    
    with Session(engine) as session:
        results = []
        
        for symbol in INDEX_LIST:
            # 查询该指数的最新记录
            latest = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == symbol)
                .order_by(MarketDataDaily.date.desc())
            ).first()
            
            if latest:
                results.append({
                    'symbol': latest.symbol,
                    'market': latest.market,
                    'date': latest.date,
                    'close': latest.close,
                    'change': latest.change,
                    'pct_change': latest.pct_change,
                    'prev_close': latest.prev_close,
                })
            else:
                results.append({
                    'symbol': symbol,
                    'market': 'N/A',
                    'date': 'N/A',
                    'close': None,
                    'change': None,
                    'pct_change': None,
                    'prev_close': None,
                })
        
        # 打印表格
        print(f"\n{'指数代码':<15} {'市场':<6} {'日期':<20} {'收盘价':<12} {'涨跌额':<12} {'涨跌幅':<12}")
        print("-" * 100)
        
        for r in results:
            symbol = r['symbol']
            market = r['market']
            date = r['date'] if r['date'] != 'N/A' else 'N/A'
            close = f"{r['close']:.2f}" if r['close'] is not None else 'N/A'
            change = f"{r['change']:.2f}" if r['change'] is not None else 'N/A'
            pct_change = f"{r['pct_change']:.2f}%" if r['pct_change'] is not None else 'N/A'
            
            print(f"{symbol:<15} {market:<6} {date:<20} {close:<12} {change:<12} {pct_change:<12}")
        
        print("\n" + "=" * 100)
        
        # 统计
        has_data = sum(1 for r in results if r['close'] is not None)
        has_change = sum(1 for r in results if r['change'] is not None)
        
        print(f"\n统计:")
        print(f"  总指数数: {len(results)}")
        print(f"  有数据: {has_data}")
        print(f"  有涨跌额/涨跌幅: {has_change}")
        
        if has_change < len(results):
            print(f"\n⚠️  {len(results) - has_change} 个指数缺少涨跌数据")

if __name__ == "__main__":
    try:
        get_latest_index_data()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
