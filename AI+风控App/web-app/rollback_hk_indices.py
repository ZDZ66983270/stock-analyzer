#!/usr/bin/env python3
"""
回滚港股指数 ID: HSCC/HSCE -> 0HSCC/0HSCE
针对 Index, Watchlist, MarketDataDaily, MarketSnapshot, RawMarketData, FinancialFundamentals 进行回滚
"""
import sys
from sqlmodel import Session, select, text

# 添加后端路径
sys.path.append('backend')
from database import engine

# 定义回滚映射: {old_symbol: new_symbol}
ROLLBACK_MAP = {
    'HK:INDEX:HSCC': 'HK:INDEX:0HSCC',
    'HK:INDEX:HSCE': 'HK:INDEX:0HSCE'
}

def migrate_table(session, table_name, id_col='symbol'):
    # 对保留字表名进行转义
    quoted_table = f'"{table_name}"' if table_name.lower() in ['index', 'user', 'order'] else table_name
    print(f"📦 正在回滚表: {table_name}...")
    
    total_updated = 0
    total_deleted = 0
    
    for old_id, new_id in ROLLBACK_MAP.items():
        # 1. 检查新 ID 是否已存在（如果存在则先删除，避免约束冲突）
        check_query = text(f"SELECT COUNT(*) FROM {quoted_table} WHERE {id_col} = :new_id")
        has_new = session.execute(check_query, {"new_id": new_id}).scalar() > 0
        
        if has_new:
            # 如果新ID记录已存在（虽然逻辑上不应该，但为了安全），则删除旧ID记录
            del_query = text(f"DELETE FROM {quoted_table} WHERE {id_col} = :old_id")
            res = session.execute(del_query, {"old_id": old_id})
            if res.rowcount > 0:
                print(f"   - 删除重复 ID 记录: {old_id}")
                total_deleted += res.rowcount
        else:
            # 如果新ID不存在，则将旧ID更新为新ID
            upd_query = text(f"UPDATE {quoted_table} SET {id_col} = :new_id WHERE {id_col} = :old_id")
            res = session.execute(upd_query, {"new_id": new_id, "old_id": old_id})
            if res.rowcount > 0:
                print(f"   - 恢复 ID: {old_id} -> {new_id} ({res.rowcount} 行)")
                total_updated += res.rowcount
                
    return total_updated, total_deleted

def main():
    print("🚀 开始回滚港股指数 ID (HSCC/HSCE -> 0HSCC/0HSCE)...")
    print("="*60)
    
    tables_to_migrate = [
        ('index', 'symbol'),
        ('watchlist', 'symbol'),
        ('marketdatadaily', 'symbol'),
        ('marketsnapshot', 'symbol'),
        ('rawmarketdata', 'symbol'),
        ('financialfundamentals', 'symbol')
    ]
    
    with Session(engine) as session:
        for table, col in tables_to_migrate:
            try:
                migrate_table(session, table, col)
            except Exception as e:
                print(f"⚠️  跳过表 {table}: {str(e).splitlines()[0]}")
        
        session.commit()
    
    print("="*60)
    print("✅ 回滚完成！港股指数已恢复为 0HSCC/0HSCE 格式。")

if __name__ == "__main__":
    main()
