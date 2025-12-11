# 股票数据分析系统

一个用于获取和分析股票数据的Python系统，支持多周期数据获取、技术指标计算和本地数据存储。

## 目录结构

```
├── main.py          # 主程序入口
├── config.py        # 配置文件
├── fetcher.py       # 数据获取模块
├── indicators.py    # 技术指标计算
├── output/          # 数据输出目录
│   └── proceeded/   # 带技术指标的数据
└── logs/           # 日志文件目录
```

## 主要功能

### 1. 数据获取 (fetcher.py)
- 支持多市场数据获取
  - 美股数据
  - 港股数据
  - A股数据
- 支持多周期数据
  - 日线数据
  - 周线数据
  - 月线数据
- 资金流数据（A股特有）

### 2. 技术指标计算 (indicators.py)
- MA (移动平均线)
- MACD (指数平滑异同平均线)
- KDJ (随机指标)
- RSI (相对强弱指标)

### 3. 数据处理流程 (main.py)
- 数据获取和处理
  - 读取股票列表
  - 获取原始数据
  - 计算技术指标
- 数据存储
  - 原始数据：保存到 output/
  - 指标数据：保存到 output/proceeded/
- 日志记录
  - 运行日志：保存到 logs/
  - 错误追踪
  - 执行统计

## 数据存储说明

### 1. 文件格式
- 使用 Excel (.xlsx) 格式
- 文件命名：股票代码_时间戳.xlsx
- 指标文件命名：股票代码_时间戳_indicators.xlsx

### 2. 目录说明
- output/：原始行情数据
- output/proceeded/：带技术指标的数据
- logs/：程序运行日志

## 使用方法

1. 配置股票列表
   - 编辑 config/symbols.txt
   - 支持多市场代码（例如：AAPL, 00700.HK, 600519.SH）

2. 运行程序
   ```bash
   python main.py
   ```

3. 查看结果
   - 原始数据：output/ 目录
   - 指标数据：output/proceeded/ 目录
   - 运行日志：logs/ 目录

## 环境要求

- Python 3.8+
- pandas
- openpyxl
- akshare（A股/港股数据）
- yfinance（美股数据）

## 注意事项

- 确保网络连接正常
- 股票代码格式必须正确
- 美股数据会自动处理时区
- 建议定期备份数据文件
