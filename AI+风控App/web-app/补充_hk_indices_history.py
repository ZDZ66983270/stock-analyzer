#!/usr/bin/env python3
"""
补充 HK 指数历史数据（使用 AkShare）
"""
import sys
sys.path.append('backend')

import akshare as ak
import pandas as pd
from sqlmodel import Session
from database import engine
from etl_service import ETLService

# HK 指数列表
HK_INDICES = [
    ('HK:INDEX:HSCC', 'HSCC', '红筹指数'),
    ('HK:INDEX:HSI', 'HSI', '恒生指数'),
    ('HK:INDEX:HSCE', 'HSCE', '国企指数'),
    ('HK:INDEX:HSTECH', 'HSTECH', '恒生科技指数'),
]

def download_hk_index(canonical_id: str, akshare_symbol: str, name: str):
    """使用 AkShare 下载 HK 指数历史数据"""
    print(f"\n{'='*70}")
    print(f"下载 {canonical_id} ({name}) - AkShare: {akshare_symbol}")
    print(f"{'='*70}")
    
    try:
        # 使用 AkShare 获取数据
        df = ak.stock_hk_index_daily_sina(symbol=akshare_symbol)
        
        if df is None or df.empty:
            print(f"⚠️  AkShare 无数据")
            return 0
        
        print(f"✅ 获取 {len(df)} 条记录")
        
        # 重命名列以匹配 ETL 期望
        df = df.rename(columns={'date': 'timestamp'})
        df.columns = [c.lower() for c in df.columns]
        
        # 使用 ETL 服务处理
        with Session(engine) as session:
            count = ETLService.process_daily_data(
                session=session,
                df=df,
                symbol=canonical_id,
                market='HK',
                is_history=True
            )
        
        print(f"✅ 成功保存 {count} 条记录")
        return count
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 0

def main():
    print("🚀 开始补充 HK 指数历史数据...")
    
    total_records = 0
    for canonical_id, akshare_symbol, name in HK_INDICES:
        saved = download_hk_index(canonical_id, akshare_symbol, name)
        total_records += saved
    
    print(f"\n{'='*70}")
    print(f"✅ 完成！总共保存 {total_records:,} 条记录")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
