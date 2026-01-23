"""
指数配置文件 - 记录正确的数据获取通道和参数

yfinance是最可靠的指数数据源，以下是经过验证的symbol映射。
"""

# 指数配置：内部symbol -> yfinance symbol
INDEX_CONFIG = {
    # US 市场指数
    "US": {
        "^DJI": {
            "yfinance_symbol": "^DJI",
            "name": "道琼斯工业指数",
            "name_en": "Dow Jones Industrial Average",
        },
        "^NDX": {
            "yfinance_symbol": "^NDX",
            "name": "纳斯达克100指数",
            "name_en": "NASDAQ-100",
        },
        "^SPX": {
            "yfinance_symbol": "^GSPC",  # S&P 500在yfinance的symbol
            "name": "标普500指数",
            "name_en": "S&P 500",
        },
        "DJI": {
            "yfinance_symbol": "^DJI",
            "name": "道琼斯工业指数",
            "name_en": "Dow Jones",
        },
        "NDX": {
            "yfinance_symbol": "^NDX",
            "name": "纳斯达克100指数",
            "name_en": "NASDAQ-100",
        },
        "SPX": {
            "yfinance_symbol": "^GSPC",
            "name": "标普500指数",
            "name_en": "S&P 500",
        },
    },
    # HK 市场指数
    "HK": {
        "HSI": {
            "yfinance_symbol": "^HSI",
            "name": "恒生指数",
            "name_en": "Hang Seng Index",
        },
        "HSTECH": {
            "yfinance_symbol": "HSTECH.HK",  # 或 ^HSTECH
            "name": "恒生科技指数",
            "name_en": "Hang Seng Tech Index",
        },
        "HSCC": {
            "yfinance_symbol": "^HSCC",
            "name": "恒生红筹股指数",
            "name_en": "Hang Seng China-Affiliated Corporations Index",
        },
        "HSCE": {
            "yfinance_symbol": "^HSCE",
            "name": "恒生中国企业指数",
            "name_en": "Hang Seng China Enterprises Index",
        },
    },
    # CN 市场指数 (如需要)
    "CN": {
        "000001.SS": {
            "yfinance_symbol": "000001.SS",
            "name": "上证综合指数",
            "name_en": "SSE Composite",
        },
        "000001": {
            "yfinance_symbol": "000001.SS",
            "name": "上证综合指数",
            "name_en": "SSE Composite",
        },
        "000300": {
            "yfinance_symbol": "000300.SS",
            "name": "沪深300指数",
            "name_en": "CSI 300",
        },
        "000016": {
            "yfinance_symbol": "000016.SS",
            "name": "上证50指数",
            "name_en": "SSE 50",
        },
        "000905": {
            "yfinance_symbol": "000905.SS",
            "name": "中证500指数",
            "name_en": "CSI 500",
        },
    },
}


def get_yfinance_symbol(internal_symbol: str, market: str) -> str:
    """
    将内部symbol转换为yfinance symbol
    
    Args:
        internal_symbol: 数据库中使用的symbol（如 ^DJI, HSI）
        market: 市场代码（US, HK, CN）
    
    Returns:
        yfinance可用的symbol
    """
    market_config = INDEX_CONFIG.get(market, {})
    index_config = market_config.get(internal_symbol, {})
    
    return index_config.get("yfinance_symbol", internal_symbol)


def is_index(symbol: str) -> bool:
    """判断symbol是否为指数"""
    # 以^开头，或者是特定的指数代码
    known_indices = {
        'HSI', 'HSTECH', 'HSCC', 'HSCE',
        '000001.SS', '000001', '000300', '000016', '000905',
        'DJI', 'NDX', 'SPX'
    }
    return symbol.startswith('^') or symbol in known_indices


def get_all_indices():
    """获取所有配置的指数列表"""
    result = []
    for market, indices in INDEX_CONFIG.items():
        for symbol, config in indices.items():
            result.append({
                "symbol": symbol,
                "market": market,
                "yfinance_symbol": config["yfinance_symbol"],
                "name": config["name"],
            })
    return result
