import pandas as pd
import numpy as np
from typing import Optional, Tuple
from datetime import datetime, timedelta

class ChipDistributionCalculator:
    """筹码分布计算类"""
    
    def __init__(self, price_data: pd.DataFrame):
        """
        初始化筹码分布计算器
        
        参数:
            price_data: 包含OHLCV数据的DataFrame
        """
        self.price_data = price_data
    
    def calculate_support_resistance(self) -> Tuple[float, float]:
        """
        计算支撑位和压力位
        
        返回:
            Tuple[float, float]: (支撑位, 压力位)
        """
        # 使用过去20天的数据计算
        window = 20
        if len(self.price_data) < window:
            window = len(self.price_data)
        
        recent_data = self.price_data.tail(window)
        
        # 支撑位：取最低价的移动平均
        support = recent_data['Low'].rolling(window=5).min().mean()
        
        # 压力位：取最高价的移动平均
        resistance = recent_data['High'].rolling(window=5).max().mean()
        
        return support, resistance
    
    def calculate_avg_cost(self) -> float:
        """
        计算平均持仓成本
        
        返回:
            float: 平均持仓成本
        """
        # 使用成交量加权平均价格作为平均持仓成本
        vwap = (self.price_data['Close'] * self.price_data['Volume']).sum() / self.price_data['Volume'].sum()
        return vwap
    
    def calculate_distribution(self) -> pd.DataFrame:
        """
        计算完整的筹码分布数据
        
        返回:
            pd.DataFrame: 包含支撑位、压力位、平均成本的数据
        """
        support, resistance = self.calculate_support_resistance()
        avg_cost = self.calculate_avg_cost()
        
        # 为每个交易日计算数据
        result = pd.DataFrame(index=self.price_data.index)
        result['SUPPORT_PRICE'] = support
        result['PRESSURE_PRICE'] = resistance
        result['AVG_COST'] = avg_cost
        
        return result

class ChipDistributionFetcher:
    """筹码分布数据获取类"""
    
    def __init__(self, symbol: str):
        """
        初始化筹码分布数据获取器
        
        参数:
            symbol: 股票代码
        """
        self.symbol = symbol
    
    def fetch_distribution_data(self, price_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        获取筹码分布数据
        
        参数:
            price_data: 股票价格数据
            
        返回:
            Optional[pd.DataFrame]: 筹码分布数据
        """
        try:
            calculator = ChipDistributionCalculator(price_data)
            distribution_data = calculator.calculate_distribution()
            return distribution_data
            
        except Exception as e:
            print(f"计算股票 {self.symbol} 的筹码分布数据时发生错误: {str(e)}")
            return None

def fetch_chip_distribution(symbol: str, price_data: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    获取单个股票的筹码分布数据
    
    参数:
        symbol: 股票代码
        price_data: 股票价格数据
        
    返回:
        Optional[pd.DataFrame]: 筹码分布数据
    """
    fetcher = ChipDistributionFetcher(symbol)
    return fetcher.fetch_distribution_data(price_data) 