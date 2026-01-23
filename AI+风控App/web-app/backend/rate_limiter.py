"""
请求限流器 (Rate Limiter)
防止过度请求数据源被拉黑
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
import threading

class RateLimiter:
    """
    请求限流器
    
    功能：
    1. Symbol级别限流：同一symbol两次请求最少间隔10秒
    2. Source级别限流：每个数据源每分钟最多5个请求
    3. 指数退避：失败后延迟重试
    """
    
    def __init__(self, symbol_interval=10, max_requests_per_minute=5):
        """
        初始化限流器
        
        Args:
            symbol_interval: 同symbol请求最小间隔（秒）
            max_requests_per_minute: 每分钟最大请求数
        """
        self.symbol_interval = symbol_interval
        self.max_requests_per_minute = max_requests_per_minute
        
        # Symbol级别：记录最后请求时间
        self.last_request_time = {}  # {symbol: timestamp}
        
        # Source级别：记录每分钟的请求次数
        self.source_requests = defaultdict(list)  # {source: [timestamp, ...]}
        
        # 线程锁
        self.lock = threading.Lock()
    
    def wait_if_needed(self, symbol: str, source: str = None) -> float:
        """
        检查并等待至满足限流条件
        
        Args:
            symbol: 股票/指数代码
            source: 数据源名称（如'akshare', 'yfinance'）
        
        Returns:
            实际等待的秒数
        """
        with self.lock:
            wait_time = 0
            now = time.time()
            
            # 1. Symbol级别限流
            if symbol in self.last_request_time:
                elapsed = now - self.last_request_time[symbol]
                if elapsed < self.symbol_interval:
                    wait_time = self.symbol_interval - elapsed
            
            # 2. Source级别限流（如果指定了source）
            if source:
                # 清理1分钟前的记录
                one_minute_ago = now - 60
                self.source_requests[source] = [
                    t for t in self.source_requests[source] 
                    if t > one_minute_ago
                ]
                
                # 检查是否超过限制
                if len(self.source_requests[source]) >= self.max_requests_per_minute:
                    # 计算需要等待到最早的请求过期
                    oldest = self.source_requests[source][0]
                    source_wait = 60 - (now - oldest) + 0.1  # 加0.1秒buffer
                    wait_time = max(wait_time, source_wait)
            
            # 执行等待
            if wait_time > 0:
                time.sleep(wait_time)
                now = time.time()  # 更新当前时间
            
            # 记录本次请求
            self.last_request_time[symbol] = now
            if source:
                self.source_requests[source].append(now)
            
            return wait_time
    
    def can_request(self, symbol: str, source: str = None) -> tuple:
        """
        检查是否可以请求（不等待）
        
        Args:
            symbol: 股票/指数代码
            source: 数据源名称
        
        Returns:
            (bool, float): (是否可以请求, 需要等待的秒数)
        """
        with self.lock:
            now = time.time()
            wait_time = 0
            
            # Symbol级别检查
            if symbol in self.last_request_time:
                elapsed = now - self.last_request_time[symbol]
                if elapsed < self.symbol_interval:
                    wait_time = self.symbol_interval - elapsed
            
            # Source级别检查
            if source:
                one_minute_ago = now - 60
                recent_requests = [
                    t for t in self.source_requests.get(source, [])
                    if t > one_minute_ago
                ]
                
                if len(recent_requests) >= self.max_requests_per_minute:
                    oldest = recent_requests[0]
                    source_wait = 60 - (now - oldest)
                    wait_time = max(wait_time, source_wait)
            
            return (wait_time == 0, wait_time)
    
    def backoff_delay(self, retry_count: int, base_delay: float = 1.0) -> float:
        """
        指数退避延迟
        
        Args:
            retry_count: 重试次数（0, 1, 2, ...）
            base_delay: 基础延迟（秒）
        
        Returns:
            实际延迟时间（秒），最多60秒
        """
        delay = min(base_delay * (2 ** retry_count), 60)
        time.sleep(delay)
        return delay
    
    def reset_symbol(self, symbol: str):
        """重置某个symbol的限流记录"""
        with self.lock:
            if symbol in self.last_request_time:
                del self.last_request_time[symbol]
    
    def reset_source(self, source: str):
        """重置某个source的限流记录"""
        with self.lock:
            if source in self.source_requests:
                del self.source_requests[source]
    
    def get_stats(self) -> dict:
        """获取限流统计信息"""
        with self.lock:
            now = time.time()
            one_minute_ago = now - 60
            
            stats = {
                'total_symbols_tracked': len(self.last_request_time),
                'sources': {}
            }
            
            for source, timestamps in self.source_requests.items():
                recent = [t for t in timestamps if t > one_minute_ago]
                stats['sources'][source] = {
                    'requests_last_minute': len(recent),
                    'limit': self.max_requests_per_minute,
                    'available': self.max_requests_per_minute - len(recent)
                }
            
            return stats


# 全局限流器实例
_global_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(
            symbol_interval=10,  # 10秒间隔
            max_requests_per_minute=5  # 每分钟5请求
        )
    return _global_rate_limiter
