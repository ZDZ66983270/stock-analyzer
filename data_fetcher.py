import akshare as ak
import yfinance as yf
import pandas as pd
from datetime import datetime
from indicator_calculator import calculate_indicators
from modules.technical_indicators import add_technical_indicators

def fetch_us_daily(symbol: str) -> pd.DataFrame:
    try:
        print(f"正在获取 {symbol} 的日线数据...")
        df = ak.stock_us_daily(symbol)
        if '日期' in df.columns:
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
            df['date'] = pd.to_datetime(df['date'])
            return df[df['date'] >= pd.Timestamp.now() - pd.Timedelta(days=15)]
    except Exception as e:
        print(f"获取 {symbol} 日线数据失败: {str(e)}")
    return None

def fetch_us_minute(symbol: str, interval: str) -> pd.DataFrame:
    try:
        print(f"正在获取 {symbol} 的 {interval} 数据...")
        df = yf.download(symbol, period='7d', interval=interval, progress=False)
        if not df.empty:
            df.reset_index(inplace=True)
            df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
            df['datetime'] = pd.to_datetime(df['Datetime'] if 'Datetime' in df.columns else df['Date'])
            return df
    except Exception as e:
        print(f"获取 {symbol} {interval} 数据失败: {str(e)}")
    return None

def fetch_cn_hk(symbol: str, period: str) -> pd.DataFrame:
    try:
        print(f"正在获取 {symbol} 的 {period} 数据...")
        code = symbol.split('.')[1]
        df = ak.stock_zh_a_hist(code, period=period, adjust="qfq")
        df['date'] = pd.to_datetime(df['日期'])
        df = df.rename(columns={'开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume'})
        return df[df['date'] >= pd.Timestamp.now() - pd.Timedelta(days=15)]
    except Exception as e:
        print(f"获取 {symbol} {period} 数据失败: {str(e)}")
    return None

def fetch_kline_data(symbol: str, period: str) -> pd.DataFrame:
    """
    获取股票K线数据
    
    Args:
        symbol: 股票代码
        period: 周期（daily/weekly/monthly）
        
    Returns:
        DataFrame: 包含K线数据的DataFrame
    """
    try:
        parts = symbol.split('.')
        if len(parts) != 2:
            raise ValueError(f"股票代码格式错误: {symbol}")
        
        code = parts[0]
        market = parts[1].upper()
        
        if period not in ['daily', 'weekly', 'monthly']:
            raise ValueError(f"不支持的周期: {period}")

        if market == 'SH' or market == 'SZ':  # A股
            if period == 'daily':
                df = ak.stock_zh_a_hist(symbol=code, adjust="qfq")
            elif period == 'weekly':
                df = ak.stock_zh_a_hist(symbol=code, adjust="qfq", period="weekly")
            elif period == 'monthly':
                df = ak.stock_zh_a_hist(symbol=code, adjust="qfq", period="monthly")

            df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            }, inplace=True)
            df['date'] = pd.to_datetime(df['date'])
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

        elif market == 'HK':  # 港股
            if period == 'daily':
                df = ak.stock_hk_daily(symbol=code)
            elif period == 'weekly':
                df = ak.stock_hk_hist(symbol=code, period="weekly")
            elif period == 'monthly':
                df = ak.stock_hk_hist(symbol=code, period="monthly")

            df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            }, inplace=True)
            df['date'] = pd.to_datetime(df['date'])
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

        elif market == 'US':  # 美股
            if period == 'daily':
                interval = '1d'
            elif period == 'weekly':
                interval = '1wk'
            elif period == 'monthly':
                interval = '1mo'

            df = yf.download(tickers=code, period='6mo', interval=interval, progress=False)
            if df.empty:
                return None
            df.reset_index(inplace=True)
            df.rename(columns={
                'Date': 'date', 'Open': 'open', 'High': 'high',
                'Low': 'low', 'Close': 'close', 'Volume': 'volume'
            }, inplace=True)
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        else:
            raise ValueError(f"未知市场标识: {market}")

        return df

    except Exception as e:
        print(f"[ERROR] 获取{symbol}的{period}数据失败: {e}")
        return None

def fetch_all_kline_data(symbol: str) -> dict:
    """
    获取所有周期的K线数据
    
    Args:
        symbol: 股票代码
        
    Returns:
        dict: 包含不同周期K线数据的字典
    """
    result = {}
    for period in ['daily', 'weekly', 'monthly']:
        df = fetch_kline_data(symbol, period)
        if df is not None:
            df = add_technical_indicators(df)
        result[period] = df

    # 为每个周期添加技术指标
    for period in ["weekly", "monthly", "2hour", "1hour", "30min", "15min", "5min"]:
        if result[period] is not None and not result[period].empty:
            try:
                # 计算MA
                result[period]['MA5'] = result[period]['CLOSE'].rolling(window=5).mean()
                result[period]['MA10'] = result[period]['CLOSE'].rolling(window=10).mean()
                result[period]['MA20'] = result[period]['CLOSE'].rolling(window=20).mean()
                result[period]['MA60'] = result[period]['CLOSE'].rolling(window=60).mean()
                
                # 计算MACD
                exp1 = result[period]['CLOSE'].ewm(span=12, adjust=False).mean()
                exp2 = result[period]['CLOSE'].ewm(span=26, adjust=False).mean()
                result[period]['DIF'] = exp1 - exp2
                result[period]['DEA'] = result[period]['DIF'].ewm(span=9, adjust=False).mean()
                result[period]['MACD'] = 2 * (result[period]['DIF'] - result[period]['DEA'])
                
                # 计算KDJ
                low_list = result[period]['LOW'].rolling(window=9, min_periods=9).min()
                high_list = result[period]['HIGH'].rolling(window=9, min_periods=9).max()
                rsv = (result[period]['CLOSE'] - low_list) / (high_list - low_list) * 100
                result[period]['K'] = rsv.ewm(com=2).mean()
                result[period]['D'] = result[period]['K'].ewm(com=2).mean()
                result[period]['J'] = 3 * result[period]['K'] - 2 * result[period]['D']
                
                # 计算RSI
                delta = result[period]['CLOSE'].diff()
                for rsi_period in [6, 12, 24]:
                    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                    rs = gain / loss
                    result[period][f'RSI{rsi_period}'] = 100 - (100 / (1 + rs))
                
            except Exception as e:
                print(f"计算{period}周期技术指标时出错: {str(e)}")
                continue
    
    return result

def fetch_fund_flow(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取股票的资金流向数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        DataFrame: 包含资金流向数据的DataFrame
    """
    try:
        parts = symbol.split('.')
        if len(parts) != 2:
            raise ValueError(f"股票代码格式错误: {symbol}")
        
        code = parts[0]
        market = parts[1].upper()
        
        if market == 'SH' or market == 'SZ':  # A股
            df = ak.stock_individual_fund_flow(symbol=code, start_date=start_date, end_date=end_date)
            
            df = df.rename(columns={
                'date': '日期',
                'code': '代码',
                'name': '名称',
                'close': '收盘价',
                'pctChg': '涨跌幅',
                'mainNetInflow': '主力净流入',
                'hugeNetInflow': '超大单净流入',
                'largeNetInflow': '大单净流入',
                'midNetInflow': '中单净流入',
                'smallNetInflow': '小单净流入'
            })
            
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
            
            return df
        else:
            print(f"[资金流向] 不支持的市场类型: {code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"获取资金流向数据失败: {e}")
        return pd.DataFrame() 