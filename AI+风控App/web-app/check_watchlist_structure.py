"""检查 Watchlist 表结构和内容"""
from backend.database import engine
from sqlalchemy import text, inspect
from sqlmodel import Session

# 1. 查看表结构
inspector = inspect(engine)
columns = inspector.get_columns('watchlist')

print("=" * 60)
print("Watchlist 表结构:")
print("=" * 60)
for col in columns:
    print(f"  {col['name']:20} {str(col['type']):15} {'NOT NULL' if not col['nullable'] else 'NULL'}")

# 2. 查看数据
with Session(engine) as session:
    result = session.exec(text("SELECT * FROM watchlist LIMIT 10")).all()
    print(f"\nWatchlist 表中有数据 (显示前10条):")
    print(f"总列数: {len(result[0]) if result else 0}")
    
    if result:
        # 获取列名
        col_names = [col['name'] for col in columns]
        print(f"\n列名: {', '.join(col_names)}")
        print("\n数据:")
        for row in result:
            print(f"  {row}")
