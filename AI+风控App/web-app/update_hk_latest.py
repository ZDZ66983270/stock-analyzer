"""
脚本：使用yfinance强制更新HK指数最新数据，并执行ETL更新生产表
"""
import sys
sys.path.insert(0, 'backend')

import pandas as pd
# Use direct imports since 'backend' is in sys.path
from data_fetcher import DataFetcher
from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily
from datetime import datetime

print("=" * 80)
print("🚀 强制更新HK指数 (yfinance -> ETL)")
print("=" * 80)

fetcher = DataFetcher()

# 目标指数
indices = ['HSI', 'HSTECH']

for symbol in indices:
    print(f"\n处理 {symbol} ...")
    
    try:
        # 1. 强制使用 yfinance 获取数据
        # 使用内部私有方法 _fetch_fallback_yfinance 绕过 AkShare 优先级
        df = fetcher._fetch_fallback_yfinance(symbol, "HK")
        
        if df.empty:
            print(f"❌ yfinance 无数据")
            continue
            
        # 2. 获取最新一条记录 (理论上是 2025-12-17)
        latest_row = df.iloc[-1]
        date_val = latest_row['时间'] # yfinance返回的是Timestamp
        
        # 格式化日期字符串
        date_str = date_val.strftime('%Y-%m-%d %H:%M:%S')
        date_short = date_val.strftime('%Y-%m-%d')
        
        print(f"  📅 最新日期: {date_short}")
        print(f"  💰 收盘价: {latest_row['close']:.2f}")
        
        # 检查是否是今天(17日)的数据
        if date_short != '2025-12-17':
            print(f"  ⚠️ 警告:并非12-17的数据，跳过")
            # continue # 暂时不跳过，因为我们要更新最新
        
        # 3. 保存到 MarketDataDaily (历史仓库)
        with Session(engine) as session:
            # 检查是否已存在
            existing = session.exec(
                select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol,
                    MarketDataDaily.market == 'HK',
                    MarketDataDaily.date == date_str
                )
            ).first()
            
            if existing:
                print(f"  ℹ️  MarketDataDaily 已存在记录，更新...")
                existing.close = float(latest_row['close'])
                existing.open = float(latest_row['open'])
                existing.high = float(latest_row['high'])
                existing.low = float(latest_row['low'])
                existing.volume = int(latest_row['volume'])
                existing.updated_at = datetime.now()
                session.add(existing)
            else:
                print(f"  💾 插入 MarketDataDaily 新记录...")
                record = MarketDataDaily(
                    symbol=symbol,
                    market='HK',
                    date=date_str,
                    open=float(latest_row['open']),
                    high=float(latest_row['high']),
                    low=float(latest_row['low']),
                    close=float(latest_row['close']),
                    volume=int(latest_row['volume']),
                    turnover=0,
                    change=0, # 暂时为0，后面ETL会算
                    pct_change=0,
                    updated_at=datetime.now()
                )
                session.add(record)
            
            session.commit()
        
        # 4. 执行ETL (save_snapshot)
        print(f"  🔄 执行ETL (save_snapshot)...")
        data_dict = {
            'price': float(latest_row['close']),
            'open': float(latest_row['open']),
            'high': float(latest_row['high']),
            'low': float(latest_row['low']),
            'close': float(latest_row['close']),
            'volume': int(latest_row['volume']),
            'change': None, # 强制ETL计算
            'pct_change': None
        }
        
        fetcher.save_snapshot(symbol, 'HK', data_dict)
        print(f"  ✅ 完成")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n" + "=" * 80)
