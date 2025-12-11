import yfinance as yf
import akshare as ak
import pandas as pd
from datetime import datetime

def test_yfinance(symbol: str):
    print(f"\n[YFinance] 开始测试 {symbol}")
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - pd.Timedelta(days=5)).strftime('%Y-%m-%d')
        df = yf.download(tickers=symbol, start=start_date, end=today, interval='1d', progress=False)
        if df.empty:
            print(f"[警告] YFinance: {symbol} 返回数据为空")
        else:
            print(f"[成功] YFinance: {symbol} 返回 {len(df)} 条记录")
            print(df.tail(2))
    except Exception as e:
        print(f"[错误] YFinance 拉取 {symbol} 失败: {e}")

def test_akshare(symbol: str):
    print(f"\n[Akshare] 开始测试 {symbol}")
    try:
        df = ak.stock_us_daily(symbol=symbol)
        if df.empty:
            print(f"[警告] Akshare: {symbol} 返回数据为空")
        else:
            print(f"[成功] Akshare: {symbol} 返回 {len(df)} 条记录")
            print(df.tail(2))
    except Exception as e:
        print(f"[错误] Akshare 拉取 {symbol} 失败: {e}")

if __name__ == "__main__":
    symbols = ['TSM', 'MSFT', 'AAPL', 'NVDA']

    for symbol in symbols:
        test_yfinance(symbol)
        test_akshare(symbol) 