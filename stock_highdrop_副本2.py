import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import yfinance as yf
import os
from datetime import datetime

# 获取用户输入的股票代码、起始日期和周期长度
stock_symbol = input("请输入股票代码: ")
start_date = input("请输入开始日期（格式：YYYY-MM-DD，留空则默认 2024-01-01）: ")
end_date = input("请输入结束日期（格式：YYYY-MM-DD，留空则默认今天）: ")
period_length = input("请输入周期长度（天数，默认为5）: ")

# 如果用户没有输入周期长度，则默认为5天
if not period_length:
    period_length = 5
else:
    period_length = int(period_length)

# 如果用户没有输入开始日期，则默认为2024年01月01日
if not start_date:
    start_date = "2024-01-01"
    print(f"开始日期默认设置为：{start_date}")

# 如果用户没有输入结束日期，则默认为今天
if not end_date:
    end_date = datetime.today().strftime('%Y-%m-%d')
    print(f"结束日期默认设置为今天：{end_date}")

# 打印出用于下载的日期，确认日期格式正确
print(f"正在下载股票数据：{stock_symbol}，从 {start_date} 到 {end_date}")

# 下载股票数据并保存到本地
try:
    data = yf.download(stock_symbol, start=start_date, end=end_date)
    if data.empty:
        raise ValueError(f"无法下载股票数据 {stock_symbol}，请检查股票代码和日期范围。")
    csv_filename = f"{stock_symbol}_data.csv"
    data.to_csv(csv_filename)
except Exception as e:
    print(f"下载数据失败: {e}")
    exit()

# 将日期列转换为datetime并移除时区信息
data['Date'] = pd.to_datetime(data.index).tz_localize(None)

# 初始化变量
historic_high = None
historic_high_date = None
results = []

# 遍历数据，查找历史新高和周期内最低价
for i in range(1, len(data)):
    current_high = data['High'].iloc[i]
    previous_high = data['High'].iloc[i - 1]

    # 确定历史新高
    if historic_high is None or current_high > historic_high:
        historic_high = current_high
        historic_high_date = data['Date'].iloc[i]

        # 获取周期内的低价
        lows = data['Low'].iloc[i:i + period_length]
        period_low = lows.min()

        # 存储结果
        results.append({
            'date': historic_high_date,
            'historic_high': historic_high,
            'period_low': period_low,
            'drop_rate': round(((period_low - historic_high) / historic_high) * 100, 1)  # 保留1位小数
        })

# 检查结果是否为空
if not results:
    print(f"在 {stock_symbol} 的数据中未找到符合条件的历史新高。")
    exit()

# 转换结果为DataFrame
results_df = pd.DataFrame(results)

# 计算平均和中位数下降百分比
droprate_average = results_df['drop_rate'].mean()
droprate_median = results_df['drop_rate'].median()

# 每页显示的结果数量
results_per_page = 10
total_pages = (len(results_df) + results_per_page - 1) // results_per_page

# 初始化当前页
current_page = 0

# 创建图形和按钮在同一窗口内的布局
fig, ax = plt.subplots(figsize=(12, 6))
plt.subplots_adjust(bottom=0.25)

# 绘制函数
def plot_results(page):
    ax.clear()
    start_idx = page * results_per_page
    end_idx = start_idx + results_per_page
    current_results = results_df.iloc[start_idx:end_idx]

    x = range(len(current_results))
    historic_high_list = current_results['historic_high'].tolist()
    period_low_list = current_results['period_low'].tolist()

    x_positions = [p + 0.4 for p in x]
    bar_width = 0.4

    ax.bar(x, list(map(float, historic_high_list)), color='#A52A2A', width=bar_width, label='Historic High', align='center')
    ax.bar(x_positions, list(map(float, period_low_list)), color='#1c7731', width=bar_width, label=f'{period_length} Days Low', align='center')

    for i in range(len(x)):
        ax.text(i, historic_high_list[i], f"{historic_high_list[i]:.2f}", ha='center', va='bottom')
        ax.text(i + 0.4, period_low_list[i], f"{period_low_list[i]:.2f}", ha='center', va='bottom')

        drop_rate_y_position = period_low_list[i] / 2
        ax.text(i + 0.4, drop_rate_y_position, f"{current_results['drop_rate'].iloc[i]:.1f}%", ha='center', color='white', fontsize=10, fontweight='bold')

    ax.set_xticks([p + 0.2 for p in x])
    ax.set_xticklabels(current_results['date'].dt.strftime('%m-%d'))
    ax.set_title(f'Historic High and {period_length} Days Low for {stock_symbol.upper()} - Page {page + 1}/{total_pages}')
    ax.set_ylabel('Price')

    # 显示droprate_average和droprate_median
    ax.text(0, -max(max(historic_high_list), max(period_low_list)) * 0.1, 
            f'Drop Rate Average: {droprate_average:.1f}%', ha='left', va='top', fontsize=12, color='blue')
    ax.text(0, -max(max(historic_high_list), max(period_low_list)) * 0.15, 
            f'Drop Rate Median: {droprate_median:.1f}%', ha='left', va='top', fontsize=12, color='blue')

    # 显示日期范围，放在关闭按钮上方，并向右移动
    ax.text(10, -max(max(historic_high_list), max(period_low_list)) * 0.1, 
            f'Date Range: {start_date} to {end_date}', ha='right', va='top', fontsize=12, color='blue')

    ax.legend()
    plt.draw()

# 初始化第一页结果的绘制
plot_results(current_page)

# 按钮控制翻页
def next_page(event):
    global current_page
    if current_page < total_pages - 1:
        current_page += 1
        plot_results(current_page)
    else:
        print("已到达最后一页。")
    update_buttons()

def prev_page(event):
    global current_page
    if current_page > 0:
        current_page -= 1
        plot_results(current_page)
    else:
        print("已经是第一页。")
    update_buttons()

def close_program(event):
    print("程序即将结束。")
    plt.close()

def update_buttons():
    if current_page == 0:
        btn_prev.ax.set_visible(False)
    else:
        btn_prev.ax.set_visible(True)

    if current_page == total_pages - 1:
        btn_next.ax.set_visible(False)
    else:
        btn_next.ax.set_visible(True)

    plt.draw()

# 创建翻页按钮
ax_prev = plt.axes([0.1, 0.05, 0.1, 0.04])
btn_prev = Button(ax_prev, '←')
btn_prev.on_clicked(prev_page)

ax_next = plt.axes([0.2, 0.05, 0.1, 0.04])
btn_next = Button(ax_next, '→')
btn_next.on_clicked(next_page)

# 创建关闭按钮
ax_close = plt.axes([0.8, 0.05, 0.1, 0.04])
btn_close = Button(ax_close, 'Close')
btn_close.on_clicked(close_program)

# 初始化按钮状态
update_buttons()

# 显示图表
plt.show()

# 删除下载的本地数据文件
os.remove(csv_filename)
print("程序正常结束，文件已删除。")
