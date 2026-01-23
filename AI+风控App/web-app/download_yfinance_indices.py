"""
使用yfinance下载CN和US指数历史数据
获取尽可能长的历史数据
"""
import sys
sys.path.insert(0, 'backend')

import yfinance as yf
from data_fetcher import normalize_symbol_db
from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily
from datetime import datetime
import pandas as pd

print("=" * 70)
print("📥 使用yfinance下载CN和US指数历史数据")
print("=" * 70)

# 定义要下载的指数
indices = [
    # CN指数
    {"symbol": "000001.SS", "name": "上证综指", "market": "CN"},
    
    # US指数
    {"symbol": "^DJI", "name": "道琼斯", "market": "US"},
    {"symbol": "^NDX", "name": "纳斯达克100", "market": "US"},
    {"symbol": "^SPX", "name": "标普500", "market": "US"},
]

success_count = 0
fail_count = 0
total_records = 0

for idx_info in indices:
    symbol = idx_info["symbol"]
    name = idx_info["name"]
    market = idx_info["market"]
    
    print(f"\n[{name}] ({symbol}, {market})")
    print("-" * 70)
    
    try:
        # 下载历史数据 (max=所有可用历史)
        print(f"  正在从yfinance下载...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="max")
        
        if df.empty:
            print(f"  ❌ 无数据")
            fail_count += 1
            continue
        
        print(f"  ✅ 获取到 {len(df)} 条记录")
        print(f"  📅 时间范围: {df.index[0].date()} ~ {df.index[-1].date()}")
        
        # 保存到数据库
        db_symbol = normalize_symbol_db(symbol, market)
        saved_count = 0
        
        with Session(engine) as session:
            for date, row in df.iterrows():
                try:
                    date_str = date.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 去重检查
                    existing = session.exec(
                        select(MarketDataDaily).where(
                            MarketDataDaily.symbol == db_symbol,
                            MarketDataDaily.market == market,
                            MarketDataDaily.date == date_str
                        )
                    ).first()
                    
                    if existing:
                        continue
                    
                    # 创建记录
                    record = MarketDataDaily(
                        symbol=db_symbol,
                        market=market,
                        date=date_str,
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume']),
                        turnover=0,
                        change=0,
                        pct_change=0,
                        updated_at=datetime.now()
                    )
                    
                    session.add(record)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"    ⚠️  跳过记录 {date}: {e}")
                    continue
            
            if saved_count > 0:
                session.commit()
                print(f"  💾 成功保存 {saved_count} 条新记录")
                total_records += saved_count
                success_count += 1
            else:
                print(f"  ℹ️  数据已存在，无新记录")
                success_count += 1
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        fail_count += 1

# 总结
print("\n" + "=" * 70)
print("📊 下载完成统计")
print("=" * 70)
print(f"✅ 成功: {success_count} 个指数")
print(f"📊 新增记录: {total_records} 条")
print(f"❌ 失败: {fail_count} 个指数")
print("=" * 70)
