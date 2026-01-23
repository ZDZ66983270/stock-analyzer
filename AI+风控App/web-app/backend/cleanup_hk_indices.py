#!/usr/bin/env python3
"""
清理重复的HK指数数据
1. 删除800000的全部数据
2. 删除800700的全部数据
3. 删除HSI的非16:00数据
4. 删除HSTECH的非16:00数据
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily, MarketSnapshot
from datetime import datetime

def cleanup_duplicate_hk_indices():
    """清理重复的HK指数数据"""
    
    print("=" * 80)
    print("清理重复的HK指数数据")
    print("=" * 80)
    
    with Session(engine) as session:
        # 1. 删除800000的全部数据
        print("\n[1/4] 删除800000的数据...")
        
        # Daily表
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '800000')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        
        daily_count = len(records)
        for record in records:
            session.delete(record)
        session.commit()
        print(f"  ✅ MarketDataDaily: 删除 {daily_count} 条")
        
        # Snapshot表
        records = session.exec(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == '800000')
            .where(MarketSnapshot.market == 'HK')
        ).all()
        
        snapshot_count = len(records)
        for record in records:
            session.delete(record)
        session.commit()
        print(f"  ✅ MarketSnapshot: 删除 {snapshot_count} 条")
        
        # 2. 删除800700的全部数据
        print("\n[2/4] 删除800700的数据...")
        
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '800700')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        
        daily_count = len(records)
        for record in records:
            session.delete(record)
        session.commit()
        print(f"  ✅ MarketDataDaily: 删除 {daily_count} 条")
        
        records = session.exec(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == '800700')
            .where(MarketSnapshot.market == 'HK')
        ).all()
        
        snapshot_count = len(records)
        for record in records:
            session.delete(record)
        session.commit()
        print(f"  ✅ MarketSnapshot: 删除 {snapshot_count} 条")
        
        # 3. 删除HSI的非16:00数据
        print("\n[3/4] 删除HSI的非收盘数据（保留16:00）...")
        
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'HSI')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        
        deleted = 0
        kept = 0
        for record in records:
            # 检查时间是否为16:00
            if record.date:
                # 处理字符串或datetime类型
                date_str = str(record.date)  # 转为字符串
                if '16:00' in date_str:
                    kept += 1
                else:
                    session.delete(record)
                    deleted += 1
        
        session.commit()
        print(f"  ✅ 删除 {deleted} 条非收盘数据")
        print(f"  ✅ 保留 {kept} 条收盘数据")
        
        # 4. 删除HSTECH的非16:00数据
        print("\n[4/4] 删除HSTECH的非收盘数据（保留16:00）...")
        
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'HSTECH')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        
        deleted = 0
        kept = 0
        for record in records:
            if record.date:
                # 处理字符串或datetime类型
                date_str = str(record.date)  # 转为字符串
                if '16:00' in date_str:
                    kept += 1
                else:
                    session.delete(record)
                    deleted += 1
        
        session.commit()
        print(f"  ✅ 删除 {deleted} 条非收盘数据")
        print(f"  ✅ 保留 {kept} 条收盘数据")
        
    print("\n" + "=" * 80)
    print("✅ 清理完成！")
    print("=" * 80)

def verify_cleanup():
    """验证清理结果"""
    
    print("\n" + "=" * 80)
    print("验证清理结果")
    print("=" * 80)
    
    with Session(engine) as session:
        # 检查800000
        count = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '800000')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        print(f"\n800000 剩余记录: {len(count)} 条（应该为0）")
        
        # 检查800700
        count = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '800700')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        print(f"800700 剩余记录: {len(count)} 条（应该为0）")
        
        # 检查HSI
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'HSI')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        
        non_closing = 0
        closing = 0
        for record in records:
            if record.date:
                date_str = str(record.date)
                if '16:00' in date_str:
                    closing += 1
                else:
                    non_closing += 1
        
        print(f"\nHSI 总记录: {len(records)} 条")
        print(f"  - 收盘数据(16:00): {closing} 条")
        print(f"  - 非收盘数据: {non_closing} 条（应该为0）")
        
        # 检查HSTECH
        records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'HSTECH')
            .where(MarketDataDaily.market == 'HK')
        ).all()
        
        non_closing = 0
        closing = 0
        for record in records:
            if record.date:
                date_str = str(record.date)
                if '16:00' in date_str:
                    closing += 1
                else:
                    non_closing += 1
        
        print(f"\nHSTECH 总记录: {len(records)} 条")
        print(f"  - 收盘数据(16:00): {closing} 条")
        print(f"  - 非收盘数据: {non_closing} 条（应该为0）")

if __name__ == "__main__":
    try:
        cleanup_duplicate_hk_indices()
        verify_cleanup()
        print("\n✅ 所有操作完成！")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
