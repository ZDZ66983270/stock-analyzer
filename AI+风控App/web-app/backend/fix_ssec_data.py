#!/usr/bin/env python3
"""
1. 删除上证指数12-18的记录
2. 重新计算所有上证指数缺失的涨跌幅、涨跌额并更新数据表
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily

def delete_ssec_1218():
    """删除上证指数12-18的记录"""
    
    print("=" * 100)
    print("删除上证指数 2025-12-18 的记录")
    print("=" * 100)
    
    with Session(engine) as session:
        # 查找12-18的记录
        record = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '000001.SS')
            .where(MarketDataDaily.date == '2025-12-18 15:00:00')
        ).first()
        
        if record:
            print(f"\n找到记录:")
            print(f"  日期: {record.date}")
            print(f"  收盘: {record.close}")
            print(f"  涨跌额: {record.change}")
            print(f"  涨跌幅: {record.pct_change}%")
            
            session.delete(record)
            session.commit()
            print(f"\n✅ 已删除")
        else:
            print("\n⚠️  未找到 2025-12-18 的记录")

def update_ssec_all():
    """更新所有上证指数的涨跌额和涨跌幅"""
    
    print("\n\n")
    print("=" * 100)
    print("更新上证指数所有记录的涨跌额和涨跌幅")
    print("=" * 100)
    
    with Session(engine) as session:
        # 获取所有记录，按日期排序
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '000001.SS')
            .order_by(MarketDataDaily.date.asc())
        ).all()
        
        print(f"\n总记录数: {len(records)}")
        
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
        print(f"✅ 更新了 {updated_count} 条记录")
        
        # 显示最近5条记录
        print("\n最近5条记录:")
        print("-" * 100)
        print(f"{'日期':<20} {'收盘价':<15} {'涨跌额':<12} {'涨跌幅':<12}")
        print("-" * 100)
        
        for r in records[-5:]:
            date = r.date
            close = f"{r.close:.2f}"
            change = f"{r.change:.2f}" if r.change is not None else "N/A"
            pct_change = f"{r.pct_change:.2f}%" if r.pct_change is not None else "N/A"
            
            print(f"{date:<20} {close:<15} {change:<12} {pct_change:<12}")

if __name__ == "__main__":
    try:
        delete_ssec_1218()
        update_ssec_all()
        print("\n" + "=" * 100)
        print("✅ 完成")
        print("=" * 100)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
