"""
只清空 MarketSnapshot 表，保留其他所有表
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session, select
from models import MarketSnapshot

print("🗑️  开始清空 MarketSnapshot 表...")

with Session(engine) as session:
    # 只清空 MarketSnapshot
    print("\n📸 清空 MarketSnapshot...")
    count_snapshot = session.exec(select(MarketSnapshot)).all()
    print(f"   当前记录数: {len(count_snapshot)}")
    
    session.query(MarketSnapshot).delete()
    session.commit()
    print("   ✅ MarketSnapshot 已清空")

print("\n🎉 MarketSnapshot 表已清空！")
print("   ℹ️  其他表（MarketDataDaily 等）保持不变")
