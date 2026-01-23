#!/usr/bin/env python3
"""
测试 ETL PE 计算集成
"""
import sys
sys.path.append('backend')
from sqlmodel import Session
from backend.database import engine
from backend.etl_service import ETLService
import pandas as pd

print("="*80)
print("测试 ETL PE 计算集成")
print("="*80)

# 创建测试数据
test_data = {
    'timestamp': ['2026-01-06 16:00:00'],
    'open': [262.00],
    'high': [263.00],
    'low': [261.00],
    'close': [262.36],
    'volume': [50000000]
}

df = pd.DataFrame(test_data)
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"\n测试数据:")
print(df)

# 测试 ETL 处理
with Session(engine) as session:
    try:
        print(f"\n开始 ETL 处理 (US:STOCK:AAPL)...")
        count = ETLService.process_daily_data(
            session=session,
            df=df,
            symbol='US:STOCK:AAPL',
            market='US',
            is_history=True
        )
        print(f"✅ ETL 处理完成: {count} 条记录")
        
        # 查询结果
        from backend.models import MarketDataDaily
        from sqlmodel import select
        
        result = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'US:STOCK:AAPL')
            .where(MarketDataDaily.timestamp == '2026-01-06 16:00:00')
        ).first()
        
        if result:
            print(f"\n查询结果:")
            print(f"  Symbol: {result.symbol}")
            print(f"  Close: {result.close}")
            print(f"  EPS: {result.eps}")
            print(f"  PE: {result.pe}")
            
            if result.pe:
                print(f"\n✅ PE 计算成功集成到 ETL！")
            else:
                print(f"\n⚠️ PE 为 None（可能缺少财报数据）")
        else:
            print(f"\n❌ 未找到记录")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

print("="*80)
