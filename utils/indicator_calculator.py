import pandas as pd
import numpy as np
from typing import Tuple, Union, Optional, List, Dict
import logging

def calculate_ma(close: pd.Series, period: int) -> pd.Series:
    """
    计算移动平均线
    """
    return close.rolling(window=period).mean()

def calculate_ema(close: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均线
    """
    return close.ewm(span=period, adjust=False).mean()

def calculate_macd(close: pd.Series, 
                  fast_period: int = 12, 
                  slow_period: int = 26, 
                  signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算MACD指标
    """
    fast_ema = calculate_ema(close, fast_period)
    slow_ema = calculate_ema(close, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    计算RSI指标
    """
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(close: pd.Series, 
                            period: int = 20, 
                            std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算布林带
    """
    middle_band = calculate_ma(close, period)
    std = close.rolling(window=period).std()
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    return upper_band, middle_band, lower_band

def calculate_kdj(high: pd.Series, 
                 low: pd.Series, 
                 close: pd.Series,
                 k_period: int = 9, 
                 d_period: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算KDJ指标
    """
    low_min = low.rolling(window=k_period).min()
    high_max = high.rolling(window=k_period).max()
    rsv = ((close - low_min) / (high_max - low_min)) * 100
    k = rsv.ewm(span=d_period, adjust=False).mean()
    d = k.ewm(span=d_period, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j

def calculate_atr(high: pd.Series, 
                 low: pd.Series, 
                 close: pd.Series, 
                 period: int = 14) -> pd.Series:
    """
    计算ATR（平均真实波幅）
    """
    high_low = high - low
    high_close = abs(high - close.shift())
    low_close = abs(low - close.shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算OBV（能量潮指标）
    """
    close_diff = close.diff()
    obv = pd.Series(index=close.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]
    
    for i in range(1, len(close_diff)):
        if close_diff.iloc[i] > 0:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close_diff.iloc[i] < 0:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv

def calculate_all_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    计算所有技术指标
    
    参数:
        df: 包含OHLCV数据的DataFrame
        params: 指标参数配置字典
        
    返回:
        pd.DataFrame: 包含所有技术指标的DataFrame
    """
    result = pd.DataFrame(index=df.index)
    
    # 计算MA
    for period in params['MA']:
        result[f'MA{period}'] = calculate_ma(df['Close'], period)
    
    # 计算EMA
    for period in params['EMA']:
        result[f'EMA{period}'] = calculate_ema(df['Close'], period)
    
    # 计算MACD
    macd_params = params['MACD']
    macd, signal, hist = calculate_macd(
        df['Close'],
        macd_params['fast_period'],
        macd_params['slow_period'],
        macd_params['signal_period']
    )
    result['MACD'] = macd
    result['MACD_SIGNAL'] = signal
    result['MACD_HIST'] = hist
    
    # 计算RSI
    for period in params['RSI']:
        result[f'RSI{period}'] = calculate_rsi(df['Close'], period)
    
    # 计算布林带
    boll_params = params['BOLL']
    upper, middle, lower = calculate_bollinger_bands(
        df['Close'],
        boll_params['period'],
        boll_params['std_dev']
    )
    result['BOLL_UPPER'] = upper
    result['BOLL_MID'] = middle
    result['BOLL_LOWER'] = lower
    
    # 计算KDJ
    kdj_params = params['KDJ']
    k, d, j = calculate_kdj(
        df['High'],
        df['Low'],
        df['Close'],
        kdj_params['k_period'],
        kdj_params['d_period']
    )
    result['KDJ_K'] = k
    result['KDJ_D'] = d
    result['KDJ_J'] = j
    
    # 计算ATR
    result['ATR'] = calculate_atr(df['High'], df['Low'], df['Close'])
    
    # 计算OBV
    result['OBV'] = calculate_obv(df['Close'], df['Volume'])
    
    return result 

class IndicatorCalculator:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_ma(data: pd.DataFrame, periods: List[int]) -> Dict[str, pd.Series]:
        """
        计算移动平均线
        
        Args:
            data: 包含'close'列的DataFrame
            periods: MA周期列表
            
        Returns:
            Dict[str, pd.Series]: MA数据，键为'MA{period}'
        """
        result = {}
        for period in periods:
            ma = data['close'].rolling(window=period).mean()
            result[f'MA{period}'] = ma
        return result
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast_period: int = 12,
                      slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        计算MACD指标
        
        Args:
            data: 包含'close'列的DataFrame
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            Dict[str, pd.Series]: MACD数据，包含DIF、DEA、HIST
        """
        # 计算快线和慢线的EMA
        ema_fast = data['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow_period, adjust=False).mean()
        
        # 计算DIF
        dif = ema_fast - ema_slow
        
        # 计算DEA
        dea = dif.ewm(span=signal_period, adjust=False).mean()
        
        # 计算MACD柱状图
        hist = 2 * (dif - dea)
        
        return {
            'MACD_DIF': dif,
            'MACD_DEA': dea,
            'MACD_HIST': hist
        }
    
    @staticmethod
    def calculate_kdj(data: pd.DataFrame, fastk_period: int = 9,
                     slowk_period: int = 3, slowd_period: int = 3) -> Dict[str, pd.Series]:
        """
        计算KDJ指标
        
        Args:
            data: 包含'high'、'low'、'close'列的DataFrame
            fastk_period: 快速K线周期
            slowk_period: 慢速K线周期
            slowd_period: 慢速D线周期
            
        Returns:
            Dict[str, pd.Series]: KDJ数据，包含K、D、J值
        """
        # 计算最低价和最高价的N日移动窗口
        low_min = data['low'].rolling(window=fastk_period).min()
        high_max = data['high'].rolling(window=fastk_period).max()
        
        # 计算RSV
        rsv = 100 * ((data['close'] - low_min) / (high_max - low_min))
        
        # 计算K值
        k = rsv.rolling(window=slowk_period).mean()
        
        # 计算D值
        d = k.rolling(window=slowd_period).mean()
        
        # 计算J值
        j = 3 * k - 2 * d
        
        return {
            'KDJ_K': k,
            'KDJ_D': d,
            'KDJ_J': j
        }
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, periods: List[int]) -> Dict[str, pd.Series]:
        """
        计算RSI指标
        
        Args:
            data: 包含'close'列的DataFrame
            periods: RSI周期列表
            
        Returns:
            Dict[str, pd.Series]: RSI数据，键为'RSI{period}'
        """
        result = {}
        
        # 计算价格变化
        delta = data['close'].diff()
        
        for period in periods:
            # 获取上涨和下跌
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # 计算相对强度
            rs = gain / loss
            
            # 计算RSI
            rsi = 100 - (100 / (1 + rs))
            
            result[f'RSI{period}'] = rsi
            
        return result
    
    @classmethod
    def calculate_all_indicators(cls, data: pd.DataFrame,
                               ma_periods: List[int],
                               rsi_periods: List[int],
                               macd_settings: Dict[str, int],
                               kdj_settings: Dict[str, int]) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            data: 原始K线数据
            ma_periods: MA周期列表
            rsi_periods: RSI周期列表
            macd_settings: MACD参数设置
            kdj_settings: KDJ参数设置
            
        Returns:
            pd.DataFrame: 包含所有技术指标的DataFrame
        """
        try:
            # 复制数据，避免修改原始数据
            result = data.copy()
            
            # 计算MA
            ma_data = cls.calculate_ma(data, ma_periods)
            for key, value in ma_data.items():
                result[key] = value
            
            # 计算MACD
            macd_data = cls.calculate_macd(
                data,
                fast_period=macd_settings['fast_period'],
                slow_period=macd_settings['slow_period'],
                signal_period=macd_settings['signal_period']
            )
            for key, value in macd_data.items():
                result[key] = value
            
            # 计算KDJ
            kdj_data = cls.calculate_kdj(
                data,
                fastk_period=kdj_settings['fastk_period'],
                slowk_period=kdj_settings['slowk_period'],
                slowd_period=kdj_settings['slowd_period']
            )
            for key, value in kdj_data.items():
                result[key] = value
            
            # 计算RSI
            rsi_data = cls.calculate_rsi(data, rsi_periods)
            for key, value in rsi_data.items():
                result[key] = value
            
            return result
            
        except Exception as e:
            logging.error(f"计算技术指标时发生错误: {str(e)}")
            raise

if __name__ == "__main__":
    # 测试代码
    # 创建示例数据
    test_data = pd.DataFrame({
        'close': [100, 102, 101, 103, 102, 104, 103, 105, 104, 106],
        'high': [102, 103, 102, 104, 103, 105, 104, 106, 105, 107],
        'low': [99, 101, 100, 102, 101, 103, 102, 104, 103, 105],
        'volume': [1000] * 10
    })
    
    try:
        # 设置参数
        ma_periods = [5, 10]
        rsi_periods = [6, 12, 24]
        macd_settings = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }
        kdj_settings = {
            'fastk_period': 9,
            'slowk_period': 3,
            'slowd_period': 3
        }
        
        # 计算指标
        result = IndicatorCalculator.calculate_all_indicators(
            test_data,
            ma_periods,
            rsi_periods,
            macd_settings,
            kdj_settings
        )
        
        print("\n计算结果示例：")
        print(result)
    except Exception as e:
        logging.error(f"计算技术指标时发生错误: {str(e)}") 