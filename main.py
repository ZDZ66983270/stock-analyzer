# main.py

import os
import logging
from datetime import datetime
import pandas as pd
from modules.utils import read_symbols_from_file, save_to_excel
from modules.data_fetcher import fetch_all_kline_data
from modules.fund_flow_fetcher import fetch_fund_flow
from modules.technical_indicators import add_technical_indicators

def setup_logger():
    """配置日志记录器"""
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)
    
    # 生成日志文件名
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/run_{current_time}.log"
    
    # 配置日志格式
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def save_raw_data(symbol: str, data: dict, fund_flow_data=None):
    """保存原始数据到output目录"""
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"{symbol.replace('.', '_')}_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for period, df in data.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=period, index=False)
        if fund_flow_data is not None and not fund_flow_data.empty:
            fund_flow_data.to_excel(writer, sheet_name='fund_flow', index=False)
    
    logging.info(f"[原始数据] 已保存到: {filepath}")

def save_indicators_data(symbol: str, data: dict):
    """保存指标数据到output/proceeded目录"""
    proceeded_dir = os.path.join('output', 'proceeded')
    os.makedirs(proceeded_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"{symbol.replace('.', '_')}_{timestamp}_indicators.xlsx"
    filepath = os.path.join(proceeded_dir, filename)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for period, df in data.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=period, index=False)
    
    logging.info(f"[指标数据] 已保存到: {filepath}")

def process_stock(symbol: str):
    """处理单个股票的数据"""
    try:
        # 1. 获取原始数据
        kline_data = fetch_all_kline_data(symbol)
        fund_flow_data = fetch_fund_flow(symbol)
        
        # 检查是否有有效数据
        no_kline = (not kline_data) or all(df is None or df.empty for df in kline_data.values())
        no_fund_flow = (fund_flow_data is None) or fund_flow_data.empty
        
        if no_kline and no_fund_flow:
            logging.warning(f"⚠️ {symbol} 无有效数据，跳过处理")
            return False
            
        # 2. 保存原始数据
        save_raw_data(symbol, kline_data, fund_flow_data)
        
        # 3. 计算技术指标
        indicator_data = {}
        for period, df in kline_data.items():
            if df is not None and not df.empty:
                indicator_data[period] = add_technical_indicators(df)
        
        # 4. 保存指标数据
        save_indicators_data(symbol, indicator_data)
        
        logging.info(f"✅ {symbol} 处理完成")
        return True
        
    except Exception as e:
        logging.error(f"❌ 处理 {symbol} 出现异常: {e}", exc_info=True)
        return False

def main():
    # 1. 设置日志
    logger = setup_logger()
    
    # 2. 创建必要的目录
    os.makedirs('output', exist_ok=True)
    os.makedirs('output/proceeded', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 3. 读取股票列表
    try:
        symbols = read_symbols_from_file('config/symbols.txt')
        logging.info(f"📄 读取到 {len(symbols)} 只股票：{symbols}")
        logging.info("=" * 60)
    except Exception as e:
        logging.error(f"❌ 读取股票列表失败: {e}")
        return
    
    # 4. 处理每只股票
    success_count = 0
    for idx, symbol in enumerate(symbols, 1):
        logging.info(f"\n🚀 [{idx}/{len(symbols)}] 开始处理 {symbol}")
        if process_stock(symbol):
            success_count += 1
    
    # 5. 输出统计信息
    logging.info("\n" + "=" * 60)
    logging.info(f"🎉 全部处理完成！成功: {success_count}/{len(symbols)}")

if __name__ == "__main__":
    main()

"""
这个 main.py 文件实现了以下功能：

1. 日志记录
   - 创建 logs 目录
   - 生成带时间戳的日志文件
   - 同时输出到文件和控制台

2. 数据保存
   - 原始数据保存到 output 目录
   - 指标数据保存到 output/proceeded 目录
   - 所有文件名都包含时间戳

3. 完整工作流程
   - 读取股票列表
   - 获取原始数据
   - 保存原始数据
   - 计算技术指标
   - 保存指标数据
   - 记录处理结果

4. 错误处理
   - 完整的异常捕获和日志记录
   - 统计成功/失败数量
   - 详细的进度显示
""" 

    