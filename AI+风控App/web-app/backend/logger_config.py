"""
统一日志配置模块
所有模块通过此配置获取logger实例，确保日志集中管理
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 统一日志文件
LOG_FILE = os.path.join(LOG_DIR, 'system.log')

# 日志格式
LOG_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 全局logger配置
_loggers = {}

def get_logger(name: str, level=logging.INFO):
    """
    获取统一配置的logger实例
    
    Args:
        name: logger名称（通常是模块名）
        level: 日志级别
        
    Returns:
        配置好的logger实例
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # 文件Handler - 轮转日志（每个文件最大10MB，保留10个备份）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # 控制台Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _loggers[name] = logger
    return logger


def read_logs(limit=100, level=None, module=None, search=None):
    """
    读取系统日志
    
    Args:
        limit: 返回最近N条日志
        level: 过滤日志级别 (INFO/WARNING/ERROR/DEBUG)
        module: 过滤模块名
        search: 搜索关键词
        
    Returns:
        日志列表，每条日志是一个字典
    """
    logs = []
    
    try:
        if not os.path.exists(LOG_FILE):
            return []
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 从后往前读（最新的在后面）
        for line in reversed(lines[-limit*3:]):  # 读取3倍数量，过滤后取limit
            line = line.strip()
            if not line:
                continue
            
            try:
                # 解析日志行
                # 格式: 2025-12-17 19:10:00 [INFO] [DataFetcher] 消息
                parts = line.split(' ', 4)
                if len(parts) < 5:
                    continue
                
                date = parts[0]
                time = parts[1]
                log_level = parts[2].strip('[]')
                log_module = parts[3].strip('[]')
                message = parts[4] if len(parts) > 4 else ''
                
                # 过滤
                if level and log_level != level:
                    continue
                if module and module not in log_module:
                    continue
                if search and search.lower() not in message.lower():
                    continue
                
                logs.append({
                    'timestamp': f"{date} {time}",
                    'level': log_level,
                    'module': log_module,
                    'message': message
                })
                
                if len(logs) >= limit:
                    break
                    
            except Exception as parse_err:
                # 解析失败，跳过该行
                continue
        
        return logs
        
    except Exception as e:
        return [{'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 'level': 'ERROR',
                 'module': 'LogReader',
                 'message': f'读取日志失败: {str(e)}'}]
