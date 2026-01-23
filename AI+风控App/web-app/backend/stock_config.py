"""
个股配置文件 - 记录各市场个股的yfinance symbol转换规则

与index_config.py配合使用，确保所有股票代码能正确转换为yfinance可用的格式。
"""

# ============================================================
# yfinance Symbol 转换规则
# ============================================================
# 
# 【CN 市场】A股
#   - 上海: 600xxx.sh → 600xxx.SS (yfinance)
#   - 深圳: 000xxx.sz → 000xxx.SZ (yfinance)
#   - 创业板: 300xxx.sz → 300xxx.SZ (yfinance)
#
# 【HK 市场】港股
#   - 标准个股: 09988.hk → 9988.HK (yfinance, 去掉前导0)
#   - 指数: HSI → ^HSI (yfinance, 加^前缀)
#
# 【US 市场】美股
#   - 个股: TSLA.OQ → TSLA (yfinance, 去掉.OQ后缀)
#   - 指数: 见 index_config.py
#
# ============================================================


def convert_to_yfinance_symbol(symbol: str, market: str) -> str:
    """
    将内部股票代码转换为yfinance可用的symbol
    
    Args:
        symbol: 数据库中使用的symbol（如 600030.sh, 09988.hk, TSLA.OQ）
        market: 市场代码（US, HK, CN）
    
    Returns:
        yfinance可用的symbol
    """
    s = symbol.upper()
    
    if market == "CN":
        # 上海: .SH → .SS
        if s.endswith('.SH'):
            return s.replace('.SH', '.SS')
        elif s.endswith('.SZ'):
            return s  # 深圳保持.SZ
        else:
            # 尝试推断
            code = s.split('.')[0]
            if code.startswith('6'):
                return f"{code}.SS"
            else:
                return f"{code}.SZ"
    
    elif market == "HK":
        # 去掉.HK后缀，去掉前导0，再加.HK
        code = s.replace('.HK', '')
        if code.isdigit():
            # 去掉前导0: 09988 → 9988
            code = str(int(code))
            return f"{code}.HK"
        else:
            # 非纯数字可能是指数
            return f"{code}.HK"
    
    elif market == "US":
        # 去掉.OQ后缀
        if '.OQ' in s:
            return s.replace('.OQ', '')
        elif '.O' in s:
            return s.replace('.O', '')
        elif '.N' in s:
            return s.replace('.N', '')
        else:
            return s
    
    return s


def convert_to_internal_symbol(yf_symbol: str, market: str) -> str:
    """
    将yfinance symbol转换回内部使用的格式
    
    Args:
        yf_symbol: yfinance symbol (如 600030.SS, 9988.HK, TSLA)
        market: 市场代码
    
    Returns:
        内部symbol格式
    """
    s = yf_symbol.upper()
    
    if market == "CN":
        # .SS → .SH
        if s.endswith('.SS'):
            return s.replace('.SS', '.SH')
        return s
    
    elif market == "HK":
        # 补全前导0: 9988.HK → 09988.HK
        if '.HK' in s:
            code = s.replace('.HK', '')
            if code.isdigit():
                return f"{int(code):05d}.HK"
        return s
    
    elif market == "US":
        # 添加.OQ后缀（如果是个股而非指数）
        if not s.startswith('^'):
            return f"{s}.OQ"
        return s
    
    return s


# ============================================================
# 自选股配置（可选：预定义的股票信息）
# ============================================================

WATCHLIST_PRESETS = {
    "CN": {
        "600030.SH": {"name": "中信证券", "sector": "券商"},
        "600309.SH": {"name": "万华化学", "sector": "化工"},
        "601519.SH": {"name": "大智慧", "sector": "软件"},
    },
    "HK": {
        "09988.HK": {"name": "阿里巴巴-W", "sector": "互联网"},
        "00005.HK": {"name": "汇丰控股", "sector": "银行"},
    },
    "US": {
        "TSLA": {"name": "特斯拉", "sector": "汽车"},
        "MSFT": {"name": "微软", "sector": "软件"},
    },
}


# ============================================================
# 数据源优先级配置
# ============================================================

DATA_SOURCE_PRIORITY = {
    "CN": ["akshare", "yfinance"],    # A股优先AkShare
    "HK": ["akshare", "yfinance"],    # 港股优先AkShare
    "US": ["yfinance"],               # 美股只用yfinance
}


def get_data_sources(market: str) -> list:
    """获取指定市场的数据源优先级列表"""
    return DATA_SOURCE_PRIORITY.get(market, ["yfinance"])
