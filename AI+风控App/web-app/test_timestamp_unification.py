#!/usr/bin/env python3
"""
测试01810.HK历史数据重新处理
验证timestamp统一后ETL是否正常工作
"""
import sys
sys.path.append('backend')

from etl_service import ETLService
from database import engine
from sqlmodel import Session, select
from models import RawMarketData, MarketDataDaily

print("="*60)
print("测试timestamp统一 - 重新处理01810.HK历史数据")
print("="*60)

# 1. 检查raw数据
with Session(engine) as session:
    raw = session.get(RawMarketData, 54)
    if raw:
        print(f"\n[1/3] Raw记录状态:")
        print(f"  ID: {raw.id}")
        print(f"  Symbol: {raw.symbol}")
        print(f"  Processed: {raw.processed}")
        print(f"  Error: {raw.error_log}")
        
        # 重置processed状态
        raw.processed = 0
        raw.error_log = None
        session.commit()
        print(f"  \u2705 已重置processed状态")
    else:
        print("\u274c Raw记录不存在")
        sys.exit(1)

# 2. 处理ETL
print(f"\n[2/3] 执行ETL处理...")
try:
    ETLService.process_raw_data(54)
    print(f"  \u2705 ETL处理完成")
except Exception as e:
    print(f"  \u274c ETL失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 验证结果
with Session(engine) as session:
    # 检查raw状态
    raw = session.get(RawMarketData, 54)
    print(f"\n[3/3] 验证结果:")
    print(f"  Raw Processed: {raw.processed}")
    print(f"  Raw Error: {raw.error_log}")
    
    # 检查daily记录数
    daily_records = session.exec(
        select(MarketDataDaily)
        .where(MarketDataDaily.symbol == '01810.HK')
    ).all()
    
    print(f"\n  Daily记录数: {len(daily_records)}")
    if daily_records:
        dates = sorted([r.timestamp for r in daily_records])
        print(f"  日期范围: {dates[0]} ~ {dates[-1]}")
        print(f"  \u2705 成功!" if len(daily_records) >= 20 else f"  \u26a0\ufe0f  记录数少于预期")
    else:
        print(f"  \u274c 没有daily记录")

print("\n" + "="*60)
