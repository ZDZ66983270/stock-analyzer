import pandas as pd
import yfinance as yf
from datetime import datetime

def analyze_stock_price(stock_symbol):
    # 获取过去12个月的股价数据
    stock_data = yf.download(stock_symbol, period='1y', interval='1d')
    
    if stock_data.empty:
        print(f"{stock_symbol} 没有可用的数据。")
        return

    # 按月重采样并获取每月最后一天的收盘价
    monthly_close = stock_data['Close'].resample('M').last()

    # 确保 monthly_close 是一个 Series，避免出现 DataFrame 的情况
    if isinstance(monthly_close, pd.DataFrame):
        monthly_close = monthly_close.squeeze()

    # 对收盘价进行排序
    sorted_monthly_close = monthly_close.sort_values(ascending=False)
    
    # 输出结果
    print(f"{stock_symbol} 的每月收盘价排序（从高到低）：")
    for month, price in sorted_monthly_close.items():
        print(f"{month.strftime('%Y-%m')}: {price:.2f}")

# 用户输入股票代码
stock_symbol_input = input("请输入股票代码（例如：AAPL）：")
analyze_stock_price(stock_symbol_input.upper())
