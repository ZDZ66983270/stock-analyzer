#!/usr/bin/env python3
import sqlite3
import sys
import requests
import time

db_path = "backend/database.db"

# 获取未处理的Raw ID
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id FROM rawmarketdata WHERE processed = 0 ORDER BY id DESC LIMIT 30")
raw_ids = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"找到 {len(raw_ids)} 条未处理的Raw记录")

if not raw_ids:
    print("无需处理")
    sys.exit(0)

# 直接在这个脚本中处理（避免导入问题）
# 重新标记为已处理，让后端API触发时自动处理
print("通过API触发同步...")

# 触发一次全局同步
try:
    response = requests.post("http://localhost:8000/api/sync-indices", timeout=120)
    print(f"API响应: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"API调用失败: {e}")

# 等待处理
time.sleep(10)

# 检查处理结果
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM rawmarketdata WHERE processed = 0")
remaining = cursor.fetchone()[0]
conn.close()

print(f"\n处理结果: 剩余 {remaining} 条未处理记录")
