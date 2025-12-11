from typing import List, Dict
import re

# OpenD连接配置
OPEND_HOST = "127.0.0.1"
OPEND_PORT = 11111

# 数据周期配置
PERIODS = ['1d', '4h', '2h', '1h', '30m', '15m', '5m', '3m']

# 技术指标配置
INDICATOR_SETTINGS = {
    'MA': [5, 10, 20],
    'RSI': [6, 12, 24],
    'MACD': {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9
    },
    'KDJ': {
        'fastk_period': 9,
        'slowk_period': 3,
        'slowd_period': 3
    }
}

# 输出配置
OUTPUT_DIR = "output"
OUTPUT_FILE_TEMPLATE = "{symbol}_merged_data.csv"

# 标准化字段名
COLUMN_NAMES = {
    # K线数据字段
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    
    # 技术指标字段
    "ma": "ma{period}",          # 如 ma5, ma10
    "ema": "ema{period}",        # 如 ema12, ema26
    "macd": "macd",
    "macd_signal": "signal",
    "macd_hist": "hist",
    "kdj_k": "k",
    "kdj_d": "d",
    "kdj_j": "j",
    "rsi": "rsi{period}",        # 如 rsi6, rsi12
    "boll_upper": "boll_upper",
    "boll_middle": "boll_mid",
    "boll_lower": "boll_lower",
    
    # 资金流向字段
    "main_inflow": "main_inflow",
    "main_outflow": "main_outflow",
    "main_net_flow": "main_net_flow",
    
    # 筹码分布字段
    "support_price": "support_price",
    "pressure_price": "pressure_price",
    "avg_cost": "avg_cost"
}

# 雪球API配置
XUEQIU_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def validate_stock_symbols(symbols: List[str]) -> bool:
    """
    验证股票代码列表
    
    格式规范：
    - 美股：无后缀，如 AAPL, GOOGL
    - 港股：以.hk结尾，如 00700.hk, 09988.hk
    - A股：以.ss或.sz结尾，如 600519.ss, 000001.sz
    
    Args:
        symbols: 股票代码列表
    
    Returns:
        bool: 是否全部有效
    """
    if not symbols:
        print("错误：未提供股票代码")
        return False
    
    if len(symbols) > 9:
        print("错误：股票代码数量超过9个限制")
        return False
    
    # 股票代码格式验证
    us_pattern = re.compile(r'^[A-Z]+$')  # 美股：纯大写字母
    hk_pattern = re.compile(r'^\d{5}\.hk$|^\d{4}\.hk$')  # 港股：4-5位数字 + .hk
    cn_pattern = re.compile(r'^\d{6}\.(ss|sz)$')  # A股：6位数字 + .ss/.sz
    
    for symbol in symbols:
        symbol = symbol.lower()  # 转换为小写以统一处理
        if not (
            us_pattern.match(symbol.upper()) or  # 美股
            hk_pattern.match(symbol) or  # 港股
            cn_pattern.match(symbol)  # A股
        ):
            print(f"错误：股票代码 {symbol} 格式无效")
            print("格式说明：")
            print("- 美股：纯大写字母，如 AAPL, GOOGL")
            print("- 港股：4-5位数字 + .hk，如 00700.hk, 09988.hk")
            print("- A股：6位数字 + .ss/.sz，如 600519.ss, 000001.sz")
            print("  上交所股票以.ss结尾（如：600519.ss）")
            print("  深交所股票以.sz结尾（如：000001.sz）")
            return False
    
    return True

# 输出CSV文件的列名配置
CSV_COLUMNS = {
    'base': ['datetime', 'open', 'high', 'low', 'close', 'volume'],
    'ma': ['ma5', 'ma10', 'ma20'],
    'macd': ['macd_dif', 'macd_dea', 'macd_hist'],
    'kdj': ['kdj_k', 'kdj_d', 'kdj_j'],
    'rsi': ['rsi6', 'rsi12', 'rsi24'],
    'capital_flow': ['capital_inflow', 'capital_outflow', 'capital_netflow']
}

# 合并所有列名
ALL_COLUMNS = (
    CSV_COLUMNS['base'] +
    CSV_COLUMNS['ma'] +
    CSV_COLUMNS['macd'] +
    CSV_COLUMNS['kdj'] +
    CSV_COLUMNS['rsi'] +
    CSV_COLUMNS['capital_flow']
)

def validate_stock_list(stock_list: List[str]) -> bool:
    """
    验证股票列表是否合法
    
    参数:
        stock_list: 股票代码列表
        
    返回:
        bool: 是否合法
    """
    if not stock_list:
        print("错误：股票列表为空")
        return False
    
    if len(stock_list) > 9:
        print("错误：股票数量超过9个")
        return False
    
    return True 