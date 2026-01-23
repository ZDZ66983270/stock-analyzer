"""
从备份恢复 MarketDataDaily 表数据
只恢复 daily 表，保持 snapshot 表为空
"""
import sys
import sqlite3
sys.path.insert(0, 'backend')

# 源数据库（当前的空数据库）
current_db = 'backend/database.db'
# 备份数据库（包含完整数据 - 12月19日 22:17 的备份）
backup_db = 'backend/database_backup_20251219_221746.db'

print("🔄 开始从备份恢复 MarketDataDaily 表...")
print(f"   源备份: {backup_db}")
print(f"   目标库: {current_db}")

# 连接到两个数据库
backup_conn = sqlite3.connect(backup_db)
current_conn = sqlite3.connect(current_db)

try:
    # 1. 从备份中读取 MarketDataDaily 的所有数据
    print("\n📋 读取备份中的 MarketDataDaily 数据...")
    backup_cursor = backup_conn.cursor()
    backup_cursor.execute("SELECT COUNT(*) FROM marketdatadaily")
    count = backup_cursor.fetchone()[0]
    print(f"   备份中有 {count} 条记录")
    
    # 2. 读取所有列名
    backup_cursor.execute("PRAGMA table_info(marketdatadaily)")
    columns = [row[1] for row in backup_cursor.fetchall()]
    print(f"   列数: {len(columns)}")
    
    # 3. 读取所有数据
    backup_cursor.execute(f"SELECT * FROM marketdatadaily")
    rows = backup_cursor.fetchall()
    
    # 4. 插入到当前数据库
    print("\n💾 恢复数据到当前数据库...")
    current_cursor = current_conn.cursor()
    
    placeholders = ','.join(['?' for _ in columns])
    insert_sql = f"INSERT INTO marketdatadaily ({','.join(columns)}) VALUES ({placeholders})"
    
    current_cursor.executemany(insert_sql, rows)
    current_conn.commit()
    
    # 5. 验证
    current_cursor.execute("SELECT COUNT(*) FROM marketdatadaily")
    restored_count = current_cursor.fetchone()[0]
    print(f"   ✅ 已恢复 {restored_count} 条记录")
    
    # 6. 确认 MarketSnapshot 仍为空
    current_cursor.execute("SELECT COUNT(*) FROM marketsnapshot")
    snapshot_count = current_cursor.fetchone()[0]
    print(f"\n📸 MarketSnapshot 状态: {snapshot_count} 条记录 (应该为 0)")
    
    print("\n🎉 恢复完成！")
    print("   ✅ MarketDataDaily: 已恢复")
    print("   ✅ MarketSnapshot: 保持清空状态")
    
except Exception as e:
    print(f"\n❌ 恢复失败: {e}")
    current_conn.rollback()
    raise
finally:
    backup_conn.close()
    current_conn.close()
