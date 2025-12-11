# modules/utils.py
import os
import pandas as pd
from datetime import datetime

def read_symbols_from_file(file_path: str):
    """读取config/symbols.txt中的股票代码"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_to_excel(symbol: str, kline_data: dict, fund_flow_data: pd.DataFrame = None):
    """保存K线数据和资金流数据到Excel文件"""
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{symbol.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")

    # 检查是否有有效数据
    has_valid_data = False
    for period, df in kline_data.items():
        if df is not None and not df.empty:
            has_valid_data = True
            break
    if fund_flow_data is not None and not fund_flow_data.empty:
        has_valid_data = True

    if not has_valid_data:
        print(f"[跳过保存] {symbol} 没有有效数据，不生成Excel文件。")
        return

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 创建一个默认的sheet，确保至少有一个可见的sheet
        pd.DataFrame().to_excel(writer, sheet_name='数据概览', index=False)
        
        sheets_written = 0
        for period, df in kline_data.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=period, index=False)
                sheets_written += 1
        if fund_flow_data is not None and not fund_flow_data.empty:
            fund_flow_data.to_excel(writer, sheet_name='FundFlow', index=False)
            sheets_written += 1

    if sheets_written == 0:
        # 如果除了默认sheet外没有其他数据，删除文件
        if os.path.exists(output_file):
            os.remove(output_file)
        print(f"[跳过保存] {symbol} 没有有效数据，不生成Excel文件。")
    else:
        print(f"[保存完成] {symbol} → {output_file}")
