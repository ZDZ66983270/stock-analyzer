import pandas as pd
import logging
from datetime import datetime
import os
from typing import List, Dict, Optional
from fetch_kline_yfinance import KlineFetcher
from fetch_capital_flow_xueqiu import CapitalFlowFetcher
from compute_indicators import TechnicalIndicator

class StockDataPipeline:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.kline_fetcher = KlineFetcher()
        self.flow_fetcher = CapitalFlowFetcher()
        self.indicator_calculator = TechnicalIndicator()
        
        # 创建输出目录
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 配置日志
        self._setup_logging()
        
    def _setup_logging(self):
        """配置日志输出"""
        log_file = os.path.join(self.output_dir, 'run_log.txt')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
        
    def process_stocks(self, symbols: List[str], intervals: List[str] = None) -> None:
        """
        批量处理股票数据
        
        Args:
            symbols: 股票代码列表
            intervals: K线周期列表，默认为 ['1d']
        """
        try:
            # 验证股票数量
            if len(symbols) > 9:
                raise ValueError("一次最多处理9支股票")
                
            # 设置默认周期
            if intervals is None:
                intervals = ['1d']
                
            # 处理每个股票
            for symbol in symbols:
                try:
                    self.logger.info(f"\n开始处理股票：{symbol}")
                    
                    # 创建Excel writer
                    excel_file = os.path.join(
                        self.output_dir,
                        f"{symbol.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    )
                    
                    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                        # 获取并处理每个周期的数据
                        for interval in intervals:
                            # 获取K线数据
                            df = self.kline_fetcher.fetch_kline(symbol, interval)
                            if df is None or df.empty:
                                self.logger.error(f"获取{interval}周期K线数据失败")
                                continue
                                
                            # 计算技术指标
                            df = self.indicator_calculator.add_technical_indicators(df)
                            
                            # 调整列顺序
                            columns = [
                                'datetime', 'open', 'high', 'low', 'close', 'volume',
                                'MA5', 'MA10', 'MA20',
                                'MACD_DIF', 'MACD_DEA', 'MACD_HIST',
                                'KDJ_K', 'KDJ_D', 'KDJ_J',
                                'RSI6', 'RSI12', 'RSI24'
                            ]
                            df = df[columns]
                            
                            # 保存到Excel的对应sheet
                            df.to_excel(writer, sheet_name=interval, index=False)
                            
                            # 设置列宽
                            worksheet = writer.sheets[interval]
                            worksheet.set_column('A:A', 20)  # datetime列
                            worksheet.set_column('B:R', 12)  # 其他列
                            
                        # 获取资金流向数据（仅限A股）
                        if symbol.startswith(('SH.', 'SZ.')):
                            flow_df = self.flow_fetcher.fetch_capital_flow(symbol)
                            if flow_df is not None and not flow_df.empty:
                                # 调整列顺序
                                flow_columns = [
                                    'datetime', 'capital_inflow',
                                    'capital_outflow', 'capital_netflow'
                                ]
                                flow_df = flow_df[flow_columns]
                                
                                # 保存到Excel
                                flow_df.to_excel(
                                    writer,
                                    sheet_name='capital_flow',
                                    index=False
                                )
                                
                                # 设置列宽
                                worksheet = writer.sheets['capital_flow']
                                worksheet.set_column('A:A', 20)
                                worksheet.set_column('B:D', 15)
                                
                    self.logger.info(f"股票{symbol}数据已保存到：{excel_file}")
                    
                except Exception as e:
                    self.logger.error(f"处理股票{symbol}时发生错误: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"批量处理股票数据时发生错误: {str(e)}")

def main():
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="股票数据批量处理工具")
    parser.add_argument(
        "symbols",
        nargs="+",
        help="股票代码列表，例如：SH.600000 SZ.000001"
    )
    parser.add_argument(
        "--intervals",
        nargs="+",
        default=['1d'],
        choices=['5m', '15m', '30m', '1h', '4h', '1d'],
        help="K线周期列表"
    )
    args = parser.parse_args()
    
    # 创建处理器实例
    pipeline = StockDataPipeline()
    
    # 处理股票数据
    pipeline.process_stocks(args.symbols, args.intervals)

if __name__ == "__main__":
    main() 