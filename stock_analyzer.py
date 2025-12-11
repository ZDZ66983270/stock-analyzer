import os
import time
import logging
import pandas as pd
import akshare as ak
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
import traceback

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_analyzer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 创建输出目录
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 日志函数
def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")

# 读取 symbols.txt
def read_symbols(file_path="symbols.txt"):
    try:
        with open(file_path, "r") as f:
            symbols = [line.strip() for line in f if line.strip()]
        log(f"读取到 {len(symbols)} 个股票代码：{symbols}")
        return symbols
    except Exception as e:
        log(f"读取symbols.txt失败: {e}")
        sys.exit(1)

# 规范化 symbol，添加市场前缀
def normalize_symbol(symbol: str) -> str:
    if symbol.isdigit():
        if len(symbol) == 6:
            if symbol.startswith('6'):
                return f'SH.{symbol}'
            else:
                return f'SZ.{symbol}'
        elif len(symbol) == 5:
            return f'HK.{symbol.zfill(5)}'
    return f'US.{symbol}'

# A股日线
def fetch_ashare_day(symbol: str) -> Optional[pd.DataFrame]:
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period='daily', adjust='qfq')
        df.rename(columns={'日期': 'datetime', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'}, inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        # 只返回最近30天的数据
        return df.tail(30)
    except Exception as e:
        logging.error(f"拉取A股日线失败 {symbol}: {e}")
        return None

# A股分钟线
def fetch_ashare_min(symbol: str, minute: str) -> Optional[pd.DataFrame]:
    try:
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period=minute)
        df.rename(columns={'时间': 'datetime', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'}, inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df.sort_values('datetime').tail(7*24*60//int(minute))
    except Exception as e:
        logging.error(f"拉取A股分钟线失败 {symbol}-{minute}: {e}")
        return None

# A股资金流
def fetch_ashare_fund(symbol: str) -> Optional[pd.DataFrame]:
    try:
        market = 'sh' if symbol.startswith('6') else 'sz'
        df = ak.stock_individual_fund_flow(stock=symbol, market=market)
        return df
    except Exception as e:
        logging.error(f"拉取资金流失败 {symbol}: {e}")
        return None

# 拉取美股日线数据（Akshare）
def fetch_us_stock(symbol):
    try:
        df = ak.stock_us_daily(symbol=symbol)
        if df is None or df.empty:
            log(f"[{symbol}] Akshare返回空数据")
            return None
            
        # 确保日期列是datetime类型
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        elif 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.rename(columns={'datetime': 'date'}, inplace=True)
            
        # 保留最近7天
        df = df.sort_values('date', ascending=False).head(7).sort_values('date')
        
        # 确保列名正确
        column_mapping = {
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        log(f"[{symbol}] 拉取成功，共{len(df)}条记录")
        return df
    except Exception as e:
        log(f"[{symbol}] 拉取失败: {e}")
        traceback.print_exc()
        return None

# 美股分钟线 - 优化版本
def fetch_us_min(symbol: str, interval: str) -> Optional[pd.DataFrame]:
    try:
        logging.info(f"尝试使用YFinance获取 {symbol} {interval} 数据...")
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        df = yf.download(tickers=symbol, start=start_date, end=today, interval=interval, progress=False)
        if df is not None and not df.empty:
            logging.info(f"YFinance成功获取 {symbol} {interval} 数据，共 {len(df)} 条记录")
            df.reset_index(inplace=True)
            df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume', 'Datetime': 'datetime', 'Date': 'datetime'}, inplace=True)
            return df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        else:
            logging.warning(f"YFinance获取 {symbol} {interval} 数据为空")
    except Exception as e:
        logging.error(f"YFinance获取 {symbol} {interval} 数据失败: {e}")
    
    return None

# 技术指标计算
def calculate_indicators(df):
    df = df.copy()
    if 'close' not in df.columns:
        return df

    # MA
    for window in [5, 10, 20]:
        df[f"MA{window}"] = df['close'].rolling(window=window, min_periods=1).mean()

    # MACD
    short_ema = df['close'].ewm(span=12, adjust=False).mean()
    long_ema = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']

    # KDJ
    low_min = df['low'].rolling(window=9, min_periods=1).min()
    high_max = df['high'].rolling(window=9, min_periods=1).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(alpha=1/3).mean()
    df['D'] = df['K'].ewm(alpha=1/3).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    rs = gain / loss
    df['RSI6'] = 100 - (100 / (1 + rs))

    return df

# 保存
def save_to_excel(symbol: str, data: Dict[str, pd.DataFrame]):
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    name = symbol.replace('.', '_')
    now = datetime.now().strftime('%Y%m%d_%H%M')
    filename = os.path.join(output_dir, f'{name}_{now}.xlsx')
    
    # 检查是否有有效数据
    valid_data = {k: v for k, v in data.items() if v is not None and not v.empty}
    if not valid_data:
        logging.error(f"没有有效数据可保存: {symbol}")
        return
        
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for period, df in valid_data.items():
            df = calculate_indicators(df)
            df.to_excel(writer, sheet_name=period, index=False)
    logging.info(f"保存成功: {filename}")

# 主程序
if __name__ == '__main__':
    symbols = read_symbols()
    periods = ['1d', '2h', '1h', '30m', '15m', '5m']

    for raw_symbol in symbols:
        symbol = normalize_symbol(raw_symbol)
        market = symbol.split('.')[0]
        code = symbol.split('.')[-1]
        logging.info(f"开始处理 {symbol}")

        all_data = {}
        if market in ['SH', 'SZ', 'HK']:
            all_data['1d'] = fetch_ashare_day(code)
            for minute in ['120', '60', '30', '15', '5']:
                all_data[f'{int(int(minute)/60) if int(minute)>=60 else minute}m'] = fetch_ashare_min(code, minute)
            fund_flow = fetch_ashare_fund(code)
            if fund_flow is not None:
                all_data['fund_flow'] = fund_flow
        elif market == 'US':
            all_data['1d'] = fetch_us_stock(code)
            for interval in ['2h', '1h', '30m', '15m', '5m']:
                all_data[interval] = fetch_us_min(code, interval)
        else:
            logging.error(f"不支持的市场: {symbol}")
            continue

        save_to_excel(symbol, all_data)