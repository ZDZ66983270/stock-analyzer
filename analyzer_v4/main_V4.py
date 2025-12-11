# run_logger.py

import os
import sys
import logging
from datetime import datetime
from fetcher_V4 import DataFetcher
from indicators_V4 import batch_process
from Trend_analyzer_V4 import analyze_trend, build_period_dfs
import pandas as pd
import re
import threading

# 初始化日志
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

def process_stock(symbol, exporter):
    """处理单个股票的数据"""
    try:
        logging.info(f"开始处理 {symbol}")
        
        # 获取市场类型
        market = get_market_type(symbol)
        if market == "Unknown":
            logging.error(f"无法识别市场类型: {symbol}")
            return

        # 获取所有K线数据（包含分钟数据和A股资金流向）
        kline_data_dict = fetch_all_kline_data(symbol)
        
        # 检查数据是否为空
        if not kline_data_dict:
            logging.warning(f"{symbol} 未获取到任何数据")
            return
            
        # 记录获取到的数据周期
        periods = [period for period, data in kline_data_dict.items() 
                  if data is not None and not data.empty]
        logging.info(f"成功获取 {symbol} 的以下周期数据: {', '.join(periods)}")
        
        # 为每个周期的数据添加技术指标
        for period in kline_data_dict:
            if period != "fund_flow":  # 跳过资金流向数据
                df = kline_data_dict[period]
                if df is not None and not df.empty:
                    try:
                        # 确保所有列名都是小写
                        df.columns = [col.lower() for col in df.columns]
                        kline_data_dict[period] = add_technical_indicators(df)
                        logging.info(f"成功为 {symbol} 的 {period} 数据添加技术指标")
                    except Exception as e:
                        logging.error(f"为 {symbol} 的 {period} 数据添加技术指标失败: {str(e)}")
        
        # 保存到Excel
        try:
            exporter.export_to_excel(symbol, kline_data_dict)
            logging.info(f"成功保存 {symbol} 的数据到Excel")
        except Exception as e:
            logging.error(f"保存 {symbol} 的数据到Excel失败: {str(e)}")
        
    except Exception as e:
        logging.error(f"处理 {symbol} 时出错: {str(e)}", exc_info=True)

def batch_trend_analysis(proceeded_dir):
    """
    对 proceeded 目录下所有已处理的Excel文件，批量做趋势分析。
    """
    for root, dirs, files in os.walk(proceeded_dir):
        for file in files:
            if file.endswith('.xlsx'):
                file_path = os.path.join(root, file)
                m = re.match(r'([A-Za-z0-9\.]+)_([A-Z]+)_.*?(\d{8})', file)
                if m:
                    symbol = m.group(1)
                    market = m.group(2)
                    date_str = m.group(3)
                else:
                    symbol = ""
                    market = ""
                    date_str = ""
                stock_name = ""  # 如有股票名映射可查表，否则留空
                try:
                    xls = pd.ExcelFile(file_path)
                    for sheet in xls.sheet_names:
                        df = xls.parse(sheet)
                        if sheet in ['1d', '5min', '15min', '30min', '1h', '2h']:
                            print(f"分析: {file} - {sheet}")
                            period_dfs = build_period_dfs(file_path)
                            # 修正：按市场分目录
                            trend_dir = os.path.join(proceeded_dir, market)
                            os.makedirs(trend_dir, exist_ok=True)
                            analyze_trend(
                                period_dfs=period_dfs,
                                symbol=symbol,
                                stock_name=stock_name,
                                market=market,
                                date_str=date_str,
                                output_dir=trend_dir
                            )
                except Exception as e:
                    print(f"趋势分析失败: {file_path}，原因: {e}")

def ask_download_reports():
    print("检测到A股代码，是否需要同时下载报表？(y/n, 10秒内不输入默认否): ", end='', flush=True)
    result = {'answer': 'n'}
    def get_input():
        ans = input()
        if ans.strip().lower() == 'y':
            result['answer'] = 'y'
    t = threading.Thread(target=get_input)
    t.daemon = True
    t.start()
    t.join(timeout=10)
    return result['answer']

def ask_trend_analysis():
    while True:
        ans = input("是否进行趋势分析？(y/n，默认n): ").strip().lower()
        if ans in ['', 'n']:
            return False
        elif ans == 'y':
            return True
        print("请输入 y 或 n")

def main():
    fetcher = DataFetcher()
    # 检查是否有A股
    has_cn = any(s.endswith('.sh') or s.endswith('.sz') or s.endswith('.bj') for s in fetcher.symbols)
    if has_cn:
        ans = ask_download_reports()
        if ans == 'y':
            fetcher.download_cn_reports(fetcher.symbols)
    fetcher.fetch_all_stocks(periods=['1', '5', '15', '30'])
    
    # 生成行情指标
    print("开始生成行情指标...")
    batch_process("output_V4/CN", "output_V4/proceeded")
    batch_process("output_V4/HK", "output_V4/proceeded")
    batch_process("output_V4/US", "output_V4/proceeded")
    print("行情指标生成完成")
    
    # 添加趋势分析
    if ask_trend_analysis():
        print("开始进行趋势分析...")
        batch_trend_analysis("output_V4/proceeded")
        print("趋势分析完成")

if __name__ == "__main__":
    main() 
