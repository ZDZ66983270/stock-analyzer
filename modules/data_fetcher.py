import os
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import time
import logging
from typing import Optional, Dict, List, Union

def identify_market(symbol: str) -> str:
    """识别股票市场"""
    if symbol.endswith(".SH"):
        return "SH"
    elif symbol.endswith(".SZ"):
        return "SZ"
    elif symbol.endswith(".HK"):
        return "HK"
    elif symbol.endswith(".US"):
        return "US"
    else:
        return "Unknown"

def fetch_kline(symbol: str, period: str = "daily") -> pd.DataFrame:
    """获取K线数据"""
    try:
        market = identify_market(symbol)
        code = symbol.split('.')[0]
        
        if market in ["SH", "SZ"]:
            # A股数据
            if period == "daily":
                df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            elif period == "weekly":
                df = ak.stock_zh_a_hist(symbol=code, period="weekly", adjust="qfq")
            elif period == "monthly":
                df = ak.stock_zh_a_hist(symbol=code, period="monthly", adjust="qfq")
            elif period.endswith('m'):
                minutes = int(period[:-1])
                df = ak.stock_zh_a_hist_min_em(symbol=code, period=f"{minutes}")
            else:
                return pd.DataFrame()
                
        elif market == "HK":
            # 港股数据
            if period == "daily":
                df = ak.stock_hk_daily(symbol=code)
            elif period.endswith('m'):
                minutes = int(period[:-1])
                df = ak.stock_hk_hist_min_em(symbol=code, period=f"{minutes}")
            else:
                return pd.DataFrame()
                
        elif market == "US":
            # 美股数据
            if period == "daily":
                df = ak.stock_us_daily(symbol=code)
            elif period.endswith('m'):
                minutes = int(period[:-1])
                df = ak.stock_us_hist_min_em(symbol=code, period=f"{minutes}")
            else:
                return pd.DataFrame()
                
        else:
            logging.error(f"不支持的市场类型: {market}")
            return pd.DataFrame()
        
        if df.empty:
            logging.warning(f"无法获取股票 {symbol} 的 {period} 周期数据")
            return pd.DataFrame()
            
        # 统一列名
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "Open": "open",
            "Close": "close",
            "High": "high",
            "Low": "low",
            "Volume": "volume"
        })
        
        return df
        
    except Exception as e:
        logging.error(f"获取{symbol}的{period}数据失败: {str(e)}")
        return pd.DataFrame()

def fetch_all_kline_data(symbol: str) -> dict:
    """获取所有周期的K线数据"""
    try:
        result = {
            "daily": None,
            "weekly": None,
            "monthly": None,
            "2hour": None,
            "1hour": None,
            "30min": None,
            "15min": None,
            "5min": None
        }
        
        market = identify_market(symbol)
        
        # 获取日线数据
        result["daily"] = fetch_kline(symbol, "daily")
        if result["daily"] is None or result["daily"].empty:
            return result
            
        # 获取分钟数据
        if market in ["SH", "SZ"]:
            result["weekly"] = fetch_kline(symbol, "weekly")
            result["monthly"] = fetch_kline(symbol, "monthly")
            
        result["5min"] = fetch_kline(symbol, "5m")
        result["15min"] = fetch_kline(symbol, "15m")
        result["30min"] = fetch_kline(symbol, "30m")
        result["1hour"] = fetch_kline(symbol, "1h")
        result["2hour"] = fetch_kline(symbol, "2h")
        
        # 为每个周期添加技术指标
        for period in ["weekly", "monthly", "2hour", "1hour", "30min", "15min", "5min"]:
            if result[period] is not None and not result[period].empty:
                try:
                    # 计算MA
                    result[period]['MA5'] = result[period]['close'].rolling(window=5).mean()
                    result[period]['MA10'] = result[period]['close'].rolling(window=10).mean()
                    result[period]['MA20'] = result[period]['close'].rolling(window=20).mean()
                    result[period]['MA60'] = result[period]['close'].rolling(window=60).mean()
                    
                    # 计算MACD
                    exp1 = result[period]['close'].ewm(span=12, adjust=False).mean()
                    exp2 = result[period]['close'].ewm(span=26, adjust=False).mean()
                    result[period]['DIF'] = exp1 - exp2
                    result[period]['DEA'] = result[period]['DIF'].ewm(span=9, adjust=False).mean()
                    result[period]['MACD'] = 2 * (result[period]['DIF'] - result[period]['DEA'])
                    
                    # 计算KDJ
                    low_list = result[period]['low'].rolling(window=9, min_periods=9).min()
                    high_list = result[period]['high'].rolling(window=9, min_periods=9).max()
                    rsv = (result[period]['close'] - low_list) / (high_list - low_list) * 100
                    result[period]['K'] = rsv.ewm(com=2).mean()
                    result[period]['D'] = result[period]['K'].ewm(com=2).mean()
                    result[period]['J'] = 3 * result[period]['K'] - 2 * result[period]['D']
                    
                    # 计算RSI
                    delta = result[period]['close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    result[period]['RSI'] = 100 - (100 / (1 + rs))
                    
                except Exception as e:
                    logging.error(f"计算{period}周期技术指标失败: {e}")
        
        return result
        
    except Exception as e:
        logging.error(f"获取 {symbol} K线数据失败: {e}")
        return result

class DataFetcher:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.setup_logging()
        self.setup_directories()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        """创建数据存储目录"""
        for market in ['a', 'hk', 'us']:
            for freq in ['daily', 'weekly', 'monthly', 'minute']:
                path = os.path.join(self.data_dir, market, freq)
                os.makedirs(path, exist_ok=True)
                
    def save_data(self, df: pd.DataFrame, market: str, symbol: str, freq: str):
        """保存数据到Excel文件"""
        if df is None or df.empty:
            return
            
        try:
            # 创建文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{freq}_{timestamp}.xlsx"
            filepath = os.path.join(self.data_dir, market, freq, filename)
            
            # 保存数据
            df.to_excel(filepath, index=True)
            self.logger.info(f"数据已保存: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
            
    def fetch_and_save(self, market: str, symbol: str, start_date: str, 
                      end_date: str, freq: str = 'daily'):
        """获取并保存数据"""
        self.logger.info(f"开始获取数据: {market} {symbol} {freq}")
        
        # 获取数据
        data = fetch_kline(symbol, freq)
        
        if data is not None and not data.empty:
            self.save_data(data, market, symbol, freq)
        else:
            self.logger.warning(f"未获取到有效数据: {market} {symbol} {freq}")
            
    def batch_fetch(self, market: str, symbols: List[str], start_date: str,
                   end_date: str, freqs: List[str] = ['daily']):
        """批量获取数据"""
        for symbol in symbols:
            for freq in freqs:
                self.fetch_and_save(market, symbol, start_date, end_date, freq)
                time.sleep(1)  # 避免请求过于频繁 