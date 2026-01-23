
import yfinance as yf

def fetch_msft_data():
    ticker_symbol = "MSFT"
    print(f"Fetching data for {ticker_symbol} from Yahoo Finance...")
    
    # 获取 Ticker 对象
    msft = yf.Ticker(ticker_symbol)
    
    # 获取 info 字典
    info = msft.info
    
    # 提取 PE 和 派息信息
    pe_trailing = info.get('trailingPE')
    pe_forward = info.get('forwardPE')
    dividend_rate = info.get('dividendRate')    # 每股股息金额
    dividend_yield = info.get('dividendYield')  # 股息率 (通常为小数，如 0.0075 代表 0.75%)
    
    print("-" * 30)
    print(f"股票代码: {ticker_symbol}")
    print(f"市盈率 (Trailing PE): {pe_trailing}")
    print(f"预测市盈率 (Forward PE): {pe_forward}")
    print(f"每股股息 (Dividend Rate): {dividend_rate}")
    if dividend_yield is not None:
        # Based on Yahoo info, 0.73 means 0.73%, so we don't multiply by 100
        print(f"股息率 (Dividend Yield): {dividend_yield}%")
    else:
        print("股息率 (Dividend Yield): None")
    print("-" * 30)

if __name__ == "__main__":
    fetch_msft_data()
