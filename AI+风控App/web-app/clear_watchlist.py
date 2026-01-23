"""
清空 Watchlist 表（个股关注表）
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session, select
from models import Watchlist

print("🗑️  开始清空 Watchlist 表...")

with Session(engine) as session:
    # 查询当前记录数
    watchlist = session.exec(select(Watchlist)).all()
    count = len(watchlist)
    
    print(f"\n📋 当前 Watchlist 记录数: {count}")
    
    if count > 0:
        print("\n以下股票将被删除:")
        for item in watchlist:
            print(f"   - {item.symbol} ({item.market}): {item.name}")
        
        # 删除所有记录
        session.query(Watchlist).delete()
        session.commit()
        print(f"\n✅ 已删除 {count} 条记录")
    else:
        print("\n⚠️  Watchlist 表已经是空的")

print("\n🎉 Watchlist 表已清空！")
