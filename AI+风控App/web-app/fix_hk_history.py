#!/usr/bin/env python3
"""
为HK股票补充昨天的历史数据作为prev_close基准
"""
import sqlite3
from datetime import datetime, timedelta

db_path = "backend/database.db"

# HK股票和它们昨日的收盘价（从日志中获取）
hk_stocks = [
    ('00700.HK', 605.0),   # 腾讯: 今天614.0, 昨天605.0
    ('09988.HK', 144.1),   # 阿里: 今天145.3, 昨天144.1
]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

yesterday = '2025-12-18 16:00:00'

for symbol, close_price in hk_stocks:
    # 检查是否已有昨天的数据
    cursor.execute(
        "SELECT COUNT(*) FROM marketdatadaily WHERE symbol=? AND date like '2025-12-18%'",
        (symbol,)
    )
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"插入 {symbol} 昨日数据: close={close_price}")
        cursor.execute("""
            INSERT INTO marketdatadaily 
            (symbol, market, date, open, high, low, close, volume, prev_close, change, pct_change, updated_at)
            VALUES (?, 'HK', ?, ?, ?, ?, ?, 0, NULL, 0, 0, datetime('now'))
        """, (symbol, yesterday, close_price, close_price, close_price, close_price))
    else:
        print(f"{symbol} 昨日数据已存在，跳过")

conn.commit()
conn.close()

print("\n完成！现在可以重新触发ETL了。")
