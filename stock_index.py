import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from matplotlib.widgets import Button
from matplotlib.dates import DayLocator, DateFormatter
from datetime import datetime

# 用户输入股票代码和时间段
stock_symbols = input("请输入股票代码（用空格分隔，例如：AAPL MSFT）: ").upper().split()
start_date = input("请输入开始日期（格式：YYYY-MM-DD，留空则默认 2024-01-01）: ")
end_date = input("请输入结束日期（格式：YYYY-MM-DD，留空则默认今天）: ")
compare_indices = input("是否需要对比三大指数（默认为显示，输入'n'则不显示）: ").lower() != 'n'

# 设置默认日期
if not start_date:
    start_date = "2024-01-01"
if not end_date:
    end_date = datetime.today().strftime('%Y-%m-%d')

# 根据用户选择添加指数
tickers = stock_symbols
if compare_indices:
    tickers += ["^GSPC", "^NDX", "^DJI"]

# 下载数据（以日为单位）
data = yf.download(tickers, start=start_date, end=end_date, interval="1d")

# 检查数据是否成功下载
if data.empty:
    print("未能成功下载数据，请检查输入的股票代码和日期范围。")
    exit()

# 检查数据格式并选择调整后的收盘价
if isinstance(data, pd.DataFrame) and 'Adj Close' in data.columns:
    data = data['Adj Close']  # 选择调整后的收盘价
else:
    print("未能获取调整后的收盘价数据，请检查输入的股票代码和日期范围。")
    exit()

# 计算起始日期的基准并转换为百分比变化
def calculate_change_from_start(df):
    start_value = df.iloc[0]  # 取得起始值
    return (df / start_value - 1) * 100  # 累积涨跌幅

# 生成每个股票/指数的累计涨跌幅
results = {}
for ticker in data.columns:
    results[ticker] = calculate_change_from_start(data[ticker])

# 将结果转化为DataFrame
results_df = pd.DataFrame(results)

# 设置系统默认字体以确保中文显示
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

# 为每个指数指定不同的颜色和线条粗细
colors = {symbol: 'blue' for symbol in stock_symbols}
line_widths = {symbol: 2.5 for symbol in stock_symbols}  # 用户股票使用较粗的线

# 设置指数的颜色和线宽
if compare_indices:
    colors.update({
        "^GSPC": 'green',
        "^NDX": 'purple',
        "^DJI": 'orange'
    })
    line_widths.update({
        "^GSPC": 1.5,
        "^NDX": 1.5,
        "^DJI": 1.5
    })

# 绘制折线图
fig, ax = plt.subplots(figsize=(12, 6))
for ticker in results_df.columns:
    ax.plot(results_df.index, results_df[ticker], label=ticker, marker='o', color=colors[ticker], linewidth=line_widths[ticker])

    # 在折线末端标注股票名称和当前变化百分比
    end_value = results_df[ticker].iloc[-1]
    ax.text(results_df.index[-1], end_value, f"{ticker} Now: {end_value:.2f}%", ha='left', color=colors[ticker])

# 设置图表属性
ax.set_xlabel("时间（按日）")
ax.set_ylabel("变化幅度（%）")
ax.set_title("股票与指数比较")
ax.axhline(0, color='gray', linewidth=0.5)
ax.legend(loc="upper left")
ax.grid()

# 调整X轴为日刻度
ax.xaxis.set_major_locator(DayLocator(interval=5))  # 每5天显示一个主刻度
ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

# 创建关闭按钮
ax_close = plt.axes([0.9, 0.05, 0.08, 0.05])
button_close = Button(ax_close, 'Close')
button_close.on_clicked(lambda event: plt.close(fig))

plt.show()

# 输出表格
print("变化幅度对比结果表格：")
print(results_df)
