
# =================================================================================================
# 🔒 IMPORT LOGIC FROZEN / 导入逻辑固化 🔒
# English: The asset import and Canonical ID generation logic are now frozen to ensure consistency.
# If any modification is required, you MUST explain the rationale to the USER and obtain 
# explicit confirmation before changing the code.
#
# 中文：资产导入和典范 ID (Canonical ID) 生成逻辑已固化以确保一致性。
# 如需任何修改，必须向用户说明并在获得明确确认后方可改动代码。
# =================================================================================================

import re

def parse_canonical_id(canonical_id: str) -> dict:
    """
    Parse a Canonical ID into its components.
    Example: 'CN:INDEX:000001' -> {'market': 'CN', 'type': 'INDEX', 'symbol': '000001'}
    """
    parts = str(canonical_id).split(':')
    if len(parts) >= 3:
        return {
            'market': parts[0],
            'type': parts[1],
            'symbol': parts[2]
        }
    return {
        'market': 'US', # Default
        'type': 'STOCK',
        'symbol': canonical_id
    }

def is_index(symbol: str) -> bool:
    """Check if a symbol (Canonical ID) represents an index."""
    return ':INDEX:' in str(symbol).upper()

def get_yahoo_symbol(symbol: str, market: str, asset_type: str = 'STOCK') -> str:
    """
    Convert internal symbol to Yahoo Finance format.
    
    Args:
        symbol: Internal symbol (e.g., '00700', '09988', '600519', 'AAPL', '000001')
        market: Market identifier ('HK', 'CN', 'US')
        asset_type: 'STOCK', 'INDEX', 'ETF', etc.
        
    Returns:
        Yahoo-compatible symbol string (e.g., '0700.HK', '600519.SS', '000001.SS')
    """
    symbol = str(symbol).strip().upper()
    asset_type = asset_type.upper() if asset_type else 'STOCK'
    
    if market == 'HK':
        # Remove suffix if present (e.g. 00700.HK -> 00700)
        clean_code = symbol.replace('.HK', '').replace('^', '')
        
        # 特殊处理：指数前缀 (HSI -> ^HSI)
        if asset_type == 'INDEX':
            # 恒生科技比较特殊，yfinance 用 HSTECH.HK (但历史有限)
            if clean_code == 'HSTECH':
                 return "HSTECH.HK"
            return f"^{clean_code}"

        # Logic: int(code) -> at least 4 digits
        try:
            code_int = int(clean_code)
            # Format as at least 4 digits (e.g., 700 -> 0700, 9988 -> 9988)
            yahoo_code = f"{code_int:04d}"
            return f"{yahoo_code}.HK"
        except ValueError:
            # Fallback if not numeric
            return f"{clean_code}.HK"

    elif market == 'CN':
        # Simple heuristic for suffix
        clean_code = symbol.replace('.SS', '').replace('.SZ', '').replace('.BJ', '')
        
        # 特殊处理：上证指数 (000001) 与 平安银行 (000001) 的冲突
        if asset_type == 'INDEX':
            # A股指数即使以0开头也通常是上海交易所 (.SS)
            # 例如: 000300 (沪深300), 000016 (上证50), 000905 (中证500)
            if clean_code in ['000001', '000300', '000016', '000905']:
                return f"{clean_code}.SS"
            
        if clean_code.startswith('6'):
            # 6xxxxx: 上海主板
            return f"{clean_code}.SS"
        elif clean_code.startswith('0') or clean_code.startswith('3'):
            # 0xxxxx, 3xxxxx: 深圳主板/创业板
            return f"{clean_code}.SZ"
        elif clean_code.startswith('8') or clean_code.startswith('4'):
            # 8xxxxx, 4xxxxx: 北京交易所
            return f"{clean_code}.BJ"
        elif clean_code.startswith('1'):
            # 1xxxxx: 深圳ETF
            return f"{clean_code}.SZ"
        elif clean_code.startswith('5'):
            # 5xxxxx: 上海ETF
            return f"{clean_code}.SS"
        else:
            # 其他默认上海（主要是指数）
            return f"{clean_code}.SS"

    elif market == 'US':
        # Crypto handling within US market
        if asset_type == 'CRYPTO':
            # Ensure it's like BTC-USD
            if not symbol.endswith('-USD'):
                return f"{symbol}-USD"
            return symbol

        # Add ^ prefix for indices in US market
        if asset_type == 'INDEX' and not symbol.startswith('^'):
            return f"^{symbol}"
        return symbol

    elif market == 'WORLD' and asset_type == 'CRYPTO': # Keep for backward compatibility or if logic reverts
        # Ensure it's like BTC-USD
        if not symbol.endswith('-USD'):
            return f"{symbol}-USD"
        return symbol

    # Default
    return symbol


