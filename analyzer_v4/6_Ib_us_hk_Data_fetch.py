# 批量获取多个股票多个周期K线，并保存为 Excel 文件（分Sheet）
from ib_insync import *
import pandas as pd
import os
import time
from ib_insync import Contract

# === 参数设置 ===
symbols = [
    ('AAPL', 'SMART', 'USD'),    # 苹果公司
]
barsizes = ['1 min', '5 mins', '15 mins', '30 mins', '1 hour', '1 day']
duration_map = {
    '1 min': '1 D',    # 1天
    '5 mins': '1 D',
    '15 mins': '2 D',
    '30 mins': '5 D',
    '1 hour': '7 D',
    '1 day': '5 Y',  # 5年
}

# === 创建输出目录 ===
os.makedirs('output_V4/us', exist_ok=True)

# === 连接 IB 本地 TWS / Gateway ===
ib = IB()
try:
    print("正在连接IB TWS...")
    print("请确保：")
    print("1. TWS已打开")
    print("2. 已启用API连接")
    print("3. 端口7497已开放")
    print("4. 127.0.0.1已添加到信任IP列表")
    ib.connect('127.0.0.1', 7497, clientId=1)
    print("连接成功！")
except Exception as e:
    print(f"连接失败：{str(e)}")
    print("请检查：")
    print("1. TWS是否已打开")
    print("2. TWS中是否已启用API连接（File -> Global Configuration -> API -> Enable ActiveX and Socket Clients）")
    print("3. 端口号是否正确（TWS默认7497，Gateway默认7497）")
    print("4. 是否已添加127.0.0.1到信任IP列表")
    exit(1)

# === 批量处理每个合约多个周期 ===
for sym, exch, ccy in symbols:
    contract = Stock(sym, exch, ccy)
    excel_path = os.path.join('output_V4/us', f'{sym}_multi_period.xlsx')
    with pd.ExcelWriter(excel_path) as writer:
        for bar_size in barsizes:
            duration = duration_map.get(bar_size, '3 D')
            try:
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
                    for col in df.select_dtypes(include=['datetimetz']).columns:
                        df[col] = df[col].dt.tz_localize(None)
                    df.to_excel(writer, sheet_name=bar_size.replace(' ', ''), index=False)
                    print(f"✅ {sym} {bar_size} 下载成功")
                else:
                    print(f"⚠️ {sym} {bar_size} 无数据返回，请检查行情权限或市场开盘状态")
            except Exception as e:
                print(f"❌ {sym} {bar_size} 下载失败：{str(e)}")
            time.sleep(1)

ib.disconnect()
print("程序执行完毕！")
