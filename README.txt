# 股票分析工具 v3.0

## 项目简介
这是一个多市场股票分析工具，支持美股、港股和沪深市场的股票数据获取、技术指标计算和资金流分析。程序会自动获取K线数据，计算技术指标，分析资金流向，并将结果保存为Excel文件。

## 功能特点
- 支持多市场：美股、港股、沪深市场
- 完整的技术分析：MA、MACD、KDJ、RSI等指标
- 资金流分析：支持各市场的资金流向数据
- 详细的日志记录：每次运行生成独立的日志文件
- 模块化设计：各个功能模块独立，便于维护和扩展

## 目录结构
```
analyzer_v3/
├── config/
│   └── symbols.txt             # 股票列表配置文件
├── modules/
│   ├── data_fetcher.py        # 股票K线数据拉取模块
│   ├── fund_flow_fetcher.py   # 资金流向拉取模块
│   ├── technical_indicators.py # 技术指标计算模块
│   └── utils.py               # 通用辅助函数模块
├── output/                    # 分析结果输出目录
├── logs/                      # 日志目录
├── run_logger.py              # 主程序
└── README.txt                 # 使用说明文档
```

## 环境要求
- Python 3.8+
- 依赖包：
  - akshare
  - pandas
  - yfinance
  - openpyxl

## 安装步骤
1. 克隆或下载项目到本地
2. 安装依赖包：
   ```bash
   pip install akshare pandas yfinance openpyxl
   ```
3. 创建必要的目录：
   ```bash
   mkdir -p config modules output logs
   ```

## 配置说明
1. 在 `config/symbols.txt` 中配置股票代码，每行一个：
   ```
   AAPL.US    # 美股
   600000.SH  # 上证
   0700.HK    # 港股
   ```

## 使用方法
1. 确保已正确配置 `symbols.txt`
2. 运行主程序：
   ```bash
   python run_logger.py
   ```
3. 程序会自动：
   - 读取股票列表
   - 获取K线数据
   - 计算技术指标
   - 获取资金流数据
   - 保存分析结果到 `output` 目录
   - 记录详细日志到 `logs` 目录

## 输出文件
1. Excel文件：`output/{symbol}_{timestamp}.xlsx`
   - 包含多个sheet：日线、分钟线、技术指标、资金流等
2. 日志文件：`logs/run_YYYYMMDD_HHMMSS.log`
   - 记录程序运行过程中的详细信息
   - 包含警告和错误信息

## 注意事项
1. 确保网络连接稳定
2. 建议先测试少量股票，确认功能正常后再批量处理
3. 美股数据可能有延迟
4. 部分股票可能无法获取资金流数据
5. 如遇到异常，请查看日志文件了解详细信息

## 常见问题
1. Q: 为什么某些股票数据获取失败？
   A: 可能是网络问题或股票代码格式不正确，请查看日志文件了解具体原因。

2. Q: 如何添加新的技术指标？
   A: 在 `modules/technical_indicators.py` 中添加新的计算函数，并在 `add_technical_indicators` 中调用。

3. Q: 资金流数据为什么有些是空的？
   A: 不同市场的数据源不同，部分市场可能无法获取完整的资金流数据。

## 更新日志
### v3.0 (2024-03-xx)
- 支持美股资金流数据获取
- 优化日志记录系统
- 改进错误处理机制
- 简化主程序流程

## 联系方式
如有问题或建议，请提交 Issue 或 Pull Request。

## 许可证
MIT License 