#!/usr/bin/env python3
"""
Daily Market Data Integrity Checker
检查 MarketDataDaily 表的数据完整性
Author: Antigravity
Date: 2025-12-21
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'backend', 'database.db')

def connect_db():
    """连接数据库"""
    return sqlite3.connect(DB_PATH)

def get_all_symbols():
    """获取所有股票代码"""
    conn = connect_db()
    query = """
    SELECT DISTINCT symbol, market 
    FROM MarketDataDaily 
    ORDER BY market, symbol
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_date_range_for_symbol(symbol, market):
    """获取某个股票的日期范围"""
    conn = connect_db()
    query = """
    SELECT 
        MIN(timestamp) as first_date,
        MAX(timestamp) as last_date,
        COUNT(*) as total_records
    FROM MarketDataDaily
    WHERE symbol = ? AND market = ?
    """
    df = pd.read_sql_query(query, conn, params=(symbol, market))
    conn.close()
    return df.iloc[0] if not df.empty else None

def get_all_dates_for_symbol(symbol, market):
    """获取某个股票的所有日期"""
    conn = connect_db()
    query = """
    SELECT timestamp, close, volume
    FROM MarketDataDaily
    WHERE symbol = ? AND market = ?
    ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn, params=(symbol, market))
    conn.close()
    return df

def find_missing_dates(timestamps, start_date, end_date):
    """找出缺失的交易日（简单版本，不考虑节假日）"""
    # Extract just the date part from timestamps
    date_set = set(pd.to_datetime(timestamps).dt.date)
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    
    # 生成所有工作日
    all_dates = pd.date_range(start=start, end=end, freq='B')  # B = business days
    all_dates_set = set(all_dates.date)
    
    # 找出缺失的日期
    missing = sorted(all_dates_set - date_set)
    return missing

def check_data_quality(df):
    """检查数据质量问题"""
    issues = []
    
    # 检查空值
    null_counts = df.isnull().sum()
    if null_counts.any():
        issues.append(f"存在空值: {null_counts[null_counts > 0].to_dict()}")
    
    # 检查异常价格（0或负数）
    if 'close' in df.columns:
        invalid_prices = df[df['close'] <= 0]
        if not invalid_prices.empty:
            issues.append(f"存在异常价格: {len(invalid_prices)} 条记录")
    
    # 检查异常成交量（负数）
    if 'volume' in df.columns:
        invalid_volume = df[df['volume'] < 0]
        if not invalid_volume.empty:
            issues.append(f"存在异常成交量: {len(invalid_volume)} 条记录")
    
    # 检查重复日期
    if 'timestamp' in df.columns:
        duplicates = df[df.duplicated(subset=['timestamp'], keep=False)]
        if not duplicates.empty:
            issues.append(f"存在重复日期: {len(duplicates)} 条记录")
    
    return issues

def generate_report():
    """生成完整性报告"""
    print("=" * 80)
    print("📊 Daily Market Data Integrity Report")
    print(f"⏰ Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 获取所有股票
    symbols_df = get_all_symbols()
    
    if symbols_df.empty:
        print("⚠️  MarketDataDaily 表为空！")
        return
    
    print(f"📈 Total Symbols: {len(symbols_df)}")
    print()
    
    # 按市场分组统计
    market_stats = defaultdict(lambda: {
        'count': 0,
        'total_records': 0,
        'symbols': []
    })
    
    all_issues = []
    
    for idx, row in symbols_df.iterrows():
        symbol = row['symbol']
        market = row['market']
        
        # 获取日期范围
        date_info = get_date_range_for_symbol(symbol, market)
        
        if date_info is None:
            continue
        
        first_date = date_info['first_date']
        last_date = date_info['last_date']
        total_records = date_info['total_records']
        
        # 更新市场统计
        market_stats[market]['count'] += 1
        market_stats[market]['total_records'] += total_records
        market_stats[market]['symbols'].append(symbol)
        
        # 获取所有日期数据
        dates_df = get_all_dates_for_symbol(symbol, market)
        
        # 检查缺失日期
        missing_dates = find_missing_dates(dates_df['timestamp'], first_date, last_date)
        
        # 检查数据质量
        quality_issues = check_data_quality(dates_df)
        
        # 计算预期交易日数量（粗略估计）
        start = pd.to_datetime(first_date)
        end = pd.to_datetime(last_date)
        expected_days = len(pd.date_range(start=start, end=end, freq='B'))
        completeness = (total_records / expected_days * 100) if expected_days > 0 else 0
        
        # 打印详细信息
        status = "✅" if completeness >= 90 and not quality_issues else "⚠️"
        print(f"{status} [{market}] {symbol}")
        print(f"   📅 Date Range: {first_date} → {last_date}")
        print(f"   📊 Records: {total_records} / ~{expected_days} expected ({completeness:.1f}%)")
        
        if missing_dates:
            print(f"   ⚠️  Missing Dates: {len(missing_dates)} days")
            if len(missing_dates) <= 10:
                print(f"      {', '.join([str(d) for d in missing_dates])}")
            else:
                print(f"      First 5: {', '.join([str(d) for d in missing_dates[:5]])}")
                print(f"      Last 5: {', '.join([str(d) for d in missing_dates[-5:]])}")
        
        if quality_issues:
            print(f"   ❌ Data Quality Issues:")
            for issue in quality_issues:
                print(f"      - {issue}")
                all_issues.append(f"{symbol} ({market}): {issue}")
        
        print()
    
    # 打印市场汇总
    print("=" * 80)
    print("📊 Market Summary")
    print("=" * 80)
    for market, stats in sorted(market_stats.items()):
        print(f"\n🌍 {market} Market:")
        print(f"   Symbols: {stats['count']}")
        print(f"   Total Records: {stats['total_records']:,}")
        print(f"   Avg Records/Symbol: {stats['total_records'] / stats['count']:.1f}")
    
    # 打印所有问题汇总
    if all_issues:
        print("\n" + "=" * 80)
        print("⚠️  All Data Quality Issues")
        print("=" * 80)
        for issue in all_issues:
            print(f"  - {issue}")
    else:
        print("\n✅ No data quality issues found!")
    
    print("\n" + "=" * 80)

def check_recent_updates():
    """检查最近更新情况"""
    print("\n" + "=" * 80)
    print("🔄 Recent Updates Check")
    print("=" * 80)
    
    conn = connect_db()
    
    # 检查最近7天的数据
    query = """
    SELECT 
        market,
        symbol,
        MAX(timestamp) as latest_date,
        COUNT(*) as records_last_7days
    FROM MarketDataDaily
    WHERE timestamp >= datetime('now', '-7 days')
    GROUP BY market, symbol
    ORDER BY market, latest_date DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("⚠️  No data in the last 7 days!")
        return
    
    today = datetime.now().date()
    
    for market in df['market'].unique():
        market_df = df[df['market'] == market]
        print(f"\n🌍 {market} Market:")
        
        for _, row in market_df.iterrows():
            symbol = row['symbol']
            latest_date = pd.to_datetime(row['latest_date']).date()
            records = row['records_last_7days']
            days_old = (today - latest_date).days
            
            status = "✅" if days_old <= 1 else "⚠️" if days_old <= 3 else "❌"
            print(f"   {status} {symbol}: {latest_date} ({days_old} days old, {records} records)")

if __name__ == "__main__":
    try:
        # 检查数据库是否存在
        if not os.path.exists(DB_PATH):
            print(f"❌ Database not found: {DB_PATH}")
            exit(1)
        
        # 生成报告
        generate_report()
        
        # 检查最近更新
        check_recent_updates()
        
        print("\n✅ Integrity check completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
