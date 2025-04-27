import pandas as pd
import numpy as np
import yfinance as yf
from typing import Union, Optional, Tuple, List

class TechnicalIndicator:
    """技术指标计算类"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化技术指标计算类
        
        参数:
            data (pd.DataFrame): 包含OHLCV数据的DataFrame，
                               需要包含['Open', 'High', 'Low', 'Close', 'Volume']这些列
        """
        self.data = data
        self._validate_data()
    
    def _validate_data(self):
        """验证输入数据的完整性"""
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            raise ValueError(f"数据缺少必需的列: {', '.join(missing_columns)}")
    
    def get_ma(self, period: int = 20) -> pd.Series:
        """
        计算移动平均线
        
        参数:
            period (int): 移动平均的周期，默认20日
            
        返回:
            pd.Series: 移动平均线数据
        """
        return self.data['Close'].rolling(window=period).mean()
    
    def get_ema(self, period: int = 20) -> pd.Series:
        """
        计算指数移动平均线
        
        参数:
            period (int): EMA的周期，默认20日
            
        返回:
            pd.Series: EMA数据
        """
        return self.data['Close'].ewm(span=period, adjust=False).mean()
    
    def get_macd(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算MACD指标
        
        参数:
            fast_period (int): 快线周期，默认12
            slow_period (int): 慢线周期，默认26
            signal_period (int): 信号线周期，默认9
            
        返回:
            Tuple[pd.Series, pd.Series, pd.Series]: (MACD线, 信号线, MACD柱状图)
        """
        fast_ema = self.get_ema(fast_period)
        slow_ema = self.get_ema(slow_period)
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        return macd_line, signal_line, macd_histogram
    
    def get_rsi(self, period: int = 14) -> pd.Series:
        """
        计算RSI指标
        
        参数:
            period (int): RSI周期，默认14日
            
        返回:
            pd.Series: RSI数据
        """
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def get_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算布林带
        
        参数:
            period (int): 移动平均的周期，默认20日
            std_dev (float): 标准差的倍数，默认2
            
        返回:
            Tuple[pd.Series, pd.Series, pd.Series]: (上轨, 中轨, 下轨)
        """
        middle_band = self.get_ma(period)
        std = self.data['Close'].rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        return upper_band, middle_band, lower_band
    
    def get_kdj(self, k_period: int = 9, d_period: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算KDJ指标
        
        参数:
            k_period (int): K值的周期，默认9日
            d_period (int): D值的周期，默认3日
            
        返回:
            Tuple[pd.Series, pd.Series, pd.Series]: (K值, D值, J值)
        """
        low_min = self.data['Low'].rolling(window=k_period).min()
        high_max = self.data['High'].rolling(window=k_period).max()
        rsv = ((self.data['Close'] - low_min) / (high_max - low_min)) * 100
        k = rsv.ewm(span=d_period, adjust=False).mean()
        d = k.ewm(span=d_period, adjust=False).mean()
        j = 3 * k - 2 * d
        return k, d, j
    
    def get_atr(self, period: int = 14) -> pd.Series:
        """
        计算ATR（平均真实波幅）
        
        参数:
            period (int): ATR周期，默认14日
            
        返回:
            pd.Series: ATR数据
        """
        high_low = self.data['High'] - self.data['Low']
        high_close = abs(self.data['High'] - self.data['Close'].shift())
        low_close = abs(self.data['Low'] - self.data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.rolling(window=period).mean()
    
    def get_obv(self) -> pd.Series:
        """
        计算OBV（能量潮指标）
        
        返回:
            pd.Series: OBV数据
        """
        close_diff = self.data['Close'].diff()
        volume = self.data['Volume']
        obv = pd.Series(index=self.data.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close_diff)):
            if close_diff.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close_diff.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv

def get_stock_data(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    获取股票历史数据
    
    参数:
        symbol (str): 股票代码
        start_date (str): 起始日期，格式：'YYYY-MM-DD'
        end_date (str): 结束日期，格式：'YYYY-MM-DD'
        
    返回:
        Optional[pd.DataFrame]: 股票历史数据，如果获取失败则返回None
    """
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(start=start_date, end=end_date)
        if data.empty:
            print(f"无法获取股票 {symbol} 的数据")
            return None
        return data
    except Exception as e:
        print(f"获取股票 {symbol} 数据时发生错误: {str(e)}")
        return None

def get_all_indicators(symbol: str, start_date: str, end_date: str) -> Optional[dict]:
    """
    获取所有技术指标数据
    
    参数:
        symbol (str): 股票代码
        start_date (str): 起始日期，格式：'YYYY-MM-DD'
        end_date (str): 结束日期，格式：'YYYY-MM-DD'
        
    返回:
        Optional[dict]: 包含所有技术指标的字典，如果获取失败则返回None
    """
    data = get_stock_data(symbol, start_date, end_date)
    if data is None:
        return None
    
    try:
        indicator = TechnicalIndicator(data)
        
        # 计算各项指标
        ma_20 = indicator.get_ma(20)
        ma_60 = indicator.get_ma(60)
        ema_12 = indicator.get_ema(12)
        ema_26 = indicator.get_ema(26)
        macd_line, signal_line, macd_hist = indicator.get_macd()
        rsi = indicator.get_rsi()
        upper_band, middle_band, lower_band = indicator.get_bollinger_bands()
        k, d, j = indicator.get_kdj()
        atr = indicator.get_atr()
        obv = indicator.get_obv()
        
        return {
            'MA20': ma_20,
            'MA60': ma_60,
            'EMA12': ema_12,
            'EMA26': ema_26,
            'MACD': {
                'MACD': macd_line,
                'Signal': signal_line,
                'Histogram': macd_hist
            },
            'RSI': rsi,
            'Bollinger': {
                'Upper': upper_band,
                'Middle': middle_band,
                'Lower': lower_band
            },
            'KDJ': {
                'K': k,
                'D': d,
                'J': j
            },
            'ATR': atr,
            'OBV': obv,
            'Price': data['Close']
        }
    except Exception as e:
        print(f"计算技术指标时发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    # 示例用法
    symbol = input("请输入股票代码（例如：AAPL）：")
    start_date = input("请输入起始日期（格式：YYYY-MM-DD）：")
    end_date = input("请输入结束日期（格式：YYYY-MM-DD）：")
    
    indicators = get_all_indicators(symbol, start_date, end_date)
    if indicators:
        print("\n获取到以下技术指标数据：")
        for indicator_name in indicators.keys():
            print(f"- {indicator_name}")
