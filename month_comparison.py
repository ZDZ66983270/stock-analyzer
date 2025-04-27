import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import time

def fetch_data_with_retries(stock_symbol, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            stock_data = yf.download(stock_symbol, start=datetime.now().replace(year=datetime.now().year - 5), end=datetime.now(), timeout=10)
            if stock_data.empty:
                print(f"{stock_symbol} 没有可用的数据。")
            return stock_data
        except Exception as e:
            print(f"下载 {stock_symbol} 数据失败，尝试第 {attempt + 1} 次：{e}")
            time.sleep(delay)  # 等待一段时间再重试
    return None

def plot_monthly_stock_prices(stock_symbol):
    stock_data = fetch_data_with_retries(stock_symbol)

    if stock_data is None or stock_data.empty:
        print(f"{stock_symbol} 数据下载失败。")
        return

    # 提取每个月的收盘价
    monthly_close = stock_data['Close'].resample('M').last()

    # 获取年份和月份
    monthly_close.index = monthly_close.index.to_period('M')  # 将索引转化为周期格式
    years = monthly_close.index.year.unique()[-5:]  # 获取最近的五年

    # 指定颜色
    color_map = {
        years[0]: 'blue',
        years[1]: 'orange',
        years[2]: 'green',
        years[3]: 'red',
        years[4]: 'purple'
    }

    # 创建图表
    plt.figure(figsize=(12, 6))

    # 绘制每一年每月的收盘价
    for year in years:
        monthly_data = monthly_close[monthly_close.index.year == year]
        if not monthly_data.empty:
            plt.plot(monthly_data.index.month, monthly_data.values, label=str(year), color=color_map.get(year, 'gray'), alpha=0.7)
            plt.text(monthly_data.index.month[0], monthly_data.values[0], str(year), color=color_map[year], fontsize=10, verticalalignment='bottom', horizontalalignment='right')
            plt.text(monthly_data.index.month[-1], monthly_data.values[-1], str(year), color=color_map[year], fontsize=10, verticalalignment='bottom', horizontalalignment='left')

    # 设置图表属性
    plt.title(f'{stock_symbol} 过去5年每月股价变化', fontsize=14)
    plt.xlabel('月份', fontsize=12)
    plt.ylabel('股价', fontsize=12)
    plt.xticks(range(1, 13), ['1月', '2月', '3月', '4月', '5月', '6月', 
                               '7月', '8月', '9月', '10月', '11月', '12月'])
    plt.legend(title='年份', loc='upper left')
    plt.grid()

    # 显示图表
    plt.tight_layout()
    plt.show()

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 确保使用支持中文的字体

# 用户输入股票代码
stock_symbol_input = input("请输入股票代码（例如：AAPL）：")
plot_monthly_stock_prices(stock_symbol_input.upper())
