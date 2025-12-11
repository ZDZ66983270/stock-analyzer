# 滑窗方式抓取 MSFT 的上一个交易日 Tick 数据（逐笔成交）并拼接保存（自动避开未来/周末，测试合约是否可用）
from ib_insync import *
import pandas as pd
from datetime import datetime, timedelta, timezone
import pytz
import time
import os

# === 合约设置（明确使用 ISLAND 替代 SMART） ===
contract = Stock('MSFT', 'ISLAND', 'USD')

# === 获取美东时间 ===
et = pytz.timezone('US/Eastern')
et_now = datetime.now(timezone.utc).astimezone(et)

# === 设定上一个交易日（自动避开周末） ===
if et_now.weekday() == 0:
    trade_day = et_now - timedelta(days=3)
elif et_now.weekday() >= 1:
    trade_day = et_now - timedelta(days=1)
else:
    raise ValueError("⚠️ 当前为周末，无法推断交易日，请在交易周内运行")

# === 设定交易时间段 ===
start_time = trade_day.replace(hour=9, minute=30, second=0, microsecond=0)
end_time = trade_day.replace(hour=16, minute=0, second=0, microsecond=0)

# === 初始化连接 ===
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=3)

# === 测试是否支持历史K线 ===
k_test = ib.reqHistoricalData(
    contract,
    endDateTime=end_time,
    durationStr='1 D',
    barSizeSetting='5 mins',
    whatToShow='TRADES',
    useRTH=True,
    formatDate=1
)

if not k_test:
    raise RuntimeError("❌ 无法获取 MSFT 的历史K线，说明账户权限可能不足或合约配置不正确")
print("✅ 合约验证通过，开始抓取 Tick 数据")

# === 创建保存路径 ===
os.makedirs('output_V4/us', exist_ok=True)
all_ticks = []
cur_time = end_time
print(f"开始抓取 {contract.symbol} Tick 数据，从 {start_time} 到 {end_time}（美东时间）")

# === 滑窗抓取（向前，每次最多1000条） ===
while cur_time > start_time:
    ticks = ib.reqHistoricalTicks(
        contract,
        startDateTime=start_time,
        endDateTime=cur_time,
        numberOfTicks=1000,
        whatToShow='Last',
        useRth=True,
        ignoreSize=False
    )

    if not ticks:
        print(f"⚠️ 在 {cur_time} 没有返回数据，提前终止")
        break

    rows = [{'时间': t.time, '价格': t.price, '数量': t.size} for t in ticks]
    all_ticks = rows + all_ticks

    cur_time = ticks[0].time - timedelta(milliseconds=1)
    print(f"✅ 抓取到 {len(ticks)} 条，滑至 {cur_time}")
    time.sleep(0.5)

# === 构建 DataFrame 并保存 ===
df = pd.DataFrame(all_ticks)
df.to_csv('output_V4/us/MSFT_tick_full.csv', index=False)
print("✅ Tick 数据抓取完成，保存至 output_V4/us/MSFT_tick_full.csv")

ib.disconnect()
