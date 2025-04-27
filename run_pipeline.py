import sys
import pytz
from datetime import datetime, timedelta
from utils.time_utils import get_trading_dates
from typing import List

from config import validate_stock_symbols
from fetch_kline_yfinance import fetch_stock_data
from fetch_capital_flow_xueqiu import fetch_capital_flow
from merge_data import merge_all_data

def get_market_type(symbol: str) -> str:
    """
    根据股票代码判断市场类型
    
    格式规范：
    - 美股：无后缀，如 AAPL, GOOGL
    - 港股：以.hk结尾，如 00700.hk, 09988.hk
    - A股：以.ss或.sz结尾，如 600519.ss, 000001.sz
    
    Args:
        symbol: 股票代码
        
    Returns:
        str: 'US' - 美股, 'HK' - 港股, 'CN' - A股
    """
    symbol = symbol.lower()  # 转换为小写以统一处理
    
    # 根据后缀判断
    if symbol.endswith('.hk'):
        return 'HK'
    elif symbol.endswith('.ss') or symbol.endswith('.sz'):
        return 'CN'
        
    # 根据前缀判断（无后缀时）
    if symbol.isdigit():
        if symbol.startswith(('60', '688')):  # 上交所
            return 'CN'
        elif symbol.startswith(('00', '300')):  # 深交所
            return 'CN'
        elif len(symbol) <= 5:  # 港股代码长度不超过5位
            return 'HK'
            
    return 'US'  # 无法判断时默认为美股

def get_market_config(market_type: str) -> dict:
    """
    获取市场相关配置
    
    Args:
        market_type: 市场类型 ('US', 'HK', 'CN')
        
    Returns:
        dict: 包含市场配置信息的字典
    """
    configs = {
        'US': {
            'timezone': 'America/New_York',
            'close_hour': 16,  # 美股收盘时间 16:00 ET
            'name': '美股'
        },
        'HK': {
            'timezone': 'Asia/Hong_Kong',
            'close_hour': 16,  # 港股收盘时间 16:00 HKT
            'name': '港股'
        },
        'CN': {
            'timezone': 'Asia/Shanghai',
            'close_hour': 15,  # A股收盘时间 15:00 CST
            'name': 'A股'
        }
    }
    return configs.get(market_type, configs['CN'])

def get_local_date(symbol: str) -> datetime:
    """
    根据股票代码获取对应市场的当前日期和时间。
    支持美股、港股和A股的不同时区和收盘时间。
    如果当前时间在收盘时间之前，返回前一个交易日。
    
    Args:
        symbol: 股票代码
        
    Returns:
        datetime: 调整后的日期时间
    """
    market_type = get_market_type(symbol)
    market_config = get_market_config(market_type)
    
    tz = pytz.timezone(market_config['timezone'])
    market_close_hour = market_config['close_hour']
    
    # 使用当前时间，而不是未来时间
    current_time = datetime.now(tz)
    print(f"当前时间 ({market_config['name']}, {tz.zone}): {current_time}")
    
    # 如果是周末，返回上周五
    if current_time.weekday() >= 5:
        days_to_subtract = current_time.weekday() - 4
        current_time = current_time - timedelta(days=days_to_subtract)
        print(f"周末调整到上周五: {current_time}")
    
    # 如果当前时间在收盘时间之前，使用前一个交易日
    if current_time.hour < market_close_hour:
        current_time = current_time - timedelta(days=1)
        # 如果调整后是周末，继续往前调整到周五
        while current_time.weekday() >= 5:
            current_time = current_time - timedelta(days=1)
        print(f"收盘时间前，调整到前一个交易日: {current_time}")
    
    return current_time.replace(hour=0, minute=0, second=0, microsecond=0)

def process_single_stock(symbol: str, start_date: str, end_date: str) -> None:
    """
    处理单个股票的数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        print(f"\n开始处理股票 {symbol} 的数据...")
        
        # 1. 获取K线数据
        print("正在获取K线数据...")
        kline_data = fetch_stock_data(symbol, start_date, end_date)
        if not kline_data:
            print(f"无法获取股票 {symbol} 的K线数据，跳过处理")
            return
        
        # 2. 获取资金流向数据
        print("正在获取资金流向数据...")
        capital_flow = fetch_capital_flow(symbol, start_date, end_date)
        
        # 3. 合并所有数据
        print("正在合并数据...")
        merged_data = merge_all_data(
            symbol,
            kline_data,
            capital_flow
        )
        
        if merged_data is not None:
            print(f"股票 {symbol} 的数据处理完成")
        else:
            print(f"股票 {symbol} 的数据处理失败")
        
    except Exception as e:
        print(f"处理股票 {symbol} 时发生错误: {str(e)}")

def main():
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("使用方法：python run_pipeline.py 股票代码1 股票代码2 ...")
        print("示例：python run_pipeline.py AAPL 00700.hk 600519.sh")
        sys.exit(1)
    
    # 解析股票列表
    stock_list = sys.argv[1:]
    
    # 验证股票列表
    if not validate_stock_symbols(stock_list):
        sys.exit(1)
    
    print(f"\n开始处理 {len(stock_list)} 只股票的数据...")
    
    # 按市场分组处理股票
    market_groups = {}
    for symbol in stock_list:
        market_type = get_market_type(symbol)
        if market_type not in market_groups:
            market_groups[market_type] = []
        market_groups[market_type].append(symbol)
    
    # 对每个市场分别处理
    for market_type, symbols in market_groups.items():
        market_config = get_market_config(market_type)
        print(f"\n处理{market_config['name']}市场的股票...")
        
        # 获取当前市场的结束日期
        end_date = get_local_date(symbols[0]).strftime('%Y-%m-%d')
        print(f"{market_config['name']}市场的结束日期: {end_date}")
        
        # 预留60天来确保能获取30个交易日
        start_date_temp = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # 获取实际的交易日列表
        trading_dates = get_trading_dates(start_date_temp, end_date)
        
        if not trading_dates:
            print(f"错误：无法获取{market_config['name']}市场的交易日数据")
            continue
        
        print(f"获取到 {len(trading_dates)} 个交易日")
        
        # 确保我们至少有30个交易日
        if len(trading_dates) >= 30:
            start_date = trading_dates[-30]
        else:
            print(f"警告：只获取到 {len(trading_dates)} 个交易日数据")
            start_date = trading_dates[0] if trading_dates else start_date_temp
        
        print(f"\n{market_config['name']}市场的分析日期范围: {start_date} 到 {end_date}")
        
        # 处理该市场的每只股票
        for symbol in symbols:
            process_single_stock(symbol, start_date, end_date)
    
    print("\n所有股票处理完成！")

if __name__ == "__main__":
    main() 