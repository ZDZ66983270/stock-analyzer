import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime, timedelta

class CapitalFlowFetcher:
    """资金流向数据获取类"""
    
    def __init__(self, symbol: str):
        """
        初始化资金流向数据获取器
        
        参数:
            symbol: 股票代码
        """
        self.symbol = symbol
    
    def fetch_flow_data(self, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取资金流向数据
        
        参数:
            start_date: 开始日期
            end_date: 结束日期
            
        返回:
            Optional[pd.DataFrame]: 资金流向数据，包含主力流入、流出、净流入等信息
        """
        try:
            # 注意：这里使用模拟数据，实际项目中需要替换为真实的数据源
            # 可以使用东方财富、新浪财经等网站的API
            
            # 创建日期范围
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            date_range = date_range[date_range.dayofweek < 5]  # 排除周末
            
            # 生成模拟数据
            n_days = len(date_range)
            
            # 使用正态分布生成随机数据
            np.random.seed(42)  # 设置随机种子以保证可重复性
            
            inflow = np.abs(np.random.normal(1e7, 5e6, n_days))  # 主力流入，均值1000万
            outflow = np.abs(np.random.normal(1e7, 5e6, n_days))  # 主力流出，均值1000万
            net_flow = inflow - outflow  # 净流入
            
            # 创建DataFrame
            data = pd.DataFrame({
                'MAIN_INFLOW': inflow,
                'MAIN_OUTFLOW': outflow,
                'MAIN_NET_FLOW': net_flow
            }, index=date_range)
            
            return data
            
        except Exception as e:
            print(f"获取股票 {self.symbol} 的资金流向数据时发生错误: {str(e)}")
            return None

def fetch_capital_flow(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    获取单个股票的资金流向数据
    
    参数:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    返回:
        Optional[pd.DataFrame]: 资金流向数据
    """
    fetcher = CapitalFlowFetcher(symbol)
    return fetcher.fetch_flow_data(start_date, end_date) 