import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    为DataFrame添加技术指标
    
    Args:
        df: 包含OHLCV数据的DataFrame
        
    Returns:
        pd.DataFrame: 添加了技术指标的DataFrame
    """
    try:
        # 确保必要的列存在
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError("数据缺少必要的列")
            
        # 计算MA
        df = calculate_ma(df)
        
        # 计算MACD
        df = calculate_macd(df)
        
        # 计算KDJ
        df = calculate_kdj(df)
        
        # 计算RSI
        df = calculate_rsi(df)
        
        return df
        
    except Exception as e:
        logger.error(f"计算技术指标时发生错误: {str(e)}")
        return df

def calculate_ma(df: pd.DataFrame) -> pd.DataFrame:
    """计算移动平均线"""
    try:
        periods = [5, 10, 20]
        for period in periods:
            df[f'ma{period}'] = df['close'].rolling(window=period).mean().round(3)
        return df
    except Exception as e:
        logger.error(f"计算MA指标时发生错误: {str(e)}")
        return df

def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """计算MACD指标"""
    try:
        # MACD参数
        fast_period = 12
        slow_period = 26
        signal_period = 9
        
        # 计算快速和慢速EMA
        fast_ema = df['close'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # 计算DIF
        df['macd_dif'] = fast_ema - slow_ema
        
        # 计算DEA
        df['macd_dea'] = df['macd_dif'].ewm(span=signal_period, adjust=False).mean()
        
        # 计算MACD柱状图
        df['macd_hist'] = 2 * (df['macd_dif'] - df['macd_dea'])
        
        # 四舍五入到3位小数
        for col in ['macd_dif', 'macd_dea', 'macd_hist']:
            df[col] = df[col].round(3)
            
        return df
        
    except Exception as e:
        logger.error(f"计算MACD指标时发生错误: {str(e)}")
        return df

def calculate_kdj(df: pd.DataFrame) -> pd.DataFrame:
    """计算KDJ指标"""
    try:
        # KDJ参数
        n = 9  # 计算RSV的周期
        m1 = 3 # 计算K值的周期
        m2 = 3 # 计算D值的周期
        
        # 计算RSV
        low_list = df['low'].rolling(window=n, min_periods=1).min()
        high_list = df['high'].rolling(window=n, min_periods=1).max()
        
        rsv = pd.Series(0.0, index=df.index)
        denom = high_list - low_list
        mask = denom != 0  # 避免除以0
        rsv[mask] = (df['close'][mask] - low_list[mask]) / denom[mask] * 100
        
        # 计算K值
        df['kdj_k'] = pd.Series(50.0, index=df.index)  # 初始值为50
        for i in range(1, len(df)):
            df['kdj_k'].iloc[i] = (2/3 * df['kdj_k'].iloc[i-1] + 1/3 * rsv.iloc[i])
            
        # 计算D值
        df['kdj_d'] = pd.Series(50.0, index=df.index)  # 初始值为50
        for i in range(1, len(df)):
            df['kdj_d'].iloc[i] = (2/3 * df['kdj_d'].iloc[i-1] + 1/3 * df['kdj_k'].iloc[i])
            
        # 计算J值
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        
        # 四舍五入到3位小数
        for col in ['kdj_k', 'kdj_d', 'kdj_j']:
            df[col] = df[col].round(3)
            
        return df
        
    except Exception as e:
        logger.error(f"计算KDJ指标时发生错误: {str(e)}")
        return df

def calculate_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """计算RSI指标"""
    try:
        periods = [6, 12, 24]
        
        # 计算价格变化
        delta = df['close'].diff()
        
        for period in periods:
            # 分别获取上涨和下跌幅度
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = -loss  # 转换为正值
            
            # 计算平均值
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # 计算相对强度（RS）
            rs = avg_gain / avg_loss
            
            # 计算RSI
            rsi = 100 - (100 / (1 + rs))
            
            # 添加到DataFrame
            df[f'rsi{period}'] = rsi.round(2)
            
        return df
        
    except Exception as e:
        logger.error(f"计算RSI指标时发生错误: {str(e)}")
        return df

if __name__ == '__main__':
    # 测试代码
    import yfinance as yf
    
    # 获取测试数据
    ticker = yf.Ticker('AAPL')
    df = ticker.history(period='1mo')
    
    # 计算指标
    df = add_technical_indicators(df)
    
    # 打印结果
    print(df.tail()) 