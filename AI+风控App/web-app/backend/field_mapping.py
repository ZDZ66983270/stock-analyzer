"""
统一字段映射配置
Unified Field Mapping Configuration

用于标准化不同数据源的字段名称
"""

# ============================================
# 标准字段定义 (Standard Fields)
# ============================================

STANDARD_FIELDS = {
    'timestamp': 'timestamp',  # 时间戳
    'open': 'open',           # 开盘价
    'high': 'high',           # 最高价
    'low': 'low',             # 最低价
    'close': 'close',         # 收盘价
    'volume': 'volume',       # 成交量
    'turnover': 'turnover',   # 成交额
    'change': 'change',       # 涨跌额
    'pct_change': 'pct_change', # 涨跌幅
    'price': 'price',         # 最新价
}

# ============================================
# yfinance 字段映射
# ============================================

YFINANCE_DAILY_MAPPING = {
    'Date': 'timestamp',
    'Open': 'open',
    'High': 'high',
    'Low': 'low',
    'Close': 'close',
    'Volume': 'volume',
}

YFINANCE_MINUTE_MAPPING = {
    'Datetime': 'timestamp',
    'Date': 'timestamp',  # 备用
    'Open': 'open',
    'High': 'high',
    'Low': 'low',
    'Close': 'close',
    'Volume': 'volume',
}

# ============================================
# AkShare 字段映射 (中文 → 英文)
# ============================================

AKSHARE_CN_SPOT_MAPPING = {
    '序号': 'index',
    '代码': 'code',
    '名称': 'name',
    '最新价': 'price',
    '今开': 'open',
    '最高': 'high',
    '最低': 'low',
    '昨收': 'prev_close',
    '成交量': 'volume',
    '成交额': 'turnover',
    '涨跌幅': 'pct_change',
    '涨跌额': 'change',
    '换手率': 'turnover_rate',
    '量比': 'volume_ratio',
    '振幅': 'amplitude',
    '总市值': 'market_cap',
    '流通市值': 'circulating_market_cap',
    '市盈率-动态': 'pe',
    '市净率': 'pb',
    '股息率': 'dividend_yield',
    '60日涨跌幅': 'pct_60d',
    '年初至今涨跌幅': 'pct_ytd',
}

AKSHARE_CN_HISTORY_MAPPING = {
    '日期': 'timestamp',
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'turnover',
    '振幅': 'amplitude',
    '涨跌幅': 'pct_change',
    '涨跌额': 'change',
    '换手率': 'turnover_rate',
}

AKSHARE_HK_SPOT_MAPPING = {
    '代码': 'code',
    '名称': 'name',
    '最新价': 'price',
    '涨跌额': 'change',
    '涨跌幅': 'pct_change',
    '今开': 'open',
    '最高': 'high',
    '最低': 'low',
    '昨收': 'prev_close',
    '成交量': 'volume',
    '成交额': 'turnover',
}

AKSHARE_HK_HISTORY_MAPPING = {
    '时间': 'timestamp',
    '日期': 'timestamp',  # 备用
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'turnover',
}

AKSHARE_US_SPOT_MAPPING = {
    '代码': 'code',
    '名称': 'name',
    '最新价': 'price',
    '涨跌额': 'change',
    '涨跌幅': 'pct_change',
}

# ============================================
# 数据源识别和映射选择
# ============================================

def get_mapping_for_source(source: str, data_type: str = 'daily') -> dict:
    """
    根据数据源和数据类型获取相应的字段映射
    
    Args:
        source: 数据源 ('yfinance', 'akshare_cn', 'akshare_hk', 'akshare_us')
        data_type: 数据类型 ('daily', 'minute', 'spot')
    
    Returns:
        字段映射字典
    """
    mapping_key = f"{source}_{data_type}".upper()
    
    mappings = {
        'YFINANCE_DAILY': YFINANCE_DAILY_MAPPING,
        'YFINANCE_MINUTE': YFINANCE_MINUTE_MAPPING,
        'AKSHARE_CN_SPOT': AKSHARE_CN_SPOT_MAPPING,
        'AKSHARE_CN_DAILY': AKSHARE_CN_HISTORY_MAPPING,
        'AKSHARE_CN_MINUTE': AKSHARE_CN_HISTORY_MAPPING,
        'AKSHARE_HK_SPOT': AKSHARE_HK_SPOT_MAPPING,
        'AKSHARE_HK_DAILY': AKSHARE_HK_HISTORY_MAPPING,
        'AKSHARE_HK_MINUTE': AKSHARE_HK_HISTORY_MAPPING,
        'AKSHARE_US_SPOT': AKSHARE_US_SPOT_MAPPING,
    }
    
    return mappings.get(mapping_key, {})


def detect_source_from_columns(columns: list) -> tuple:
    """
    从DataFrame的列名自动检测数据源
    
    Args:
        columns: DataFrame的列名列表
    
    Returns:
        (source, data_type) 元组
    """
    columns_set = set(columns)
    
    # yfinance特征
    if 'Date' in columns_set and 'Open' in columns_set:
        return ('yfinance', 'daily')
    if 'Datetime' in columns_set and 'Open' in columns_set:
        return ('yfinance', 'minute')
    
    # akshare特征 (中文字段)
    if '最新价' in columns_set:
        if '代码' in columns_set:
            # 判断市场
            return ('akshare_cn', 'spot')  # 默认CN，调用方需进一步判断
        return ('akshare_cn', 'spot')
    
    if '开盘' in columns_set and '收盘' in columns_set:
        if '日期' in columns_set or '时间' in columns_set:
            return ('akshare_cn', 'daily')  # 默认，调用方判断
    
    return ('unknown', 'unknown')


# ============================================
# 向后兼容的中文字段映射（用于检测和转换）
# ============================================

CHINESE_TO_ENGLISH_MAPPING = {
    '时间': 'timestamp',
    '日期': 'timestamp',
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'turnover',
    '涨跌幅': 'pct_change',
    '涨跌额': 'change',
    '最新价': 'price',
    '昨收': 'prev_close',
}

# ============================================
# 必需字段定义
# ============================================

REQUIRED_FIELDS_DAILY = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
REQUIRED_FIELDS_MINUTE = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
REQUIRED_FIELDS_SPOT = ['price']

def get_required_fields(data_type: str) -> list:
    """获取特定数据类型的必需字段"""
    required_map = {
        'daily': REQUIRED_FIELDS_DAILY,
        'minute': REQUIRED_FIELDS_MINUTE,
        'spot': REQUIRED_FIELDS_SPOT,
    }
    return required_map.get(data_type, [])
