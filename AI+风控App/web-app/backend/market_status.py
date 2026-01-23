"""
市场状态检测工具
提供统一的市场开闭市判断逻辑，供data_fetcher和ETL服务使用
"""

import pytz
from datetime import datetime, time
import logging

logger = logging.getLogger("MarketStatus")

class MarketStatus:
    """市场状态检测器"""
    
    # 市场时区配置
    TIMEZONES = {
        'US': 'US/Eastern',
        'HK': 'Asia/Hong_Kong',
        'CN': 'Asia/Shanghai'
    }
    
    # 交易时间配置
    TRADING_HOURS = {
        'US': {
            'sessions': [
                {'open': time(9, 30), 'close': time(16, 0)}
            ]
        },
        'HK': {
            'sessions': [
                {'open': time(9, 30), 'close': time(16, 0)}  # 9:30-16:00（含午休）
            ]
        },
        'CN': {
            'sessions': [
                {'open': time(9, 30), 'close': time(15, 0)}  # 9:30-15:00（含午休）
            ]
        }
    }
    
    @classmethod
    def is_market_open(cls, market: str) -> bool:
        """
        检查指定市场是否开市
        
        Args:
            market: 市场代码 ('US', 'HK', 'CN')
            
        Returns:
            bool: True=开市, False=闭市
        """
        if market not in cls.TIMEZONES:
            logger.warning(f"Unknown market: {market}, assuming closed")
            return False
        
        # 获取市场当前时间
        tz = pytz.timezone(cls.TIMEZONES[market])
        now = datetime.now(tz)
        
        # 周末不开市
        if now.weekday() >= 5:
            return False
        
        # 检查是否在交易时间段内
        current_time = now.time()
        sessions = cls.TRADING_HOURS[market]['sessions']
        
        for session in sessions:
            if session['open'] <= current_time < session['close']:
                return True
        
        return False
    
    @classmethod
    def get_market_time(cls, market: str) -> datetime:
        """
        获取指定市场的当前时间
        
        Args:
            market: 市场代码
            
        Returns:
            datetime: 市场当前时间（带时区）
        """
        if market not in cls.TIMEZONES:
            return datetime.now()
        
        tz = pytz.timezone(cls.TIMEZONES[market])
        return datetime.now(tz)
    
    @classmethod
    def get_market_status_info(cls, market: str) -> dict:
        """
        获取市场状态的详细信息
        
        Args:
            market: 市场代码
            
        Returns:
            dict: {
                'market': 市场代码,
                'is_open': 是否开市,
                'current_time': 当前时间,
                'timezone': 时区,
                'is_weekend': 是否周末
            }
        """
        market_time = cls.get_market_time(market)
        is_open = cls.is_market_open(market)
        
        return {
            'market': market,
            'is_open': is_open,
            'current_time': market_time.strftime('%Y-%m-%d %H:%M:%S'),
            'timezone': cls.TIMEZONES.get(market, 'UTC'),
            'is_weekend': market_time.weekday() >= 5
        }

    @classmethod
    def get_market_close_time(cls, market: str) -> time:
        """
        获取指定市场的收盘时间（最后一节交易结束时间）
        
        Args:
            market: 市场代码
            
        Returns:
            time: 收盘时间
        """
        if market not in cls.TRADING_HOURS:
            # Default to 16:00 if unknown
            return time(16, 0)
            
        # Get the last session's close time
        sessions = cls.TRADING_HOURS[market]['sessions']
        return sessions[-1]['close']
# 便捷函数
def is_market_open(market: str) -> bool:
    """快捷函数：检查市场是否开市"""
    return MarketStatus.is_market_open(market)


def get_market_time(market: str) -> datetime:
    """快捷函数：获取市场当前时间"""
    return MarketStatus.get_market_time(market)



def get_market_close_time(market: str) -> time:
    """快捷函数：获取市场收盘时间"""
    return MarketStatus.get_market_close_time(market)

# 使用示例
if __name__ == "__main__":
    # 测试
    for market in ['US', 'HK', 'CN']:
        info = MarketStatus.get_market_status_info(market)
        print(f"{market} Market:")
        print(f"  Current Time: {info['current_time']} ({info['timezone']})")
        print(f"  Status: {'OPEN' if info['is_open'] else 'CLOSED'}")
        print(f"  Weekend: {info['is_weekend']}")
        print(f"  Close Time: {MarketStatus.get_market_close_time(market)}")
        print()
