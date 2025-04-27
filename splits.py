import pandas as pd
import yfinance as yf

def get_stock_splits(symbol):
    stock = yf.Ticker(symbol)
    splits = stock.splits  # 获取送股记录
    return splits

# 用户输入股票代码
stock_symbol = input("请输入股票代码：")
splits = get_stock_splits(stock_symbol)

# 输出送股记录
if splits.empty:
    print(f"{stock_symbol} 没有送股记录。")
else:
    print(f"{stock_symbol} 送股记录：")
    for date, ratio in splits.items():
        print(f"日期: {date.date()}, 送股比例: {ratio}")
