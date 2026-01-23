"""
Data Validation Utilities for Market Data

Provides functions to validate, clean, and repair market data.
"""

from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def validate_market_data(data: Dict, symbol: str, market: str) -> Tuple[bool, list]:
    """
    Validate market data completeness and correctness.
    
    Args:
        data: Market data dictionary
        symbol: Stock symbol
        market: Market code (US/HK/CN)
    
    Returns:
        tuple: (is_valid, errors)
        - is_valid: True if data passes validations
        - errors: List of validation error messages
    """
    errors = []
    
    # Required fields
    required_fields = ['symbol', 'market', 'price', 'date']
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Price validation
    if 'price' in data:
        price = data.get('price', 0)
        if not isinstance(price, (int, float)):
            errors.append(f"Invalid price type: {type(price)}")
        elif price <= 0:
            errors.append(f"Invalid price data: {price} (must be > 0)")
    
    # Volume validation
    if 'volume' in data:
        volume = data.get('volume', 0)
        if not isinstance(volume, (int, float)):
            errors.append(f"Invalid volume type: {type(volume)}")
        elif volume < 0:
            errors.append(f"Invalid volume: {volume} (must be >= 0)")
    
    # Change validation
    if 'change' in data and 'pct_change' in data:
        change = data.get('change')
        pct_change = data.get('pct_change')
        price = data.get('price', 0)
        
        if change is not None and pct_change is not None and price > 0:
            # Verify change and pct_change are consistent
            # pct_change should be approximately (change / (price - change)) * 100
            expected_baseline = price - change
            if expected_baseline > 0:
                expected_pct = (change / expected_baseline) * 100
                tolerance = 0.1 # Allow 0.1% difference due to rounding
                
                if abs(expected_pct - pct_change) > tolerance:
                    errors.append(f"Inconsistent change data: change={change}, pct_change={pct_change}, expected={expected_pct:.2f}")
    
    # Date format validation
    if 'date' in data:
        date_str = str(data['date'])
        # Basic format check: should contain date part at minimum
        if len(date_str) < 10:
            errors.append(f"Invalid date format: {date_str} (too short)")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        logger.warning(f"Validation failed for {symbol} ({market}): {errors}")
    
    return (is_valid, errors)


def repair_market_data(data: Dict, prev_data: Optional[Dict] = None) -> Dict:
    """
    Attempt to repair/supplement missing or invalid market data.
    
    Args:
        data: Current market data dictionary
        prev_data: Optional previous data point for reference
    
    Returns:
        dict: Repaired data (may still have issues if repair fails)
    """
    repaired = data.copy()
    
    # Repair change/pct_change if missing but we have prev_close
    if 'change' not in repaired or repaired['change'] is None or repaired['change'] == 0:
        price = repaired.get('price', 0)
        prev_close = repaired.get('prev_close', 0)
        open_price = repaired.get('open', 0)
        
        if price > 0 and (prev_close > 0 or open_price > 0):
            # Use calculate_change_pct function
            from data_fetcher import calculate_change_pct
            change, pct_change = calculate_change_pct(price, prev_close, open_price)
            
            repaired['change'] = change
            repaired['pct_change'] = pct_change
            logger.info(f"Repaired change data: change={change}, pct_change={pct_change}%")
    
    # Repair prev_close from previous data
    if ('prev_close' not in repaired or repaired['prev_close'] is None) and prev_data:
        if 'close' in prev_data and prev_data['close']:
            repaired['prev_close'] = prev_data['close']
            logger.info(f"Repaired prev_close from historical data: {repaired['prev_close']}")
    
    # Set defaults for missing optional fields
    defaults = {
        'volume': 0,
        'turnover': 0.0,
        'pe': None,
        'dividend_yield': None
    }
    
    for key, default_val in defaults.items():
        if key not in repaired or repaired[key] is None:
            repaired[key] = default_val
    
    return repaired


def log_data_quality(symbol: str, market: str, is_valid: bool, errors: list):
    """
    Log data quality metrics for monitoring.
    
    Args:
        symbol: Stock symbol
        market: Market code
        is_valid: Whether data passed validation
        errors: List of validation errors
    """
    status = "PASS" if is_valid else "FAIL"
    logger.info(f"[DATA_QUALITY] {symbol} ({market}): {status}")
    
    if not is_valid and errors:
        for error in errors:
            logger.warning(f"[DATA_QUALITY] {symbol} ({market}): {error}")
