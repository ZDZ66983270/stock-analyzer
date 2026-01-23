from datetime import datetime, time, timedelta
import pytz
from enum import Enum

class MarketStatus(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    POST_MARKET = "POST_MARKET"
    UNKNOWN = "UNKNOWN"

class MarketSchedule:
    @staticmethod
    def get_status(market: str) -> MarketStatus:
        """
        Determine if the market is currently OPEN or CLOSED.
        """
        now_utc = datetime.now(pytz.utc)
        
        if market == "CN":
            tz = pytz.timezone('Asia/Shanghai')
            now = now_utc.astimezone(tz)
            if now.weekday() >= 5: return MarketStatus.CLOSED
            
            t = now.time()
            # 9:30-15:00 (不考虑午休，全程开市)
            if time(9,30) <= t <= time(15,0):
                return MarketStatus.OPEN
            return MarketStatus.CLOSED
            
        elif market == "HK":
            tz = pytz.timezone('Asia/Hong_Kong')
            now = now_utc.astimezone(tz)
            if now.weekday() >= 5: return MarketStatus.CLOSED
            
            t = now.time()
            # 9:30-16:00 (不考虑午休，全程开市)
            if time(9,30) <= t <= time(16,0):
                return MarketStatus.OPEN
            return MarketStatus.CLOSED
            
        elif market == "US":
            tz = pytz.timezone('America/New_York')
            now = now_utc.astimezone(tz)
            if now.weekday() >= 5: return MarketStatus.CLOSED
            
            t = now.time()
            # 9:30-16:00 EST
            if time(9,30) <= t <= time(16,0):
                return MarketStatus.OPEN
            return MarketStatus.CLOSED
        
        return MarketStatus.UNKNOWN
    
    @staticmethod
    def is_trading_day(market: str) -> bool:
        """
        Check if today is a trading day (including lunch break).
        Returns True if we should fetch/display minute data.
        
        Logic:
        - During trading hours: True
        - During lunch break on trading day: True (show morning data)
        - After market close on trading day: True (show today's data)
        - Weekend/Holiday: False
        """
        now_utc = datetime.now(pytz.utc)
        
        if market == "CN":
            tz = pytz.timezone('Asia/Shanghai')
            now = now_utc.astimezone(tz)
            if now.weekday() >= 5: return False  # Weekend
            
            t = now.time()
            # Trading day: 9:00 - 15:30 (includes pre-market, trading, and slight buffer)
            if time(9,0) <= t <= time(15,30):
                return True
            return False
            
        elif market == "HK":
            tz = pytz.timezone('Asia/Hong_Kong')
            now = now_utc.astimezone(tz)
            if now.weekday() >= 5: return False  # Weekend
            
            t = now.time()
            # Trading day: 9:00 - 16:30
            if time(9,0) <= t <= time(16,30):
                return True
            return False
            
        elif market == "US":
            tz = pytz.timezone('America/New_York')
            now = now_utc.astimezone(tz)
            if now.weekday() >= 5: return False  # Weekend
            
            t = now.time()
            # Trading day: 9:00 - 17:00 EST
            if time(9,0) <= t <= time(17,0):
                return True
            return False
        
        return False
    
    @staticmethod
    def is_market_open(market: str) -> tuple[bool, str]:
        """
        Helper to return (is_open, reason/status_str) for legacy compatibility.
        """
        status = MarketSchedule.get_status(market)
        return (status == MarketStatus.OPEN, status.value)

    @staticmethod
    def is_stale(last_update_time: datetime, market: str, ttl_seconds: int = 60) -> bool:
        """
                     If we are in weekend, data from Friday is valid.
                     So: If CLOSED, always Fresh? 
                     User Rule: "In closed state... Last close is valid".
                     So return False (Not Stale).
        """
        status = MarketSchedule.get_status(market)
        
        if status == MarketStatus.CLOSED:
             # Ideally we check if it is indeed the 'latest' session.
             # But simplistic Rule 1 says: "Closed -> Invalidated only by next open".
             # So always Fresh if we have data.
             return False
             
        # Market OPEN
        if not last_update_time:
            return True
            
        # Ensure timezone awareness
        now = datetime.now(last_update_time.tzinfo or pytz.utc)
        if last_update_time.tzinfo is None:
             # Assume system local time if naive, which matches datetime.now() usually
             now = datetime.now()
             
        diff = (now - last_update_time).total_seconds()
        return diff > ttl_seconds
