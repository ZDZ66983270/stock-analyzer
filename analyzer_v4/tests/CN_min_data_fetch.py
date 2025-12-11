import os
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import time

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

def test_wanhua_data():
    """
    测试获取万华化学数据
    
    功能说明：
    1. 获取90日内的日线数据
    2. 获取15日内的1小时、30分钟、15分钟和5分钟数据
    3. 数据包含：时间、开盘价、收盘价、最高价、最低价、成交量、成交额等
    4. 自动保存数据到CSV文件
    """
    # 创建保存目录
    os.makedirs("test_data/wanhua", exist_ok=True)
    
    # 设置日期范围
    end_date = datetime.now()
    daily_start_date = end_date - timedelta(days=90)  # 90日数据
    min_start_date = end_date - timedelta(days=15)    # 15日数据
    
    # 格式化日期时间
    daily_start_date_str = daily_start_date.strftime("%Y-%m-%d")
    min_start_date_str = min_start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    try:
        # 获取日线数据
        logger.info("开始获取万华化学日线数据")
        logger.info(f"日期范围: {daily_start_date_str} 到 {end_date_str}")
        
        df_daily = ak.stock_zh_a_hist(symbol="600309", period="daily", 
                                    start_date=daily_start_date_str, 
                                    end_date=end_date_str,
                                    adjust="qfq")
        
        if df_daily is not None and not df_daily.empty:
            # 保存数据到CSV文件
            filename = "wanhua_daily.csv"
            filepath = os.path.join("test_data/wanhua", filename)
            df_daily.to_csv(filepath, index=False)
            logger.info(f"日线数据已保存到 {filepath}")
            
            # 输出数据统计信息
            logger.info(f"日线数据统计信息:")
            logger.info(f"数据条数: {len(df_daily)}")
            logger.info(f"日期范围: {df_daily['日期'].min()} 到 {df_daily['日期'].max()}")
            logger.info(f"开盘价范围: {df_daily['开盘'].min():.2f} - {df_daily['开盘'].max():.2f}")
            logger.info(f"收盘价范围: {df_daily['收盘'].min():.2f} - {df_daily['收盘'].max():.2f}")
            logger.info(f"成交量范围: {df_daily['成交量'].min():.0f} - {df_daily['成交量'].max():.0f}")
            logger.info(f"成交额范围: {df_daily['成交额'].min():.2f} - {df_daily['成交额'].max():.2f}")
        
        # 获取分钟数据
        periods = {
            "60": "1小时",
            "30": "30分钟",
            "15": "15分钟",
            "5": "5分钟"
        }
        
        for period, period_name in periods.items():
            logger.info(f"开始获取万华化学{period_name}数据")
            logger.info(f"日期范围: {min_start_date_str} 到 {end_date_str}")
            
            df_min = ak.stock_zh_a_hist_min_em(symbol="600309", period=period,
                                              start_date=min_start_date_str,
                                              end_date=end_date_str)
            
            if df_min is not None and not df_min.empty:
                # 保存数据到CSV文件
                filename = f"wanhua_{period}min.csv"
                filepath = os.path.join("test_data/wanhua", filename)
                df_min.to_csv(filepath, index=False)
                logger.info(f"{period_name}数据已保存到 {filepath}")
                
                # 输出数据统计信息
                logger.info(f"{period_name}数据统计信息:")
                logger.info(f"数据条数: {len(df_min)}")
                logger.info(f"时间范围: {df_min['时间'].min()} 到 {df_min['时间'].max()}")
                logger.info(f"开盘价范围: {df_min['开盘'].min():.2f} - {df_min['开盘'].max():.2f}")
                logger.info(f"收盘价范围: {df_min['收盘'].min():.2f} - {df_min['收盘'].max():.2f}")
                logger.info(f"成交量范围: {df_min['成交量'].min():.0f} - {df_min['成交量'].max():.0f}")
                logger.info(f"成交额范围: {df_min['成交额'].min():.2f} - {df_min['成交额'].max():.2f}")
            
    except Exception as e:
        logger.error(f"获取万华化学数据失败: {str(e)}")

