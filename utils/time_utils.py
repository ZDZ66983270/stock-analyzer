from datetime import datetime, timedelta
from typing import Union, Tuple
import akshare as ak
import pandas as pd

def parse_period(period: str) -> Tuple[int, str]:
    """
    解析时间周期字符串
    
    参数:
        period: 周期字符串，如 "1d", "4h", "30m"
        
    返回:
        Tuple[int, str]: (数值, 单位)
    """
    units = {
        'd': 'day',
        'h': 'hour',
        'm': 'minute'
    }
    
    value = int(period[:-1])
    unit = period[-1]
    
    if unit not in units:
        raise ValueError(f"不支持的时间单位: {unit}")
        
    return value, units[unit]

def get_period_timedelta(period: str) -> timedelta:
    """
    获取周期对应的时间间隔
    
    参数:
        period: 周期字符串，如 "1d", "4h", "30m"
        
    返回:
        timedelta: 时间间隔
    """
    value, unit = parse_period(period)
    
    if unit == 'day':
        return timedelta(days=value)
    elif unit == 'hour':
        return timedelta(hours=value)
    elif unit == 'minute':
        return timedelta(minutes=value)
    else:
        raise ValueError(f"不支持的时间单位: {unit}")

def format_datetime(dt: Union[datetime, str], output_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    参数:
        dt: 日期时间对象或字符串
        output_format: 输出格式
        
    返回:
        str: 格式化后的时间字符串
    """
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("不支持的日期时间格式")
    
    return dt.strftime(output_format)

def get_trading_dates(start_date: str, end_date: str) -> list:
    """
    获取指定日期范围内的所有交易日
    
    Args:
        start_date: 开始日期，格式为'YYYY-MM-DD'
        end_date: 结束日期，格式为'YYYY-MM-DD'
    
    Returns:
        list: 交易日列表，格式为['YYYY-MM-DD', ...]
    """
    try:
        # 确保结束日期不超过当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        if end_date > current_date:
            end_date = current_date
            print(f"警告：结束日期超过当前日期，已自动调整为当前日期: {current_date}")
        
        # 获取交易日历
        trade_cal = ak.tool_trade_date_hist_sina()
        
        # 转换日期格式
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # 转换交易日历日期
        trade_cal['trade_date'] = pd.to_datetime(trade_cal['trade_date'])
        
        # 过滤日期范围内的交易日
        mask = (trade_cal['trade_date'] >= start_dt) & (trade_cal['trade_date'] <= end_dt)
        trading_dates = trade_cal[mask]['trade_date'].dt.strftime('%Y-%m-%d').tolist()
        
        return sorted(trading_dates)  # 确保日期是按照升序排列的
    except Exception as e:
        print(f"获取交易日历时发生错误: {str(e)}")
        # 如果获取失败，返回一个基于日历的估计（不包括周末）
        dates = []
        current = pd.to_datetime(start_date)
        end = pd.to_datetime(min(end_date, current_date))  # 确保不超过当前日期
        while current <= end:
            if current.weekday() < 5:  # 0-4 表示周一到周五
                dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        return dates 