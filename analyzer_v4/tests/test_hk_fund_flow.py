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
def fetch_stock_fund_flow(stock, market):
    """获取个股资金流向数据"""
    return ak.stock_individual_fund_flow(stock=stock, market=market)

def test_single_stock(stock, market):
    """
    测试单个股票的资金流向数据获取
    :param stock: 股票代码
    :param market: 市场代码（sh/sz/bj）
    """
    logger.info(f"开始测试股票 {stock} 的资金流向数据获取...")
    
    try:
        # 获取资金流向数据
        fund_flow_data = fetch_stock_fund_flow(stock, market)
        if fund_flow_data is not None and len(fund_flow_data) > 0:
            # 创建保存目录
            os.makedirs("test_data/a_stock_fund_flow", exist_ok=True)
            # 保存数据
            fund_flow_data.to_csv(f"test_data/a_stock_fund_flow/{stock}_{market}_fund_flow.csv", encoding='utf-8-sig')
            logger.info(f"获取到 {len(fund_flow_data)} 条资金流向数据")
            logger.info(f"数据字段: {', '.join(fund_flow_data.columns)}")
            logger.info(f"数据示例:\n{fund_flow_data.head()}")
            return True
        else:
            logger.warning(f"未获取到股票 {stock} 的资金流向数据")
            return False
    except Exception as e:
        logger.error(f"测试股票 {stock} 时出错: {str(e)}")
        return False

def test_a_stock_fund_flow():
    """
    测试A股资金流向数据接口
    测试内容：
    1. 个股资金流向数据
       - 主力净流入
       - 超大单净流入
       - 大单净流入
       - 中单净流入
       - 小单净流入
    """
    # 测试股票列表
    test_stocks = [
        ("600309", "sh"),  # 万华化学
        ("000001", "sz"),  # 平安银行
        ("300750", "sz"),  # 宁德时代
    ]
    
    try:
        logger.info("开始测试A股资金流向数据...")
        success_count = 0
        for stock, market in test_stocks:
            if test_single_stock(stock, market):
                logger.info(f"股票 {stock} 资金流向数据获取成功")
                success_count += 1
            else:
                logger.warning(f"股票 {stock} 资金流向数据获取失败")
        
        logger.info(f"A股资金流向数据测试完成! 成功率: {success_count}/{len(test_stocks)}")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
        raise

if __name__ == "__main__":
    test_a_stock_fund_flow() 