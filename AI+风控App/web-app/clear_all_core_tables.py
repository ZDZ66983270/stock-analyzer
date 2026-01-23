#!/usr/bin/env python3
"""
清空数据库核心表
清空: 行情表、财报表、Watchlist表、Index表
"""
import sys
sys.path.append('backend')

from sqlmodel import Session, delete, select, func
from backend.database import engine
from backend.models import (
    MarketDataDaily, 
    MarketSnapshot, 
    RawMarketData,
    FinancialFundamentals, 
    Watchlist,
    Index
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClearTables")


def clear_all_core_tables():
    """清空所有核心表"""
    print(f"\n{'='*80}")
    print(f"🗑️  清空数据库核心表")
    print(f"{'='*80}\n")
    
    tables_to_clear = [
        (MarketDataDaily, "行情日线数据 (MarketDataDaily)"),
        (MarketSnapshot, "行情快照 (MarketSnapshot)"),
        (RawMarketData, "原始数据 (RawMarketData)"),
        (FinancialFundamentals, "财报数据 (FinancialFundamentals)"),
        (Watchlist, "观察列表 (Watchlist)"),
        (Index, "指数表 (Index)")
    ]
    
    with Session(engine) as session:
        for model, name in tables_to_clear:
            try:
                # 先统计记录数
                count_before = session.exec(select(func.count()).select_from(model)).one()
                logger.info(f"  📊 {name}: {count_before} 条记录")
                
                # 执行删除
                result = session.exec(delete(model))
                session.commit()
                
                # 验证删除
                count_after = session.exec(select(func.count()).select_from(model)).one()
                
                if count_after == 0:
                    logger.info(f"  ✅ 已清空 {name} ({count_before} → 0)")
                else:
                    logger.warning(f"  ⚠️ {name} 未完全清空 (剩余 {count_after} 条)")
                    
            except Exception as e:
                logger.error(f"  ❌ 清空 {name} 失败: {e}")
                session.rollback()
    
    # 最终验证
    print(f"\n{'='*80}")
    print("📊 清空后各表状态:")
    print(f"{'='*80}\n")
    
    with Session(engine) as session:
        all_empty = True
        for model, name in tables_to_clear:
            count = session.exec(select(func.count()).select_from(model)).one()
            status = "✅ 空" if count == 0 else f"⚠️ 剩 {count} 条"
            print(f"  {name:<40}: {status}")
            if count > 0:
                all_empty = False
    
    print(f"\n{'='*80}")
    if all_empty:
        print("✅ 所有表已成功清空!")
    else:
        print("⚠️ 部分表未完全清空,请检查")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    print("\n⚠️  警告: 此操作将清空以下表的所有数据:")
    print("  - 行情日线数据 (MarketDataDaily)")
    print("  - 行情快照 (MarketSnapshot)")
    print("  - 原始数据 (RawMarketData)")
    print("  - 财报数据 (FinancialFundamentals)")
    print("  - 观察列表 (Watchlist)")
    print("  - 指数表 (Index)")
    print("\n此操作不可恢复!")
    
    try:
        response = input("\n确认清空? 输入 'YES' 继续: ")
        if response == "YES":
            clear_all_core_tables()
        else:
            print("\n❌ 操作已取消")
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
        sys.exit(0)
