import os
import pandas as pd
import logging
from datetime import datetime, timedelta
import time
import akshare as ak

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_us_min_data(symbol, start_date=None, end_date=None, max_retries=3):
    """
    获取美股分时数据（使用东方财富网接口）
    
    参数:
        symbol (str): 股票代码，例如 "ATER"
        start_date (str): 开始日期，格式 "YYYY-MM-DD HH:MM:SS"
        end_date (str): 结束日期，格式 "YYYY-MM-DD HH:MM:SS"
        max_retries (int): 最大重试次数
    
    返回:
        pd.DataFrame: 分时数据
    """
    retry_count = 0
    
    # 如果没有指定日期，默认获取最近5个交易日的数据
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构建完整的股票代码（添加市场前缀）
    full_symbol = f"105.{symbol}"
    
    while retry_count < max_retries:
        try:
            logger.info(f"开始获取 {symbol} 分时数据（第{retry_count + 1}次尝试）")
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
            os.makedirs("test_data/us_min_data", exist_ok=True)
            
            # 保存数据到CSV文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"us_min_{symbol}_{timestamp}.csv"
            filepath = os.path.join("test_data/us_min_data", filename)
            
            # 保存数据
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"数据已保存到 {filepath}")
            
            # 输出数据统计信息
            logger.info("数据获取成功")
            logger.info(f"总记录数: {len(df)}")
            logger.info(f"数据时间范围: {df['时间'].min()} 至 {df['时间'].max()}")
            logger.info("注意：数据有延时")
            
            # 输出数据示例
            logger.info("\n数据示例:")
            logger.info(df.head().to_string())
            
            return df
            
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            retry_count += 1
            if retry_count < max_retries:
                logger.info(f"等待5秒后重试...")
                time.sleep(5)
    
    if retry_count >= max_retries:
        logger.error(f"已达到最大重试次数（{max_retries}次），获取数据失败")
        return None

def test_us_min_data():
    """
    测试获取美股分时数据
    """
    # 测试获取特定股票的分时数据
    symbols = ['ATER', 'AAPL', 'MSFT']
    
    for symbol in symbols:
        logger.info(f"\n测试获取 {symbol} 的分时数据")
        df = get_us_min_data(symbol=symbol)
        
        if df is not None:
            # 输出数据统计信息
            logger.info(f"\n{symbol} 数据统计:")
            logger.info(f"数据条数: {len(df)}")
            logger.info(f"时间范围: {df['时间'].min()} 至 {df['时间'].max()}")
            logger.info(f"价格范围: {df['最低'].min()} - {df['最高'].max()}")
            logger.info(f"成交量: {df['成交量'].sum():,.0f}")
            logger.info(f"成交额: {df['成交额'].sum():,.2f}")

if __name__ == "__main__":
    test_us_min_data() 