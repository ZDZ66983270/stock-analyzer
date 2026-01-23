import yfinance as yf

ticker = yf.Ticker('0005.HK')
info = ticker.info

print("=" * 60)
print("汇丰控股 (0005.HK) - Yahoo Finance 财报数据测试")
print("=" * 60)

print("\n【基本信息】")
print(f"公司名称: {info.get('longName')}")
print(f"流通股数: {info.get('sharesOutstanding'):,}")
print(f"EPS (TTM): {info.get('trailingEps')}")

print("\n【损益表 - 年度】")
fin = ticker.financials
print(f"可用年份: {len(fin.columns)} 年")
if not fin.empty:
    latest = fin.columns[0]
    print(f"最新年份: {latest.year}")
    rev = fin.loc['Total Revenue', latest] if 'Total Revenue' in fin.index else None
    ni = fin.loc['Net Income', latest] if 'Net Income' in fin.index else None
    print(f"营业收入: {rev:,.0f}" if rev else "营业收入: N/A")
    print(f"净利润: {ni:,.0f}" if ni else "净利润: N/A")

print("\n【资产负债表 - 年度】")
bs = ticker.balance_sheet
print(f"可用年份: {len(bs.columns)} 年")
if not bs.empty:
    latest = bs.columns[0]
    assets = bs.loc['Total Assets', latest] if 'Total Assets' in bs.index else None
    cash = bs.loc['Cash And Cash Equivalents', latest] if 'Cash And Cash Equivalents' in bs.index else None
    print(f"总资产: {assets:,.0f}" if assets else "总资产: N/A")
    print(f"现金: {cash:,.0f}" if cash else "现金: N/A")

print("\n【现金流量表 - 年度】")
cf = ticker.cashflow
print(f"可用年份: {len(cf.columns)} 年")
if not cf.empty:
    latest = cf.columns[0]
    ocf = cf.loc['Operating Cash Flow', latest] if 'Operating Cash Flow' in cf.index else None
    fcf = cf.loc['Free Cash Flow', latest] if 'Free Cash Flow' in cf.index else None
    print(f"经营现金流: {ocf:,.0f}" if ocf else "经营现金流: N/A")
    print(f"自由现金流: {fcf:,.0f}" if fcf else "自由现金流: N/A")

print("\n" + "=" * 60)
print("✅ 测试完成")
