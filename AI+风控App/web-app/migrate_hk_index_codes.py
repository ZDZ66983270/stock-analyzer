#!/usr/bin/env python3
"""
HK 指数代码规范化迁移脚本
去除红筹指数和国企指数的 0 前缀
"""
import sys
sys.path.append('backend')

from database import engine
from sqlmodel import Session, text

MIGRATION_MAP = {
    'HK:INDEX:0HSCC': 'HK:INDEX:HSCC',
    'HK:INDEX:0HSCE': 'HK:INDEX:HSCE'
}

def migrate():
    print("🔄 开始 HK 指数代码规范化迁移...")
    print("="*60)
    
    with Session(engine) as session:
        for old_id, new_id in MIGRATION_MAP.items():
            print(f"\n📝 迁移 {old_id} → {new_id}")
            
            # 1. Index 表
            stmt = text("UPDATE 'index' SET symbol = :new WHERE symbol = :old").bindparams(new=new_id, old=old_id)
            result = session.exec(stmt)
            print(f"   Index: {result.rowcount} 条")
            
            # 2. MarketDataDaily 表
            stmt = text("UPDATE marketdatadaily SET symbol = :new WHERE symbol = :old").bindparams(new=new_id, old=old_id)
            result = session.exec(stmt)
            print(f"   MarketDataDaily: {result.rowcount} 条")
            
            # 3. MarketSnapshot 表
            stmt = text("UPDATE marketsnapshot SET symbol = :new WHERE symbol = :old").bindparams(new=new_id, old=old_id)
            result = session.exec(stmt)
            print(f"   MarketSnapshot: {result.rowcount} 条")
            
            # 4. RawMarketData 表
            stmt = text("UPDATE rawmarketdata SET symbol = :new WHERE symbol = :old").bindparams(new=new_id, old=old_id)
            result = session.exec(stmt)
            print(f"   RawMarketData: {result.rowcount} 条")
        
        session.commit()
    
    print("\n" + "="*60)
    print("✅ 迁移完成！")
    print("="*60)
    
    # 验证
    print("\n📊 验证结果：")
    with Session(engine) as session:
        result = session.exec(text(
            "SELECT symbol, COUNT(*) as count FROM marketdatadaily WHERE symbol LIKE 'HK:INDEX:%' GROUP BY symbol ORDER BY symbol"
        ))
        for row in result:
            print(f"   {row[0]}: {row[1]} 条记录")

if __name__ == "__main__":
    migrate()
