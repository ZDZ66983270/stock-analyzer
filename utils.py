# ✅ modules/utils.py
import os
import pandas as pd
from datetime import datetime

def save_to_excel(symbol, kline_data, fund_flow_df=None):
    today_str = datetime.now().strftime('%Y%m%d_%H%M')
    file_name = f"output/{symbol.replace('.', '_')}_{today_str}.xlsx"
    os.makedirs("output", exist_ok=True)

    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        for period, df in kline_data.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=period, index=False)
        if fund_flow_df is not None and not fund_flow_df.empty:
            fund_flow_df.to_excel(writer, sheet_name="fund_flow", index=False)
    print(f"✅ {symbol} 数据保存至 {file_name}")

# ✅ modules/data_fetcher.py
import akshare as ak
import yfinance as yf
import pandas as pd
from modules.technical_indicators import add_technical_indicators

def fetch_kline_data(symbol, period):
    try:
        if period == "daily":
            return ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        elif period == "weekly":
            return ak.stock_zh_a_hist(symbol=symbol, period="weekly", adjust="qfq")
        elif period == "monthly":
            return ak.stock_zh_a_hist(symbol=symbol, period="monthly", adjust="qfq")
    except Exception as e:
        print(f"[ERROR] 获取{symbol}的{period}数据失败: {e}")
        return None

def fetch_all_kline_data(symbol):
    kline_data = {}
    for period in ["daily", "weekly", "monthly"]:
        df = fetch_kline_data(symbol, period)
        if df is not None and not df.empty:
            df.columns = [c.lower() for c in df.columns]
            df = add_technical_indicators(df)
        kline_data[period] = df
    return kline_data

# ✅ modules/technical_indicators.py
import pandas as pd

def add_technical_indicators(df):
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ema12'] = df['close'].ewm(span=12).mean()
    df['ema26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9).mean()
    df['hist'] = df['macd'] - df['signal']

    low_min = df['low'].rolling(window=9).min()
    high_max = df['high'].rolling(window=9).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    df['kdj_k'] = rsv.ewm(com=2).mean()
    df['kdj_d'] = df['kdj_k'].ewm(com=2).mean()
    df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    return df

# ✅ run_logger.py
import logging
from modules.utils import save_to_excel
from modules.data_fetcher import fetch_all_kline_data

def read_symbols():
    with open("config/symbols.txt", "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logging.info("\U0001F4C4 读取到股票列表...")

    symbols = read_symbols()
    logging.info(f"📄 读取到 {len(symbols)} 只股票：{symbols}")
    logging.info("=" * 60)

    for i, symbol in enumerate(symbols, 1):
        logging.info(f"\n🚀 [{i}/{len(symbols)}] 开始处理 {symbol}")
        try:
            kline_data = fetch_all_kline_data(symbol)
            save_to_excel(symbol, kline_data)
        except Exception as e:
            logging.error(f"❌ 处理 {symbol} 出现异常: {e}")

    logging.info("\n🎉 全部处理完成！")

if __name__ == "__main__":
    main()
