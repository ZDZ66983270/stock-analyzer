#!/usr/bin/env python3
"""
1. 更新HK两个指数的涨跌额和涨跌幅
2. 列出CN指数最近5天的收盘价
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily

def update_hk_indices():
    """更新HK指数的涨跌额和涨跌幅"""
    
    print("=" * 100)
    print("更新HK指数涨跌额和涨跌幅")
    print("=" * 100)
    
    with Session(engine) as session:
        for symbol in ['HSI', 'HSTECH']:
            print(f"\n处理 {symbol}...")
            
            # 获取所有记录，按日期排序
            records = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == symbol)
                .order_by(MarketDataDaily.date.asc())
            ).all()
            
            print(f"  总记录数: {len(records)}")
            
            # 遍历记录，计算涨跌额和涨跌幅
            updated_count = 0
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
            print(f"  ✅ 更新了 {updated_count} 条记录")
            
            # 显示最新记录
            latest = records[-1] if records else None
            if latest:
                print(f"  最新记录 ({latest.date}):")
                print(f"    收盘: {latest.close:.2f}")
                print(f"    涨跌额: {latest.change:.2f}")
                print(f"    涨跌幅: {latest.pct_change:.2f}%")

def list_cn_index_recent():
    """列出CN指数最近5天的收盘价"""
    
    print("\n\n")
    print("=" * 100)
    print("CN指数(000001.SS)最近5天收盘价")
    print("=" * 100)
    
    with Session(engine) as session:
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '000001.SS')
            .order_by(MarketDataDaily.date.desc())
            .limit(5)
        ).all()
        
        print(f"\n{'日期':<20} {'收盘价':<15} {'涨跌额':<12} {'涨跌幅':<12}")
        print("-" * 100)
        
        for r in reversed(records):  # 反转以从旧到新显示
            date = r.date
            close = f"{r.close:.2f}"
            change = f"{r.change:.2f}" if r.change is not None else "N/A"
            pct_change = f"{r.pct_change:.2f}%" if r.pct_change is not None else "N/A"
            
            print(f"{date:<20} {close:<15} {change:<12} {pct_change:<12}")

if __name__ == "__main__":
    try:
        update_hk_indices()
        list_cn_index_recent()
        print("\n" + "=" * 100)
        print("✅ 完成")
        print("=" * 100)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
