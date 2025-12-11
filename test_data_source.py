import akshare as ak
import yfinance as yf
import traceback
import sys

print("Python版本:", sys.version)
print("Akshare版本:", ak.__version__)
print("YFinance版本:", yf.__version__)

print("\n=== 开始测试 Akshare 获取美股 AAPL 日线 ===")
try:
    print("正在调用 ak.stock_us_daily...")
    df_ak = ak.stock_us_daily(symbol="AAPL")
    if df_ak is None:
        print("[Akshare] 返回 None")
    elif df_ak.empty:
        print("[Akshare] 返回空DataFrame")
    else:
        print("[Akshare] 成功，前5行数据：")
        print(df_ak.head())
except Exception as e:
    print("[Akshare] 获取失败，异常信息如下：")
    traceback.print_exc()

print("\n=== 开始测试 YFinance 获取美股 AAPL 日线 ===")
try:
    print("正在调用 yf.download...")
    df_yf = yf.download(tickers="AAPL", period="7d", interval="1d", progress=False)
    if df_yf is None:
        print("[YFinance] 返回 None")
    elif df_yf.empty:
        print("[YFinance] 返回空DataFrame")
    else:
        print("[YFinance] 成功，前5行数据：")
        print(df_yf.head())
except Exception as e:
    print("[YFinance] 获取失败，异常信息如下：")
    traceback.print_exc()

print("\n=== 测试结束 ===") 