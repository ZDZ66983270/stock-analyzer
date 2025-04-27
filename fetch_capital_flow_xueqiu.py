import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Optional, Dict
import logging
from functools import wraps
import json
from config import XUEQIU_HEADERS
from utils.data_validator import DataValidator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def retry_on_exception(retries: int = 3, delay: int = 2):
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
                    if attempt < retries - 1:
                        logging.warning(f"第{attempt + 1}次尝试失败: {str(e)}, {delay}秒后重试...")
                        time.sleep(delay * (attempt + 1))  # 递增延迟
                    else:
                        logging.error(f"最后一次尝试失败: {str(e)}")
            raise last_exception
        return wrapper
    return decorator

class CapitalFlowFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = DataValidator()
        self.request_interval = 1  # 请求间隔（秒）
        self.last_request_time = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Referer': 'https://xueqiu.com'
        }
        
    def fetch_capital_flow(self, symbol: str, days: int = 90) -> Optional[pd.DataFrame]:
        """
        获取股票资金流向数据
        
        Args:
            symbol: 股票代码（如 SH.600536）
            days: 获取天数，默认90天
            
        Returns:
            pd.DataFrame: 包含资金流向数据的DataFrame，如果获取失败则返回None
        """
        try:
            # 解析市场和代码
            market, code = symbol.split('.')
            
            # 构建雪球股票代码
            if market.upper() in {'SH', 'SZ'}:
                xq_symbol = f"{market.upper()}{code}"
            else:
                raise ValueError("目前仅支持A股资金流向数据获取")
                
            # 获取Cookie（这里需要实现登录逻辑）
            cookie = self._get_xueqiu_cookie()
            if not cookie:
                self.logger.error("获取雪球Cookie失败")
                return None
                
            # 构建请求URL
            url = "https://stock.xueqiu.com/v5/stock/capital/flow.json"
            params = {
                "symbol": xq_symbol,
                "period": "all"
            }
            
            # 添加Cookie到请求头
            self.headers['Cookie'] = cookie
            
            # 控制请求频率
            current_time = time.time()
            if current_time - self.last_request_time < self.request_interval:
                time.sleep(self.request_interval)
                
            # 发送请求
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.logger.error(f"请求失败，状态码：{response.status_code}")
                return None
                
            data = response.json()
            if 'data' not in data or 'items' not in data['data']:
                self.logger.error("返回数据格式错误")
                return None
                
            # 解析数据
            items = data['data']['items']
            rows = []
            for item in items:
                row = {
                    'datetime': datetime.fromtimestamp(item['timestamp'] / 1000),
                    'capital_inflow': item['main_inflow'],
                    'capital_outflow': item['main_outflow'],
                    'capital_netflow': item['main_inflow'] - item['main_outflow']
                }
                rows.append(row)
                
            # 创建DataFrame
            df = pd.DataFrame(rows)
            
            # 验证数据
            if not self.validator.validate_capital_flow(df):
                self.logger.error("资金流向数据验证失败")
                return None
                
            self.logger.info(f"成功获取 {len(df)} 条资金流向数据")
            self.last_request_time = time.time()
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取资金流向数据失败: {str(e)}")
            return None
            
    def _get_xueqiu_cookie(self) -> Optional[str]:
        """获取雪球Cookie"""
        try:
            # 访问首页获取Cookie
            response = requests.get(
                "https://xueqiu.com",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return '; '.join([f"{k}={v}" for k, v in response.cookies.items()])
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"获取Cookie失败: {str(e)}")
            return None

def fetch_capital_flow(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取资金流数据的主函数
    
    Args:
        symbol: 股票代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        pd.DataFrame: 资金流数据
    """
    fetcher = CapitalFlowFetcher()
    return fetcher.fetch_capital_flow(symbol)

if __name__ == "__main__":
    # 测试代码
    symbol = "US.AAPL"
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        df = fetch_capital_flow(symbol, start_date, end_date)
        print("\n资金流数据示例：")
        print(df.head())
    except Exception as e:
        print(f"测试失败: {str(e)}") 