#!/usr/bin/env python3
"""
手动保存HK指数19日数据到数据库
"""
import sys
sys.path.append('backend')

from data_fetcher import DataFetcher
import pandas as pd

fetcher = DataFetcher()

for symbol in ['HSI', 'HSTECH']:
    print(f'\n{'='*60}')
    print(f'处理 {symbol}')
    print(f'{'='*60}')
    
    # 获取历史数据
    df = fetcher.fetch_hk_daily_data(symbol)
    
    if df is not None and not df.empty:
        print(f'✅ 获取到 {len(df)} 条数据')
        
        # 保存到数据库（通过RawMarketData → ETL流程）
        # 构造period_data
        period_data = {'1d': df}
        
        fetcher.save_to_db(symbol, 'HK', period_data)
        print(f'✅ 已保存到数据库')
    else:
        print(f'❌ 获取失败')

print('\n' + '='*60)
print('完成！')
print('='*60)
