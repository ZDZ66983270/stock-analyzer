import os
import pandas as pd
import logging
from datetime import datetime, timedelta
import time
import akshare as ak
import yfinance as yf

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_realtime_data(symbols):
    """
    获取美股实时行情数据
    
    参数:
        symbols (list): 股票代码列表，例如 ['TSM', 'MSFT']
    
    返回:
        pd.DataFrame: 股票数据
    """
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            logger.info(f"开始获取美股实时行情数据（第{retry_count + 1}次尝试）")
            
            # 使用akshare获取数据
            logger.info("正在请求数据...")
            df = ak.stock_us_spot()
            
            if df is None or df.empty:
                logger.error("获取数据为空")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"等待5秒后重试...")
                    time.sleep(5)
                continue
            
            # 只保留指定股票的数据
            df = df[df['symbol'].isin(symbols)]
            if df.empty:
                logger.error(f"未找到指定的股票代码: {symbols}")
                return None
            logger.info(f"成功获取到 {len(df)} 只指定股票的数据")
            
            # 创建保存目录
            os.makedirs("test_data/us_stocks", exist_ok=True)
            
            # 保存数据到CSV文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"us_stocks_{'_'.join(symbols)}_{timestamp}.csv"
            filepath = os.path.join("test_data/us_stocks", filename)
            
            # 选择要保存的列
            columns_to_save = [
                'symbol', 'name', 'cname', 'price', 'diff', 'chg',
                'preclose', 'open', 'high', 'low', 'volume', 'mktcap', 'pe'
            ]
            
            # 保存数据
            df[columns_to_save].to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"数据已保存到 {filepath}")
            
            # 输出数据统计信息
            logger.info("数据获取成功")
            logger.info(f"总记录数: {len(df)}")
            logger.info(f"数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("注意：数据有15分钟延迟")
            
            # 输出数据示例
            logger.info("\n数据示例:")
            logger.info(df[columns_to_save].to_string())
            
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

def get_historical_data(symbols):
    """
    获取美股历史数据
    
    参数:
        symbols (list): 股票代码列表，例如 ['TSM', 'MSFT']
    
    返回:
        dict: 包含每个股票历史数据的字典
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    result = {}
    for symbol in symbols:
        try:
            logger.info(f"开始获取{symbol}的历史数据")
            
            # 使用yfinance获取数据
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval="1d"
            )
            
            if df.empty:
                logger.error(f"获取{symbol}的历史数据为空")
                continue
                
            # 添加datetime列
            df['datetime'] = df.index
            
            # 重命名列
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 创建保存目录
            os.makedirs("test_data/us_stocks", exist_ok=True)
            
            # 保存数据到CSV文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{symbol}_historical_{timestamp}.csv"
            filepath = os.path.join("test_data/us_stocks", filename)
            
            # 保存数据
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"数据已保存到 {filepath}")
            
            # 输出数据统计信息
            logger.info(f"获取{symbol}的历史数据成功")
            logger.info(f"总记录数: {len(df)}")
            logger.info(f"数据时间范围: {df['datetime'].min()} 到 {df['datetime'].max()}")
            
            result[symbol] = df
            
        except Exception as e:
            logger.error(f"获取{symbol}的历史数据失败: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
    
    return result

def test_tsm_msft():
    """
    测试获取TSM和MSFT的行情数据
    """
    symbols = ['TSM', 'MSFT']
    
    # 获取实时数据
    logger.info("开始获取实时数据...")
    realtime_data = get_realtime_data(symbols)
    
    # 获取历史数据
    logger.info("开始获取历史数据...")
    historical_data = get_historical_data(symbols)
    
    return realtime_data, historical_data

if __name__ == "__main__":
    test_tsm_msft() 