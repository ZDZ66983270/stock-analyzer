import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from matplotlib.dates import MonthLocator, DateFormatter

# 用户输入需要分析的年份
years_to_analyze = int(input("请输入需要分析的年份数（例如，5表示分析从2024年到2020年）："))

# 设置要分析的年份
current_year = 2024
start_year = current_year - years_to_analyze + 1

# 选定的大选年份及其党派和控制情况
election_years = {
    2000: ('Democratic', 'Bill Clinton', False),
    2004: ('Republican', 'George W. Bush', True),
    2008: ('Democratic', 'Barack Obama', False),
    2012: ('Democratic', 'Barack Obama', False),
    2016: ('Republican', 'Donald Trump', True),
    2020: ('Democratic', 'Joe Biden', False),
    2024: ('Unknown', 'Not Yet Elected', False)  # 2024年尚未进行大选
}

# 符合条件的年份（总统、参议院和众议院都属于共和党）
years_republican_control = [year for year, (party, president, full_control) in election_years.items()
                            if full_control and start_year <= year <= current_year]

# 创建图表
plt.figure(figsize=(14, 8))

# 循环绘制S&P 500, 上证指数和恒生指数在符合条件的年份的数据
for year in years_republican_control:
    start_date = f"{year}-11-01"
    end_date = f"{year + 1}-10-31"
    
    # 下载S&P 500 (^GSPC)，上证指数 (000001.SS)，恒生指数 (^HSI)
    try:
        sp500_data = yf.download('^GSPC', start=start_date, end=end_date)
        shanghai_data = yf.download('000001.SS', start=start_date, end=end_date)
        hang_seng_data = yf.download('^HSI', start=start_date, end=end_date)
    except Exception as e:
        print(f"无法下载{year}年的某些指数数据，请检查股票代码和日期范围。")
        continue

    # 检查数据是否下载成功
    if sp500_data.empty or shanghai_data.empty or hang_seng_data.empty:
        print(f"无法下载{year}年的某些指数数据，请检查股票代码和日期范围。")
        continue

    # 归一化数据（将起始点调整为100）
    sp500_normalized = sp500_data['Adj Close'] / sp500_data['Adj Close'].iloc[0] * 100
    shanghai_normalized = shanghai_data['Adj Close'] / shanghai_data['Adj Close'].iloc[0] * 100
    hang_seng_normalized = hang_seng_data['Adj Close'] / hang_seng_data['Adj Close'].iloc[0] * 100

    # 将日期索引映射到通用年份（例如2000年），便于从11月到次年10月显示
    sp500_data.index = sp500_data.index.map(lambda date: date.replace(year=2000 if date.month >= 11 else 2001))
    shanghai_data.index = shanghai_data.index.map(lambda date: date.replace(year=2000 if date.month >= 11 else 2001))
    hang_seng_data.index = hang_seng_data.index.map(lambda date: date.replace(year=2000 if date.month >= 11 else 2001))

    # 绘制S&P 500
    plt.plot(sp500_data.index, sp500_normalized, label=f"S&P 500 {year} (Republican Control)", color='red', alpha=0.7)
    # 在曲线末尾添加标签
    plt.text(sp500_data.index[-1], sp500_normalized.iloc[-1], f"S&P 500 {year}", color='red', ha='left', va='center')

    # 绘制上海综合指数
    if not shanghai_data.empty:
        plt.plot(shanghai_data.index, shanghai_normalized, label=f"Shanghai Composite {year}", color='green', linestyle='--', alpha=0.7)
        # 在曲线末尾添加标签
        plt.text(shanghai_data.index[-1], shanghai_normalized.iloc[-1], f"Shanghai {year}", color='green', ha='left', va='center')

    # 绘制恒生指数
    if not hang_seng_data.empty:
        plt.plot(hang_seng_data.index, hang_seng_normalized, label=f"Hang Seng {year}", color='blue', linestyle=':', alpha=0.7)
        # 在曲线末尾添加标签
        plt.text(hang_seng_data.index[-1], hang_seng_normalized.iloc[-1], f"Hang Seng {year}", color='blue', ha='left', va='center')

# 设置图表属性
plt.title('S&P 500, Shanghai Composite, and Hang Seng Index Performance from Election Month to Following October')
plt.xlabel('Months from Election')
plt.ylabel('Index Performance (Normalized to 100)')

# 设置X轴从11月到次年10月，仅显示月份名称
plt.gca().xaxis.set_major_locator(MonthLocator())
plt.gca().xaxis.set_major_formatter(DateFormatter('%b'))
plt.setp(plt.gca().get_xticklabels(), rotation=45, ha='right')

# 显示网格
plt.grid()

# 显示图例
plt.legend()

# 显示图表
plt.tight_layout()
plt.show()
