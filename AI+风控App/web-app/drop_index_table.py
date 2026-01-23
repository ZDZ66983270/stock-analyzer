"""
删除 Index 表 - 统一资产管理升级的一部分
将所有指数数据迁移到 Watchlist 表后,删除独立的 Index 表
"""
from backend.database import engine
from sqlalchemy import text
from sqlmodel import Session

def main():
    with Session(engine) as session:
        # 1. 检查 Index 表中的数据
        print("=" * 60)
        print("检查 Index 表中的数据...")
        print("=" * 60)
        
        result = session.exec(text('SELECT COUNT(*) as count FROM "index"')).first()
        count = result[0] if result else 0
        print(f"\nIndex 表中有 {count} 条记录")
        
        if count > 0:
            print("\n当前 Index 表数据:")
            records = session.exec(text('SELECT symbol, name, market FROM "index"')).all()
            for r in records:
                print(f"  - {r[0]:15} {r[1]:20} ({r[2]})")
        
        # 2. 确认删除
        print("\n" + "=" * 60)
        confirm = input("确认删除 Index 表? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ 取消删除操作")
            return
        
        # 3. 删除表
        print("\n正在删除 Index 表...")
        session.exec(text('DROP TABLE IF EXISTS "index"'))
        session.commit()
        
        print("✅ Index 表已成功删除")
        
        # 4. 验证删除结果
        print("\n验证删除结果...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'index' in tables:
            print("❌ 错误: Index 表仍然存在")
        else:
            print("✅ 确认: Index 表已被删除")
            print(f"\n当前数据库中的表 ({len(tables)} 个):")
            for table in sorted(tables):
                print(f"  - {table}")

if __name__ == "__main__":
    main()
