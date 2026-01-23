"""
数据验证器 (Data Validator)
验证获取数据的完整性和合理性
"""

from datetime import datetime
from typing import Dict, List, Tuple

class DataValidator:
    """
    数据质量验证器
    
    功能：
    1. 数据完整性检查（必填字段）
    2. 数值范围检查（price>0, volume>=0）
    3. 时间戳合理性检查（不能是未来）
    """
    
    def __init__(self):
        pass
    
    def validate_price_data(self, symbol: str, data: dict, prev_data: dict = None) -> Tuple[bool, List[str]]:
        """
        验证价格数据
        
        Args:
            symbol: 股票/指数代码
            data: 新数据
            prev_data: 前一日数据（可选，用于价格突变检测）
        
        Returns:
            (is_valid, errors): (是否有效, 错误列表)
        """
        errors = []
        
        # 1. 数据完整性检查
        required_fields = ['close', 'price', 'date']
        optional_but_recommended = ['volume', 'open', 'high', 'low']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # 2. 数值范围检查
        price = data.get('close') or data.get('price', 0)
        if price is not None:
            try:
                price_float = float(price)
                if price_float <= 0:
                    errors.append(f"Invalid price: {price_float} (must be > 0)")
            except (ValueError, TypeError):
                errors.append(f"Price is not a number: {price}")
        
        volume = data.get('volume', 0)
        if volume is not None:
            try:
                volume_int = int(volume)
                if volume_int < 0:
                    errors.append(f"Invalid volume: {volume_int} (must be >= 0)")
            except (ValueError, TypeError):
                # Volume可能是None或字符串，这是可接受的（某些指数没有成交量）
                pass
        
        # 3. 时间戳合理性检查
        date_str = data.get('date')
        if date_str:
            try:
                # 尝试解析日期
               if isinstance(date_str, str):
                    # 提取日期部分 (YYYY-MM-DD)
                    date_part = date_str.split(' ')[0]
                    data_date = datetime.strptime(date_part, '%Y-%m-%d')
                    
                    # 检查是否是未来日期
                    now = datetime.now()
                    if data_date > now:
                        errors.append(f"Future date not allowed: {date_str}")
                    
                    # 检查是否过于久远（超过100年）
                    if (now - data_date).days > 36500:
                        errors.append(f"Date too old: {date_str}")
                        
            except (ValueError, TypeError, IndexError) as e:
                errors.append(f"Invalid date format: {date_str} ({e})")
        
        # 4. 可选：价格突变检测（用户要求不实施，所以注释掉）
        # if prev_data:
        #     prev_price = prev_data.get('close') or prev_data.get('price', 0)
        #     if prev_price and price:
        #         change_pct = abs(price - prev_price) / prev_price
        #         if change_pct > 0.2:  # 20%突变
        #             errors.append(f"Suspicious price change: {change_pct:.1%}")
        
        return (len(errors) == 0, errors)
    
    def validate_and_log(self, symbol: str, data: dict, logger=None) -> bool:
        """
        验证数据并记录错误
        
        Args:
            symbol: 股票/指数代码
            data: 数据字典
            logger: 日志记录器（可选）
        
        Returns:
            bool: 数据是否有效
        """
        is_valid, errors = self.validate_price_data(symbol, data)
        
        if not is_valid and logger:
            logger.warning(f"Data validation failed for {symbol}:")
            for error in errors:
                logger.warning(f"  - {error}")
        
        return is_valid
    
    def sanitize_data(self, data: dict) -> dict:
        """
        清理和修正数据
        
        Args:
            data: 原始数据
        
        Returns:
            清理后的数据
        """
        if not data:
            return data
        
        sanitized = data.copy()
        
        # 1. 确保price字段存在
        if 'price' not in sanitized and 'close' in sanitized:
            sanitized['price'] = sanitized['close']
        
        # 2. 确保volume为整数
        if 'volume' in sanitized and sanitized['volume'] is not None:
            try:
                sanitized['volume'] = int(float(sanitized['volume']))
            except (ValueError, TypeError):
                sanitized['volume'] = 0
        
        # 3. 清理None值
        for key in ['change', 'pct_change']:
            if key in sanitized and sanitized[key] is None:
                sanitized[key] = 0
        
        return sanitized


# 全局验证器实例
_global_validator = None

def get_validator() -> DataValidator:
    """获取全局验证器实例"""
    global _global_validator
    if _global_validator is None:
        _global_validator = DataValidator()
    return _global_validator
