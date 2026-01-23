#!/usr/bin/env python3
"""
修复US市场的涨跌额和涨跌幅
通过前一天的收盘价计算prev_close
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily

def fix_us_market():
    """修复US市场所有股票的涨跌数据"""
    
    print("=" * 100)
    print("修复US市场涨跌额和涨跌幅")
    print("=" * 100)
    
    with Session(engine) as session:
        # 获取所有US市场的symbol
        symbols = session.exec(
            select(MarketDataDaily.symbol)
            .where(MarketDataDaily.market == 'US')
            .distinct()
        ).all()
        
        print(f"\n找到 {len(symbols)} 个US股票/指数")
        
        total_updated = 0
        
        for symbol in symbols:
            # 获取该symbol的所有记录，按日期排序
            records = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == symbol)
                .where(MarketDataDaily.market == 'US')
                .order_by(MarketDataDaily.date.asc())
            ).all()
            
            if len(records) < 2:
                continue
            
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
                
                # 更新记录（只更新缺失的）
                if record.change is None or record.pct_change is None:
                    record.change = change
                    record.pct_change = pct_change
                    record.prev_close = prev_record.close
                    session.add(record)
                    updated_count += 1
            
            if updated_count > 0:
                total_updated += updated_count
                print(f"  {symbol}: 更新 {updated_count} 条记录")
        
        session.commit()
        print(f"\n✅ 总共更新了 {total_updated} 条记录")

if __name__ == "__main__":
    try:
        fix_us_market()
        print("\n" + "=" * 100)
        print("✅ 完成")
        print("=" * 100)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
