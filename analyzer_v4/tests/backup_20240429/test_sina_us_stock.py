import os
import pandas as pd
import logging
from datetime import datetime
import time
import akshare as ak

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_stock_data(symbols=None, save_all=False):
    """
    获取美股实时行情数据
    
    参数:
        symbols (list): 股票代码列表，例如 ['AAPL', 'MSFT', 'TSM']
        save_all (bool): 是否保存所有股票数据，默认False
    
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
            
            # 如果指定了股票代码，则只保留这些股票的数据
            if symbols:
                df = df[df['symbol'].isin(symbols)]
                if df.empty:
                    logger.error(f"未找到指定的股票代码: {symbols}")
                    return None
                logger.info(f"成功获取到 {len(df)} 只指定股票的数据")
            
            # 创建保存目录
            os.makedirs("test_data/us_stocks", exist_ok=True)
            
            # 保存数据到CSV文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if symbols:
                filename = f"us_stocks_{'_'.join(symbols)}_{timestamp}.csv"
            else:
                filename = f"us_stocks_all_{timestamp}.csv"
            
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
            logger.info(df[columns_to_save].head().to_string())
            
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

def test_us_stocks():
    """
    测试获取美股实时行情数据
    """
    # 测试获取特定股票的数据
    symbols = ['AAPL', 'MSFT', 'TSM', 'NVDA', 'AMZN']
    df = get_stock_data(symbols=symbols)
    
    if df is not None:
        # 输出每只股票的详细信息
        for symbol in symbols:
            stock_data = df[df['symbol'] == symbol].iloc[0]
            logger.info(f"\n{symbol} 股票信息:")
            logger.info(f"公司名称: {stock_data['cname']} ({stock_data['name']})")
            logger.info(f"当前价格: {stock_data['price']}")
            logger.info(f"涨跌幅: {stock_data['chg']}%")
            logger.info(f"成交量: {stock_data['volume']}")
            logger.info(f"市值: {stock_data['mktcap']}")
            logger.info(f"市盈率: {stock_data['pe']}")

if __name__ == "__main__":
    test_us_stocks() 