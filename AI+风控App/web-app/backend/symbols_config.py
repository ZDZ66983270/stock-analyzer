"""
统一的股票/指数配置文件
所有下载清单和规则从这里获取，消除代码中的硬编码
"""

# 支持的指数列表（用于市场页面显示和自动下载）
# 支持的指数列表（用于市场页面显示和自动下载）
INDEX_LIST = [
    "^DJI", "^NDX", "^SPX", "DJI", "NDX", "SPX",
    "HSI", "HSTECH", "HSCC", "HSCE",
    "000001.SS", "000001", "000300", "000016", "000905"
]

# ============================================
# 符号别名映射（防止重复数据）
# ============================================
# 多个代码指向同一个标准代码
# 用途：不同数据源可能使用不同的代码表示同一个指数/股票
SYMBOL_ALIASES = {
    # HK指数别名
    "800000": "HSI",      # AkShare恒生指数代码 → 标准代码
    "800700": "HSTECH",   # AkShare恒生科技代码 → 标准代码
    
    # 可能的其他别名（未来扩展）
    # "^GSPC": "^SPX",    # S&P 500的不同代码
    # "000001.SS": "^SSEC",  # 上证指数的不同代码
}

def get_canonical_symbol(symbol: str) -> str:
    """
    获取标准符号（规范化符号）
    
    将别名转换为标准代码，防止同一指数/股票有多个代码导致重复数据
    
    Args:
        symbol: 输入符号（可能是别名）
        
    Returns:
        标准符号
        
    Examples:
        >>> get_canonical_symbol("800000")
        "HSI"
        
        >>> get_canonical_symbol("HSI")
        "HSI"
        
        >>> get_canonical_symbol("800700")
        "HSTECH"
        
        >>> get_canonical_symbol("TSLA")
        "TSLA"
    """
    return SYMBOL_ALIASES.get(symbol, symbol)

