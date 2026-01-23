#!/usr/bin/env python3
"""
数据库Schema迁移：date → timestamp
将所有表的date字段重命名为timestamp

影响的表：
1. MarketDataDaily
2. MarketDataMinute
3. MarketSnapshot
"""
import sys
import shutil
from datetime import datetime
sys.path.append('backend')

from database import engine
from sqlmodel import Session, text

def backup_database():
    """备份数据库"""
    db_path = "backend/database.db"
    backup_path = f"backend/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    print(f"\n[1/5] 备份数据库...")
    shutil.copy2(db_path, backup_path)
    print(f"  ✅ 备份完成: {backup_path}")
    return backup_path

def migrate_table(session: Session, table_name: str):
    """迁移单个表的date字段为timestamp"""
    print(f"\n[迁移] {table_name}...")
    
    try:
        # SQLite不支持直接RENAME COLUMN，需要重建表
        # 1. 创建新表
        if table_name == "marketdatadaily":
            create_sql = """
            CREATE TABLE marketdatadaily_new (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                turnover REAL,
                change REAL,
                pct_change REAL,
                prev_close REAL,
                pe REAL,
                pb REAL,
                ps REAL,
                dividend_yield REAL,
                eps REAL,
                market_cap REAL,
                updated_at TEXT,
                CONSTRAINT uq_symbol_market_timestamp UNIQUE (symbol, market, timestamp)
            )
            """
        elif table_name == "marketdataminute":
            create_sql = """
            CREATE TABLE marketdataminute_new (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                period TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                change REAL,
                pct_change REAL,
                updated_at TEXT,
                CONSTRAINT uq_minute_symbol_period_timestamp UNIQUE (symbol, period, timestamp)
            )
            """
        elif table_name == "marketsnapshot":
            create_sql = """
            CREATE TABLE marketsnapshot_new (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                price REAL NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                prev_close REAL,
                change REAL,
                pct_change REAL,
                volume INTEGER,
                turnover REAL,
                pe REAL,
                pb REAL,
                ps REAL,
                dividend_yield REAL,
                market_cap REAL,
                timestamp TEXT,
                data_source TEXT,
                fetch_time TEXT,
                updated_at TEXT,
                CONSTRAINT uq_snapshot_symbol_market UNIQUE (symbol, market)
            )
            """
        else:
            print(f"  ⚠️  未知表: {table_name}")
            return False
        
        session.exec(text(create_sql))
        print(f"  ✅ 创建新表 {table_name}_new")
        
        # 2. 复制数据（date → timestamp）
        copy_sql = f"""
        INSERT INTO {table_name}_new
        SELECT 
            id, symbol, market,
            {'timestamp' if table_name != 'marketsnapshot' else 'period, timestamp'
             if table_name == 'marketdataminute' else ''},
            date as timestamp,  -- 重命名
            {', '.join([col for col in get_remaining_columns(table_name)])}
        FROM {table_name}
        """
        
        # 简化：直接构造完整的列列表
        if table_name == "marketdatadaily":
            copy_sql = f"""
            INSERT INTO {table_name}_new (id, symbol, market, timestamp, open, high, low, close, volume, turnover, change, pct_change, prev_close, pe, pb, ps, dividend_yield, eps, market_cap, updated_at)
            SELECT id, symbol, market, date, open, high, low, close, volume, turnover, change, pct_change, prev_close, pe, pb, ps, dividend_yield, eps, market_cap, updated_at
            FROM {table_name}
            """
        elif table_name == "marketdataminute":
            copy_sql = f"""
            INSERT INTO {table_name}_new (id, symbol, market, period, timestamp, open, high, low, close, volume, change, pct_change, updated_at)
            SELECT id, symbol, market, period, date, open, high, low, close, volume, change, pct_change, updated_at
            FROM {table_name}
            """
        elif table_name == "marketsnapshot":
            copy_sql = f"""
            INSERT INTO {table_name}_new (id, symbol, market, price, open, high, low, prev_close, change, pct_change, volume, turnover, pe, pb, ps, dividend_yield, market_cap, timestamp, data_source, fetch_time, updated_at)
            SELECT id, symbol, market, price, open, high, low, prev_close, change, pct_change, volume, turnover, pe, pb, ps, dividend_yield, market_cap, date, data_source, fetch_time, updated_at
            FROM {table_name}
            """
        
        result = session.exec(text(copy_sql))
        print(f"  ✅ 复制数据到新表")
        
        # 3. 删除旧表
        session.exec(text(f"DROP TABLE {table_name}"))
        print(f"  ✅ 删除旧表")
        
        # 4. 重命名新表
        session.exec(text(f"ALTER TABLE {table_name}_new RENAME TO {table_name}"))
        print(f"  ✅ 重命名新表为 {table_name}")
        
        # 5. 重建索引
        session.exec(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol ON {table_name}(symbol)"))
        session.exec(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_market ON {table_name}(market)"))
        session.exec(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)"))
        print(f"  ✅ 重建索引")
        
        session.commit()
        return True
        
    except Exception as e:
        print(f"  ❌ 迁移失败: {e}")
        session.rollback()
        return False

def get_remaining_columns(table_name):
    """获取剩余列名（排除id, symbol, market, date）"""
    if table_name == "marketdatadaily":
        return ['open', 'high', 'low', 'close', 'volume', 'turnover', 'change', 'pct_change', 'prev_close', 'pe', 'pb', 'ps', 'dividend_yield', 'eps', 'market_cap', 'updated_at']
    elif table_name == "marketdataminute":
        return ['open', 'high', 'low', 'close', 'volume', 'change', 'pct_change', 'updated_at']
    elif table_name == "marketsnapshot":
        return ['price', 'open', 'high', 'low', 'prev_close', 'change', 'pct_change', 'volume', 'turnover', 'pe', 'pb', 'ps', 'dividend_yield', 'market_cap', 'data_source', 'fetch_time', 'updated_at']
    return []

def verify_migration(session: Session):
    """验证迁移结果"""
    print(f"\n[5/5] 验证迁移结果...")
    
    tables = ["marketdatadaily", "marketdataminute", "marketsnapshot"]
    
    for table in tables:
        # 检查timestamp列是否存在
        result = session.exec(text(f"PRAGMA table_info({table})")).all()
        columns = [row[1] for row in result]
        
        if 'timestamp' in columns and 'date' not in columns:
            print(f"  ✅ {table}: timestamp列存在，date列已删除")
        else:
            print(f"  ❌ {table}: 迁移可能未成功")
            print(f"     列: {columns}")

def main():
    print("="*60)
    print("  数据库Schema迁移: date → timestamp")
    print("="*60)
    
    # 1. 备份
    backup_path = backup_database()
    
    # 2-4. 迁移表
    with Session(engine) as session:
        success = True
        
        print(f"\n[2/5] 迁移 MarketDataDaily...")
        if not migrate_table(session, "marketdatadaily"):
            success = False
        
        print(f"\n[3/5] 迁移 MarketDataMinute...")
        if not migrate_table(session, "marketdataminute"):
            success = False
        
        print(f"\n[4/5] 迁移 MarketSnapshot...")
        if not migrate_table(session, "marketsnapshot"):
            success = False
        
        if not success:
            print(f"\n❌ 迁移失败！请从备份恢复: {backup_path}")
            return
        
        # 5. 验证
        verify_migration(session)
    
    print(f"\n{'='*60}")
    print(f"✅ 迁移完成！")
    print(f"{'='*60}")
    print(f"\n备份文件: {backup_path}")
    print(f"如有问题，可从备份恢复")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 迁移异常: {e}")
        import traceback
        traceback.print_exc()
