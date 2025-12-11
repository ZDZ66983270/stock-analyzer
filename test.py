import logging
from modules.utils import read_symbols_from_file, save_to_excel
from modules.data_fetcher import fetch_kline_data
from modules.fund_flow_fetcher import fetch_fund_flow
from modules.technical_indicators import add_technical_indicators

def main():
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # 读取股票代码
    try:
        symbols = read_symbols_from_file('config/symbols.txt')
        logging.info(f"📄 读取到 {len(symbols)} 只股票：{symbols}")
    except Exception as e:
        logging.error(f"❌ 读取股票代码失败: {e}")
        return
    
    # 遍历处理每只股票
    for i, symbol in enumerate(symbols, 1):
        logging.info(f"\n🚀 [{i}/{len(symbols)}] 开始处理 {symbol}")
        
        try:
            # 获取K线数据
            kline_data = {}
            for period in ['daily', 'weekly', 'monthly']:
                df = fetch_kline_data(symbol, period)
                if df is not None and not df.empty:
                    df = add_technical_indicators(df)
                kline_data[period] = df
            
            # 获取资金流向
            fund_flow = fetch_fund_flow(symbol)
            
            # 保存到Excel
            save_to_excel(symbol, kline_data, fund_flow)
            
        except Exception as e:
            logging.error(f"❌ 处理 {symbol} 出现异常: {e}")
    
    logging.info("\n🎉 全部处理完成！")

if __name__ == "__main__":
    main() 