import os
import sys
import logging
from datetime import datetime
import pandas as pd

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.data_fetcher import fetch_all_kline_data, fetch_fund_flow

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_symbols():
    """
    从 config/symbols.txt 文件中加载股票代码
    
    返回:
        dict: 按市场分类的股票代码字典
    """
    symbols = {
        "A股": [],
        "港股": [],
        "美股": []
    }
    
    try:
        with open("config/symbols.txt", "r", encoding="utf-8") as f:
            current_market = None
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    if "A股" in line:
                        current_market = "A股"
                    elif "港股" in line:
                        current_market = "港股"
                    elif "美股" in line:
                        current_market = "美股"
                    continue
                
                if current_market:
                    # 转换股票代码格式
                    if current_market == "A股":
                        if ".SH" in line:
                            symbols["A股"].append(f"SH.{line.split('.')[0]}")
                        elif ".SZ" in line:
                            symbols["A股"].append(f"SZ.{line.split('.')[0]}")
                    elif current_market == "港股":
                        if ".HK" in line:
                            symbols["港股"].append(f"HK.{line.split('.')[0]}")
                    elif current_market == "美股":
                        if ".US" in line:
                            symbols["美股"].append(f"US.{line.split('.')[0]}")
        
        return symbols
    except Exception as e:
        logger.error(f"加载股票代码失败: {str(e)}")
        return symbols

def test_single_stock(symbol: str, save_dir: str):
    """
    测试单个股票的数据获取
    
    参数:
        symbol: 股票代码
        save_dir: 数据保存目录
    """
    logger.info(f"开始测试股票 {symbol} 的数据获取...")
    
    # 创建保存目录
    stock_dir = os.path.join(save_dir, symbol.replace(".", "_"))
    os.makedirs(stock_dir, exist_ok=True)
    
    # 获取所有K线数据
    data_dict = fetch_all_kline_data(symbol)
    
    # 保存数据
    for period, df in data_dict.items():
        if df is not None and not df.empty:
            file_path = os.path.join(stock_dir, f"{period}.csv")
            df.to_csv(file_path, encoding='utf-8-sig', index=False)
            logger.info(f"保存{period}数据到 {file_path}，共{len(df)}条")
    
    # 单独测试资金流向数据（仅A股）
    if symbol.startswith(("SH.", "SZ.")):
        fund_flow_data = fetch_fund_flow(symbol)
        if fund_flow_data is not None:
            file_path = os.path.join(stock_dir, "fund_flow.csv")
            fund_flow_data.to_csv(file_path, encoding='utf-8-sig', index=False)
            logger.info(f"保存资金流向数据到 {file_path}，共{len(fund_flow_data)}条")

def test_all_markets():
    """测试所有市场的数据获取"""
    # 创建测试数据保存目录
    base_dir = "test_data"
    os.makedirs(base_dir, exist_ok=True)
    
    # 从配置文件加载股票代码
    test_stocks = load_symbols()
    
    # 测试每个市场的股票
    for market, stocks in test_stocks.items():
        if not stocks:
            logger.warning(f"{market}市场没有配置股票代码")
            continue
            
        logger.info(f"\n开始测试{market}市场...")
        market_dir = os.path.join(base_dir, market)
        os.makedirs(market_dir, exist_ok=True)
        
        for symbol in stocks:
            try:
                test_single_stock(symbol, market_dir)
            except Exception as e:
                logger.error(f"测试股票 {symbol} 时出错: {str(e)}")
                continue

if __name__ == "__main__":
    logger.info("开始测试所有市场数据获取...")
    test_all_markets()
    logger.info("测试完成！") 