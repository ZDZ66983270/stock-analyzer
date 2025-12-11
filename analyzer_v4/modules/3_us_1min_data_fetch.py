import os
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import time

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_us_min_data(symbol, period, start_date=None, end_date=None, max_retries=3):
    """
    获取美股1分钟数据（使用东方财富网接口）
    
    参数:
        symbol (str): 股票代码，例如 "TSM"
        period (str): 时间周期，支持 "1min"
        start_date (str): 开始日期，格式 "YYYY-MM-DD"
        end_date (str): 结束日期，格式 "YYYY-MM-DD"
        max_retries (int): 最大重试次数
    
    返回:
        pd.DataFrame: 1分钟数据
    """
    retry_count = 0
    
    # 如果没有指定日期，默认获取最近15天的数据
    if not start_date:
        start_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 添加市场前缀
    prefix = "106" if symbol == "TSM" else "105"
    full_symbol = f"{prefix}.{symbol}"
    
    while retry_count < max_retries:
        try:
            logger.info(f"开始获取 {symbol} 1分钟数据（第{retry_count + 1}次尝试）")
            logger.info(f"时间范围: {start_date} 至 {end_date}")
            
            # 使用akshare获取数据
            logger.info("正在请求数据...")
            df = ak.stock_us_hist_min_em(
                symbol=full_symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                logger.error("获取数据为空")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"等待5秒后重试...")
                    time.sleep(5)
                continue
            
            # 创建保存目录
            os.makedirs("output", exist_ok=True)
            
            # 保存数据到CSV文件
            filename = f"{symbol.lower()}_1min.csv"
            filepath = os.path.join("output", filename)
            
            # 保存数据
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"数据已保存到 {filepath}")
            
            # 输出数据统计信息
            logger.info("数据获取成功")
            logger.info(f"总记录数: {len(df)}")
            logger.info(f"数据时间范围: {df['时间'].min()} 至 {df['时间'].max()}")
            logger.info(f"开盘价范围: {df['开盘'].min():.2f} - {df['开盘'].max():.2f}")
            logger.info(f"收盘价范围: {df['收盘'].min():.2f} - {df['收盘'].max():.2f}")
            logger.info(f"成交量范围: {df['成交量'].min():.0f} - {df['成交量'].max():.0f}")
            logger.info(f"成交额范围: {df['成交额'].min():.2f} - {df['成交额'].max():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                logger.info(f"等待5秒后重试...")
                time.sleep(5)
    
    logger.error(f"已达到最大重试次数（{max_retries}次），获取数据失败")
    return None

def test_us_min_data():
    """
    测试获取美股1分钟数据
    """
    # 测试股票列表
    symbols = ['TSM', 'MSFT']
    
    # 设置日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=15)
    
    for symbol in symbols:
        logger.info(f"\n开始获取 {symbol} 的1分钟数据")
        
        df = get_us_min_data(
            symbol=symbol,
            period="1min",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        if df is not None:
            logger.info(f"成功获取 {symbol} 的1分钟数据")
        else:
            logger.error(f"获取 {symbol} 的1分钟数据失败")

if __name__ == "__main__":
    test_us_min_data() 