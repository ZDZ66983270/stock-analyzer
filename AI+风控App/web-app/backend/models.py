"""
VERA Data Models & Schema (数据库架构核心)
==============================================================================

本模块定义了系统的所有持久化实体，基于 SQLModel (SQLAlchemy + Pydantic) 构建。
它是整个系统“数据语言”的基石，规定了从原始采集到清洗加工、最后到应用展现的每一层格式。

架构层次:
========================================

I. Core Market Data (核心行情层)
----------------------------------------
1. **MarketDataDaily**: **日线历史库**。
   - 存储归一化后的历史日线数据（OHLCV + 估值指标）。
   - 具备唯一约束 `(symbol, market, timestamp)`。
   - 用途: 回测、长周期图表展示、估值历史回溯。
2. **MarketSnapshot**: **生产实时快照**。
   - 每个资产仅保留最新一条记录。
   - 用途: 满足前端高频访问需求（如首页自选股列表）。
   - 特性: 盘中实时更新时仅触达此表。

II. Financial & Valuation (财务与估值层)
----------------------------------------
3. **FinancialFundamentals**: **财报基础数据库**。
   - 处理过后的 PIT (Point-in-Time) 财报指标（TTM 利润、总资产、股本等）。
   - 为 `valuation_calculator.py` 提供原始输入。
4. **ForexRate**: **汇率历史库**。
   - 存储核心货币对的历史汇率（如 USD/CNY），支持估值计算时的跨币种折算。

III. User & Analysis (用户与分析层)
----------------------------------------
5. **Watchlist**: **自选股配置表**。
   - 记录用户关注的资产列表，驱动后台的定时抓取任务。
6. **AssetAnalysisHistory**: **风险评估历史**。
   - 存储 AI 驱动的深度风险评估 JSON 结果和截图路径。

IV. Infrastructure (基础设施层)
----------------------------------------
7. **RawMarketData**: **原始数据缓冲区**。
   - 存储 API 返回的原始 JSON。
   - 它是 ETL 流水线的起点，支持数据追溯与重新加工。
8. **MacroData**: **宏观经济指标**。
   - 存储美债收益率、CPI 等宏观参数。

作者: Antigravity
日期: 2026-01-23
"""

from typing import Optional
from sqlmodel import Field, SQLModel, UniqueConstraint
from datetime import datetime

class MacroData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    country: str = Field(index=True)  # CN or US
    month: str = Field(index=True)    # YYYY-MM
    indicator: str                    # e.g., "10y_bond"
    value: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ForexRate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)       # YYYY-MM-DD
    from_currency: str = Field(index=True) 
    to_currency: str = Field(index=True)
    rate: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AssetAnalysisHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    full_result_json: str  # Stores the entire JSON result from AI
    screenshot_path: Optional[str] = None



# ============================================================
# 📚 历史数据仓库 (Historical Data Warehouse)
# ============================================================
# 用途：
#   1. 存储所有历史日线数据（可追溯数年）
#   2. 实时数据也会UPSERT到这里（更新当天记录）
#   3. ETL计算涨跌幅时查询此表的前一日收盘价
# 
# 注意：前端不直接查询此表，应查询 MarketSnapshot
# ============================================================
class MarketDataDaily(SQLModel, table=True):
    # ✅ 添加唯一约束，防止重复记录
    __table_args__ = (
        UniqueConstraint('symbol', 'market', 'timestamp', name='uq_symbol_market_timestamp'),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    market: str = Field(index=True)  # CN, HK, US
    timestamp: str = Field(index=True)    # YYYY-MM-DD HH:MM:SS
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: Optional[float] = None # 成交额
    
    # Computed/Snapshot fields (Daily usually has these calculated)
    change: Optional[float] = None
    pct_change: Optional[float] = None
    prev_close: Optional[float] = None
    
    # Valuation & Indicators 
    pe: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    ps: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    market_cap: Optional[float] = None

    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)



class StockInfo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)
    name: str
    market: str = Field(index=True) # CN, HK, US
    list_date: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)
    name: Optional[str] = None
    market: Optional[str] = None # CN, HK, US, inferred
    added_at: datetime = Field(default_factory=datetime.utcnow)

