import akshare as ak
import sys

print("开始测试...")
print("Python版本:", sys.version)
print("Akshare版本:", ak.__version__)

try:
    print("\n尝试获取美股AAPL数据...")
    df = ak.stock_us_daily(symbol="AAPL")
    
    if df is None:
        print("返回None")
    elif df.empty:
        print("返回空DataFrame")
    else:
        print("\n数据获取成功:")
        print("数据形状:", df.shape)
        print("列名:", df.columns.tolist())
        print("\n前5行数据:")
        print(df.head())
except Exception as e:
    print("发生错误:", str(e))
    import traceback
    traceback.print_exc()

print("\n测试结束") 