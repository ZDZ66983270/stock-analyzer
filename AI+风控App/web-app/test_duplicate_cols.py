#!/usr/bin/env python3
"""
测试CN股票数据获取，检查是否有重复列名
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.data_fetcher import DataFetcher

# 测试获取601519.sh的数据
fetcher = DataFetcher()

print("测试获取601519.sh的日线数据...")
try:
    # 模拟获取CN股票的日线数据
    symbol = "601519"
    df = fetcher.fetch_cn_daily_data(symbol)
    
    if df is not None and not df.empty:
        print(f"\n获取成功，共 {len(df)} 行数据")
        print(f"\n列名: {list(df.columns)}")
        print(f"\n列名数量: {len(df.columns)}")
        print(f"唯一列名数量: {len(set(df.columns))}")
        
        # 检查重复列
        duplicate_cols = [col for col in df.columns if list(df.columns).count(col) > 1]
        if duplicate_cols:
            print(f"\n❌ 发现重复列: {set(duplicate_cols)}")
            # 显示每个重复列的索引位置
            for col in set(duplicate_cols):
                indices = [i for i, c in enumerate(df.columns) if c == col]
                print(f"  {col}: 出现在索引 {indices}")
        else:
            print("\n✅ 没有重复列")
        
        # 显示最后几行数据的列名和值
        print(f"\n最后一行数据:")
        print(df.iloc[-1])
    else:
        print("获取数据失败或为空")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
