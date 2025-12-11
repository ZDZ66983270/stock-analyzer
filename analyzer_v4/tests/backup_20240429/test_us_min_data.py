import os
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_us_min_data():
    """
    测试美股分时数据获取功能
    
    功能说明：
    1. 使用东方财富网数据源获取美股分时数据
    2. 支持获取最近5个交易日的分钟数据
    3. 数据包含：时间、开盘价、收盘价、最高价、最低价、成交量、成交额、最新价
    4. 自动保存数据到CSV文件
    
    注意事项：
    1. 美股代码格式为：market.code，例如：105.AAPL
    2. 数据更新有延时
    3. 价格单位为美元，成交量单位为股，成交额单位为美元
    4. 只返回最近5个交易日的数据
    """
    # 测试股票列表 - 尝试不同的代码格式
    test_stocks = [
        "BABA",       # 阿里巴巴 - 仅代码
        "105.BABA",   # 阿里巴巴 - 标准格式
        "BABA.US",    # 阿里巴巴 - 带市场后缀
        "US.BABA",    # 阿里巴巴 - 市场前缀
        "BABA.NYSE",  # 阿里巴巴 - 纽约证券交易所
        "NYSE.BABA",  # 阿里巴巴 - 纽约证券交易所（另一种格式）
        "1810.HK",    # 小米 - 香港交易所
        "1810",       # 小米 - 仅代码
        "HK.1810",    # 小米 - 市场前缀
        "1810.HK.US", # 小米 - 香港交易所（美股）
        "US.1810.HK", # 小米 - 美股（香港）
        "XIACY",      # 小米ADR - 仅代码
        "105.XIACY",  # 小米ADR - 标准格式
        "XIACY.US",   # 小米ADR - 带市场后缀
        "US.XIACY",   # 小米ADR - 市场前缀
        "XIACY.ADR",  # 小米ADR - ADR后缀
        "ADR.XIACY",  # 小米ADR - ADR前缀
        "XIACY.OTC",  # 小米ADR - OTC市场
        "OTC.XIACY",  # 小米ADR - OTC市场（另一种格式）
        "NYSE:TSM",   # 台积电 - 纽约证券交易所（冒号格式）
        "TSM:NYSE",   # 台积电 - 纽约证券交易所（冒号格式，另一种顺序）
    ]
    
    # 设置日期范围为最近5个交易日
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # 多取几天以确保覆盖5个交易日
    
    # 格式化日期时间
    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建保存目录
    os.makedirs("test_data/us_min", exist_ok=True)
    
    for symbol in test_stocks:
        try:
            logger.info(f"测试获取 {symbol} 分时数据")
            logger.info(f"日期范围: {start_date_str} 到 {end_date_str}")
            
            # 获取分时数据
            df = ak.stock_us_hist_min_em(
                symbol=symbol,
                start_date=start_date_str,
                end_date=end_date_str
            )
            
            if df is None or df.empty:
                logger.warning(f"获取 {symbol} 分时数据为空")
                continue
            
            # 输出数据基本信息
            logger.info(f"数据获取成功，形状: {df.shape}")
            logger.info(f"列名: {df.columns.tolist()}")
            logger.info(f"时间范围: {df['时间'].min()} 到 {df['时间'].max()}")
            
            # 保存数据到CSV文件
            filename = f"{symbol.replace('.', '_')}_min.csv"
            filepath = os.path.join("test_data/us_min", filename)
            df.to_csv(filepath, index=False)
            logger.info(f"数据已保存到 {filepath}")
            
            # 输出数据统计信息
            logger.info(f"数据统计信息:")
            logger.info(f"开盘价范围: {df['开盘'].min():.2f} - {df['开盘'].max():.2f}")
            logger.info(f"收盘价范围: {df['收盘'].min():.2f} - {df['收盘'].max():.2f}")
            logger.info(f"成交量范围: {df['成交量'].min():.0f} - {df['成交量'].max():.0f}")
            logger.info(f"成交额范围: {df['成交额'].min():.2f} - {df['成交额'].max():.2f}")
            
        except Exception as e:
            logger.error(f"获取 {symbol} 分时数据失败: {str(e)}")

if __name__ == "__main__":
    logger.info("开始测试美股分时数据获取功能")
    test_us_min_data()
    logger.info("测试完成") 