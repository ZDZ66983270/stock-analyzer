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

        for year in range(current_year - years_to_analyze + 1, current_year + 1):
            dividends_year = dividends[dividends.index.year == year]
            if not dividends_year.empty:
                total_dividend = dividends_year.sum()
                # 获取支付股息的当日股价
                prices = stock.history(start=f"{year}-01-01", end=f"{year + 1}-01-01")
                dividend_yield = 0
                price_on_payment_list = []  # 存储当日股价

                for date, dividend in dividends_year.items():
                    if date in prices.index:
                        price_on_payment = prices['Close'][date]
                        price_on_payment_list.append(price_on_payment)  # 记录当日股价
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

        results[symbol] = {
            'Company Name': company_name,
            'Annual Dividends': annual_dividends,
            'Dividend Yields': dividend_yields
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
              f"股息率 = {values['Dividend Yield']:.2f}%, "
              f"当日股价 = [{price_on_payment_str}]")

    # 计算平均股息率和股息率中位数
    average_yield = sum(data['Dividend Yields']) / len(data['Dividend Yields']) if data['Dividend Yields'] else 0
    median_yield = pd.Series(data['Dividend Yields']).median() if data['Dividend Yields'] else 0

    # 输出平均股息率和股息率中位数
    print(f"平均股息率 = {average_yield:.2f}%, 股息率中位数 = {median_yield:.2f}%")
