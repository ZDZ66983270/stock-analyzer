import sys
from sqlmodel import Session, text

# 添加后端路径
sys.path.append('backend')
from database import engine

# 定义物理修复映射: { 误标记ID : 正确ID }
FIX_MAP = {
    # 上证指数 (关键)
    'CN:STOCK:000001': 'CN:INDEX:000001',
    'CN:STOCK:000300': 'CN:INDEX:000300',
    # 美股指数
    'US:STOCK:DJI': 'US:INDEX:DJI',
    'US:STOCK:NDX': 'US:INDEX:NDX',
    'US:STOCK:SPX': 'US:INDEX:SPX',
    # 港股指数
    'HK:STOCK:HSI': 'HK:INDEX:HSI',
    'HK:STOCK:0HSCE': 'HK:INDEX:0HSCE',
    'HK:STOCK:0HSCC': 'HK:INDEX:0HSCC',
    'HK:STOCK:HSTECH': 'HK:INDEX:HSTECH',
    # 债券 ETF
    'US:STOCK:TLT': 'US:ETF:TLT'
}

def execute_surgical_fix():
    print("🚀 开始数据库 ID 物理外科手术式修复与去重...")
    print("=" * 60)
    
    tables = ['"index"', 'watchlist', 'marketdatadaily', 'marketsnapshot', 'rawmarketdata', 'financialfundamentals']
    
    with Session(engine) as session:
        for old_id, new_id in FIX_MAP.items():
            print(f"🛠️ 处理映射: {old_id} -> {new_id}")
            
            for table in tables:
                # 1. 检查是否存在新 ID 记录
                check_sql = text(f"SELECT COUNT(*) FROM {table} WHERE symbol = :new_id")
                has_new = session.execute(check_sql, {"new_id": new_id}).scalar() > 0
                
                # 2. 物理操作决策
                if has_new:
                    # 如果新 ID 已经有一套数据了，我们直接物理删除旧 ID 记录（因为它是误标产生的垃圾数据）
                    del_sql = text(f"DELETE FROM {table} WHERE symbol = :old_id")
                    res = session.execute(del_sql, {"old_id": old_id})
                    if res.rowcount > 0:
                        print(f"   - [DELETED] {table}: 已删除 {res.rowcount} 条旧 ID 冗余。")
                else:
                    # 如果新 ID 还没数据，我们只需把旧 ID 改名即可
                    upd_sql = text(f"UPDATE {table} SET symbol = :new_id WHERE symbol = :old_id")
                    res = session.execute(upd_sql, {"new_id": new_id, "old_id": old_id})
                    if res.rowcount > 0:
                        print(f"   - [UPDATED] {table}: 已将 {res.rowcount} 条记录更新为正确 ID。")
            print("-" * 40)
        
        session.commit()
    print("✅ 修复与去重完成。数据已完全规范化。")

if __name__ == "__main__":
    execute_surgical_fix()
