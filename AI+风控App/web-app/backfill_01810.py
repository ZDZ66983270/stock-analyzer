#!/usr/bin/env python3
"""
手动为01810.HK下载30天历史数据
"""
import sys
sys.path.append('backend')

from data_fetcher import DataFetcher
import logging

logging.basicConfig(level=logging.INFO)

def main():
    fetcher = DataFetcher()
    
    print("=" * 60)
    print("为 01810.HK 下载30天历史数据")
    print("=" * 60)
    
    result = fetcher.backfill_missing_data('01810.HK', 'HK', days=30)
    
    print("\n" + "=" * 60)
    if result.get('success'):
        print(f"✅ 成功: {result.get('records_fetched', 0)} 条记录")
    else:
        print(f"❌ 失败: {result.get('message', '未知错误')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
