import sys
import os
import logging
from typing import List, Tuple, Dict, Optional, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import time
import requests
from bs4 import BeautifulSoup
import xlsxwriter
import argparse
from utils.excel_exporter import ExcelExporter
from utils.data_validator import DataValidator
import pytz
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_analyzer.log'),
        logging.StreamHandler()
    ]
)

class StockAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 支持的市场前缀
        self.valid_prefixes = {'US', 'SH', 'SZ', 'HK'}
        # 最大支持的股票数量
        self.max_stocks = 10
        # 支持的周期及其对应的历史数据长度
        self.periods = {
            '15m': '7d',    # 拉7天数据，确保MACD/KDJ/RSI能正常计算
            '30m': '14d',   # 拉14天数据
            '1h': '30d',    # 拉30天数据
            '2h': '60d',    # 拉60天数据
            '1d': '60d'     # 拉60天数据，足够计算技术指标
        }
        # 技术指标的默认参数
        self.indicator_params = {
            'ma': {
                'periods': [5, 10, 20]
            },
            'macd': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            },
            'kdj': {
                'n': 9,
                'k_period': 3,
                'd_period': 3
            },
            'rsi': {
                'periods': [6, 12, 24]
            }
        }
        # 输出目录
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 请求间隔（秒）
        self.request_interval = 1
        
        # 上次请求时间
        self.last_request_time = 0
        
        # 数据源配置
        self.data_sources = {
            'US': ['yfinance'],
            'SH': ['xueqiu'],
            'SZ': ['xueqiu'],
            'HK': ['xueqiu']
        }
        
        # 雪球Cookie（可选，不设置时使用游客模式）
        self.xueqiu_cookie = os.getenv('XUEQIU_COOKIE', '')
        
        # 修改KDJ基准值设置，增加周期维度
        self.kdj_base = {
            '1d': {'date': None, 'k': 50.0, 'd': 50.0, 'j': 50.0},
            '1h': {'datetime': None, 'k': 50.0, 'd': 50.0, 'j': 50.0},
            '30m': {'datetime': None, 'k': 50.0, 'd': 50.0, 'j': 50.0},
            '15m': {'datetime': None, 'k': 50.0, 'd': 50.0, 'j': 50.0}
        }
        
        self.excel_exporter = ExcelExporter()
        self.data_validator = DataValidator()
        
        self.price_limits = {
            'min': 0.01,  # 最小价格
            'max': 1000000  # 最大价格
        }
        self.volume_limits = {
            'min': 0,  # 最小成交量
            'max': 1000000000000  # 最大成交量（1万亿）
        }
        
    def get_latest_trading_day(self, market: str) -> datetime:
        """
        获取指定市场的最新交易日
        
        Args:
            market: 市场代码（US/HK/SH/SZ）
        Returns:
            datetime: 最新交易日（如果当日为交易日且在交易时段内，则返回当日）
        """
        try:
            # 获取当前时间（市场所在时区）
            tz = self.market_timezones[market]
            now = datetime.now(tz)
            
            # 定义各市场的交易时间
            market_hours = {
                'US': {
                    'start': 9.5,   # 9:30
                    'end': 16.0,    # 16:00
                    'timezone': 'America/New_York'
                },
                'HK': {
                    'start': 9.5,   # 9:30
                    'end': 16.0,    # 16:00
                    'timezone': 'Asia/Hong_Kong'
                },
                'SH': {
                    'start': 9.5,   # 9:30
                    'end': 15.0,    # 15:00
                    'timezone': 'Asia/Shanghai'
                },
                'SZ': {
                    'start': 9.5,   # 9:30
                    'end': 15.0,    # 15:00
                    'timezone': 'Asia/Shanghai'
                }
            }
            
            # 获取市场时间信息
            market_info = market_hours[market]
            market_tz = pytz.timezone(market_info['timezone'])
            market_time = now.astimezone(market_tz)
            
            # 计算当前小时数（包含小数部分）
            current_hour = market_time.hour + market_time.minute / 60.0
            
            # 判断是否为交易日
            is_trading_day = market_time.weekday() < 5  # 周一至周五
            
            # 判断是否在交易时段
            is_trading_hours = (market_info['start'] <= current_hour <= market_info['end'])
            
            if is_trading_day and is_trading_hours:
                # 如果是交易日且在交易时段内，返回当前日期
                self.logger.info(f"{market}市场当前正在交易中")
                return market_time.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # 如果不在交易时段，获取最近的交易日
                current_date = market_time.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # 如果当天不是交易日或已经收盘，回退到上一个交易日
                if not is_trading_day or current_hour > market_info['end']:
                    current_date -= timedelta(days=1)
                    while current_date.weekday() >= 5:  # 跳过周末
                        current_date -= timedelta(days=1)
                
                self.logger.info(f"{market}市场当前未在交易，使用最近交易日：{current_date.strftime('%Y-%m-%d')}")
                return current_date
            
        except Exception as e:
            self.logger.error(f"获取最新交易日失败: {str(e)}")
            # 返回当前日期作为后备
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def fetch_stock_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict[str, pd.DataFrame]: 包含不同周期数据的字典
        """
        try:
            results = {}
            
            # 获取K线数据
            if symbol.startswith('US.'):
                # 美股使用雪球API
                for period in self.periods.keys():
                    try:
                        self.logger.info(f"从雪球获取{symbol}的{period}周期数据")
                        df = self._fetch_xueqiu_data(symbol, period)
                        
                        if df is not None and not df.empty:
                            results[period] = df
                            self.logger.info(f"成功获取{len(df)}条{period}周期数据")
                            
                    except Exception as e:
                        self.logger.error(f"获取{period}周期数据失败: {str(e)}")
                        continue
                        
            else:
                # A股和港股使用东方财富API
                for period in self.periods.keys():
                    try:
                        self.logger.info(f"从东方财富获取{symbol}的{period}周期数据")
                        df = self._fetch_eastmoney_data(symbol, period)
                        
                        if df is not None and not df.empty:
                            results[period] = df
                            self.logger.info(f"成功获取{len(df)}条{period}周期数据")
                            
                    except Exception as e:
                        self.logger.error(f"获取{period}周期数据失败: {str(e)}")
                        continue
            
            if not results:
                raise ValueError(f"未能获取到{symbol}的任何数据")
            
            # 获取资金流向数据（仅限A股）
            if symbol.startswith(('SH.', 'SZ.')):
                try:
                    # 首先尝试从东方财富获取资金流向数据
                    fund_flow_df = self._fetch_eastmoney_fund_flow(symbol)
                    
                    # 如果东方财富获取失败，尝试从腾讯财经获取
                    if fund_flow_df is None:
                        self.logger.info("从东方财富获取资金流向数据失败，尝试从腾讯财经获取...")
                        fund_flow_df = self._fetch_qq_fund_flow(symbol)
                    
                    # 如果腾讯财经也获取失败，尝试从通达信获取
                    if fund_flow_df is None:
                        self.logger.info("从腾讯财经获取资金流向数据失败，尝试从通达信获取...")
                        fund_flow_df = self._fetch_tdx_fund_flow(symbol)
                    
                    if fund_flow_df is not None and not fund_flow_df.empty:
                        results['fund_flow'] = fund_flow_df
                        self.logger.info("成功获取资金流向数据")
                    else:
                        self.logger.warning("所有数据源都无法获取到资金流向数据")
                        
                except Exception as e:
                    self.logger.error(f"获取资金流向数据失败: {str(e)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"获取股票数据失败: {str(e)}")
            if isinstance(e, ValueError):
                raise
            return {}

    def _get_xueqiu_cookie(self) -> str:
        """
        获取雪球网站的cookie
        """
        try:
            # 使用固定的token
            xq_tokens = {
                'xq_a_token': '1dca4f6e362b6d93e96297c4a1be072928647d75',
                'xq_r_token': 'ec2cfc4cd5a99fa5687b4479e954c899d7ef06a1'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 构建cookie字符串
            cookie_str = f"xq_a_token={xq_tokens['xq_a_token']}; xq_r_token={xq_tokens['xq_r_token']}"
            
            # 首先访问首页获取其他必要的cookie
            session = requests.Session()
            session.headers.update(headers)
            session.cookies.update({k: v for k, v in [cookie.split('=') for cookie in cookie_str.split('; ')]})
            
            response = session.get('https://xueqiu.com/', allow_redirects=True)
            
            if response.status_code == 200:
                # 获取所有cookie并合并
                all_cookies = session.cookies.get_dict()
                all_cookies.update(xq_tokens)
                
                # 构建最终的cookie字符串
                final_cookie_str = '; '.join([f"{k}={v}" for k, v in all_cookies.items()])
                
                self.logger.info("成功获取雪球cookie")
                return final_cookie_str
            else:
                self.logger.error(f"获取雪球cookie失败，状态码: {response.status_code}")
                return cookie_str  # 返回基础token作为后备
            
        except Exception as e:
            self.logger.error(f"获取雪球cookie时发生错误: {str(e)}")
            return ''

    def _fetch_xueqiu_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        从雪球获取股票数据
        """
        max_retries = 3
        retry_delay = 2
        
        # 修改周期映射
        period_map = {
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '1d': '101'  # 日K使用101
        }
        
        for retry in range(max_retries):
            try:
                market, code = symbol.split('.')
                
                # 构建雪球股票代码
                if market == 'HK':
                    xq_symbol = f"HK{code}"
                else:  # SH或SZ
                    xq_symbol = f"{market}{code}"
                
                # 获取当前时间戳
                end_time = int(time.time() * 1000)
                
                # 根据周期确定开始时间和请求参数
                period_params = {
                    '15m': {'count': 480},   # 15分钟线，取7天
                    '30m': {'count': 960},   # 30分钟线，取60天
                    '1h': {'count': 1440},   # 60分钟线，取180天
                    '1d': {'count': 1800}    # 日线，取5年
                }
                
                params = period_params.get(period)
                if not params:
                    raise ValueError(f"不支持的时间周期: {period}")
                
                # 构建请求URL
                base_url = "https://stock.xueqiu.com/v5/stock/chart"
                url = f"{base_url}/minute.json" if period != '1d' else f"{base_url}/kline.json"
                
                params.update({
                    'symbol': xq_symbol,
                    'period': period_map.get(period, '101'),
                    'type': 'before',
                    'indicator': 'kline,ma,vol',
                    'timestamp': end_time,
                    'count': params['count']
                })
                
                # 获取新的cookie
                if not self.xueqiu_cookie or retry > 0:
                    self.xueqiu_cookie = self._get_xueqiu_cookie()
                
                # 构建请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Cookie': self.xueqiu_cookie,
                    'Referer': f'https://xueqiu.com/S/{xq_symbol}',
                    'sec-ch-ua': '"Chromium";v="122", "Google Chrome";v="122", "Not(A:Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"macOS"',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin'
                }
                
                # 使用session保持连接
                session = requests.Session()
                session.headers.update(headers)
                response = session.get(url, params=params, timeout=10)
                
                if response.status_code != 200:
                    self.logger.error(f"请求失败，状态码: {response.status_code}，响应内容: {response.text}")
                    if retry < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return None
                
                data = response.json()
                
                if 'data' in data and ('items' in data['data'] or 'item' in data['data']):
                    items = data['data'].get('items') or data['data'].get('item', [])
                    
                    if not items:
                        self.logger.warning(f"获取到的数据为空: {xq_symbol}")
                        if retry < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return None
                    
                    # 解析数据
                    df_data = []
                    for item in items:
                        if isinstance(item, list):  # K线数据格式
                            df_data.append({
                                'datetime': pd.to_datetime(item[0], unit='ms'),
                                'open': float(item[2]),
                                'high': float(item[3]),
                                'low': float(item[4]),
                                'close': float(item[5]),
                                'volume': float(item[6]),
                                'amount': float(item[7]) if len(item) > 7 else float(item[5]) * float(item[6])
                            })
                        else:  # 分钟数据格式
                            df_data.append({
                                'datetime': pd.to_datetime(item['timestamp'], unit='ms'),
                                'open': float(item['open']),
                                'high': float(item['high']),
                                'low': float(item['low']),
                                'close': float(item['close']),
                                'volume': float(item['volume']),
                                'amount': float(item['amount'])
                            })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.sort_values('datetime', inplace=True)
                        self.logger.info(f"成功获取{symbol} {period}周期数据，共{len(df)}条记录")
                        return df
                
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                
                return None
                
            except Exception as e:
                self.logger.error(f"从雪球获取数据失败 (重试 {retry + 1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return None

    def _fetch_eastmoney_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        从东方财富获取股票数据
        
        Args:
            symbol: 股票代码
            period: 时间周期
        """
        try:
            market, code = symbol.split('.')
            
            # 转换市场代码
            market_map = {
                'SH': '1',
                'SZ': '0',
                'HK': '116'  # 港股
            }
            
            if market not in market_map:
                raise ValueError(f"不支持的市场: {market}")
            
            # 转换周期
            period_map = {
                '1m': '1',
                '5m': '5',
                '15m': '15',
                '30m': '30',
                '1h': '60',
                '2h': '120',  # 添加2小时周期
                '1d': '101',
                '1w': '102',
                '1M': '103'
            }
            
            if period not in period_map:
                raise ValueError(f"不支持的周期: {period}")
            
            # 根据周期设置数据条数限制
            limit_map = {
                '15m': 7 * 48,     # 7天 * 每天48个15分钟
                '30m': 14 * 24,    # 14天 * 每天24个30分钟
                '1h': 30 * 12,     # 30天 * 每天12个小时
                '2h': 60 * 6,      # 60天 * 每天6个2小时
                '1d': 60           # 60天
            }
            
            # 构建请求参数
            params = {
                'secid': f"{market_map[market]}.{code}",  # 股票ID
                'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': period_map[period],  # 周期
                'fqt': '1',  # 复权类型：0不复权 1前复权 2后复权
                'end': '20500101',
                'lmt': str(limit_map.get(period, 1000))  # 数据条数限制
            }
            
            # 发送请求
            url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.logger.error(f"请求失败，状态码: {response.status_code}")
                return None
            
            data = response.json()
            
            if data['rc'] != 0 or 'data' not in data or 'klines' not in data['data']:
                self.logger.error(f"获取数据失败: {data.get('msg', '未知错误')}")
                return None
            
            # 解析数据
            klines = data['data']['klines']
            df_data = []
            
            for line in klines:
                fields = line.split(',')
                if len(fields) >= 7:
                    df_data.append({
                        'datetime': pd.to_datetime(fields[0]),
                        'open': float(fields[1]),
                        'close': float(fields[2]),
                        'high': float(fields[3]),
                        'low': float(fields[4]),
                        'volume': float(fields[5]),
                        'amount': float(fields[6])
                    })
            
            if df_data:
                df = pd.DataFrame(df_data)
                df.sort_values('datetime', inplace=True)
                # 只保留最近的数据
                df = df.tail(limit_map.get(period, len(df)))
                self.logger.info(f"成功获取{symbol} {period}周期数据，共{len(df)}条记录")
                return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"从东方财富获取数据失败: {str(e)}")
            return None

    def calculate_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        计算各个周期的技术指标
        
        Args:
            data: 不同周期的数据字典
            
        Returns:
            Dict[str, Dict]: 各个周期的指标数据
        """
        try:
            # 首先验证所有周期的数据
            validation_errors = self.data_validator.validate_all_periods(data)
            if validation_errors:
                self.logger.error("数据验证失败:")
                for error in validation_errors:
                    self.logger.error(error)
                return {}
                
            results = {}
            for period, df in data.items():
                self.logger.info(f"计算{period}周期的技术指标...")
                
                # 跳过资金流向数据的技术指标计算
                if period == 'fund_flow':
                    results[period] = df
                    continue
                
                # 计算各项技术指标
                try:
                    macd_data = self.calculate_macd(df)
                    kdj_data = self.calculate_kdj(df)
                    rsi_data = self.calculate_rsi(df)
                    
                    results[period] = {
                        'macd': macd_data,
                        'kdj': kdj_data,
                        'rsi': rsi_data
                    }
                    
                    self.logger.info(f"{period}周期指标计算完成")
                    
                except Exception as e:
                    self.logger.error(f"{period}周期指标计算失败: {str(e)}")
                    results[period] = {}
            
            return results
            
        except Exception as e:
            self.logger.error(f"计算技术指标时发生错误: {str(e)}")
            return {}

    def calculate_macd(self, data: pd.DataFrame, period: str = '1d') -> pd.DataFrame:
        """
        计算MACD指标
        MACD: 移动平均收敛散度
        参数:
            - fast_period: 快速EMA周期（默认12）
            - slow_period: 慢速EMA周期（默认26）
            - signal_period: 信号线周期（默认9）
        """
        try:
            params = self.indicator_params['macd']
            close = data['close']
            
            # 计算快速和慢速EMA
            exp1 = close.ewm(span=params['fast_period'], adjust=False).mean()
            exp2 = close.ewm(span=params['slow_period'], adjust=False).mean()
            
            # 计算MACD线
            macd = exp1 - exp2
            
            # 计算信号线
            signal = macd.ewm(span=params['signal_period'], adjust=False).mean()
            
            # 计算MACD柱状图
            hist = 2 * (macd - signal)  # MACD柱状图
            
            # 添加到原始数据中
            data[f'MACD_{period}'] = macd.round(3)
            data[f'MACD_{period}_Signal'] = signal.round(3)
            data[f'MACD_{period}_Hist'] = hist.round(3)
            
            # 记录最新状态
            latest = data.iloc[-1]
            print(f"\n{period}周期MACD指标计算完成：")
            print(f"- MACD线：{latest[f'MACD_{period}']:.3f}")
            print(f"- 信号线：{latest[f'MACD_{period}_Signal']:.3f}")
            print(f"- 柱状图：{latest[f'MACD_{period}_Hist']:.3f}")
            
            return data
            
        except Exception as e:
            print(f"计算MACD指标时发生错误: {str(e)}")
            return data

    def calculate_kdj(self, data: pd.DataFrame, period: str = '1d') -> pd.DataFrame:
        """
        计算KDJ指标，支持不同周期
        
        Args:
            data: 数据DataFrame
            period: 周期，支持 '1d', '1h', '30m', '15m'等
        """
        try:
            # 确保必要的列存在且为数值类型
            required_columns = ['high', 'low', 'close']
            for col in required_columns:
                if col not in data.columns:
                    print(f"缺少必要的列：{col}")
                    return data
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # 计算RSV
            n = self.indicator_params['kdj']['n']  # 默认9日KDJ
            k_period = self.indicator_params['kdj']['k_period']  # 默认3日K值
            d_period = self.indicator_params['kdj']['d_period']  # 默认3日D值
            
            # 使用rolling计算n日内的最高价和最低价
            high_n = data['high'].rolling(window=n, min_periods=1).max()
            low_n = data['low'].rolling(window=n, min_periods=1).min()
            
            # 计算RSV，处理为0的情况
            rsv = (data['close'] - low_n) * 100 / (high_n - low_n)
            rsv = rsv.fillna(50)  # 处理分母为0的情况，设为50
            
            # 初始化K、D值
            k = pd.Series(index=data.index, dtype=float)
            d = pd.Series(index=data.index, dtype=float)
            
            # 设置初始值
            k.iloc[0] = 50.0
            d.iloc[0] = 50.0
            
            # 计算K、D值
            for i in range(1, len(data)):
                k.iloc[i] = (k_period - 1) / k_period * k.iloc[i-1] + rsv.iloc[i] / k_period
                d.iloc[i] = (d_period - 1) / d_period * d.iloc[i-1] + k.iloc[i] / d_period
            
            # 计算J值
            j = 3 * k - 2 * d
            
            # 限制KDJ的范围在0-100之间
            k = k.clip(0, 100)
            d = d.clip(0, 100)
            j = j.clip(0, 100)
            
            # 添加到原始数据中
            data[f'KDJ_{period}_K'] = k.round(2)
            data[f'KDJ_{period}_D'] = d.round(2)
            data[f'KDJ_{period}_J'] = j.round(2)
            
            # 记录最新状态
            latest = data.iloc[-1]
            print(f"\n{period}周期KDJ指标计算完成：")
            print(f"- K值：{latest[f'KDJ_{period}_K']:.2f}")
            print(f"- D值：{latest[f'KDJ_{period}_D']:.2f}")
            print(f"- J值：{latest[f'KDJ_{period}_J']:.2f}")
            
            return data
            
        except Exception as e:
            print(f"计算KDJ指标时发生错误: {str(e)}")
            return data

    def calculate_rsi(self, data: pd.DataFrame, period: str = '1d') -> pd.DataFrame:
        """
        计算RSI指标（6日，12日，24日），支持不同周期
        RSI = 100 - (100 / (1 + RS))
        RS = 平均上涨幅度 / 平均下跌幅度
        
        Args:
            data: 数据DataFrame
            period: 周期，支持 '1d', '1h', '30m', '15m'等
        """
        try:
            # 计算价格变化
            delta = data['close'].diff()
            
            # 计算三个不同周期的RSI
            periods = [6, 12, 24]  # RSI 1, RSI 2, RSI 3
            
            for rsi_period in periods:
                # 分别获取上涨和下跌幅度
                gain = delta.copy()
                loss = delta.copy()
                gain[gain < 0] = 0
                loss[loss > 0] = 0
                loss = -loss  # 转换为正值
                
                # 处理第一个值
                first_valid = delta.first_valid_index()
                if first_valid is not None:
                    gain.iloc[first_valid] = 0
                    loss.iloc[first_valid] = 0
                
                # 计算初始平均值（使用简单移动平均）
                avg_gain = gain.rolling(window=rsi_period, min_periods=1).mean()
                avg_loss = loss.rolling(window=rsi_period, min_periods=1).mean()
                
                # 计算平滑移动平均
                for i in range(rsi_period, len(delta)):
                    avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (rsi_period-1) + gain.iloc[i]) / rsi_period
                    avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (rsi_period-1) + loss.iloc[i]) / rsi_period
                
                # 计算相对强度（RS）
                rs = avg_gain / avg_loss
                
                # 处理除以0的情况
                rs = rs.replace([np.inf, -np.inf], 100)  # 当avg_loss为0时，设置较大的RS值
                rs = rs.fillna(1)  # 当avg_gain和avg_loss都为0时，设置RS为1
                
                # 计算RSI并确保在0-100范围内
                rsi = 100 - (100 / (1 + rs))
                rsi = rsi.clip(0, 100)  # 限制在0-100范围内
                
                # 处理价格不变的情况
                no_change_mask = (gain == 0) & (loss == 0)
                rsi[no_change_mask] = 50  # 价格不变时RSI设为50
                
                # 添加到数据中
                data[f'RSI_{period}_{rsi_period}'] = rsi.round(2)
            
            # 记录最新状态
            latest = data.iloc[-1]
            print(f"\n{period}周期RSI指标计算完成：")
            for rsi_period in periods:
                print(f"- RSI_{rsi_period}：{latest[f'RSI_{period}_{rsi_period}']:.2f}")
            
            return data
            
        except Exception as e:
            print(f"计算RSI指标时发生错误: {str(e)}")
            return data

    def calculate_ma(self, data: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            data: 数据DataFrame
            period: 周期标识
        Returns:
            pd.DataFrame: 添加了MA指标的DataFrame
        """
        try:
            ma_periods = self.indicator_params['ma']['periods']
            
            for p in ma_periods:
                col_name = f'ma{p}_{period}'  # 使用与其他指标一致的命名方式
                data[col_name] = data['close'].rolling(window=p).mean().round(3)
            
            # 记录最新状态
            latest = data.iloc[-1]
            print(f"\n{period}周期MA指标计算完成：")
            for p in ma_periods:
                print(f"- MA{p}：{latest[f'ma{p}_{period}']:.3f}")
            
            return data
            
        except Exception as e:
            print(f"计算MA指标时发生错误: {str(e)}")
            return data

    def save_to_excel(self, data_dict: Dict[str, pd.DataFrame], symbol: str) -> None:
        """
        将数据保存到Excel文件
        
        Args:
            data_dict: 包含不同周期数据的字典
            symbol: 股票代码
        """
        try:
            # 构建输出文件路径
            output_file = f"output/{symbol.replace('.', '_')}_data.xlsx"
            
            # 定义标准列顺序
            standard_columns = [
                'datetime', 'open', 'high', 'low', 'close', 'volume', 'amount',
                'capital_main', 'capital_super', 'capital_big', 'capital_middle', 'capital_small',
                'MACD_15m', 'MACD_15m_Signal', 'MACD_15m_Hist',
                'MACD_30m', 'MACD_30m_Signal', 'MACD_30m_Hist',
                'MACD_1h', 'MACD_1h_Signal', 'MACD_1h_Hist',
                'MACD_1d', 'MACD_1d_Signal', 'MACD_1d_Hist',
                'KDJ_15m_K', 'KDJ_15m_D', 'KDJ_15m_J',
                'KDJ_30m_K', 'KDJ_30m_D', 'KDJ_30m_J',
                'KDJ_1h_K', 'KDJ_1h_D', 'KDJ_1h_J',
                'KDJ_1d_K', 'KDJ_1d_D', 'KDJ_1d_J',
                'RSI_15m_6', 'RSI_15m_12', 'RSI_15m_24',
                'RSI_30m_6', 'RSI_30m_12', 'RSI_30m_24',
                'RSI_1h_6', 'RSI_1h_12', 'RSI_1h_24',
                'RSI_1d_6', 'RSI_1d_12', 'RSI_1d_24',
                'ma5_15m', 'ma10_15m', 'ma20_15m',
                'ma5_30m', 'ma10_30m', 'ma20_30m',
                'ma5_1h', 'ma10_1h', 'ma20_1h',
                'ma5_1d', 'ma10_1d', 'ma20_1d'
            ]
            
            # 创建Excel写入器
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 保存资金流向数据
                if 'fund_flow' in data_dict:
                    fund_flow_df = data_dict['fund_flow']
                    # 确保所有列都存在
                    for col in ['capital_main', 'capital_super', 'capital_big', 'capital_middle', 'capital_small']:
                        if col not in fund_flow_df.columns:
                            fund_flow_df[col] = None
                    fund_flow_df.to_excel(writer, sheet_name='资金流向', index=False)
                
                # 保存各个周期的数据
                for period in ['1d', '1h', '30m', '15m']:
                    if period in data_dict:
                        df = data_dict[period]
                        # 确保所有列都存在
                        for col in standard_columns:
                            if col not in df.columns:
                                df[col] = None
                        # 按标准列顺序重新排列
                        df = df[standard_columns]
                        df.to_excel(writer, sheet_name=f'{period}数据', index=False)
            
            print(f"数据已保存到: {output_file}")
            
        except Exception as e:
            print(f"保存Excel文件失败: {str(e)}")

    def _fetch_eastmoney_fund_flow(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        从东方财富获取资金流向数据
        """
        try:
            market, code = symbol.split('.')
            
            # 转换市场代码
            market_map = {
                'SH': '1',
                'SZ': '0',
                'HK': '116'
            }
            
            if market not in market_map:
                raise ValueError(f"不支持的市场: {market}")
            
            # 构建请求参数
            params = {
                'lmt': '5',  # 获取最近5条数据
                'klt': '101',  # 日期类型
                'secid': f"{market_map[market]}.{code}",
                'fields1': 'f1,f2,f3,f4,f5,f6,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
                'ut': 'b2884a393a59ad64002292a3e90d46a5'
            }
            
            # 发送请求
            url = 'https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://quote.eastmoney.com/'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.logger.error(f"请求失败，状态码: {response.status_code}")
                return None
            
            data = response.json()
            
            if data['rc'] != 0 or 'data' not in data or 'klines' not in data['data']:
                self.logger.error(f"获取数据失败: {data.get('msg', '未知错误')}")
                return None
            
            # 解析数据
            rows = []
            for line in data['data']['klines']:
                fields = line.split(',')
                if len(fields) >= 8:
                    row = {
                        'datetime': pd.to_datetime(fields[0]),
                        'capital_main': float(fields[1]),  # 主力净流入
                        'capital_super': float(fields[2]),  # 超大单净流入
                        'capital_big': float(fields[3]),    # 大单净流入
                        'capital_middle': float(fields[4]), # 中单净流入
                        'capital_small': float(fields[5])   # 小单净流入
                    }
                    rows.append(row)
            
            if rows:
                df = pd.DataFrame(rows)
                
                # 显示资金流数据
                self.logger.info("\n资金流数据：")
                self.logger.info("=" * 100)
                self.logger.info(f"{'时间':<12} {'主力净流入':<12} {'超大单净流入':<12} {'大单净流入':<12} {'中单净流入':<12} {'小单净流入':<12}")
                self.logger.info("-" * 100)
                for row in rows:
                    self.logger.info(f"{row['datetime'].strftime('%Y-%m-%d'):<12} {row['capital_main']:>12,.2f} {row['capital_super']:>12,.2f} {row['capital_big']:>12,.2f} {row['capital_middle']:>12,.2f} {row['capital_small']:>12,.2f}")
                self.logger.info("=" * 100)
                
                return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"从东方财富获取资金流数据失败: {str(e)}")
            return None

    def _fetch_qq_fund_flow(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        从腾讯财经获取资金流向数据
        """
        try:
            market, code = symbol.split('.')
            
            # 转换市场代码
            market_map = {
                'SH': 'sh',
                'SZ': 'sz',
                'HK': 'hk'
            }
            
            if market not in market_map:
                raise ValueError(f"不支持的市场: {market}")
            
            # 构建腾讯股票代码
            qq_symbol = f"{market_map[market]}{code}"
            
            # 构建请求URL
            url = f"https://qt.gtimg.cn/q=ff_{qq_symbol}"
            
            # 发送请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://gu.qq.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'gbk'  # 设置正确的编码
            
            if response.status_code != 200:
                self.logger.error(f"请求失败，状态码: {response.status_code}")
                return None
            
            # 解析数据
            text = response.text
            if not text.startswith('v_ff_'):
                self.logger.error("获取数据失败：返回数据格式错误")
                return None
            
            # 提取数据部分
            data_str = text.split('=')[1].strip('"').strip(';')
            fields = data_str.split('~')
            
            if len(fields) < 10:
                self.logger.error("获取数据失败：数据字段不完整")
                return None
            
            # 解析数据
            row = {
                'datetime': pd.to_datetime('now').strftime('%Y-%m-%d'),
                'capital_main': float(fields[1]) + float(fields[3]),  # 主力净流入（超大单+大单）
                'capital_super': float(fields[1]),  # 超大单净流入
                'capital_big': float(fields[3]),    # 大单净流入
                'capital_middle': float(fields[5]), # 中单净流入
                'capital_small': float(fields[7])   # 小单净流入
            }
            
            df = pd.DataFrame([row])
            
            # 显示资金流数据
            self.logger.info("\n资金流数据：")
            self.logger.info("=" * 100)
            self.logger.info(f"{'时间':<12} {'主力净流入':<12} {'超大单净流入':<12} {'大单净流入':<12} {'中单净流入':<12} {'小单净流入':<12}")
            self.logger.info("-" * 100)
            self.logger.info(f"{row['datetime']:<12} {row['capital_main']:>12,.2f} {row['capital_super']:>12,.2f} {row['capital_big']:>12,.2f} {row['capital_middle']:>12,.2f} {row['capital_small']:>12,.2f}")
            self.logger.info("=" * 100)
            
            return df
            
        except Exception as e:
            self.logger.error(f"从腾讯财经获取资金流数据失败: {str(e)}")
            return None

    def _fetch_tdx_fund_flow(self, symbol):
        """从通达信获取资金流向数据"""
        try:
            market = 1 if symbol.startswith('SH') else 0
            code = symbol.split('.')[1]
            
            url = f'http://push2.eastmoney.com/api/qt/stock/fflow/kline/get'
            params = {
                'secid': f'{market}.{code}',
                'fields1': 'f1,f2,f3,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63',
                'klt': '101',  # 日线
                'lmt': '5',    # 最近5天
                'ut': 'b2884a393a59ad64002292a3e90d46a5'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'http://quote.eastmoney.com/'
            }
            
            response = requests.get(url, params=params, headers=headers)
            data = response.json()
            
            if data['data'] and data['data']['klines']:
                fund_flow_data = []
                for line in data['data']['klines']:
                    items = line.split(',')
                    fund_flow_data.append({
                        'datetime': pd.to_datetime(items[0]),
                        'capital_main': float(items[1]),  # 主力净流入
                        'capital_super': float(items[2]),  # 超大单净流入
                        'capital_big': float(items[3]),    # 大单净流入
                        'capital_middle': float(items[4]), # 中单净流入
                        'capital_small': float(items[5])   # 小单净流入
                    })
                
                df = pd.DataFrame(fund_flow_data)
                
                # 显示资金流向数据
                self.logger.info(f'\n最近5天资金流向数据：')
                for _, row in df.iterrows():
                    self.logger.info(f'日期：{row["datetime"].strftime("%Y-%m-%d")}')
                    self.logger.info(f'主力净流入：{row["capital_main"]/10000:.2f}万')
                    self.logger.info(f'超大单净流入：{row["capital_super"]/10000:.2f}万')
                    self.logger.info(f'大单净流入：{row["capital_big"]/10000:.2f}万')
                    self.logger.info(f'中单净流入：{row["capital_middle"]/10000:.2f}万')
                    self.logger.info(f'小单净流入：{row["capital_small"]/10000:.2f}万')
                    self.logger.info('-' * 50)
                
                return df
            else:
                self.logger.error('未能获取到资金流向数据')
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f'获取资金流向数据时发生错误: {str(e)}')
            return pd.DataFrame()

    def process_stock_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        处理股票数据的完整流程
        
        Args:
            symbol: 股票代码（如：SH.600536）
            
        Returns:
            Dict[str, pd.DataFrame]: 包含不同周期数据的字典
        """
        try:
            print(f"\n开始处理股票 {symbol}")
            
            # 获取资金流数据
            fund_flow_df = None
            try:
                fund_flow_df = self._fetch_tdx_fund_flow(symbol)
                if fund_flow_df is not None:
                    print("成功获取资金流数据")
                else:
                    print("未能获取资金流数据")
            except Exception as e:
                print(f"获取资金流数据失败: {str(e)}")
            
            # 获取各个周期的K线数据
            data_dict = {}
            periods = ['1d', '1h', '30m', '15m']
            
            for period in periods:
                try:
                    print(f"获取{period}周期数据...")
                    df = self._fetch_eastmoney_data(symbol, period)
                    
                    if df is not None and not df.empty:
                        # 计算技术指标
                        df = self.calculate_macd(df, period)
                        df = self.calculate_kdj(df, period)
                        df = self.calculate_rsi(df, period)
                        df = self.calculate_ma(df, period)
                        
                        # 如果有资金流数据，合并到当前周期数据中
                        if fund_flow_df is not None:
                            df['date'] = pd.to_datetime(df['datetime']).dt.date
                            fund_flow_df['date'] = pd.to_datetime(fund_flow_df['datetime']).dt.date
                            df = pd.merge(df, fund_flow_df[['date', 'capital_main', 'capital_super', 
                                                          'capital_big', 'capital_middle', 'capital_small']], 
                                        on='date', how='left')
                            df = df.drop('date', axis=1)
                        
                        data_dict[period] = df
                        print(f"成功处理{period}周期数据，共{len(df)}条记录")
                    else:
                        print(f"未能获取{period}周期数据")
                        
                except Exception as e:
                    print(f"处理{period}周期数据失败: {str(e)}")
                    continue
            
            # 添加资金流向数据到字典
            if fund_flow_df is not None:
                data_dict['fund_flow'] = fund_flow_df
            
            # 显示最新的技术指标和资金流向数据
            self.display_latest_indicators(data_dict)
            
            return data_dict
            
        except Exception as e:
            print(f"处理股票数据失败: {str(e)}")
            return {}

    def validate_stock_symbols(self, symbols: List[str]) -> bool:
        """
        验证股票代码格式
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            bool: 是否全部验证通过
        """
        try:
            if len(symbols) > self.max_stocks:
                self.logger.error(f"股票数量超过限制（最大{self.max_stocks}个）")
                return False
            
            for symbol in symbols:
                # 检查格式
                if '.' not in symbol:
                    self.logger.error(f"股票代码格式错误: {symbol}，正确格式为: 市场.代码")
                    return False
                
                market, code = symbol.split('.')
                market = market.upper()
                
                # 检查市场代码
                if market not in self.valid_prefixes:
                    self.logger.error(f"不支持的市场: {market}")
                    return False
                
                # 检查股票代码
                if market == 'US':
                    # 美股代码可以包含字母和数字
                    if not code.isalnum():
                        self.logger.error(f"美股代码必须为字母和数字的组合: {code}")
                        return False
                    if len(code) > 5:
                        self.logger.error(f"美股代码长度不能超过5位: {code}")
                        return False
                else:
                    # 其他市场（A股、港股）的代码必须是数字
                    if not code.isdigit():
                        self.logger.error(f"股票代码必须为数字: {code}")
                        return False
                    # 检查代码长度
                    if market in ['SH', 'SZ'] and len(code) != 6:
                        self.logger.error(f"A股代码必须为6位: {code}")
                        return False
                    elif market == 'HK' and not (1 <= len(code) <= 5):
                        self.logger.error(f"港股代码长度必须在1-5位之间: {code}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证股票代码时发生错误: {str(e)}")
            return False

    def main(self):
        """主函数，处理命令行参数并执行分析"""
        try:
            # 解析命令行参数
            parser = argparse.ArgumentParser(description='股票技术分析工具')
            parser.add_argument('symbols', nargs='+', help='股票代码列表，例如：SH.600000 SZ.000001')
            parser.add_argument('--periods', nargs='+', default=['1d', '2h', '1h', '30m', '15m'],
                            help='时间周期列表，例如：1d 2h 1h 30m 15m')
            parser.add_argument('--debug', action='store_true', help='启用调试模式')
            args = parser.parse_args()

            # 配置日志级别
            if args.debug:
                self.logger.setLevel(logging.DEBUG)

            # 验证股票代码
            if not self.validate_stock_symbols(args.symbols):
                sys.exit(1)

            # 处理每个股票
            for symbol in args.symbols:
                print(f"\n开始分析股票 {symbol}")
                
                try:
                    # 获取股票数据
                    data = self.fetch_stock_data(symbol)
                    if not data:
                        print(f"无法获取{symbol}的数据")
                        continue
                    
                    # 显示K线数据获取情况
                    for period in ['15m', '30m', '1h', '1d']:
                        if period in data and data[period] is not None:
                            print(f"{period}周期数据：{len(data[period])}条记录")
                    
                    # 计算技术指标
                    for period, df in data.items():
                        if df is not None and not df.empty:
                            # 跳过资金流向数据的技术指标计算
                            if period == 'fund_flow':
                                continue
                                
                            print(f"计算{period}周期的技术指标...")
                            df = self.calculate_macd(df, period)
                            df = self.calculate_kdj(df, period)
                            df = self.calculate_rsi(df, period)
                            df = self.calculate_ma(df, period)
                            data[period] = df
                    
                    # 保存到Excel
                    self.save_to_excel(data, symbol)
                    print(f"已保存{symbol}的分析结果到Excel文件")
                    
                    # 显示最新的技术指标和资金流向数据
                    self.display_latest_indicators(data)
                    
                except Exception as e:
                    print(f"处理{symbol}时发生错误: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"程序执行出错: {str(e)}")
            sys.exit(1)

    def display_latest_indicators(self, data_dict: Dict[str, pd.DataFrame]) -> None:
        """
        显示最新的技术指标和资金流向数据
        
        Args:
            data_dict: 包含不同周期数据的字典
        """
        try:
            # 显示资金流向数据
            fund_flow_df = data_dict.get('fund_flow')
            if isinstance(fund_flow_df, pd.DataFrame) and not fund_flow_df.empty:
                latest_fund_flow = fund_flow_df.iloc[-1]
                print("\n资金流向数据：")
                print("-" * 100)
                print(f"日期：{latest_fund_flow['datetime'].strftime('%Y-%m-%d')}")
                print(f"主力净流入：{latest_fund_flow['capital_main']:,.2f}")
                print(f"超大单净流入：{latest_fund_flow['capital_super']:,.2f}")
                print(f"大单净流入：{latest_fund_flow['capital_big']:,.2f}")
                print(f"中单净流入：{latest_fund_flow['capital_middle']:,.2f}")
                print(f"小单净流入：{latest_fund_flow['capital_small']:,.2f}")
                print("-" * 100)
            
            # 显示各个周期的技术指标，按照从小到大的顺序
            for period in ['15m', '30m', '1h', '2h', '1d']:
                df = data_dict.get(period)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # 获取每个交易日最后一条数据
                    df['date'] = df['datetime'].dt.date
                    latest_by_date = df.groupby('date').last().reset_index()
                    latest = latest_by_date.iloc[-1]
                    
                    print(f"\n{period}周期技术指标：")
                    print("-" * 100)
                    print(f"日期时间：{latest['datetime'].strftime('%Y-%m-%d %H:%M')}")
                    print(f"MACD: {latest[f'MACD_{period}']:.3f}, 信号线: {latest[f'MACD_{period}_Signal']:.3f}, 柱状图: {latest[f'MACD_{period}_Hist']:.3f}")
                    print(f"KDJ: K={latest[f'KDJ_{period}_K']:.2f}, D={latest[f'KDJ_{period}_D']:.2f}, J={latest[f'KDJ_{period}_J']:.2f}")
                    print(f"RSI: RSI6={latest[f'RSI_{period}_6']:.2f}, RSI12={latest[f'RSI_{period}_12']:.2f}, RSI24={latest[f'RSI_{period}_24']:.2f}")
                    print(f"MA: MA5={latest[f'ma5_{period}']:.3f}, MA10={latest[f'ma10_{period}']:.3f}, MA20={latest[f'ma20_{period}']:.3f}")
                    print("-" * 100)
            
        except Exception as e:
            print(f"显示最新指标时发生错误: {str(e)}")
            self.logger.error(f"显示最新指标时发生错误: {str(e)}")

def main():
    """程序入口点"""
    analyzer = StockAnalyzer()
    analyzer.main()

if __name__ == '__main__':
    main() 