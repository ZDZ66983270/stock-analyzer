import pandas as pd
import yfinance as yf
from typing import Dict, Optional
from datetime import datetime, timedelta

from config import PERIODS
from utils.time_utils import get_period_timedelta, format_datetime

class KlineDataFetcher:
    """K线数据获取类"""
    
    def __init__(self, symbol: str):
        """
        初始化K线数据获取器
        
        参数:
            symbol: 股票代码
        """
        # 转换A股代码格式
        if symbol.startswith(('sh.', 'sz.')):
            # 将sh.600000转换为600000.SS或sz.000001转换为000001.SZ
            code = symbol[3:]
            market = symbol[:2].upper()
            if market == 'SH':
                self.symbol = f"{code}.SS"
            else:
                self.symbol = f"{code}.SZ"
        else:
            self.symbol = symbol
        
        self.ticker = yf.Ticker(self.symbol)
    
    def fetch_period_data(self, period: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取指定周期的K线数据
        
        参数:
            period: 周期字符串，如 "1d", "4h", "30m"
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            Optional[pd.DataFrame]: K线数据，如果获取失败则返回None
        """
        try:
            # 对于分钟级别数据，需要调整时间范围
            if period.endswith('m'):
                # Yahoo Finance对分钟级别数据有限制，这里做相应调整
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_dt = end_dt - timedelta(days=7)  # 只获取最近7天的分钟数据
                start_date = start_dt.strftime("%Y-%m-%d")
            
            # 获取数据
            interval = period
            if period.endswith('h'):
                # Yahoo Finance使用小时数据时需要特殊处理
                interval = f"{period[:-1]}hour"
            
            data = self.ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            if data.empty:
                print(f"无法获取股票 {self.symbol} 的 {period} 周期数据")
                return None
                
            # 重命名列
            data.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
            
            # 删除不需要的列
            data = data.drop(['Dividends', 'Stock Splits'], axis=1)
            
            # 处理时区
            data.index = data.index.tz_localize(None)
            
            return data
            
        except Exception as e:
            print(f"获取股票 {self.symbol} 的 {period} 周期数据时发生错误: {str(e)}")
            return None
    
    def fetch_all_periods(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        获取所有周期的K线数据
        
        参数:
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            Dict[str, pd.DataFrame]: 不同周期的K线数据字典
        """
        result = {}
        
        for period in PERIODS:
            print(f"正在获取 {self.symbol} 的 {period} 周期数据...")
            data = self.fetch_period_data(period, start_date, end_date)
            if data is not None:
                result[period] = data
        
        return result

def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """
    获取单个股票的所有周期数据
    
    参数:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    返回:
        Dict[str, pd.DataFrame]: 不同周期的K线数据字典
    """
    fetcher = KlineDataFetcher(symbol)
    return fetcher.fetch_all_periods(start_date, end_date) 