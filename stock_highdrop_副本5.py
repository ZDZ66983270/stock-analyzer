import yfinance as yf
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# 设置字体以防止编码问题
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']  # 或其他可用的字体
plt.rcParams['axes.unicode_minus'] = False  # 修复负号显示问题

class StockAnalyzerApp:
    def __init__(self):
        self.page_number = 0
        self.period_df = None
        self.stock_code = ""

    def analyze_stock(self, stock, begin_date=None, end_date=None):
        self.stock_code = stock  # 存储股票代码以供绘图使用

        # 设置默认开始日期为今年年初，结束日期为今天
        if begin_date is None:
            begin_date = f"{datetime.now().year}-01-01"
        if end_date is None:
            end_date = pd.to_datetime("today").strftime('%Y-%m-%d')

        # 下载股票数据以确保价格数据完整
        data = yf.download(stock, start=begin_date, end=end_date, actions='inline')[['Open', 'High', 'Low', 'Close']]
        
        # 如果数据有多重索引，将其展平
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # 检查是否成功下载所需的列
        required_columns = {'Open', 'High', 'Low', 'Close'}
        if not required_columns.issubset(data.columns):
            print(f"\nError: Data for {stock} is missing some required columns. Available columns: {data.columns}")
            return

        # 确保日期索引没有时区信息，并去除无效日期
        data.index = pd.to_datetime(data.index, errors='coerce').tz_localize(None)
        data = data.dropna(subset=['Low'])  # 删除 NaT 日期或 'Low' 列为空的行

        # 计算每一个历史新高
        historic_highs = []
        historic_high_dates = []
        highest_price = -float('inf')
        
        for date, row in data.iterrows():
            high = row['High']
            if high > highest_price:
                highest_price = high
                historic_highs.append(high)
                historic_high_dates.append(date)

        # 计算每段周期的最低值及下降百分比
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
                i + 1,  # 序号
                start_date.strftime('%Y-%m-%d'),  # 新高日期
                f"{historic_highs[i]:.2f}",  # 新高股价
                period_low_date.strftime('%Y-%m-%d'),  # 最大回调日期
                f"{period_low:.2f}",  # 周期最低价
                f"{decline_percentage:.2f}%",  # 回调幅度
                days_interval  # 间隔天数
            ])

        # 计算最后一个历史新高到结束日期的最低值及下降百分比
        last_high = historic_highs[-1]
        last_high_date = historic_high_dates[-1]
        end_date = pd.to_datetime(end_date)  # 确保 end_date 为 Timestamp 格式

        if last_high_date < end_date:
            final_period_data = data.loc[last_high_date:end_date]
            final_period_low = final_period_data['Low'].min()
            final_period_low_date = final_period_data['Low'].idxmin()
            final_decline_percentage = ((last_high - final_period_low) / last_high) * 100
            final_days_interval = (final_period_low_date - last_high_date).days

            # 添加最后一段数据
            period_data.append([
                len(historic_high_dates),  # 序号
                last_high_date.strftime('%Y-%m-%d'),  # 新高日期
                f"{last_high:.2f}",  # 新高股价
                final_period_low_date.strftime('%Y-%m-%d'),  # 最大回调日期
                f"{final_period_low:.2f}",  # 周期最低价
                f"{final_decline_percentage:.2f}%",  # 回调幅度
                final_days_interval  # 间隔天数
            ])

        # 将数据转换为 DataFrame
        columns = ["序号", "新高日期", "新高股价", "最大回调日期", "周期最低价", "回调幅度", "间隔天数"]
        self.period_df = pd.DataFrame(period_data, columns=columns)

        # 输出表格
        print("\n周期回调数据:")
        print(self.period_df)

        # 保存为 CSV 文件
        begin_date_str = pd.to_datetime(begin_date).strftime('%Y%m%d')
        end_date_str = pd.to_datetime(end_date).strftime('%Y%m%d')
        filename = f"{stock}_{begin_date_str}_to_{end_date_str}.csv"  # 使用 YYYYMMDD 格式
        self.period_df.to_csv(filename, index=False, encoding='utf-8-sig')  # 保存为 CSV 文件
        print(f"\n数据已保存为: {filename}")

        # 绘制柱状图
        self.plot_data()

    def plot_data(self):
        # 分页逻辑
        total_rows = len(self.period_df)
        total_pages = (total_rows + 9) // 10  # 每页 10 个柱子

        fig, ax = plt.subplots(figsize=(12, 6))

        def update_plot():
            # 清空当前图形
            ax.clear()
            start_index = self.page_number * 10
            end_index = min(start_index + 10, total_rows)
            page_data = self.period_df.iloc[start_index:end_index]

            # 创建日期和价格列表
            high_dates = pd.to_datetime(page_data['新高日期']).tolist()  # 确保日期为 datetime 对象
            low_dates = pd.to_datetime(page_data['最大回调日期']).tolist()  # 确保日期为 datetime 对象
            high_prices = page_data['新高股价'].astype(float).tolist()  # 新高股价
            low_prices = page_data['周期最低价'].astype(float).tolist()  # 周期最低价

            # 计算柱子的位置
            x = range(len(page_data))
            width = 0.4  # 每个柱子的宽度

            # 绘制柱状图
            bars1 = ax.bar([p - width / 2 for p in x], high_prices, width=width, color='red', label='New High')
            bars2 = ax.bar([p + width / 2 for p in x], low_prices, width=width, color='green', label='Pullback')

            # 添加标签
            for bar, price, date in zip(bars1, high_prices, high_dates):
                ax.annotate(f"{price:.2f}", xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                            ha='center', va='bottom')
                ax.annotate(date.strftime('%y%m%d'), xy=(bar.get_x() + bar.get_width() / 2, 0), 
                            ha='center', va='top')

            for i, (bar, price) in enumerate(zip(bars2, low_prices)):
                ax.annotate(f"{price:.2f}", xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                            ha='center', va='bottom')
                # 只在绿色柱子上显示回调百分比
                ax.annotate(f"{page_data.iloc[i]['回调幅度']}", 
                            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height() / 2), 
                            ha='center', va='center', color='yellow', fontsize=12, fontweight='bold')  # 黄色并加粗

            ax.set_xlabel('Date (yymmdd)')
            ax.set_ylabel('Stock Price')
            plt.title(f"{self.stock_code} New High and Pullback Analysis (Page {self.page_number + 1})")
            ax.set_xticks([p for p in x])  # 设置 x 轴刻度仅显示新高日期
            ax.set_xticklabels([])  # 不显示任何文字
            plt.xticks(rotation=45)  # 旋转 x 轴标签
            plt.tight_layout()  # 自动调整布局
            
            # 添加翻页和关闭按钮
            ax_next = plt.axes([0.8, 0.01, 0.1, 0.05])  # 右下角用于下一页按钮
            ax_prev = plt.axes([0.7, 0.01, 0.1, 0.05])  # 右下角用于上一页按钮
            ax_close = plt.axes([0.9, 0.01, 0.1, 0.05])  # 右下角用于关闭按钮
            btn_next = Button(ax_next, 'Next')  # 使用英文
            btn_prev = Button(ax_prev, 'Prev')  # 使用英文
            btn_close = Button(ax_close, 'Close')  # 使用英文

            # 设置按钮的可见性
            btn_prev.set_active(self.page_number > 0)  # 第一页不显示上一页按钮
            btn_next.set_active(self.page_number < total_pages - 1)  # 最后一页不显示下一页按钮
            
            # 绑定按钮事件
            btn_next.on_clicked(self.next_page)
            btn_prev.on_clicked(self.prev_page)
            btn_close.on_clicked(self.close)

            plt.show()

        update_plot()  # 绘制初始图形

    def next_page(self, event):
        if (self.page_number + 1) * 10 < len(self.period_df):
            self.page_number += 1
            self.plot_data()

    def prev_page(self, event):
        if self.page_number > 0:
            self.page_number -= 1
            self.plot_data()

    def close(self, event):
        plt.close('all')

# 使用示例
if __name__ == "__main__":
    stock_code = input("请输入股票代码：")
    begin_date = input("请输入开始日期 (格式: YYYY-MM-DD，默认本年初): ") or None
    end_date = input("请输入结束日期 (格式: YYYY-MM-DD，默认今天): ") or None

    analyzer = StockAnalyzerApp()
    analyzer.analyze_stock(stock_code, begin_date, end_date)
