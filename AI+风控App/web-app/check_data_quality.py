"""
数据完整性检查脚本
检查下载的数据量、日期范围、缺失情况
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session, text
import pandas as pd

print("=" * 80)
print("📊 数据完整性检查报告")
print("=" * 80)

with Session(engine) as session:
    # 1. 总体统计
    print("\n【1. 总体统计】")
    result = session.exec(text("""
        SELECT 
            market,
            COUNT(DISTINCT symbol) as symbols,
            COUNT(*) as records,
            MIN(date) as earliest,
            MAX(date) as latest
        FROM marketdatadaily
        GROUP BY market
        ORDER BY market
    """))
    
    df = pd.DataFrame(result.fetchall(), columns=['市场', 'Symbol数', '记录数', '最早日期', '最新日期'])
    print(df.to_string(index=False))
    
    # 2. 每个symbol详情
    print("\n【2. 各Symbol数据范围】")
    result = session.exec(text("""
        SELECT 
            symbol,
            market,
            COUNT(*) as days,
            MIN(date) as start_date,
            MAX(date) as end_date,
            ROUND(AVG(volume), 0) as avg_volume
        FROM marketdatadaily
        GROUP BY symbol, market
        ORDER BY market, symbol
    """))
    
    df = pd.DataFrame(result.fetchall(), 
                     columns=['Symbol', '市场', '天数', '开始日期', '结束日期', '平均成交量'])
    print(df.to_string(index=False))
    
    # 3. 检查最近7天数据完整性
    print("\n【3. 最近7天数据检查】")
    result = session.exec(text("""
        SELECT 
            symbol,
            market,
            date,
            close,
            volume
        FROM marketdatadaily
        WHERE date >= date('now', '-7 days')
        ORDER BY symbol, date DESC
        LIMIT 50
    """))
    
    df = pd.DataFrame(result.fetchall(), 
                     columns=['Symbol', '市场', '日期', '收盘价', '成交量'])
    print(df.to_string(index=False))
    
    # 4. 数据质量检查
    print("\n【4. 数据质量问题】")
    
    # 检查价格为0的记录
    result = session.exec(text("""
        SELECT symbol, market, COUNT(*) as count
        FROM marketdatadaily
        WHERE close = 0 OR close IS NULL
        GROUP BY symbol, market
    """))
    
    zero_price = result.fetchall()
    if zero_price:
        print(f"⚠️  价格为0或NULL的记录:")
        for row in zero_price:
            print(f"   {row[0]} ({row[1]}): {row[2]}条")
    else:
        print("✅ 无价格异常记录")
    
    # 检查重复记录
    result = session.exec(text("""
        SELECT symbol, market, date, COUNT(*) as dup_count
        FROM marketdatadaily
        GROUP BY symbol, market, date
        HAVING COUNT(*) > 1
    """))
    
    duplicates = result.fetchall()
    if duplicates:
        print(f"\n⚠️  重复记录:")
        for row in duplicates:
            print(f"   {row[0]} ({row[1]}) {row[2]}: {row[3]}次")
    else:
        print("✅ 无重复记录")

print("\n" + "=" * 80)
print("📋 检查完成")
print("=" * 80)
