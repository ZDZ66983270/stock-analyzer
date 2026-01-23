#!/usr/bin/env python3
"""
修复US三大指数的涨跌额和涨跌幅
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily

def fix_us_indices():
    """修复US三大指数的涨跌数据"""
    
    print("=" * 100)
    print("修复US三大指数涨跌额和涨跌幅")
    print("=" * 100)
    
    indices = ['^DJI', '^NDX', '^SPX']
    
    with Session(engine) as session:
        total_updated = 0
        
        for symbol in indices:
            print(f"\n处理 {symbol}...")
            
            # 获取该指数的所有记录，按日期排序
            records = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == symbol)
                .where(MarketDataDaily.market == 'US')
                .order_by(MarketDataDaily.date.asc())
            ).all()
            
            print(f"  总记录数: {len(records)}")
            
            updated_count = 0
            
            # 遍历记录，计算涨跌额和涨跌幅
            for i, record in enumerate(records):
                if i == 0:
                    # 第一条记录，没有前一天数据
                    continue
                
                prev_record = records[i-1]
                
                # 计算涨跌额和涨跌幅
                change = record.close - prev_record.close
                pct_change = (change / prev_record.close) * 100 if prev_record.close else 0
                
                # 更新记录
                if record.change != change or record.pct_change != pct_change:
                    record.change = change
                    record.pct_change = pct_change
                    record.prev_close = prev_record.close
                    session.add(record)
                    updated_count += 1
            
            session.commit()
            total_updated += updated_count
            print(f"  ✅ 更新了 {updated_count} 条记录")
            
            # 显示2008-08-08的数据
            record_2008 = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == symbol)
                .where(MarketDataDaily.date == '2008-08-08 16:00:00')
            ).first()
            
            if record_2008:
                print(f"  2008-08-08数据:")
                print(f"    收盘: {record_2008.close:.2f}")
                print(f"    涨跌额: {record_2008.change:.2f}")
                print(f"    涨跌幅: {record_2008.pct_change:.2f}%")
        
        print(f"\n✅ 总共更新了 {total_updated} 条记录")

if __name__ == "__main__":
    try:
        fix_us_indices()
        print("\n" + "=" * 100)
        print("✅ 完成")
        print("=" * 100)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
