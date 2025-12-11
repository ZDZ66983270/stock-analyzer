# 股票数据分析系统

一个用于获取和分析股票数据的Python系统，支持多周期数据获取、技术指标计算和本地数据存储。

## 主要功能

### 1. 数据获取模块 (fetcher.py)

#### USDataFetcher类 (美股数据获取)
- `__init__()`: 初始化数据获取器
- `fetch_minute_data()`: 获取分钟级数据
- `fetch_daily_data()`: 获取日线数据
- `save_data()`: 保存数据到Excel文件

特点：
- 支持的周期：1d, 1h, 30m, 15m, 5m
- 使用 yfinance 作为数据源
- 自动处理时区转换（美东时间）

#### HKDataFetcher类 (港股数据获取)
- `__init__()`: 初始化数据获取器
- `fetch_minute_data()`: 获取分钟级数据
- `fetch_daily_data()`: 获取日线数据
- `save_data()`: 保存数据到Excel文件

特点：
- 支持的周期：1d, 1h, 30m, 15m, 5m
- 使用 akshare 作为数据源
- 自动处理时区转换（香港时间）

#### CNDataFetcher类 (A股数据获取)
- `__init__()`: 初始化数据获取器
- `fetch_minute_data()`: 获取分钟级数据
- `fetch_daily_data()`: 获取日线数据
- `save_data()`: 保存数据到Excel文件

特点：
- 支持的周期：1d, 1h, 30m, 15m, 5m
- 使用 akshare 作为数据源
- 包含实时行情和历史数据

### 2. 技术指标计算模块 (indicators.py)

#### TechnicalIndicator类
- `__init__()`: 初始化技术指标计算器
- `validate_data()`: 验证输入数据的有效性
- `calculate_ma()`: 计算移动平均线
- `calculate_macd()`: 计算MACD指标
- `calculate_kdj()`: 计算KDJ指标
- `calculate_rsi()`: 计算RSI指标
- `calculate_all()`: 计算所有技术指标

## 数据字段说明

### 1. 基础数据字段
- `datetime/date`: 日期时间
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量

### 2. 技术指标字段

#### MA系列
- `ma5`, `ma10`, `ma20`, `ma60`: 不同周期的移动平均线

#### MACD系列
- `macd_dif`: MACD差离值
- `macd_dea`: MACD信号线
- `macd_hist`: MACD柱状图

#### KDJ系列
- `kdj_k`: K值
- `kdj_d`: D值
- `kdj_j`: J值

#### RSI系列
- `rsi6`: 6日RSI
- `rsi12`: 12日RSI
- `rsi24`: 24日RSI

## 功能特点

### 1. 数据获取
✅ 支持多市场多周期数据获取
- 市场：美股、港股、A股
- 周期：1d, 1h, 30m, 15m, 5m
- 多数据源支持
- 自动时区转换

### 2. 技术指标计算
✅ 支持多个技术指标
- MA（移动平均线）：5、10、20、60日
- MACD（指数平滑移动平均）：12、26、9
- KDJ（随机指标）：9、3、3
- RSI（相对强弱指标）：6、12、24日

### 3. 数据存储
✅ 本地文件存储
- Excel格式保存（.xlsx）
- 自动创建输出目录
- 规范的文件命名
- 分表存储不同周期数据

### 4. 日志系统
✅ 完整的日志记录
- 双输出（文件和控制台）
- 时间戳记录
- 错误信息记录
- 处理进度跟踪

## 目录结构

```
analyzer_v4/
├── config/
│   └── symbols.txt              # 股票列表配置
├── logs/
│   └── error.log               # 错误日志
├── modules/
│   ├── data_fetcher.py        # K线数据获取
│   ├── data_fetcher_cn_hk.py  # A股和港股数据获取
│   ├── min_data_fetcher.py    # 分钟数据获取
│   ├── fund_flow_fetcher.py   # 资金流数据
│   ├── technical_indicators.py # 技术指标计算
│   └── utils.py               # 工具函数
├── output/                    # 输出目录
├── tests/                     # 测试目录
├── run_logger.py              # 主程序
└── README.md                  # 项目说明
```

## 环境要求

- Python 3.8+
- akshare
- pandas
- openpyxl

## 使用方法

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置股票列表：
编辑 `config/symbols.txt`，添加需要分析的股票代码

3. 运行程序：
```bash
python run_logger.py
```

## 注意事项

- 确保网络连接正常
- 美股数据会自动处理时区
- 输出文件保存在 output 目录
- 错误日志记录在 logs 目录 