# 批量获取多个股票多个周期K线，并保存为 Excel 文件（分Sheet）
from ib_insync import *
import pandas as pd
import os

# === 参数设置 ===
symbols = [
    ('AAPL', 'SMART', 'USD'),    # 美股苹果
    ('TSM', 'SMART', 'USD'),     # 美股台积电
    ('9988', 'SEHK', 'HKD'),     # 港股阿里巴巴
]
barsizes = ['5 mins', '15 mins', '30 mins', '1 hour']
duration_map = {
    '5 mins': '1 D',
    '15 mins': '2 D',
    '30 mins': '5 D',
    '1 hour': '7 D',
}

# === 创建输出目录 ===
os.makedirs('output_V4/us', exist_ok=True)

# === 连接 IB 本地 TWS / Gateway ===
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# === 批量处理每个合约多个周期 ===
for sym, exch, ccy in symbols:
    contract = Stock(sym, exch, ccy)
    excel_path = os.path.join('output_V4/us', f'{sym}_multi_period.xlsx')
    with pd.ExcelWriter(excel_path) as writer:
        for bar_size in barsizes:
            duration = duration_map.get(bar_size, '3 D')
            bars = ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )

            if bars:
                df = util.df(bars)
                df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
                df.rename(columns={'date': '时间', 'open': '开盘', 'high': '最高', 'low': '最低', 'close': '收盘', 'volume': '成交量'}, inplace=True)
                df.to_excel(writer, sheet_name=bar_size.replace(' ', ''), index=False)
                print(f"✅ {sym} {bar_size} 下载成功")
            else:
                print(f"⚠️ {sym} {bar_size} 无数据返回，请检查行情权限或市场开盘状态")

ib.disconnect()