# 指数配置：内部symbol -> 数据源symbol和元数据
SYMBOLS_CONFIG = {
    # ============ 美指 ============
    "^DJI": {
        "market": "US",
        "type": "index",
        "yfinance_symbol": "^DJI",
        "akshare_symbol": ".DJI",  # AkShare使用.DJI
        "name": "道琼斯",
        "name_en": "Dow Jones Industrial Average",
        "data_sources": ["akshare", "yfinance"],  # 优先AkShare避免被yahoo拉黑
    },
    "^NDX": {
        "market": "US",
        "type": "index",
        "yfinance_symbol": "^NDX",  # 纳斯达克100，不是^IXIC(综合指数)
        "akshare_symbol": ".NDX",  # AkShare的纳斯达克100代码
        "name": "纳斯达克100",
        "name_en": "NASDAQ-100",
        "data_sources": ["akshare", "yfinance"],
        "note": "注意：^NDX是纳斯达克100，^IXIC是纳斯达克综合指数，两者不同"
    },
    "^SPX": {
        "market": "US",
        "type": "index",
        "yfinance_symbol": "^GSPC",  # yfinance用S&P 500
        "akshare_symbol": ".INX",  # AkShare使用.INX
        "name": "标普500",
        "name_en": "S&P 500",
        "data_sources": ["akshare", "yfinance"],
    },
    
    # ============ 港指 ============
    "HSI": {
        "market": "HK",
        "type": "index",
        "yfinance_symbol": "^HSI",
        "akshare_symbol": "800000",  # ✅ AkShare实际需要800000
        "name": "恒生指数",
        "name_en": "Hang Seng Index",
        "data_sources": ["akshare", "yfinance"],
    },
    "HSTECH": {
        "market": "HK",
        "type": "index",
        "yfinance_symbol": "HSTECH.HK",  # ✅ Yahoo Finance的正确代码
        "akshare_symbol": "800700",  # ✅ AkShare实际需要800700
        "name": "恒生科技指数",
        "name_en": "Hang Seng Tech Index",
        "data_sources": ["akshare", "yfinance"],
    },
    
    # ============ 沪深指 ============
    "000001.SS": {
        "market": "CN",
        "type": "index",
        "yfinance_symbol": "000001.SS",
        "akshare_symbol": "sh000001",  # ← 关键修复！AkShare使用sh000001而不是000001
        "name": "上证综合指数",
        "name_en": "SSE Composite",
        "data_sources": ["akshare", "yfinance"],
        "note": "注意：000001是平安银行，sh000001才是上证指数"
    },
    "000001": {
        "market": "CN",
        "type": "index",
        "yfinance_symbol": "000001.SS",
        "akshare_symbol": "sh000001",
        "name": "上证综合指数",
        "name_en": "SSE Composite",
        "data_sources": ["akshare", "yfinance"],
    },
    "000300": {
        "market": "CN",
        "type": "index",
        "yfinance_symbol": "000300.SS",
        "akshare_symbol": "sh000300",
        "name": "沪深300",
        "name_en": "CSI 300",
        "data_sources": ["akshare", "yfinance"],
    },
    "000016": {
        "market": "CN",
        "type": "index",
        "yfinance_symbol": "000016.SS",
        "akshare_symbol": "sh000016",
        "name": "上证50",
        "name_en": "SSE 50",
        "data_sources": ["akshare", "yfinance"],
    },
    "000905": {
        "market": "CN",
        "type": "index",
        "yfinance_symbol": "000905.SS",
        "akshare_symbol": "sh000905",
        "name": "中证500",
        "name_en": "CSI 500",
        "data_sources": ["akshare", "yfinance"],
    },
    
    # ============ US 别名 (不带^) ============
    "DJI": {
        "market": "US",
        "type": "index",
        "yfinance_symbol": "^DJI",
        "akshare_symbol": ".DJI",
        "name": "道琼斯",
        "name_en": "Dow Jones Industrial Average",
        "data_sources": ["akshare", "yfinance"],
    },
    "NDX": {
        "market": "US",
        "type": "index",
        "yfinance_symbol": "^NDX",
        "akshare_symbol": ".NDX",
        "name": "纳斯达克100",
        "name_en": "NASDAQ-100",
        "data_sources": ["akshare", "yfinance"],
    },
    "SPX": {
        "market": "US",
        "type": "index",
        "yfinance_symbol": "^GSPC",
        "akshare_symbol": ".INX",
        "name": "标普500",
        "name_en": "S&P 500",
        "data_sources": ["akshare", "yfinance"],
    },
    
    # ============ HK 更多指数 ============
    "HSCC": {
        "market": "HK",
        "type": "index",
        "yfinance_symbol": "^HSCC",
        "akshare_symbol": "800000", # TODO: 确认AkShare具体的HSCC代码，暂用HSI占位
        "name": "恒生红筹股指数",
        "name_en": "Hang Seng China-Affiliated Corporations Index",
        "data_sources": ["yfinance"],
    },
    "HSCE": {
        "market": "HK",
        "type": "index",
        "yfinance_symbol": "^HSCE",
        "akshare_symbol": "800100", # AkShare恒生中国企业指数代码通常是800100
        "name": "恒生中国企业指数",
        "name_en": "Hang Seng China Enterprises Index",
        "data_sources": ["akshare", "yfinance"],
    },
    
    # ============ 其他映射 ============
    "0P0001T7E6": {
        "market": "US",
        "type": "trust",
        "yfinance_symbol": "0P0001T7E6.L",
        "name": "PIMCO GIS Bal Inc & Gr",
        "data_sources": ["yfinance"],
    },
}

import yfinance as yf

# 静态汇率配置，用于财报货币与市场报价之间的换算
FOREX_RATES = {
    'USD/TWD': 32.5,  # 台积电等 ADR
    'USD/CNY': 7.2,   # 中概股
    'HKD/CNY': 0.92,  # 港股通
    'USD/HKD': 7.8,   # 港币/美元
}

