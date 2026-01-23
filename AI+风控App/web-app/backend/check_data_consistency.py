#!/usr/bin/env python3
"""
数据一致性跟踪脚本
用于验证：下载库(RawMarketData) → 生产库(MarketDataDaily) → 前端显示 的数据一致性
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend/market_data_V4.db"

def check_data_consistency(symbol: str, market: str):
    """检查指定股票的数据一致性"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"\n{'='*80}")
    print(f"数据一致性检查: {symbol} ({market})")
    print(f"{'='*80}\n")
    
    # 1. 检查原始数据（下载库）
    print("📥 【下载库 RawMarketData】")
    cursor.execute("""
        SELECT id, source, period, processed, created_at, payload
        FROM rawmarketdata
        WHERE symbol = ? AND market = ?
        ORDER BY created_at DESC
        LIMIT 3
    """, (symbol, market))
    
    raw_records = cursor.fetchall()
    if raw_records:
        for rec in raw_records:
            rec_id, source, period, processed, created_at, payload = rec
            status = "✅ 已处理" if processed else "⏳ 待处理"
            print(f"  ID: {rec_id} | Period: {period} | {status} | Time: {created_at}")
            
            # 解析payload获取价格数据
            try:
                data = json.loads(payload)
                if data and len(data) > 0:
                    latest = data[0] if isinstance(data, list) else data
                    price = latest.get('close', 'N/A')
                    print(f"    └─ Price: {price}")
            except:
                print(f"    └─ Payload parse error")
    else:
        print("  ❌ 无数据")
    
    # 2. 检查生产数据（生产库）
    print(f"\n📦 【生产库 MarketDataDaily】")
    cursor.execute("""
        SELECT date, open, high, low, close, volume, change, pct_change, updated_at
        FROM marketdatadaily
        WHERE symbol = ? AND market = ?
        ORDER BY date DESC
        LIMIT 3
    """, (symbol, market))
    
    daily_records = cursor.fetchall()
    if daily_records:
        for rec in daily_records:
            date, open_p, high, low, close, volume, change, pct_change, updated_at = rec
            print(f"  Date: {date}")
            print(f"    Price: {close} | Change: {change} ({pct_change}%)")
            print(f"    Volume: {volume:,} | Updated: {updated_at}")
    else:
        print("  ❌ 无数据")
    
    # 3. 检查分钟数据
    print(f"\n⏱️  【分钟数据 MarketDataMinute】")
    cursor.execute("""
        SELECT date, close, volume, change, pct_change
        FROM marketdataminute
        WHERE symbol = ? AND market = ?
        ORDER BY date DESC
        LIMIT 3
    """, (symbol, market))
    
    minute_records = cursor.fetchall()
    if minute_records:
        for rec in minute_records:
            date, close, volume, change, pct_change = rec
            print(f"  {date} | Price: {close} | {pct_change}% | Vol: {volume:,}")
    else:
        print("  ❌ 无数据")
    
    conn.close()
    print(f"\n{'='*80}\n")


def main():
    """检查自选列表中的所有股票"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取自选列表
    cursor.execute("SELECT symbol, market FROM watchlist ORDER BY id")
    watchlist = cursor.fetchall()
    
    print("\n" + "="*80)
    print("🔍 开始数据一致性检查")
    print("="*80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"检查项目数: {len(watchlist)}")
    
    for symbol, market in watchlist:
        check_data_consistency(symbol, market)
    
    conn.close()
    
    print("\n✅ 检查完成！")
    print("\n请执行强制刷新，然后再次运行此脚本对比数据变化。\n")


if __name__ == "__main__":
    main()
