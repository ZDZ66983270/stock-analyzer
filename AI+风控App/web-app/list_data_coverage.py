#!/usr/bin/env python3
"""
数据覆盖度统计脚本
列出所有资产的：
1. 行情数据时长 (Start Date, End Date, Count)
2. 财报数据覆盖 (Start Date, End Date, Count)
"""
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from database import engine
from sqlmodel import Session, text

def list_coverage():
    print("# 全量资产数据覆盖度报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    with Session(engine) as session:
        # 1. 获取行情统计
        print("## 📈 行情数据时长 (Market Data Coverage)\n")
        market_query = text("""
            SELECT 
                symbol, 
                market,
                COUNT(id) as count,
                MIN(timestamp) as start_date,
                MAX(timestamp) as end_date
            FROM marketdatadaily 
            GROUP BY symbol 
            ORDER BY market, symbol
        """)
        market_stats = session.exec(market_query).all()
        
        # 存入字典以便后续合并
        market_data_map = {row[0]: row for row in market_stats}
        
        # 打印表头
        header = f"| 市场 | 代码 | 类型 | 记录数 | 开始日期 | 结束日期 | 时长(年) |"
        print(header)
        print("|:---|:---|:---|---:|:---|:---|---:|")
        
        for row in market_stats:
            symbol = row[0]
            market = row[1]
            count = row[2]
            start = pd.to_datetime(row[3]).strftime('%Y-%m-%d') if row[3] else "N/A"
            end = pd.to_datetime(row[4]).strftime('%Y-%m-%d') if row[4] else "N/A"
            
            # 计算时长
            years = 0.0
            if row[3] and row[4]:
                diff = pd.to_datetime(row[4]) - pd.to_datetime(row[3])
                years = diff.days / 365.25
            
            # 解析类型
            type_str = "STOCK"
            if ":INDEX:" in symbol: type_str = "INDEX"
            elif ":ETF:" in symbol: type_str = "ETF"
            elif "CRYPTO" in market: type_str = "CRYPTO"
            
            print(f"| {market} | {symbol} | {type_str} | {count} | {start} | {end} | {years:.1f} |")
            
        print("\n\n## 📑 财报数据覆盖 (Financial Data Coverage)\n")
        
        financial_query = text("""
            SELECT 
                symbol, 
                COUNT(id) as count,
                MIN(as_of_date) as start_date,
                MAX(as_of_date) as end_date
            FROM financialfundamentals 
            GROUP BY symbol 
            ORDER BY symbol
        """)
        fin_stats = session.exec(financial_query).all()
        
        header_fin = f"| 代码 | 财报份数 | 最早财报 | 最新财报 |"
        print(header_fin)
        print("|:---|---:|:---|:---|")
        
        for row in fin_stats:
            symbol = row[0]
            count = row[1]
            start = row[2] if row[2] else "N/A"
            end = row[3] if row[3] else "N/A"
            
            print(f"| {symbol} | {count} | {start} | {end} |")
            
    print("\n" + "="*60)

if __name__ == "__main__":
    list_coverage()