def get_yfinance_symbol(symbol: str) -> str:
    """
    获取yfinance使用的symbol
    
    Args:
        symbol: 内部使用的symbol（如 ^DJI, ^NDX）
    
    Returns:
        yfinance可用的symbol（如 ^DJI, ^IXIC, ^GSPC）
    """
    config = SYMBOLS_CONFIG.get(symbol, {})
    return config.get("yfinance_symbol", symbol)


def get_akshare_symbol(symbol: str) -> str:
    """
    获取AkShare使用的symbol（集中管理映射关系）
    
    这是解决映射关系表被fetch调用问题的核心函数。
    所有AkShare symbol映射都在SYMBOLS_CONFIG中定义，
    fetch代码只需调用此函数，不需要硬编码映射关系。
    
    Args:
        symbol: 内部使用的symbol（如 ^DJI, 000001.SS, HSTECH）
    
    Returns:
        AkShare可用的symbol（如 .DJI, sh000001, HSTECH）
        
    Examples:
        >>> get_akshare_symbol("^DJI")
        ".DJI"
        
        >>> get_akshare_symbol("000001.SS")
        "sh000001"  # 不是000001！
        
        >>> get_akshare_symbol("HSTECH")
        "HSTECH"
    """
    config = SYMBOLS_CONFIG.get(symbol, {})
    return config.get("akshare_symbol", symbol)


def is_index(symbol: str) -> bool:
    """
    判断symbol是否为指数
    
    Args:
        symbol: 内部symbol
    
    Returns:
        True if index, False otherwise
    """
    return symbol in INDEX_LIST


def get_symbol_info(symbol: str) -> dict:
    """
    获取symbol的完整配置信息
    
    Args:
        symbol: 内部symbol
    
    Returns:
        配置字典，如果不存在返回空字典
    """
    return SYMBOLS_CONFIG.get(symbol, {})


def get_all_indices() -> list:
    """
    获取所有配置的指数列表
    
    Returns:
        指数symbol列表
    """
    return INDEX_LIST.copy()


def get_indices_by_market(market: str) -> list:
    """
    获取某市场的所有指数
    
    Args:
        market: 市场代码（US, HK, CN）
    
    Returns:
        该市场的指数symbol列表
    """
    return [
        symbol for symbol, config in SYMBOLS_CONFIG.items()
        if config.get("market") == market and config.get("type") == "index"
    ]

def normalize_code(symbol: str) -> str:
    """
    Remove market/type prefixes to get the core ticker.
    e.g. US:STOCK:AAPL -> AAPL
         HK:STOCK:00700 -> 00700
    """
    if ":" in symbol:
        return symbol.split(":")[-1]
    return symbol

# ADR Conversion Ratios (1 ADR = N Common Shares)
# Add TSM specific configuration
SYMBOLS_CONFIG['TSM'] = {
    "market": "US",
    "type": "stock",
    "adr_ratio": 5.0,  # 1 ADR = 5 Common Shares
    "currency": "USD", # Market Currency
    "name": "Taiwan Semiconductor",
    "yfinance_symbol": "TSM"
}

# Major Chinese ADRs
SYMBOLS_CONFIG['BABA'] = {
    "market": "US", "type": "stock", "adr_ratio": 8.0, "currency": "USD", "name": "Alibaba Group", "yfinance_symbol": "BABA"
}
SYMBOLS_CONFIG['JD'] = {
    "market": "US", "type": "stock", "adr_ratio": 2.0, "currency": "USD", "name": "JD.com", "yfinance_symbol": "JD"
}
SYMBOLS_CONFIG['PDD'] = {
    "market": "US", "type": "stock", "adr_ratio": 4.0, "currency": "USD", "name": "PDD Holdings", "yfinance_symbol": "PDD"
}
SYMBOLS_CONFIG['BIDU'] = {
    "market": "US", "type": "stock", "adr_ratio": 8.0, "currency": "USD", "name": "Baidu", "yfinance_symbol": "BIDU"
}
