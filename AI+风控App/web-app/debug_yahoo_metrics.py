
import yfinance as yf

def debug_ticker(symbol):
    print(f"--- Debugging {symbol} ---")
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    # 打印关键字段
    keys = ['trailingPE', 'forwardPE', 'dividendYield', 'trailingEps', 'forwardEps', 'marketCap']
    for k in keys:
        print(f"{k}: {info.get(k)} (Type: {type(info.get(k))})")

if __name__ == "__main__":
    debug_ticker("MSFT")
    debug_ticker("TSLA")
