#!/usr/bin/env python3
"""
清空数据表（保留schema）
"""
import sqlite3

db_path = "backend/database.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 清空表
tables_to_clear = [
    'rawmarketdata',
    'marketdatadaily', 
    'marketsnapshot',
    'watchlist'
]

for table in tables_to_clear:
    print(f"清空表: {table}")
    cursor.execute(f"DELETE FROM {table}")
    count = cursor.rowcount
    print(f"  删除了 {count} 条记录")

conn.commit()
conn.close()

print("\n✅ 数据表已清空，schema保留")
