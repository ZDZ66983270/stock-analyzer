# 标准化字段名
COLUMN_NAMES = {
    # 基础K线字段
    'datetime': 'datetime',  # 日期时间
    'open': 'open',         # 开盘价
    'high': 'high',         # 最高价
    'low': 'low',           # 最低价
    'close': 'close',       # 收盘价
    'volume': 'volume',     # 成交量
    
    # MA指标
    'ma5': 'ma5',
    'ma10': 'ma10',
    'ma20': 'ma20',
    'ma60': 'ma60',
    
    # MACD指标
    'macd_dif': 'macd_dif',
    'macd_dea': 'macd_dea',
    'macd_hist': 'macd_hist',
    
    # KDJ指标
    'kdj_k': 'kdj_k',
    'kdj_d': 'kdj_d',
    'kdj_j': 'kdj_j',
    
    # RSI指标
    'rsi6': 'rsi6',
    'rsi12': 'rsi12',
    'rsi24': 'rsi24',
    
    # 布林带
    'boll_mid': 'boll_mid',
    'boll_upper': 'boll_upper',
    'boll_lower': 'boll_lower',
    
    # 成交量均线
    'volume_ma5': 'volume_ma5',
    'volume_ma10': 'volume_ma10',
    'volume_ma20': 'volume_ma20',
    
    # 资金流向字段
    'main_net_inflow': 'main_net_inflow',
    'main_net_inflow_pct': 'main_net_inflow_pct',
    'super_large_net_inflow': 'super_large_net_inflow',
    'super_large_net_inflow_pct': 'super_large_net_inflow_pct',
    'large_net_inflow': 'large_net_inflow',
    'large_net_inflow_pct': 'large_net_inflow_pct',
    'medium_net_inflow': 'medium_net_inflow',
    'medium_net_inflow_pct': 'medium_net_inflow_pct',
    'small_net_inflow': 'small_net_inflow',
    'small_net_inflow_pct': 'small_net_inflow_pct'
}

# 中文到英文的字段映射
CN_TO_EN_MAPPING = {
    '日期': 'datetime',
    '时间': 'datetime',
    '开盘': 'open',
    '收盘': 'close',
    '最高': 'high',
    '最低': 'low',
    '成交量': 'volume',
    '成交额': 'amount'
}

# 英文到中文的字段映射
EN_TO_CN_MAPPING = {v: k for k, v in CN_TO_EN_MAPPING.items()}

# 必需的基础列
REQUIRED_BASE_COLUMNS = ['datetime', 'open', 'high', 'low', 'close', 'volume']

# 必需的技术指标列
REQUIRED_INDICATOR_COLUMNS = [
    'ma5', 'ma10', 'ma20', 'ma60',
    'macd_dif', 'macd_dea', 'macd_hist',
    'kdj_k', 'kdj_d', 'kdj_j',
    'rsi6', 'rsi12', 'rsi24',
    'boll_mid', 'boll_upper', 'boll_lower',
    'volume_ma5', 'volume_ma10', 'volume_ma20'
]

# 必需的资金流向列
REQUIRED_FUND_FLOW_COLUMNS = [
    'main_net_inflow', 'main_net_inflow_pct',
    'super_large_net_inflow', 'super_large_net_inflow_pct',
    'large_net_inflow', 'large_net_inflow_pct',
    'medium_net_inflow', 'medium_net_inflow_pct',
    'small_net_inflow', 'small_net_inflow_pct'
]

import os
from datetime import datetime, timedelta

# 1. 基础路径配置 - 必需，确保数据存储位置统一
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 自动创建必要目录
for dir_path in [DATA_DIR, LOG_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# 2. 数据获取配置 - 必需，确保数据获取的稳定性
FETCH_CONFIG = {
    'retry_times': 3,           # 重试次数
    'retry_interval': 5,        # 重试间隔(秒)
    'timeout': 30,             # 请求超时时间(秒)
    'batch_size': 100          # 批量获取数据大小
}

# 3. 时间配置 - 必需，统一时间处理
TIME_CONFIG = {
    'date_format': '%Y-%m-%d',
    'datetime_format': '%Y-%m-%d %H:%M:%S',
    'default_start_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),  # 默认获取90天数据
    'default_end_date': datetime.now().strftime('%Y-%m-%d')
}

# 4. 数据周期配置 - 必需，定义支持的时间周期
PERIODS = {
    'daily': {'name': '日线', 'seconds': 86400},
    '1h': {'name': '1小时', 'seconds': 3600},
    '30m': {'name': '30分钟', 'seconds': 1800},
    '15m': {'name': '15分钟', 'seconds': 900},
    '5m': {'name': '5分钟', 'seconds': 300}
}

# 5. 字段映射配置 - 必需，统一不同数据源的字段名
FIELD_MAPPINGS = {
    'eastmoney': {
        'datetime': '日期',
        'open': '开盘',
        'high': '最高',
        'low': '最低',
        'close': '收盘',
        'volume': '成交量'
    },
    'akshare': {
        'datetime': 'datetime',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume'
    }
}

# 6. 技术指标参数配置 - 必需，便于统一调整指标参数
INDICATOR_PARAMS = {
    'ma': [5, 10, 20, 60],
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'kdj': {'n': 9, 'm1': 3, 'm2': 3},
    'rsi': [6, 12, 24]
}

# 7. 日志配置 - 必需，方便调试和监控
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': os.path.join(LOG_DIR, f'stock_system_{datetime.now().strftime("%Y%m%d")}.log')
}

# 需要添加数据源配置
DATA_SOURCE = {
    'us': 'akshare',  # 美股数据源
    'hk': 'eastmoney', # 港股数据源
    'cn': 'eastmoney'  # A股数据源
} 