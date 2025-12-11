import pandas as pd
import numpy as np

# MA 均线
def calculate_ma(df: pd.DataFrame) -> pd.DataFrame:
    for period in [5, 10, 20]:
        df[f"MA{period}"] = df['CLOSE'].rolling(window=period).mean()
    return df

# MACD
def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    short = 12
    long = 26
    signal = 9
    df['EMA_SHORT'] = df['CLOSE'].ewm(span=short, adjust=False).mean()
    df['EMA_LONG'] = df['CLOSE'].ewm(span=long, adjust=False).mean()
    df['MACD_DIF'] = df['EMA_SHORT'] - df['EMA_LONG']
    df['MACD_DEA'] = df['MACD_DIF'].ewm(span=signal, adjust=False).mean()
    df['MACD_HIST'] = 2 * (df['MACD_DIF'] - df['MACD_DEA'])
    return df

# KDJ
def calculate_kdj(df: pd.DataFrame) -> pd.DataFrame:
    low_min = df['LOW'].rolling(window=9, min_periods=1).min()
    high_max = df['HIGH'].rolling(window=9, min_periods=1).max()
    rsv = (df['CLOSE'] - low_min) / (high_max - low_min) * 100
    df['KDJ_K'] = rsv.ewm(com=2).mean()
    df['KDJ_D'] = df['KDJ_K'].ewm(com=2).mean()
    df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']
    return df

# RSI
def calculate_rsi(df: pd.DataFrame) -> pd.DataFrame:
    delta = df['CLOSE'].diff()
    for period in [6, 12, 24]:
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df[f"RSI{period}"] = 100 - (100 / (1 + rs))
    return df

# 总调用接口
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_kdj(df)
    df = calculate_rsi(df)
    return df

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    给定DataFrame，统一加上 MA、MACD、KDJ、RSI
    """
    if df is None or df.empty:
        return df
    return calculate_indicators(df)

def add_technical_indicators_old(df):
    """添加技术指标
    
    Args:
        df: DataFrame with columns ['datetime', 'open', 'high', 'low', 'close', 'volume']
        
    Returns:
        DataFrame with additional technical indicators
    """
    # 确保数据按时间排序
    df = df.sort_values('datetime')
    
    # 计算移动平均线
    df['MA5'] = df['CLOSE'].rolling(window=5).mean()
    df['MA10'] = df['CLOSE'].rolling(window=10).mean()
    df['MA20'] = df['CLOSE'].rolling(window=20).mean()
    df['MA30'] = df['CLOSE'].rolling(window=30).mean()
    
    # 计算MACD
    exp1 = df['CLOSE'].ewm(span=12, adjust=False).mean()
    exp2 = df['CLOSE'].ewm(span=26, adjust=False).mean()
    df['MACD_DIF'] = exp1 - exp2
    df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_HIST'] = 2 * (df['MACD_DIF'] - df['MACD_DEA'])
    
    # 计算RSI
    delta = df['CLOSE'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算布林带
    df['BOLL_MID'] = df['CLOSE'].rolling(window=20).mean()
    df['BOLL_STD'] = df['CLOSE'].rolling(window=20).std()
    df['BOLL_UP'] = df['BOLL_MID'] + 2 * df['BOLL_STD']
    df['BOLL_DOWN'] = df['BOLL_MID'] - 2 * df['BOLL_STD']
    
    return df 