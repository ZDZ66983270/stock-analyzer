import os
import pandas as pd
from datetime import datetime, timedelta
from modules.data_fetcher import fetch_kline, fetch_all_kline_data
import logging

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fetch_kline():
    """
    测试单个周期数据获取功能
    
    功能说明：
    1. 支持A股、港股、美股的数据获取
    2. 支持多个时间周期：日线(daily)、周线(weekly)、月线(monthly)
    3. 支持分钟级数据：5分钟(5min)、15分钟(15min)、30分钟(30min)、60分钟(60min)
    4. 自动保存数据到CSV文件
    
    测试用例：
    - A股：平安银行(000001.SZ)的日线和5分钟线
    - 港股：阿里巴巴(09988.HK)的日线，腾讯(00700.HK)的60分钟线
    - 美股：苹果(AAPL.US)、微软(MSFT.US)、台积电(TSM.US)的日线和30分钟线
    """
    test_cases = [
        # A股测试用例
        ("000001.SZ", "daily"),    # 平安银行日线数据
        ("600000.SH", "weekly"),   # 浦发银行周线数据
        ("000001.SZ", "5min"),     # 平安银行5分钟线数据
        
        # 港股测试用例
        ("09988.HK", "daily"),     # 阿里巴巴日线数据
        ("00700.HK", "60min"),     # 腾讯控股60分钟线数据
        
        # 美股测试用例
        ("AAPL.US", "daily"),      # 苹果日线数据
        ("MSFT.US", "daily"),      # 微软日线数据
        ("TSM.US", "daily"),       # 台积电日线数据
        ("MSFT.US", "30min"),      # 微软30分钟线数据
        ("TSM.US", "30min"),       # 台积电30分钟线数据
    ]
    
    for symbol, period in test_cases:
        try:
            logger.info(f"测试 {symbol} {period} 数据获取")
            # 调用数据获取函数
            df = fetch_kline(symbol, period)
            
            if df.empty:
                logger.warning(f"获取 {symbol} {period} 数据为空")
                continue
                
            # 输出数据基本信息
            logger.info(f"数据获取成功，形状: {df.shape}")
            logger.info(f"列名: {df.columns.tolist()}")
            logger.info(f"时间范围: {df['date'].min()} 到 {df['date'].max()}")
            
            # 保存数据到CSV文件
            os.makedirs("test_data", exist_ok=True)
            filename = f"{symbol.replace('.', '_')}_{period}.csv"
            df.to_csv(os.path.join("test_data", filename), index=False)
            logger.info(f"数据已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"测试 {symbol} {period} 失败: {str(e)}")

def test_fetch_all_kline_data():
    """
    测试所有周期数据获取功能
    
    功能说明：
    1. 一次性获取指定股票的所有可用周期数据
    2. 支持的周期包括：日线、周线、月线、60分钟、30分钟、15分钟、5分钟
    3. 自动保存所有周期的数据到独立的CSV文件
    
    测试股票：
    - A股：平安银行(000001.SZ)
    - 港股：阿里巴巴(09988.HK)
    - 美股：苹果(AAPL.US)、微软(MSFT.US)、台积电(TSM.US)
    """
    test_cases = [
        "000001.SZ",    # 平安银行
        "09988.HK",     # 阿里巴巴
        "AAPL.US",      # 苹果
        "MSFT.US",      # 微软
        "TSM.US",       # 台积电
    ]
    
    for symbol in test_cases:
        try:
            logger.info(f"测试 {symbol} 所有周期数据获取")
            # 获取所有周期的数据
            result = fetch_all_kline_data(symbol)
            
            for period, df in result.items():
                if df is None or df.empty:
                    logger.warning(f"{symbol} {period} 数据为空")
                    continue
                    
                # 输出数据基本信息
                logger.info(f"{symbol} {period} 数据获取成功，形状: {df.shape}")
                logger.info(f"列名: {df.columns.tolist()}")
                logger.info(f"时间范围: {df['date'].min()} 到 {df['date'].max()}")
                
                # 保存数据到CSV文件
                os.makedirs("test_data", exist_ok=True)
                filename = f"{symbol.replace('.', '_')}_{period}.csv"
                df.to_csv(os.path.join("test_data", filename), index=False)
                logger.info(f"数据已保存到 {filename}")
                
        except Exception as e:
            logger.error(f"测试 {symbol} 所有周期数据获取失败: {str(e)}")

if __name__ == "__main__":
    logger.info("开始测试数据获取功能")
    test_fetch_kline()
    test_fetch_all_kline_data()
    logger.info("测试完成") 