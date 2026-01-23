#!/usr/bin/env python3
"""
批量处理 RAW 数据 - ETL 处理脚本
处理所有未处理的 RawMarketData 记录
"""

import sys
sys.path.append('backend')

from sqlmodel import Session, create_engine, select
from backend.models import RawMarketData
from backend.etl_service import ETLService
from datetime import datetime
import time

engine = create_engine('sqlite:///backend/database.db')

def process_all_raw_data():
    """处理所有未处理的 RAW 数据"""
    print("=" * 80)
    print("批量 ETL 处理")
    print("=" * 80)
    print(f"执行时间: {datetime.now()}")
    print()
    
    with Session(engine) as session:
        # 查询所有未处理的记录
        unprocessed = session.exec(
            select(RawMarketData).where(RawMarketData.processed == False)
        ).all()
        
        total = len(unprocessed)
        
        if total == 0:
            print("✅ 没有待处理的记录")
            return
        
        print(f"📋 待处理记录: {total} 条")
        print()
        
        success = 0
        failed = 0
        
        for idx, record in enumerate(unprocessed, 1):
            print(f"[{idx}/{total}] 处理 {record.symbol} (ID: {record.id})")
            
            try:
                ETLService.process_raw_data(record.id)
                success += 1
                print(f"  ✅ 成功")
            except Exception as e:
                failed += 1
                print(f"  ❌ 失败: {e}")
            
            # 避免过快
            if idx < total:
                time.sleep(0.1)
        
        print()
        print("=" * 80)
        print("处理完成")
        print("=" * 80)
        print(f"✅ 成功: {success}")
        print(f"❌ 失败: {failed}")
        print(f"📊 总计: {total}")

if __name__ == "__main__":
    try:
        process_all_raw_data()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
