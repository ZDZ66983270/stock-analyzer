#!/usr/bin/env python3
"""
检查HK和CN市场的最新数据记录
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from sqlmodel import Session, select
from models import MarketDataDaily, MarketDataMinute
from database import engine

# Connect to database
session = Session(engine)

def format_timestamp(ts):
    """格式化时间戳为可读格式"""
    if ts is None:
        return "None"
    if isinstance(ts, str):
        return ts
    # 假设是毫秒时间戳
    try:
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        beijing_time = dt.astimezone(tz=timezone.utc).replace(tzinfo=None)
        return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)

def check_market_data(market, symbols):
    """检查特定市场的数据"""
    print(f"\n{'='*80}")
    print(f"市场: {market}")
    print(f"{'='*80}")
    
    for symbol in symbols:
        print(f"\n--- {symbol} ---")
        
        # 检查日线数据
        stmt = select(MarketDataDaily).where(
            MarketDataDaily.symbol == symbol,
            MarketDataDaily.market == market
        ).order_by(MarketDataDaily.timestamp.desc()).limit(3)
        daily_records = session.exec(stmt).all()
        
        print(f"\n日线数据 (最新3条):")
        if daily_records:
            for i, record in enumerate(daily_records, 1):
                print(f"  {i}. 日期: {record.timestamp}, 收盘: {record.close}, "
                      f"涨跌幅: {record.pct_change}%, "
                      f"更新时间: {record.updated_at}")
        else:
            print("  ❌ 无数据")
        
        # 检查分钟数据
        stmt = select(MarketDataMinute).where(
            MarketDataMinute.symbol == symbol,
            MarketDataMinute.market == market
        ).order_by(MarketDataMinute.timestamp.desc()).limit(3)
        minute_records = session.exec(stmt).all()
        
        print(f"\n分钟数据 (最新3条):")
        if minute_records:
            for i, record in enumerate(minute_records, 1):
                print(f"  {i}. 日期: {record.timestamp}, 收盘: {record.close}, "
                      f"涨跌幅: {record.pct_change}%, "
                      f"更新时间: {record.updated_at}")
        else:
            print("  ❌ 无数据")

# 检查CN市场
cn_symbols = ['000001.SS', '600030.SH', '600309.SH', '601519.SH']
check_market_data('CN', cn_symbols)

# 检查HK市场
hk_symbols = ['800000', '800700', '09988.HK', '00005.HK']
check_market_data('HK', hk_symbols)

print(f"\n{'='*80}")
print("检查完成")
print(f"{'='*80}\n")

session.close()
