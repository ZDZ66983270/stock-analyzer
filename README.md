# 股票数据采集系统

基于免费公开数据源的股票数据采集系统，用于替代付费API。系统支持获取美股的K线数据、技术指标和资金流数据。

## 功能特点

- 支持多只股票批量获取（最多9只）
- 支持多个周期的K线数据（日线、4h、2h、1h、30m、15m、5m、3m）
- 自动计算常用技术指标：
  - MA（5、10、20日）
  - MACD（DIF、DEA、HIST）
  - KDJ（K、D、J）
  - RSI（6、12、24日）
- 获取雪球网资金流数据
- 数据自动合并并保存为CSV格式

## 安装说明

1. 克隆项目到本地：
```bash
git clone <repository_url>
cd stock-data-collector
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用说明

1. 直接运行数据采集：
```bash
python run_pipeline.py US.AAPL US.MSFT US.GOOGL
```

2. 通过菜单运行：
```bash
python menu.py
```

### 股票代码格式

- 美股代码格式：US.XXXX（例如：US.AAPL, US.MSFT）
- 一次最多支持9只股票
- 股票代码之间用空格分隔

### 输出数据

- 所有数据保存在 `output/` 目录下
- 文件名格式：`{股票代码}.csv`
- CSV文件包含以下字段：
  - 时间：time
  - K线：open, high, low, close, volume
  - 均线：MA5, MA10, MA20
  - MACD：MACD_DIF, MACD_DEA, MACD_HIST
  - KDJ：KDJ_K, KDJ_D, KDJ_J
  - RSI：RSI6, RSI12, RSI24
  - 资金流：capital_inflow, capital_outflow, capital_netflow

## 注意事项

1. yfinance的数据获取限制：
   - 5分钟数据只能获取最近7天
   - 15分钟和30分钟数据只能获取最近60天
   - 小时级数据只能获取最近730天
   - 日线数据无时间限制

2. 雪球网的访问限制：
   - 添加了请求延迟和重试机制
   - 使用随机User-Agent防止被封
   - 每次请求之间有1秒延迟

3. 数据质量说明：
   - K线数据来源于Yahoo Finance
   - 资金流数据来源于雪球网
   - 技术指标由系统本地计算
   - 所有数据仅供参考，不构成投资建议

## 开发说明

### 项目结构
```
.
├── config.py                    # 配置文件
├── fetch_kline_yfinance.py     # K线数据获取
├── fetch_capital_flow_xueqiu.py # 资金流数据获取
├── merge_data.py               # 数据合并
├── run_pipeline.py             # 主程序
├── menu.py                     # 菜单程序
├── requirements.txt            # 依赖列表
├── utils/
│   ├── indicator_calculator.py # 技术指标计算
│   └── time_utils.py          # 时间处理工具
└── output/                     # 输出目录
    └── *.csv                  # 输出文件
```

### 开发计划

- [ ] 添加更多技术指标
- [ ] 支持港股数据获取
- [ ] 添加数据可视化功能
- [ ] 优化数据缓存机制
- [ ] 添加数据质量检查

## 许可证

MIT License 