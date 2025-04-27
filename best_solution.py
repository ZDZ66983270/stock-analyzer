import yfinance as yf
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import os

# 设置字体
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False

class StockAnalyzerApp:
    def __init__(self):
        self.page_number = 0
        self.period_df = None
        self.stock_code = ""
        self.csv_filename = ""

    def analyze_stock(self, stock, begin_date=None, end_date=None):
        self.stock_code = stock

        # 默认开始日期为一年前，结束日期为今天
        if begin_date is None:
            begin_date = (datetime.now() - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = pd.to_datetime("today").strftime('%Y-%m-%d')

        # 下载股票数据
        try:
            data = yf.download(stock, start=begin_date, end=end_date, actions='inline')[['Open', 'High', 'Low', 'Close']]
        except Exception as e:
            print(f"Error downloading data: {e}")
            return

        # 数据清洗
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.index = pd.to_datetime(data.index, errors='coerce').tz_localize(None)
        data = data.dropna(subset=['Low'])

        # 历史新高数据
        historic_highs = []
        historic_high_dates = []
        highest_price = -float('inf')
        for date, row in data.iterrows():
            high = row['High']
            if high > highest_price:
                highest_price = high
                historic_highs.append(high)
                historic_high_dates.append(date)

        if not historic_highs:
            print(f"No historical highs found for {stock}.")
            return

        # 周期最低点及回调幅度
        period_data = []
        for i in range(len(historic_high_dates) - 1):
            start_date = historic_high_dates[i]
            next_high_date = historic_high_dates[i + 1]
            period_low_data = data.loc[start_date:next_high_date]
            period_low = period_low_data['Low'].min()
            period_low_date = period_low_data['Low'].idxmin()
            decline_percentage = ((historic_highs[i] - period_low) / historic_highs[i]) * 100
            days_interval = (period_low_date - start_date).days

            period_data.append([
                i + 1,
                start_date.strftime('%Y-%m-%d'),
                f"{historic_highs[i]:.2f}",
                period_low_date.strftime('%Y-%m-%d'),
                f"{period_low:.2f}",
                decline_percentage,
                days_interval
            ])

        # 最后一段数据
        last_high = historic_highs[-1]
        last_high_date = historic_high_dates[-1]
        end_date = pd.to_datetime(end_date)
        if last_high_date < end_date:
            final_period_data = data.loc[last_high_date:end_date]
            final_period_low = final_period_data['Low'].min()
            final_period_low_date = final_period_data['Low'].idxmin()
            final_decline_percentage = ((last_high - final_period_low) / last_high) * 100
            final_days_interval = (final_period_low_date - last_high_date).days

            period_data.append([
                len(historic_high_dates),
                last_high_date.strftime('%Y-%m-%d'),
                f"{last_high:.2f}",
                final_period_low_date.strftime('%Y-%m-%d'),
                f"{final_period_low:.2f}",
                final_decline_percentage,
                final_days_interval
            ])

        # 转换为 DataFrame
        columns = ["序号", "新高日期", "新高股价", "最大回调日期", "周期最低价", "回调幅度", "间隔天数"]
        self.period_df = pd.DataFrame(period_data, columns=columns)

        # 计算回调幅度中位数
        median_decline = self.period_df["回调幅度"].median()
        print(f"\n动态回调幅度中位数: {median_decline:.2f}%")

        # 输出表格
        print("\n周期回调数据:")
        print(self.period_df)

        # 保存为 CSV 文件
        begin_date_str = pd.to_datetime(begin_date).strftime('%Y%m%d')
        end_date_str = pd.to_datetime(end_date).strftime('%Y%m%d')
        self.csv_filename = f"{stock}_{begin_date_str}_to_{end_date_str}.csv"
        self.period_df.to_csv(self.csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存为: {self.csv_filename}")

    def plot_bar(self):
        # 绘制柱状图
        pass  # 此处省略以保持代码简洁

    def plot_line(self):
        # 绘制折线图
        pass  # 此处省略以保持代码简洁

    def next_page(self, event):
        pass  # 此处省略

    def prev_page(self, event):
        pass  # 此处省略

    def close(self, event):
        plt.close('all')

# 使用示例
if __name__ == "__main__":
    stock_code = input("请输入股票代码：")
    begin_date = input("请输入开始日期 (格式: YYYY-MM-DD，默认一年前): ") or None
    end_date = input("请输入结束日期 (格式: YYYY-MM-DD，默认今天): ") or None

    analyzer = StockAnalyzerApp()
    analyzer.analyze_stock(stock_code, begin_date, end_date)
