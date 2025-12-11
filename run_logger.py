# run_logger.py

import os
import logging
from datetime import datetime
from modules.utils import read_symbols_from_file, save_to_excel
from modules.data_fetcher import fetch_all_kline_data
from modules.fund_flow_fetcher import fetch_fund_flow
from modules.technical_indicators import add_technical_indicators

# 初始化日志
today_str = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename=f'logs/run_{today_str}.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

def main():
    logging.info("📄 读取到股票列表...")
    symbols = read_symbols_from_file('config/symbols.txt')
    logging.info(f"📄 读取到 {len(symbols)} 只股票：{symbols}")
    logging.info("=" * 60)

    for idx, symbol in enumerate(symbols, start=1):
        logging.info(f"\n🚀 [{idx}/{len(symbols)}] 开始处理 {symbol}")
        try:
            kline_data = fetch_all_kline_data(symbol)
            fund_flow_data = fetch_fund_flow(symbol)

            # ⚡ 新增核心判断
            no_kline = (not kline_data) or all((df is None or df.empty) for df in kline_data.values())
            no_fund_flow = (fund_flow_data is None) or fund_flow_data.empty

            if no_kline and no_fund_flow:
                logging.warning(f"⚠️ {symbol} 无有效K线数据且无资金流数据，跳过保存")
                continue

            # 有有效数据的，才继续计算指标并保存
            for period, df in kline_data.items():
                if df is not None and not df.empty:
                    kline_data[period] = add_technical_indicators(df)

            save_to_excel(symbol, kline_data, fund_flow_data)
            logging.info(f"✅ {symbol} 处理完成")
        except Exception as e:
            logging.error(f"❌ 处理 {symbol} 出现异常: {e}", exc_info=True)

    logging.info("\n🎉 全部处理完成！")

if __name__ == '__main__':
    main() 