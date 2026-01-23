#!/usr/bin/env python3
"""
符号规范化数据迁移脚本
将历史数据从AkShare代码迁移到标准代码：
- 800000 → HSI
- 800700 → HSTECH

保留所有历史数据，只是统一存储为标准代码
"""
import sys
sys.path.append('backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily, MarketSnapshot, RawMarketData
from symbols_config import SYMBOL_ALIASES

def migrate_symbol_data(old_symbol: str, new_symbol: str, market: str):
    """迁移单个符号的数据"""
    with Session(engine) as session:
        print(f"\n{'='*60}")
        print(f"迁移: {old_symbol} → {new_symbol} (Market: {market})")
        print(f"{'='*60}")
        
        # 1. 迁移 MarketDataDaily
        daily_records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == old_symbol)
            .where(MarketDataDaily.market == market)
        ).all()
        
        print(f"\n[1/3] MarketDataDaily: 找到 {len(daily_records)} 条记录")
        
        if daily_records:
            # 检查目标符号是否已有记录
            existing_dates = set()
            existing_records = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == new_symbol)
                .where(MarketDataDaily.market == market)
            ).all()
            
            for rec in existing_records:
                existing_dates.add(rec.timestamp)
            
            print(f"  目标符号已有 {len(existing_records)} 条记录")
            
            # 迁移记录
            migrated = 0
            skipped = 0
            for record in daily_records:
                if record.timestamp in existing_dates:
                    # 已存在，删除旧记录
                    session.delete(record)
                    skipped += 1
                else:
                    # 不存在，更新符号
                    record.symbol = new_symbol
                    migrated += 1
            
            session.commit()
            print(f"  ✅ 迁移: {migrated} 条, 跳过重复: {skipped} 条")
        
        # 2. 迁移 MarketSnapshot
        snapshot = session.exec(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == old_symbol)
            .where(MarketSnapshot.market == market)
        ).first()
        
        print(f"\n[2/3] MarketSnapshot: ", end="")
        if snapshot:
            # 检查目标是否存在
            target_snapshot = session.exec(
                select(MarketSnapshot)
                .where(MarketSnapshot.symbol == new_symbol)
                .where(MarketSnapshot.market == market)
            ).first()
            
            if target_snapshot:
                # 目标存在，删除旧的
                session.delete(snapshot)
                session.commit()
                print(f"删除旧快照（目标已存在）")
            else:
                # 目标不存在，更新符号
                snapshot.symbol = new_symbol
                session.commit()
                print(f"✅ 迁移快照")
        else:
            print("无快照记录")
        
        # 3. 迁移 RawMarketData (可选，保留原始数据)
        raw_records = session.exec(
            select(RawMarketData)
            .where(RawMarketData.symbol == old_symbol)
            .where(RawMarketData.market == market)
        ).all()
        
        print(f"\n[3/3] RawMarketData: 找到 {len(raw_records)} 条记录")
        if raw_records:
            for record in raw_records:
                record.symbol = new_symbol
            session.commit()
            print(f"  ✅ 迁移: {len(raw_records)} 条")
        
        print(f"\n✅ {old_symbol} → {new_symbol} 迁移完成!")

def verify_migration():
    """验证迁移结果"""
    with Session(engine) as session:
        print(f"\n{'='*60}")
        print("验证迁移结果")
        print(f"{'='*60}\n")
        
        symbols_to_check = ['800000', '800700', 'HSI', 'HSTECH']
        
        for symbol in symbols_to_check:
            daily_count = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == symbol)
            ).all()
            
            snapshot = session.exec(
                select(MarketSnapshot)
                .where(MarketSnapshot.symbol == symbol)
            ).first()
            
            print(f"{symbol:12} - Daily: {len(daily_count):5} 条, " + 
                  f"Snapshot: {'✓' if snapshot else '✗'}")

def main():
    print("=" * 60)
    print("           符号规范化数据迁移")
    print("=" * 60)
    
    # 迁移HK指数
    migrate_symbol_data("800000", "HSI", "HK")
    migrate_symbol_data("800700", "HSTECH", "HK")
    
    # 验证结果
    verify_migration()
    
    print(f"\n{'='*60}")
    print("迁移完成！")
    print(f"{'='*60}")
    print("\n下一步:")
    print("1. 重启后端: 新的ETL会自动规范化符号")
    print("2. 触发数据刷新验证")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
