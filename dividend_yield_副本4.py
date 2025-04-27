import pandas as pd
import yfinance as yf
from datetime import datetime

def get_dividend_yield(stock_symbols):
    current_year = datetime.now().year
    years_to_analyze = 10  # 分析过去10年
    results = {}

    for symbol in stock_symbols:
        # 获取股息数据
        stock = yf.Ticker(symbol)
        dividends = stock.dividends

        # 获取公司名称
        company_name = stock.info.get('longName', 'N/A')

        if dividends.empty:
            print(f"{symbol} ({company_name}) 没有分红数据。")
            continue

        # 存储每年总股息和对应股价
        annual_dividends = {}
        dividend_yields = []  # 存储每年的股息率
        total_dividend_sum = 0  # 用于计算股息总计
        min_price = float('inf')  # 用于计算期间内最低股价
        start_price = None  # 用于存储起始股价
        price_list = []  # 用于存储股价以计算中位数

        # 复合收益率计算初始化
        total_shares = 1.0  # 初始持股数量，假设初始投入为1股

        for year in range(current_year - years_to_analyze + 1, current_year + 1):
            dividends_year = dividends[dividends.index.year == year]
            if not dividends_year.empty:
                total_dividend = dividends_year.sum()
                total_dividend_sum += total_dividend  # 累加股息
                # 获取支付股息的当日股价
                prices = stock.history(start=f"{year}-01-01", end=f"{year + 1}-01-01")
                dividend_yield = 0
                price_on_payment_list = []  # 存储当日股价

                for date, dividend in dividends_year.items():
                    if date in prices.index:
                        price_on_payment = prices['Close'][date]
                        price_on_payment_list.append(price_on_payment)  # 记录当日股价
                        price_list.append(price_on_payment)  # 用于计算中位数
                        dividend_yield += (dividend / price_on_payment) * 100  # 转换为百分比

                        # 输出每次股息及其对应的股价
                        print(f"{symbol} ({company_name}) 在 {year} 年 {date.date()} 的股息为 {dividend:.4f}，"
                              f"当日股价为 {price_on_payment:.2f}")

                annual_dividends[year] = {
                    'Total Dividend': total_dividend,
                    'Dividend Yield': dividend_yield,
                    'Price on Payment': price_on_payment_list
                }

                # 添加年度股息率到列表
                dividend_yields.append(dividend_yield)

                # 更新最低股价
                min_price = min(min_price, prices['Close'].min())

                # 记录第一年股价
                if start_price is None:
                    start_price = prices['Close'].iloc[0]

                # 复合收益率计算
                total_shares += total_dividend / start_price  # 假设股息投资于股票

        # 获取派息率并转换为百分比
        payout_ratio = stock.info.get('payoutRatio', None)  # 获取派息率
        if payout_ratio is not None:
            payout_ratio *= 100  # 转换为百分比

        results[symbol] = {
            'Company Name': company_name,
            'Annual Dividends': annual_dividends,
            'Dividend Yields': dividend_yields,
            'Total Dividend Sum': total_dividend_sum,  # 新增字段
            'Current Price': stock.history(period='1d')['Close'].iloc[-1],  # 当前股价
            'Min Price': min_price,  # 最低股价
            'Start Price': start_price,  # 期初股价
            'Total Shares': total_shares,  # 复合收益率计算
            'Median Price': pd.Series(price_list).median(),  # 股价中位数
            'Payout Ratio': payout_ratio  # 新增字段
        }

    return results

# 用户输入股票代码
stock_symbols_input = input("请输入股票代码（用空格分隔，最多5个）：")
stock_symbols = stock_symbols_input.split()

# 获取股息和股息率
dividend_data = get_dividend_yield(stock_symbols)

# 输出结果
for symbol, data in dividend_data.items():
    print(f"\n{symbol} ({data['Company Name']}) 分红数据及股息率：")
    for year, values in data['Annual Dividends'].items():
        price_on_payment_str = ', '.join(f"{price:.2f}" for price in values['Price on Payment'])
        print(f"{year}年: 总股息 = {values['Total Dividend']:.4f}, "
              f"年股息率 = {values['Dividend Yield']:.2f}%, "
              f"当日股价 = [{price_on_payment_str}]")

    # 计算平均股息率和股息率中位数
    average_yield = sum(data['Dividend Yields']) / len(data['Dividend Yields']) if data['Dividend Yields'] else 0
    median_yield = pd.Series(data['Dividend Yields']).median() if data['Dividend Yields'] else 0

    # 计算当前股价与股价中位数的变化百分比
    current_price = data['Current Price']
    median_price = data['Median Price']
    price_change_percentage = ((current_price - median_price) / median_price) * 100 if median_price > 0 else 0

    # 计算当前股价与期初股价的变化百分比
    start_price = data['Start Price']
    initial_price_change_percentage = ((current_price - start_price) / start_price) * 100 if start_price > 0 else 0

    # 计算复合收益率
    compounded_return = ((data['Total Shares'] - 1) * 100)  # 计算复合收益率为百分比

    # 输出结果
    payout_ratio_display = f"{data['Payout Ratio']:.2f}%" if data['Payout Ratio'] is not None else "N/A"
    print(f"股息总计 = {data['Total Dividend Sum']:.4f}, "
          f"平均年股息率 = {average_yield:.2f}%, 年股息率中位数 = {median_yield:.2f}%, "
          f"最新派息率 = {payout_ratio_display}")

    # 输出当前股价变化百分比
    print(f"当前股价与股价中位数的变化百分比 = {price_change_percentage:.2f}%")
    print(f"当前股价与期初股价的变化百分比 = {initial_price_change_percentage:.2f}%")
    print(f"复合收益率 = {compounded_return:.2f}%")

# 计算复合收益率和年均股息率排名
average_yields = {symbol: sum(data['Dividend Yields']) / len(data['Dividend Yields']) if data['Dividend Yields'] else 0 for symbol, data in dividend_data.items()}
compounded_returns = {symbol: ((data['Total Shares'] - 1) * 100) for symbol, data in dividend_data.items()}

# 排序
average_yield_ranking = sorted(average_yields.items(), key=lambda x: x[1], reverse=True)
compounded_return_ranking = sorted(compounded_returns.items(), key=lambda x: x[1], reverse=True)

# 输出排名
print("\n年均股息率排名：")
for rank, (symbol, avg_yield) in enumerate(average_yield_ranking, start=1):
    company_name = dividend_data[symbol]['Company Name']
    print(f"{rank}. {symbol} ({company_name}) ({avg_yield:.2f}%)")

print("\n复合收益率排名：")
for rank, (symbol, comp_return) in enumerate(compounded_return_ranking, start=1):
    company_name = dividend_data[symbol]['Company Name']
    print(f"{rank}. {symbol} ({company_name}) ({comp_return:.2f}%)")
