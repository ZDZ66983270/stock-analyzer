import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import yfinance as yf
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
for i in range(len(data)):
    current_high = data['High'].iloc[i].item()  # 使用 .item() 获取标量值

    # 更新历史新高
    if historic_high is None or (isinstance(historic_high, float) and current_high > historic_high):
        historic_high = float(current_high)  # 确保是标量值
        historic_high_date = data['Date'].iloc[i]

        # 查找下一个新高之前的最低价格
        period_data = data.iloc[i + 1:]  # 从当前高点之后的数据开始
        next_high_index = period_data[period_data['High'] > historic_high].index

        if not next_high_index.empty:
            # 找到下一个新高
            next_high_date = period_data.loc[next_high_index[0]]['Date']
            # 查找两个新高之间的最低值
            period_low_series = period_data.loc[data.index[i + 1]:next_high_index[0]]['Low']
            if not period_low_series.empty:
                period_low = period_low_series.min()
                period_low_index = period_low_series.idxmin()

                # 确保 period_low_index 是单一的时间戳
                if isinstance(period_low_index, pd.Series):
                    period_low_index = period_low_index.iloc[0]

                # 获取 period_low 对应的日期
                period_low_date = data.loc[period_low_index]['Date'] if period_low_index in data.index else None

                # 强制将 period_low 转为标量值
                period_low_value = float(period_low) if isinstance(period_low, (float, int)) else None

                # 计算降幅，确保使用标量值进行比较
                if period_low_value is not None and historic_high != 0:  # 避免除以零
                    drop_rate = round(((period_low_value - historic_high) / historic_high * 100), 1)
                else:
                    drop_rate = None

                # 确保 period_low_date 和 historic_high_date 是标量值
                if period_low_date is not None and isinstance(period_low_date, pd.Timestamp):
                    period_length = (period_low_date - historic_high_date).days
                else:
                    period_length = None

                # 保存结果
                results.append({
                    'date': historic_high_date,
                    'historic_high': historic_high,
                    'period_low': period_low_value if period_low_value is not None else float('nan'),  # 用 NaN 替代 None
                    'period_low_date': period_low_date,
                    'drop_rate': drop_rate,
                    'period_length': period_length
                })

# 转换结果为DataFrame
results_df = pd.DataFrame(results)

# 确保 drop_rate 列中的数据为数值类型，并去除无效数据
results_df['drop_rate'] = pd.to_numeric(results_df['drop_rate'], errors='coerce')

# 计算平均和中位数下降百分比
droprate_average = results_df['drop_rate'].mean() if results_df['drop_rate'].notna().any() else None
droprate_median = results_df['drop_rate'].median() if results_df['drop_rate'].notna().any() else None

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

    # 设置柱宽和位置
    bar_width = 0.2  # 红色柱体宽度
    x_positions = [p + bar_width for p in x]  # 绿色柱体的位置向右偏移

    ax.bar(x, historic_high_list, color='red', width=bar_width, label='Historic High', align='center')
    ax.bar(x_positions, period_low_list, color='green', width=bar_width, label='Period Low', align='center')

    for i in range(len(x)):
        ax.text(i, historic_high_list[i], f"{historic_high_list[i]:.2f}", ha='center', va='bottom')
        if pd.notna(period_low_list[i]):  # 确保是标量值
            ax.text(i + bar_width, period_low_list[i], f"{period_low_list[i]:.2f}", ha='center', va='bottom')
            ax.text(i + bar_width, period_low_list[i] / 2, 'Callback', ha='center', color='white', fontsize=10, fontweight='bold')
            drop_rate_y_position = period_low_list[i] / 2
            ax.text(i + bar_width, drop_rate_y_position, f"{current_results['drop_rate'].iloc[i]:.1f}%", ha='center', color='white', fontsize=10, fontweight='bold')

    ax.set_xticks([p + bar_width / 2 for p in x])
    ax.set_xticklabels(current_results['date'].dt.strftime('%m-%d'))
    ax.set_title(f'Historic High and Period Low for {stock_symbol.upper()} - Page {page + 1}/{total_pages}')
    ax.set_ylabel('Price')
    
    average_text = f'Drop Rate Average: {droprate_average:.1f}%' if droprate_average is not None else 'Drop Rate Average: N/A'
    median_text = f'Drop Rate Median: {droprate_median:.1f}%' if droprate_median is not None else 'Drop Rate Median: N/A'
    
    ax.text(0, -max(max(historic_high_list), max(period_low_list)) * 0.1, average_text, ha='left', va='top', fontsize=12, color='blue')
    ax.text(0, -max(max(historic_high_list), max(period_low_list)) * 0.15, median_text, ha='left', va='top', fontsize=12, color='blue')
    
    # 显示Period Low数值
    for i in range(len(current_results)):
        if current_results['period_low'].iloc[i] is not None:
            ax.text(i + bar_width, current_results['period_low'].iloc[i], f"Period Low: {current_results['period_low'].iloc[i]:.2f}", ha='center', va='bottom', color='black')

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
    plt.close()

# 创建翻页按钮
ax_prev = plt.axes([0.1, 0.05, 0.1, 0.04])
btn_prev = Button(ax_prev, '◀️')
btn_prev.on_clicked(prev_page)

ax_next = plt.axes([0.2, 0.05, 0.1, 0.04])
btn_next = Button(ax_next, '▶️')
btn_next.on_clicked(next_page)

ax_close = plt.axes([0.8, 0.05, 0.1, 0.04])
btn_close = Button(ax_close, '❌')
btn_close.on_clicked(close_program)

plt.show()
