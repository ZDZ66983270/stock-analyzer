#!/usr/bin/env python3
"""
重新处理Raw表中的数据以修复Snapshot表
修复bug后需要运行此脚本
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlmodel import create_engine, Session, select
from backend.models import RawMarketData
from backend.etl_service import ETLService

def main():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'database.db'))
    engine = create_engine(f"sqlite:///{db_path}")
    
    print(f"连接数据库: {db_path}\n")
    
    with Session(engine) as session:
        # 获取所有已处理的Raw数据，按ID倒序（最新的优先）
        stmt = select(RawMarketData).where(
            RawMarketData.processed == True
        ).order_by(RawMarketData.id.desc()).limit(50)  # 只处理最近的50条
        
        raw_records = session.exec(stmt).all()
        
        print(f"找到 {len(raw_records)} 条已处理的Raw记录")
        print("开始重新处理...\n")
        
        # 临时标记为未处理
        for record in raw_records:
            record.processed = False
        session.commit()
        
        # 重新处理
        success_count = 0
        for record in raw_records:
            print(f"处理 Raw ID={record.id}, Symbol={record.symbol}, Market={record.market}")
            try:
                ETLService.process_raw_data(record.id)
                success_count += 1
                print(f"  ✅ 成功")
            except Exception as e:
                print(f"  ❌ 失败: {e}")
        
        print(f"\n完成！成功处理 {success_count}/{len(raw_records)} 条记录")

if __name__ == "__main__":
    main()
