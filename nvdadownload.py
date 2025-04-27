import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

def fetch_data(symbol, start_date, end_date):
    nvda_data = yf.download(symbol, start=start_date, end=end_date)
    return nvda_data

def save_to_csv(data, filename):
    data.to_csv(filename)

# 主程序
if __name__ == "__main__":
    symbol = 'NVDA'
    start_date = '2024-06-10'
    end_date = '2024-10-23'  # 修改为10月23日
    
    nvda_data = fetch_data(symbol, start_date, end_date)
    
    print(nvda_data)  # 打印整个数据集

    # 保存数据到 CSV 文件
    save_to_csv(nvda_data, f'{symbol}_data.csv')
    print(f'Data saved to {symbol}_data.csv')