def test_xiaomi_data():
    """
    测试获取小米（XIACY）数据
    
    功能说明：
    1. 获取小米的实时行情数据
    2. 数据包含：股票代码、名称、价格、涨跌幅、成交量等
    3. 自动保存数据到CSV文件
    """
    # 创建保存目录
    os.makedirs("test_data/xiaomi", exist_ok=True)
    
    try:
        # 获取实时行情数据
        logger.info("开始获取小米实时行情数据")
        
        df = ak.stock_us_spot()
        
        if df is not None and not df.empty:
            # 查找小米的数据
            xiaomi_data = df[df['symbol'] == 'XIACY']
            
            if not xiaomi_data.empty:
                # 保存数据到CSV文件
                filename = "xiaomi_spot.csv"
                filepath = os.path.join("test_data/xiaomi", filename)
                xiaomi_data.to_csv(filepath, index=False)
                logger.info(f"实时行情数据已保存到 {filepath}")
                
                # 输出数据统计信息
                logger.info("实时行情数据统计信息:")
                logger.info(f"股票代码: {xiaomi_data['symbol'].values[0]}")
                logger.info(f"股票名称: {xiaomi_data['name'].values[0]}")
                logger.info(f"当前价格: {xiaomi_data['price'].values[0]}")
                logger.info(f"涨跌幅: {xiaomi_data['chg'].values[0]}%")
                logger.info(f"成交量: {xiaomi_data['volume'].values[0]}")
                logger.info(f"市值: {xiaomi_data['mktcap'].values[0]}")
            else:
                logger.error("未找到小米（XIACY）的数据")
        else:
            logger.error("获取实时行情数据失败")
            
    except Exception as e:
        logger.error(f"获取小米数据失败: {str(e)}")

def test_xiaomi_sina_data():
    """
    使用新浪财经接口获取小米（美股）数据
    
    功能说明：
    1. 获取小米的实时行情数据
    2. 数据包含：股票代码、名称、价格、涨跌幅、成交量等
    3. 自动保存数据到CSV文件
    """
    # 创建保存目录
    os.makedirs("test_data/xiaomi", exist_ok=True)
    
    try:
        # 获取实时行情数据
        logger.info("开始获取小米实时行情数据（新浪财经接口）")
        
        # 使用新浪财经接口获取数据
        df = ak.stock_us_daily(symbol="XIACY")
        
        if df is not None and not df.empty:
            # 保存数据到CSV文件
            filename = "xiaomi_daily_sina.csv"
            filepath = os.path.join("test_data/xiaomi", filename)
            df.to_csv(filepath, index=False)
            logger.info(f"日线数据已保存到 {filepath}")
            
            # 输出数据统计信息
            logger.info("日线数据统计信息:")
            logger.info(f"数据条数: {len(df)}")
            logger.info(f"日期范围: {df['date'].min()} 到 {df['date'].max()}")
            logger.info(f"开盘价范围: {df['open'].min():.2f} - {df['open'].max():.2f}")
            logger.info(f"收盘价范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
            logger.info(f"成交量范围: {df['volume'].min():.0f} - {df['volume'].max():.0f}")
            
            # 获取分钟级别数据
            periods = {
                "60": "1小时",
                "30": "30分钟",
                "15": "15分钟",
                "5": "5分钟"
            }
            
            for period, period_name in periods.items():
                logger.info(f"开始获取小米{period_name}数据")
                
                df_min = ak.stock_us_hist_min_em(symbol="XIACY", period=period)
                
                if df_min is not None and not df_min.empty:
                    # 保存数据到CSV文件
                    filename = f"xiaomi_{period}min_sina.csv"
                    filepath = os.path.join("test_data/xiaomi", filename)
                    df_min.to_csv(filepath, index=False)
                    logger.info(f"{period_name}数据已保存到 {filepath}")
                    
                    # 输出数据统计信息
                    logger.info(f"{period_name}数据统计信息:")
                    logger.info(f"数据条数: {len(df_min)}")
                    logger.info(f"时间范围: {df_min['时间'].min()} 到 {df_min['时间'].max()}")
                    logger.info(f"开盘价范围: {df_min['开盘'].min():.2f} - {df_min['开盘'].max():.2f}")
                    logger.info(f"收盘价范围: {df_min['收盘'].min():.2f} - {df_min['收盘'].max():.2f}")
                    logger.info(f"成交量范围: {df_min['成交量'].min():.0f} - {df_min['成交量'].max():.0f}")
        else:
            logger.error("获取小米数据失败")
            
    except Exception as e:
        logger.error(f"获取小米数据失败: {str(e)}")

if __name__ == "__main__":
    logger.info("开始测试获取万华化学数据")
    test_wanhua_data()
    logger.info("测试完成")

    logger.info("开始测试获取小米数据")
    test_xiaomi_data()
    logger.info("测试完成")

    logger.info("开始测试获取小米数据（新浪财经接口）")
    test_xiaomi_sina_data()
    logger.info("测试完成") 