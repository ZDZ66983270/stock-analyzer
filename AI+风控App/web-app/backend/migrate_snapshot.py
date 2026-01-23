"""
数据库迁移脚本：为MarketSnapshot添加data_source字段
"""

import sqlite3
from pathlib import Path

def migrate_marketsnapshot():
    """为MarketSnapshot表添加data_source字段"""
    
    db_path = Path(__file__).parent / "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(marketsnapshot)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'data_source' not in columns:
            print("Adding data_source column to marketsnapshot table...")
            cursor.execute("""
                ALTER TABLE marketsnapshot 
                ADD COLUMN data_source VARCHAR DEFAULT 'legacy'
            """)
            conn.commit()
            print("✅ Migration completed: data_source column added")
        else:
            print("✅ data_source column already exists, skipping migration")
        
        # 显示表结构
        cursor.execute("PRAGMA table_info(marketsnapshot)")
        print("\nCurrent marketsnapshot schema:")
        for row in cursor.fetchall():
            print(f"  {row[1]}: {row[2]}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_marketsnapshot()
