"""
创建 MarketSnapshot 表并添加唯一索引
"""
import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'database.db')

print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 创建唯一索引
    print("Creating unique index on (symbol, market)...")
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_market_snapshot_symbol_market 
        ON marketsnapshot (symbol, market)
    """)
    
    conn.commit()
    print("✅ Unique index created successfully")
    
    # 验证表结构
    cursor.execute("PRAGMA table_info(marketsnapshot)")
    columns = cursor.fetchall()
    
    if columns:
        print("\n📋 MarketSnapshot table structure:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")
    else:
        print("⚠️ MarketSnapshot table not found - will be created on first app start")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\nDone!")
