import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import yfinance as yf
import os
from datetime import datetime

# 获取用户输入的股票代码、开始日期和结束日期
stock_symbol = input("请输入股票代码: ")
start_date = input("请输入开始日期（格式：YYYY-MM-DD，留空则默认 2024-01-01）: ") or "2024-01-01"
end_date = input("请输入结束日期（格式：YYYY-MM-DD，留空则默认今天）: ") or datetime.today().strftime('%Y-%m-%d')

# 下载股票数据
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
period_lengths = []

# 遍历数据，查找历史新高和周期内最低价
for i in range(len(data)):
    current_high = data['High'].iloc[i]

    if historic_high is None or current_high > historic_high:
        if historic_high is not None:
            # 记录前一个历史新高的相关信息
            period_low = data['Low'].iloc[historic_high_index + 1:i].min()
            period_length = i - historic_high_index - 1
            period_lengths.append(period_length)

            # 保存结果
            results.append({
                'date': historic_high_date,
                'historic_high': historic_high,
                'period_low': period_low,
                'period_length': period_length
            })

        # 更新历史新高
        historic_high = current_high
        historic_high_date = data['Date'].iloc[i]
        historic_high_index = i

# 处理最后一个历史新高
if historic_high_index is not None and historic_high_index + 1 < len(data):
    period_low = data['Low'].iloc[historic_high_index + 1:].min()
    period_length = len(data) - historic_high_index - 1
    period_lengths.append(period_length)
    results.append({
        'date': historic_high_date,
        'historic_high': historic_high,
        'period_low': period_low,
        'period_length': period_length
    })

# 转换结果为DataFrame
results_df = pd.DataFrame(results)

# 计算平均和中位数的周期长度
average_period_length = sum(period_lengths) / len(period_lengths) if period_lengths else 0
median_period_length = pd.Series(period_lengths).median() if period_lengths else 0

# 每页显示的结果数量
results_per_page = 10
total_pages = (len(results_df) + results_per_page - 1) // results_per_page
current_page = 0  # 初始化当前页

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

    ax.bar(x, historic_high_list, color='#A52A2A', label='Historic High', align='center')
    ax.bar([p + 0.4 for p in x], period_low_list, color='#1c7731', label='Period Low', align='center')

    for i in range(len(x)):
        ax.text(i, historic_high_list[i], f"{historic_high_list[i]:.2f}", ha='center', va='bottom')
        ax.text(i + 0.4, period_low_list[i], f"{period_low_list[i]:.2f}", ha='center', va='bottom')

    ax.set_xticks([p + 0.2 for p in x])
    ax.set_xticklabels(current_results['date'].dt.strftime('%m-%d'))
    ax.set_title(f'Historic High and Period Low for {stock_symbol.upper()} - Page {page + 1}/{total_pages}')
    ax.set_ylabel('Price')
    ax.text(0, -max(max(historic_high_list), max(period_low_list)) * 0.1,
            f'Average Period Length: {average_period_length:.1f} days', ha='left', va='top', fontsize=12, color='blue')
    ax.text(0, -max(max(historic_high_list), max(period_low_list)) * 0.15,
            f'Median Period Length: {median_period_length:.1f} days', ha='left', va='top', fontsize=12, color='blue')
    ax.legend()
    plt.draw()

# 初始化第一页结果的绘制
plot_results(current_page)

# 翻页按钮功能
def next_page(event):
    global current_page
    if current_page < total_pages - 1:
        current_page += 1
        plot_results(current_page)

def prev_page(event):
    global current_page
    if current_page > 0:
        current_page -= 1
        plot_results(current_page)

def close_program(event):
    print("程序即将结束。")
    plt.close()

# 创建翻页按钮（用图标替代文字）
ax_prev = plt.axes([0.1, 0.05, 0.1, 0.04])
btn_prev = Button(ax_prev, '◀️')  # 左箭头图标
btn_prev.on_clicked(prev_page)

ax_next = plt.axes([0.2, 0.05, 0.1, 0.04])
btn_next = Button(ax_next, '▶️')  # 右箭头图标
btn_next.on_clicked(next_page)

ax_close = plt.axes([0.8, 0.05, 0.1, 0.04])
btn_close = Button(ax_close, '❌')  # 关闭图标
btn_close.on_clicked(close_program)

plt.show()

# 程序结束时删除下载的本地数据文件
os.remove(csv_filename)
print("程序正常结束，文件已删除。")
