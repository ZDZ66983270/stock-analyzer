import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from datetime import datetime, timedelta
import os


def format_date(input_date):
    """格式化用户输入日期为标准的 YYYY-MM-DD 格式"""
    try:
        return datetime.strptime(input_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        print("输入的日期格式无效，请使用 YYYY-M-D 格式（例如 2024-1-1）。")
        return None


def display_stock_and_options(stock, start_date=None, end_date=None, options_info=None):
    today = datetime.now()
    if not start_date:
        start_date = (today - timedelta(days=6 * 30)).replace(day=1).strftime('%Y-%m-%d')  # 默认6个月前的月初
    if not end_date:
        end_date = today.strftime('%Y-%m-%d')

    # 下载股票数据
    print(f"正在下载股票数据: {stock} 从 {start_date} 到 {end_date}")
    try:
        stock_data = yf.download(stock, start=start_date, end=end_date)
    except Exception as e:
        print(f"无法获取股票数据: {e}")
        return

    if stock_data.empty:
        print("无法获取股票数据。请检查股票代码或网络连接。")
        return

    # 获取股票价格
    current_price = float(stock_data['Close'].iloc[-1])  # 确保转换为浮点数
    print(f"股票数据获取成功！")
    print(f"当前股价为: {current_price:.2f}")

    # 获取期权数据
    options_data = {}
    temp_files = []  # 用于存储临时文件路径
    for option in options_info:
        strike = option['strike']
        expiration = option['expiration']
        print(f"正在获取期权链: {stock} 到期日期 {expiration}，行权价 {strike}")
        ticker = yf.Ticker(stock)
        if expiration not in ticker.options:
            print(f"无效的到期日期: {expiration}。可用到期日期为: {ticker.options}")
            continue

        option_chain = ticker.option_chain(expiration)
        selected_options = option_chain.calls if option['type'].lower() == 'call' else option_chain.puts
        option_row = selected_options[selected_options['strike'] == strike]
        if option_row.empty:
            print(f"未找到行权价为 {strike} 的期权数据。")
            continue

        symbol = option_row['contractSymbol'].values[0]
        print(f"正在下载期权数据: {symbol}")
        data = yf.download(symbol, start=start_date, end=end_date)
        if not data.empty:
            csv_filename = f"temp_{symbol}.csv"
            data.to_csv(csv_filename, index=True)  # 保存为临时 CSV 文件
            temp_files.append(csv_filename)  # 添加到临时文件列表
            options_data[f"{symbol} ({strike}, {expiration})"] = data['Close']
        else:
            print(f"无数据: {symbol}")

    if not options_data:
        print("期权数据获取失败，无法绘制图表。")
        return

    # 绘图
    fig, ax1 = plt.subplots(figsize=(14, 7))
    lines = {}

    # 股票价格绘图
    lines['stock'], = ax1.plot(stock_data.index, stock_data['Close'], label=f"{stock} Close Price", color='blue', linewidth=2)
    ax1.set_ylabel(f"{stock} Price", fontsize=12, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # 标注正股价格末端
    last_date = stock_data.index[-1]
    last_price = stock_data['Close'].iloc[-1]
    ax1.text(last_date, float(last_price), f"{float(last_price):.2f}", color='blue', fontsize=10, ha='left', va='center')

    # 期权价格绘图
    ax2 = ax1.twinx()
    colors = ['green', 'orange', 'purple', 'red', 'brown']
    for i, (label, data) in enumerate(options_data.items()):
        lines[label], = ax2.plot(data.index, data, label=label, color=colors[i % len(colors)])
        # 标注期权价格末端
        last_date = data.index[-1]
        last_price = data.iloc[-1]
        ax2.text(last_date, float(last_price), f"{float(last_price):.2f}", color=colors[i % len(colors)], fontsize=10, ha='left', va='center')

    ax2.set_ylabel("Option Price", fontsize=12)
    ax2.tick_params(axis='y')

    # 添加图例
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

    # 按钮用于显示/隐藏曲线
    ax_button_stock = plt.axes([0.7, 0.02, 0.1, 0.04])
    btn_stock = Button(ax_button_stock, 'Toggle Stock')

    buttons = []
    for i, label in enumerate(options_data.keys()):
        ax_button = plt.axes([0.1 + i * 0.2, 0.02, 0.1, 0.04])
        btn = Button(ax_button, f"Toggle {label[:10]}")
        buttons.append((btn, label))

    def toggle_line(event, line_key):
        line = lines[line_key]
        line.set_visible(not line.get_visible())
        fig.canvas.draw()

    btn_stock.on_clicked(lambda event: toggle_line(event, 'stock'))
    for btn, label in buttons:
        btn.on_clicked(lambda event, label=label: toggle_line(event, label))

    plt.title(f"{stock} vs Options")
    plt.show()

    # 删除临时文件
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"已删除临时文件: {temp_file}")


# 示例运行
if __name__ == "__main__":
    stock_code = input("请输入股票代码：")
    start_date = input("请输入开始日期 (YYYY-M-D，默认6个月前的月初)：")
    if start_date:
        start_date = format_date(start_date)
    end_date = input("请输入结束日期 (YYYY-M-D，默认今天)：")
    if end_date:
        end_date = format_date(end_date)

    options_info = []
    while True:
        print("\n请输入期权信息（行权价、到期日期、类型）。")
        strike = float(input("行权价（例如 140.0）："))
        expiration = input("到期日期 (YYYY-M-D)：")
        expiration = format_date(expiration)
        option_type = input("期权类型（Call/Put，默认Call）：") or "Call"
        options_info.append({'strike': strike, 'expiration': expiration, 'type': option_type})
        cont = input("是否继续输入更多期权？（Y/N，默认N）：") or "N"
        if cont.lower() != 'y':
            break

    display_stock_and_options(stock_code, start_date, end_date, options_info)
