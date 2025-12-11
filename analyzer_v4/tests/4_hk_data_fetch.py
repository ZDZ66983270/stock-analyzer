import akshare as ak
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
import time
from requests.exceptions import RequestException
import requests
import urllib3
import ssl

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置SSL上下文
ssl._create_default_https_context = ssl._create_unverified_context

def retry_on_failure(func, max_retries=3, delay=5):
    """
    重试机制装饰器
    :param func: 要重试的函数
    :param max_retries: 最大重试次数
    :param delay: 重试间隔（秒）
    :return: 函数执行结果
    """
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"第 {attempt + 1} 次尝试失败: {str(e)}")
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
        return None
    return wrapper

@retry_on_failure
def fetch_hk_hist(symbol, period, start_date, end_date, adjust):
    """获取港股历史行情数据"""
    return ak.stock_hk_hist(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )

@retry_on_failure
def fetch_hk_hist_min_em(symbol, period, start_date, end_date):
    """获取港股分时数据"""
    return ak.stock_hk_hist_min_em(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date
    )

@retry_on_failure
def fetch_sina_hk_daily(symbol, adjust):
    """获取新浪港股历史行情数据"""
    return ak.stock_hk_daily(symbol=symbol, adjust=adjust)

@retry_on_failure
def fetch_xq_hk_info(symbol):
    """获取雪球港股个股信息"""
    return ak.stock_individual_basic_info_hk_xq(symbol=symbol)

def test_single_stock(symbol):
    """
    测试单个股票的数据获取
    :param symbol: 股票代码
    """
    logger.info(f"开始测试股票 {symbol} 的数据获取...")
    success_count = 0
    
    try:
        # 1. 测试日线历史数据（东方财富）
        logger.info("测试日线历史数据（东方财富）...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 获取90天的日线数据
        hist_data = fetch_hk_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust=""
        )
        if hist_data is not None and len(hist_data) > 0:
            hist_data.to_csv(f"../output/{symbol}_hist_em.csv", encoding='utf-8-sig')
            logger.info(f"获取到 {len(hist_data)} 条东方财富历史数据")
            success_count += 1
        
        # 2. 测试新浪历史数据
        logger.info("测试新浪历史数据...")
        sina_hist_data = fetch_sina_hk_daily(symbol=symbol, adjust="")
        if sina_hist_data is not None and len(sina_hist_data) > 0:
            # 只保留最近90天的数据
            sina_hist_data['date'] = pd.to_datetime(sina_hist_data['date'])
            sina_hist_data = sina_hist_data[sina_hist_data['date'] >= start_date]
            sina_hist_data.to_csv(f"../output/{symbol}_hist_sina.csv", encoding='utf-8-sig')
            logger.info(f"获取到 {len(sina_hist_data)} 条新浪历史数据")
            success_count += 1
        
        # 3. 测试分时数据
        logger.info("测试分时数据...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=15)  # 获取15天的分时数据
        
        # 测试不同时间周期
        periods = {
            "1": "1分钟",
            "5": "5分钟",
            "15": "15分钟",
            "30": "30分钟",
            "60": "1小时"
        }
        
        for period, period_name in periods.items():
            try:
                logger.info(f"获取{period_name}数据...")
                min_data = fetch_hk_hist_min_em(
                    symbol=symbol,
                    period=period,
                    start_date=start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    end_date=end_date.strftime("%Y-%m-%d %H:%M:%S")
                )
                if min_data is not None and len(min_data) > 0:
                    # 验证数据时间范围
                    min_data['时间'] = pd.to_datetime(min_data['时间'])
                    min_data = min_data[min_data['时间'] >= start_date]
                    min_data.to_csv(f"../output/{symbol}_min_{period}min.csv", encoding='utf-8-sig')
                    logger.info(f"获取到 {len(min_data)} 条{period_name}数据")
                    success_count += 1
            except Exception as e:
                logger.error(f"获取{period_name}数据失败: {str(e)}")
        
        # 4. 测试个股信息
        logger.info("测试个股信息...")
        info_data = fetch_xq_hk_info(symbol=symbol)
        if info_data is not None and len(info_data) > 0:
            info_data.to_csv(f"../output/{symbol}_info.csv", encoding='utf-8-sig')
            logger.info(f"获取到个股信息")
            success_count += 1
        
        return success_count > 0
    except Exception as e:
        logger.error(f"测试股票 {symbol} 时出错: {str(e)}")
        return False

def test_hk_data():
    """
    测试港股数据接口
    测试内容：
    1. 东方财富接口
       - 日线历史数据
       - 分时数据（1分钟、5分钟、15分钟、30分钟、1小时）
    2. 新浪财经接口
       - 历史数据
    3. 雪球接口
       - 个股基本信息
    """
    # 测试股票列表
    test_symbols = ["09988", "00998", "01810"]  # 阿里巴巴、中信银行、小米集团
    
    try:
        # 测试个股数据
        logger.info("开始测试个股数据...")
        success_count = 0
        for symbol in test_symbols:
            if test_single_stock(symbol):
                logger.info(f"股票 {symbol} 测试成功")
                success_count += 1
            else:
                logger.warning(f"股票 {symbol} 测试失败")
        
        logger.info(f"港股数据接口测试完成! 成功率: {success_count}/{len(test_symbols)}")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
        raise

if __name__ == "__main__":
    test_hk_data() 