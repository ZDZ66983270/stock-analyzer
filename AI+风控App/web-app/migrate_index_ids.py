#!/usr/bin/env python3
"""
修复误标记的指数 ID (Fix Mis-labeled Index IDs: STOCK -> INDEX)
针对 Index, MarketDataDaily, MarketSnapshot, RawMarketData, FinancialFundamentals 进行迁移
"""
import sys
from sqlmodel import Session, select, text

# 添加后端路径
sys.path.append('backend')
from database import engine

# 定义迁移映射: {old_symbol: new_symbol}
MIGRATION_MAP = {
    'CN:STOCK:000001': 'CN:INDEX:000001',
    'CN:STOCK:000016': 'CN:INDEX:000016',
    'CN:STOCK:000300': 'CN:INDEX:000300',
    'CN:STOCK:000905': 'CN:INDEX:000905',
    'HK:STOCK:0HSCC': 'HK:INDEX:0HSCC',
    'HK:STOCK:0HSCE': 'HK:INDEX:0HSCE',
    'US:STOCK:DJI': 'US:INDEX:DJI',
    'US:STOCK:NDX': 'US:INDEX:NDX',
    # 港股指数：移除补位 0
    'HK:INDEX:0HSCC': 'HK:INDEX:HSCC',
    'HK:INDEX:0HSCE': 'HK:INDEX:HSCE'
}

def migrate_table(session, table_name, id_col='symbol'):
    # 对保留字表名进行转义
    quoted_table = f'"{table_name}"' if table_name.lower() in ['index', 'user', 'order'] else table_name
    print(f"📦 正在处理表: {table_name}...")
    
    total_updated = 0
    total_deleted = 0
    
    for old_id, new_id in MIGRATION_MAP.items():
        # 1. 检查是否存在重复（如果更新会导致唯一约束冲突）
        # 我们直接删除那些“如果改为新ID就会变重复”的旧记录
        check_query = text(f"SELECT COUNT(*) FROM {quoted_table} WHERE {id_col} = :new_id")
        has_new = session.execute(check_query, {"new_id": new_id}).scalar() > 0
        
        if has_new:
            # 如果新ID记录已存在，则直接删除旧ID记录
            del_query = text(f"DELETE FROM {quoted_table} WHERE {id_col} = :old_id")
            res = session.execute(del_query, {"old_id": old_id})
            if res.rowcount > 0:
                print(f"   - 删除重复旧记录: {old_id} ({res.rowcount} 行)")
                total_deleted += res.rowcount
        else:
            # 如果新ID不存在，则将旧ID更新为新ID
            upd_query = text(f"UPDATE {quoted_table} SET {id_col} = :new_id WHERE {id_col} = :old_id")
            res = session.execute(upd_query, {"new_id": new_id, "old_id": old_id})
            if res.rowcount > 0:
                print(f"   - 更新 ID: {old_id} -> {new_id} ({res.rowcount} 行)")
                total_updated += res.rowcount
                
    return total_updated, total_deleted

def main():
    print("🚀 开始修正指数 ID (STOCK -> INDEX)...")
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
            # 检查表是否存在
            try:
                migrate_table(session, table, col)
            except Exception as e:
                print(f"⚠️  跳过表 {table} (可能不存在或字段不同): {str(e).splitlines()[0]}")
        
        session.commit()
    
    print("="*60)
    print("✅ 迁移完成！所有误标记的指数 ID 已修正。")

if __name__ == "__main__":
    main()
