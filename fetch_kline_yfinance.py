import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import time
from functools import wraps
import logging
from config import PERIODS
import re
from utils.data_validator import DataValidator

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

def retry_on_exception(retries: int = 3, delay: int = 1):
    """
    重试装饰器
    
    Args:
        retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:  # 如果不是最后一次尝试
                        logging.warning(f"第{attempt + 1}次尝试失败: {str(e)}, {delay}秒后重试...")
                        time.sleep(delay)
                    else:
                        logging.error(f"最后一次尝试失败: {str(e)}")
            raise last_exception
        return wrapper
    return decorator

class YFinanceKlineFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.retry_delay = 2
        self.validator = DataValidator()
        self.request_interval = 1  # 请求间隔（秒）
        self.last_request_time = 0
        
        # 支持的周期及其对应的历史数据长度
        self.periods = {
            '5m': '7d',    # 7天
            '15m': '7d',   # 7天
            '30m': '60d',  # 60天
            '1h': '180d',  # 180天
            '4h': '2y',    # 2年
            '1d': '5y'     # 5年
        }

    def get_market_type(self, symbol: str) -> str:
        """
        判断股票市场类型
        :param symbol: 股票代码
        :return: 市场类型 (US/HK/SH/SZ)
        """
        symbol = str(symbol).upper().strip()
        
        if symbol.endswith('.HK'):
            return 'HK'
        elif symbol.endswith(('.SS', '.SH')):
            return 'SH'
        elif symbol.endswith('.SZ'):
            return 'SZ'
        elif symbol.isdigit():
            if len(symbol) == 6:
                if symbol.startswith('6'):
                    return 'SH'
                elif symbol.startswith(('0', '3')):
                    return 'SZ'
            elif len(symbol) <= 4:
                return 'HK'
        
        return 'US'

    def convert_symbol_to_yf(self, symbol: str) -> str:
        """
        转换股票代码为yfinance支持的格式
        :param symbol: 原始股票代码
        :return: 转换后的股票代码
        """
        symbol = str(symbol).strip()
        market_type = self.get_market_type(symbol)
        self.logger.info(f"市场类型: {market_type}, 原始股票代码: {symbol}")

        # 移除可能存在的后缀
        clean_symbol = symbol.upper().split('.')[0]

        if market_type == 'HK':
            # 港股统一使用4位数字格式
            numeric_symbol = clean_symbol.zfill(4)
            return f"{numeric_symbol}.HK"
        elif market_type == 'SH':
            # 上证股票
            numeric_symbol = clean_symbol.zfill(6)
            return f"{numeric_symbol}.SS"
        elif market_type == 'SZ':
            # 深证股票
            numeric_symbol = clean_symbol.zfill(6)
            return f"{numeric_symbol}.SZ"
        else:
            # 美股保持原样
            return clean_symbol

    def convert_period_to_yf(self, period: str) -> str:
        """
        转换时间周期为yfinance支持的格式
        :param period: 时间周期
        :return: yfinance支持的时间周期格式
        """
        period_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '60m': '60m',
            '1d': '1d',
            '1w': '1wk',
            '1M': '1mo'
        }
        return period_map.get(period, period)

    def parse_date(self, date_str: str) -> datetime:
        """
        解析日期字符串为datetime对象
        :param date_str: 日期字符串 (YYYY-MM-DD格式)
        :return: datetime对象
        """
        return datetime.strptime(date_str, '%Y-%m-%d')

    def adjust_interval_start_date(self, period: str, start_date: str) -> datetime:
        """
        根据时间周期调整开始日期
        :param period: 时间周期
        :param start_date: 开始日期
        :return: 调整后的开始日期
        """
        now = datetime.now()
        start_date = self.parse_date(start_date)
        
        # 根据不同周期限制历史数据范围
        period_limits = {
            '1m': 7,
            '5m': 60,
            '15m': 60,
            '30m': 60,
            '60m': 730,
            '1d': 10000,
            '1wk': 10000,
            '1M': 10000
        }
        
        days = period_limits.get(period, 10000)
        adjusted_start = max(start_date, now - timedelta(days=days))
        return adjusted_start

    def fetch_single_period(self, symbol: str, period: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取单个周期的K线数据
        :param symbol: 股票代码
        :param period: 时间周期
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: K线数据DataFrame或None
        """
        yf_symbol = self.convert_symbol_to_yf(symbol)
        yf_period = self.convert_period_to_yf(period)
        start_date = self.adjust_interval_start_date(period, start_date)
        end_date = self.parse_date(end_date)

        for attempt in range(self.max_retries):
            try:
                stock = yf.Ticker(yf_symbol)
                df = stock.history(
                    period='max',
                    start=start_date,
                    end=end_date,
                    interval=yf_period
                )
                
                if df.empty:
                    self.logger.warning(f"获取到空数据: {yf_symbol}, period={yf_period}")
                    return None
                
                return df
                
            except Exception as e:
                self.logger.error(f"获取数据失败 (尝试 {attempt + 1}/{self.max_retries}): {yf_symbol}, {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"达到最大重试次数，放弃获取: {yf_symbol}")
                    return None

    def fetch_kline_data(self, symbol: str, periods: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        获取多个周期的K线数据
        :param symbol: 股票代码
        :param periods: 时间周期列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 包含不同周期数据的字典
        """
        result = {}
        for period in periods:
            df = self.fetch_single_period(symbol, period, start_date, end_date)
            if df is not None:
                result[period] = df
        return result

    def fetch_kline(self, symbol: str, interval: str = '1d', period: str = '5y') -> Optional[pd.DataFrame]:
        """
        从yfinance获取K线数据
        
        Args:
            symbol: 股票代码（如 AAPL, MSFT）
            interval: 时间间隔（1m,5m,15m,30m,60m,1d）
            period: 时间范围（1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max）
            
        Returns:
            pd.DataFrame: 包含OHLCV数据的DataFrame，None表示获取失败
        """
        try:
            logger.info(f"开始获取{symbol}的{interval}周期数据...")
            
            # 移除市场前缀（如US.）
            if '.' in symbol:
                symbol = symbol.split('.')[1]
            
            # 创建Ticker对象
            ticker = yf.Ticker(symbol)
            
            # 获取历史数据
            df = ticker.history(period=period, interval=interval)
            
            if df is None or df.empty:
                logger.error(f"获取{symbol}数据失败：返回空数据")
                return None
                
            # 统一列名为小写
            df.columns = [col.lower() for col in df.columns]
            
            # 重置索引，保留时间列
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'datetime'}, inplace=True)
            
            # 计算成交额
            if 'amount' not in df.columns:
                df['amount'] = df['close'] * df['volume']
            
            logger.info(f"成功获取{len(df)}条{interval}周期数据")
            return df
            
        except Exception as e:
            logger.error(f"获取{symbol}数据时发生错误: {str(e)}")
            return None

def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """
    获取股票数据的主函数
    :param symbol: 股票代码
    :param start_date: 开始日期 (YYYY-MM-DD)
    :param end_date: 结束日期 (YYYY-MM-DD)
    :return: 包含不同周期数据的字典
    """
    fetcher = YFinanceKlineFetcher()
    return fetcher.fetch_kline_data(symbol, PERIODS, start_date, end_date)

def test_symbol_conversion():
    """
    测试股票代码转换功能
    """
    fetcher = YFinanceKlineFetcher()
    test_cases = [
        # 港股测试用例
        ('0700', '0700.HK'),  # 腾讯控股
        ('700', '0700.HK'),
        ('9988', '9988.HK'),  # 阿里巴巴
        ('9988.HK', '9988.HK'),
        
        # A股测试用例
        ('600000', '600000.SS'),  # 浦发银行
        ('600000.SH', '600000.SS'),
        ('000001', '000001.SZ'),  # 平安银行
        ('000001.SZ', '000001.SZ'),
        ('300059', '300059.SZ'),  # 东方财富
        
        # 美股测试用例
        ('AAPL', 'AAPL'),
        ('GOOGL', 'GOOGL'),
        ('BABA', 'BABA'),
    ]
    
    print("\n开始测试股票代码转换...")
    for original, expected in test_cases:
        result = fetcher.convert_symbol_to_yf(original)
        status = '✓' if result == expected else '✗'
        print(f"{status} {original:10} -> {result:10} {'(预期: ' + expected + ')' if result != expected else ''}")

if __name__ == '__main__':
    test_symbol_conversion()
    # 测试代码
    test_symbol = 'AAPL'
    df = fetch_kline(test_symbol)
    if df is not None:
        print(df.head()) 