class RawMarketData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str  # e.g. "yahoo", "akshare"
    symbol: str
    market: str
    period: str  # '1d', '1m'
    fetch_time: datetime = Field(default_factory=datetime.utcnow)
    payload: str  # JSON serialized string
    processed: bool = Field(default=False)
    error_log: Optional[str] = None


# ============================================================
# 📸 生产快照表 (Production Snapshot)
# ============================================================
# ============================================================
# 📸 生产快照表 (Production Snapshot)
# ============================================================
# 用途：
#   1. 存储每个symbol的最新行情状态（包括盘中实时状态）
#   2. 前端API查询此表获取实时数据（包括首页列表）
#   3. 盘中数据更新时，只更新此表，不写入 MarketDataDaily
# 
# 数据流：
#   - 盘中: 数据源 → (Raw) → MarketSnapshot
#   - 收盘后: 数据源 → (Raw) → MarketDataDaily → (更新) MarketSnapshot
# ============================================================
class MarketSnapshot(SQLModel, table=True):
    """
    统一市场行情快照表 - 替代 MarketDataDaily 和 MarketDataMinute
    每个 (symbol, market) 只保留最新快照
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 唯一标识
    symbol: str = Field(index=True)
    market: str = Field(index=True)  # CN, HK, US
    
    # 价格数据
    price: float                      # 最新价（等同于close）
    open: float
    high: float
    low: float
    prev_close: Optional[float] = None
    
    # 涨跌数据
    change: float
    pct_change: float                # 涨跌幅 %
    
    # 成交数据
    volume: int
    turnover: Optional[float] = None # 成交额
    
    # 估值指标（可选）
    pe: Optional[float] = None
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    ps: Optional[float] = None
    dividend_yield: Optional[float] = None
    market_cap: Optional[float] = None
    
    # 元数据
    timestamp: str                        # 数据时间 YYYY-MM-DD HH:MM:SS
    data_source: str                 # 'akshare', 'yfinance', 'tencent'
    fetch_time: datetime = Field(default_factory=datetime.utcnow)  # 获取时间
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # 更新时间
    
    class Config:
        # 唯一约束：每个symbol+market组合只能有一条记录
        # SQLModel会自动创建唯一索引
        table_args = {'sqlite_autoincrement': True}

# ============================================================
# 📊 财务基本面数据 (Financial Fundamentals)
# ============================================================
# 用途：
#   1. 存储个股的财务基本面数据（季度/年度/TTM）
#   2. 包含营收、利润、现金流、资产负债等核心指标
#   3. 通常由 fetch_financials.py 定期更新 (e.g. weekly/monthly)
# ============================================================
class FinancialFundamentals(SQLModel, table=True):
    # 复合主键: symbol + as_of_date
    __table_args__ = (
        UniqueConstraint('symbol', 'as_of_date', name='uq_fund_symbol_date'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)  # Corresponds to asset_id
    as_of_date: str = Field(index=True)   # YYYY-MM-DD
    report_type: str = Field(default='annual')  # 'annual' or 'quarterly'
    
    # --- 盈利与现金流 (Profitability & Cash Flow) ---
    revenue_ttm: Optional[float] = None
    net_income_ttm: Optional[float] = None
    net_income_common_ttm: Optional[float] = None # Added for VERA: Net Income Available to Common
    eps: Optional[float] = None 
    eps_diluted: Optional[float] = None # Added for VERA: Diluted EPS
    shares_diluted: Optional[float] = None # Added for VERA: Weighted Average Diluted Shares
    filing_date: Optional[str] = None # Added for VERA: PIT Compliance (YYYY-MM-DD)
    operating_cashflow_ttm: Optional[float] = None
    free_cashflow_ttm: Optional[float] = None
    
    # --- 资产负债 (Balance Sheet) ---
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    net_debt: Optional[float] = None
    
    # --- 杠杆与覆盖 (Leverage & Coverage) ---
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    current_ratio: Optional[float] = None
    
    # --- 股东回报 (Shareholder Returns) ---
    dividend_yield: Optional[float] = None
    dividend_amount: Optional[float] = None # Added: Total Dividends Paid (Absolute)
    payout_ratio: Optional[float] = None
    buyback_ratio: Optional[float] = None
    
    # --- 元信息 (Meta) ---
    data_source: str = Field(default='yahoo')
    currency: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
