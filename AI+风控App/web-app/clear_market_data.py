"""
清空数据库行情表
保留 Watchlist 和其他配置表
"""

from sqlmodel import Session, create_engine, text
from datetime import datetime

# 使用backend目录下的数据库
engine = create_engine('sqlite:///backend/database.db')

print("=" * 80)
print("清空数据库行情表")
print("=" * 80)
print(f"执行时间: {datetime.now()}")
print()

with Session(engine) as session:
    # 先查看表的记录数
    tables_to_clear = [
        'rawmarketdata',
        'marketdatadaily', 
        'marketsnapshot'
    ]
    
    print("清空前记录数:")
    print("-" * 80)
    for table in tables_to_clear:
        try:
            result = session.exec(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.first()[0]
            print(f"  {table:20s}: {count:,} 条记录")
        except Exception as e:
            print(f"  {table:20s}: 表不存在或错误 ({e})")
    
    print()
    print("开始清空...")
    print("-" * 80)
    
    # 清空表
    for table in tables_to_clear:
        try:
            session.exec(text(f"DELETE FROM {table}"))
            print(f"  ✅ 已清空 {table}")
        except Exception as e:
            print(f"  ❌ 清空 {table} 失败: {e}")
    
    # 提交更改
    session.commit()
    
    print()
    print("清空后记录数:")
    print("-" * 80)
    for table in tables_to_clear:
        try:
            result = session.exec(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.first()[0]
            print(f"  {table:20s}: {count:,} 条记录")
        except Exception as e:
            print(f"  {table:20s}: 错误 ({e})")
    
    # 检查保留的表
    print()
    print("保留的表:")
    print("-" * 80)
    preserved_tables = ['watchlist', 'financialfundamentals', 'dividendfact', 'splitfact']
    for table in preserved_tables:
        try:
            result = session.exec(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.first()[0]
            print(f"  {table:20s}: {count:,} 条记录 (保留)")
        except Exception as e:
            print(f"  {table:20s}: 表不存在")

print()
print("=" * 80)
print("✅ 清空完成!")
print("=" * 80)