def get_all_symbols_to_update(session) -> list[dict]:
    """
    获取所有需要更新的资产 (统一从 Watchlist 表获取)
    """
    from sqlmodel import select
    from models import Watchlist
    
    symbols = []
    
    # 1. 获取所有Watchlist中的资产
    watchlist_items = session.exec(select(Watchlist)).all()
    for item in watchlist_items:
        # 自动判断类型
        asset_type = 'INDEX' if ':INDEX:' in item.symbol else 'STOCK'
        if ':CRYPTO:' in item.symbol: asset_type = 'CRYPTO'
        if ':ETF:' in item.symbol: asset_type = 'ETF'
        if ':TRUST:' in item.symbol: asset_type = 'TRUST'
        
        symbols.append({
            "symbol": item.symbol,
            "name": item.name or item.symbol,
            "market": item.market,
            "type": asset_type,
            "source": "watchlist"
        })
    
    return symbols


def get_symbols_by_market(session, market: str) -> list[dict]:
    """
    获取指定市场的所有资产 (统一从 Watchlist 表获取)
    """
    from sqlmodel import select
    from models import Watchlist
    
    symbols = []
    
    # 1. Watchlist中的资产
    watchlist_items = session.exec(
        select(Watchlist).where(Watchlist.market == market)
    ).all()
    for item in watchlist_items:
        asset_type = 'INDEX' if ':INDEX:' in item.symbol else 'STOCK'
        if ':CRYPTO:' in item.symbol: asset_type = 'CRYPTO'
        if ':ETF:' in item.symbol: asset_type = 'ETF'
        if ':TRUST:' in item.symbol: asset_type = 'TRUST'

        symbols.append({
            "symbol": item.symbol,
            "name": item.name or item.symbol,
            "market": item.market,
            "type": asset_type,
            "source": "watchlist"
        })
    
    return symbols


# =================================================================================================
# 🔒 CRITICAL LOGIC: DO NOT MODIFY WITHOUT USER CONSENT / 关键逻辑：未经用户同意请勿修改 🔒
# =================================================================================================
def get_canonical_id(symbol: str, market: str, asset_type: str = 'STOCK') -> tuple[str, str]:
    """
    构造典范 ID (Canonical ID)
    Examples:
        ('600519', 'CN', 'STOCK') -> ('CN:STOCK:600519', 'CN')
        ('00700', 'HK', 'STOCK') -> ('HK:STOCK:00700', 'HK')
        ('AAPL', 'US', 'STOCK') -> ('US:STOCK:AAPL', 'US')
        ('BTC', 'CRYPTO', 'CRYPTO') -> ('US:CRYPTO:BTC-USD', 'US')
    """
    symbol = symbol.strip().upper()
    market = market.upper()
    asset_type = asset_type.upper() if asset_type else 'STOCK'

    # Special handling for Crypto: Move to US market
    if asset_type == 'CRYPTO' or market == 'CRYPTO':
        market = 'US' # Changed from WORLD to US per user request
        asset_type = 'CRYPTO'
        # Ensure -USD suffix for consistency
        if not symbol.endswith('-USD'):
            # Remove any existing -BTC or similar if it's there? No, just add -USD if missing
            symbol = f"{symbol}-USD"
        canonical_id = f"{market}:{asset_type}:{symbol}"
        return canonical_id, market

    # Remove yahoo suffixes if present
    if market == 'CN':
        symbol = symbol.replace('.SS', '').replace('.SZ', '').replace('.BJ', '')
    elif market == 'HK':
        symbol = symbol.replace('.HK', '')
    
    # Strip '^' from indices to ensure DJI and ^DJI map to the same ID
    # This also handles cases where user provides ^HSI instead of HSI
    symbol = symbol.replace('^', '')
    
    # Standardize numeric symbols
    if market == 'HK' and symbol.isdigit():
        symbol = f"{int(symbol):05d}"
    if market == 'CN' and symbol.isdigit():
        symbol = f"{int(symbol):06d}"
        
    canonical_id = f"{market}:{asset_type}:{symbol}"
    return canonical_id, market
