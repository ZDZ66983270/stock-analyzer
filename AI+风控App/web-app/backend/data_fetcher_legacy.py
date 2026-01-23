"""
VERA Data Fetching Engine (Legacy & Unified Core)
==============================================================================

本模块是 VERA 系统的数据抓取核心。它负责对接全球多个金融数据源（AkShare, yfinance, FMP），
并集成了复杂的反爬、限流、时区转换以及容错回退机制。

核心功能:
========================================

I. 数据源分发 (Multi-Source Dispatching)
----------------------------------------
1. **CN/HK (Domestic)**: 
   - 优先使用 **AkShare (EastMoney API)** 获取实时行情与历史日线。
   - 针对国内域名（*.eastmoney.com）实现了特殊的 `NO_PROXY` 自动配置，绕过系统 VPN 以提升稳定性。
2. **US (International)**:
   - 优先使用 **yfinance** 获取分钟级与日线数据。
   - **FMP Cloud**: 用于获取高价值 of US 财报（归母净利润、稀释股数、PIT 财报日期）。
3. **Indices (Indices)**: 专门管理全球指数（^DJI, ^NDX, ^SPX, HSI 等）的同步逻辑。

II. 智能决策机制 (Orchestration Integration)
----------------------------------------
- 与 `DataOrchestrator` 集成：在发起网络请求前，自动判断市场状态（开市/闭市/午休）。
- **Skip Logic**: 如果市场已闭盘且数据库已有今日终值，则自动跳过抓取，直接返回缓存数据。
- **Backfill Integration**: 支持自动化的缺失数据补填逻辑（Backfill Missing Data）。

III. 数据清洗与标准化 (ETL Preparation)
----------------------------------------
- 实现 `standardize_akshare_fields`: 将 AkShare 的中文字段（今开、昨收等）归一化为标准的英文 Key。
- 引入 `RateLimiter`: 针对单 symbol 和全局数据源频率进行严格限流，防范 IP 封禁。

作者: Antigravity
日期: 2026-01-23
"""

import akshare as ak
import pandas as pd
import requests
from typing import Optional, Dict
import sqlite3
import os
import logging # Kept logging as it's used extensively in the class
import time
import threading
import pytz
from datetime import datetime, time as dtime
from sqlalchemy import create_engine
from database import engine
from sqlmodel import Session, select

from models import MarketDataDaily

# ✅ 使用统一的符号转换工具
from utils.symbol_utils import normalize_symbol_db, to_akshare_us_symbol, get_market

def calculate_change_pct(current_price: float, prev_close: float, open_price: float = None) -> tuple:
    """
    ⚠️ DEPRECATED: This function is now handled by ETL Service.
    Use ETL Service for all change/pct_change calculations.
    
    Unified calculation for change amount and percentage change.
    
    Args:
        current_price: Current/latest price
        prev_close: Previous day's closing price
        open_price: Optional, today's opening price (fallback if prev_close is missing)
    
    Returns:
        tuple: (change, pct_change)
        - change: Price difference (rounded to 2 decimals)
        - pct_change: Percentage change (rounded to 2 decimals)
    
    Logic:
        - If prev_close is valid, use it as baseline
        - If prev_close is 0 or None, try to use open_price
        - If both are invalid, return (0.0, 0.0)
    """
    baseline = prev_close
    
    # Fallback to open_price if prev_close is invalid
    if not baseline or baseline == 0:
        if open_price and open_price > 0:
            baseline = open_price
        else:
            return (0.0, 0.0)
    
    change = current_price - baseline
    pct_change = (change / baseline) * 100
    
    return (round(change, 2), round(pct_change, 2))

class DataFetcher:
    def __init__(self, log_dir="logs_V4", output_dir="output_V4"):
        """
        初始化DataFetcher
        
        Args:
            log_dir: 日志目录
            output_dir: 输出目录
        
        Note: symbols_V4.txt已废弃，股票列表从数据库加载
        """
        # Make paths absolute relative to this file to avoid CWD issues
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # ⚠️ DEBUG: 标记代码版本
        self.CODE_VERSION = "v2.0_smart_period"  # 版本标记
        print(f"[DEBUG] DataFetcher.__init__ called, VERSION={self.CODE_VERSION}")
        
        self.log_dir = os.path.join(base_dir, log_dir)
        self.output_dir = os.path.join(base_dir, output_dir)
        
        # --- FIX: Disable System Proxy for AkShare/CN Data ---
        # User environment likely has a Proxy (VPN) active for Yahoo/US data.
        # But EastMoney (CN/HK data) causes ProxyError or is slow via proxy.
        # We configure 'no_proxy' to force direct connection for domestic domains.
        
        # 1. Unset strictly explicit proxies if they are causing 'Unable to connect' globally
        # But if Yahoo still worked, maybe we SHOULD keep them? 
        # The logs showed ProxyError for EastMoney. 
        # Strategy: Keep proxies generally (if set by system), but BYPASS for specific domains.
        
        # Current code unsets them all. If Yahoo still worked, maybe User has a Transparent Proxy (System VPN) 
        # that doesn't rely on HTTP_PROXY env vars, OR Python isn't picking them up but AkShare for US uses something else?
        # WAIT: The log said "Caused by ProxyError". This proves Python IS trying to use an HTTP Proxy.
        # Implication: My previous `del os.environ` failed to clear it effectively for `requests` on macOS 
        # because `requests` searches macOS system registry via `urllib` if env vars are missing.
        
        # 2. Force NO_PROXY for EastMoney
        no_proxy_domains = [
            "eastmoney.com", "push2his.eastmoney.com", "quote.eastmoney.com", "*.eastmoney.com",
            "gtimg.cn", "sinajs.cn", "163.com", "baidu.com"
        ]
        
        # Append to existing no_proxy or create new
        current_no_proxy = os.environ.get("no_proxy", "")
        # Normalize
        if current_no_proxy:
            current_no_proxy += ","
        
        os.environ["no_proxy"] = current_no_proxy + ",".join(no_proxy_domains)
        os.environ["NO_PROXY"] = os.environ["no_proxy"]
        
        print(f"DEBUG: Configured no_proxy for CN domains: {os.environ['no_proxy']}")
        # ----------------------------------------------------

        self.est_tz = pytz.timezone('Asia/Shanghai')
        print(f"DEBUG: Initializing DataFetcher. Log dir: {self.log_dir}")
        self._setup_logger()
        self.symbols = self._load_symbols()
        
        # --- Bulk Fetch Cache & Safety ---
        self._snapshot_cache: Dict[str, dict] = {} # market -> {symbol_base: row_data}
        # 5. Internal State
        self.market_snapshots = {}  # { market: (data_dict, timestamp) }
        self.snapshot_cache_duration = 60  # seconds
        
        # 6. Rate Limiter - 防止被拉黑
        from rate_limiter import get_rate_limiter
        self.rate_limiter = get_rate_limiter()
        self.logger.info("Rate Limiter initialized: 10s symbol interval, 5 requests/minute")
        
        self._snapshot_time: Dict[str, float] = {} # market -> timestamp
        self._snapshot_lock = threading.Lock()
    
    def standardize_akshare_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        统一AkShare字段命名
        所有AkShare接口都使用'date'或'日期'作为时间字段，需要统一转换为'timestamp'
        """
        if df is None or df.empty:
            return df
        
        # 1. 统一时间字段为timestamp
        if 'timestamp' not in df.columns:
            for time_field in ['date', '日期', '时间']:
                if time_field in df.columns:
                    df['timestamp'] = pd.to_datetime(df[time_field])
                    self.logger.debug(f"Standardized time field: {time_field} → timestamp")
                    break
        
        # 2. 统一中文字段为英文（如果还没转换）
        field_mapping = {
            '开盘': 'open',
            '收盘': 'close', 
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'turnover'
        }
        
        for cn_field, en_field in field_mapping.items():
            if cn_field in df.columns and en_field not in df.columns:
                df[en_field] = df[cn_field]
        
        return df

    
    def is_market_open_with_tz(self, market: str) -> bool:
        """
        ⚠️ DEPRECATED: Use market_status.is_market_open() instead.
        
        判断市场是否开市（考虑时区）
        
        Args:
            market: 市场代码 (CN/HK/US)
        
        Returns:
            True: 开市期间（含盘前盘后）→ 保存到MarketDataMinute
            False: 闭市 → 保存到MarketDataDaily
        """
        import warnings
        warnings.warn(
            "is_market_open_with_tz() is deprecated. Use market_status.is_market_open() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        from market_status import is_market_open
        return is_market_open(market)
        try:
            from market_schedule import MarketSchedule, MarketStatus
            
            status = MarketSchedule.get_status(market)
            
            # OPEN, PRE_MARKET, POST_MARKET都算开市期间，使用分钟数据
            is_open = status in [MarketStatus.OPEN, MarketStatus.PRE_MARKET, MarketStatus.POST_MARKET]
            
            self.logger.info(f"{market} market status: {status.value}, is_open={is_open}")
            return is_open
            
        except Exception as e:
            self.logger.error(f"Failed to get market status for {market}: {e}")
            # 默认返回False（闭市），使用Daily表更安全
            return False
        
    def _get_safe_delay(self):
        """Random delay to prevent anti-scraping triggers"""
        import random
        return random.uniform(0.5, 2.0)

    def _setup_logger(self):
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_V4.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        # Check if handler already exists to avoid duplicates in re-eintrant cases
        if not logging.getLogger().handlers:
            logging.getLogger().addHandler(console)
        self.logger = logging.getLogger(__name__)

    def _load_symbols(self) -> list:
        """
        从数据库加载股票列表
        
        来源:
        1. Watchlist表 - 用户自选股
        2. symbols_config - 系统指数
        
        Note: symbols_V4.txt已废弃
        """
        symbols = set()
        
        try:
            from database import engine
            from models import Watchlist
            from sqlmodel import Session, select
            from symbols_config import get_all_indices
            
            with Session(engine) as session:
                # 1. 用户自选股
                db_symbols = session.exec(select(Watchlist.symbol)).all()
                for s in db_symbols:
                    symbols.add(s)
                
                # 2. 系统指数
                indices = get_all_indices()
                for idx in indices:
                    symbols.add(idx)
                    
        except Exception as e:
            self.logger.error(f"Error loading symbols from DB: {str(e)}")

        self.logger.info(f"Loaded {len(symbols)} symbols from database (watchlist + indices)")
        return list(symbols)



    def fetch_us_min_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetch US minute data. Priority: yfinance (reliable) > AkShare (fallback)
        """
        try:
            self.logger.info(f"Fetching US minute data for {symbol} (yfinance primary)...")
            
            # PRIMARY: Try yfinance first (more reliable)
            df = self._fetch_fallback_yfinance_min(symbol, "US")
            if df is not None and not df.empty:
                self.logger.info(f"US minute data fetched via yfinance: {len(df)} records")
                return df
            
            # FALLBACK: Try AkShare if yfinance fails
            self.logger.warning(f"yfinance failed for US {symbol}, trying AkShare...")
            # 限流
            self.rate_limiter.wait_if_needed(symbol, 'akshare')
            df = ak.stock_us_hist_min_em(symbol=symbol)
            if df is not None and not df.empty:
                df = self.standardize_akshare_fields(df)
                if 'timestamp' in df.columns:
                    df['日期'] = df['timestamp'].dt.date
                last_date = df['日期'].max()
                first_date = last_date - pd.Timedelta(days=29)
                df = df[df['日期'] >= first_date]
                df = df.drop(columns=['日期'])
                self.logger.info(f"US minute data fetched via AkShare: {len(df)} records")
                return df
            
            self.logger.error(f"Both yfinance and AkShare failed for US {symbol}")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error fetching US minute data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_hk_min_data(self, symbol: str, period: str = '1') -> pd.DataFrame:
        """
        Fetch HK minute data. Priority: yfinance (reliable) > AkShare (fallback)
        """
        try:
            self.logger.info(f"Fetching HK minute data for {symbol} (yfinance primary)...")
            
            # PRIMARY: Try yfinance first
            # User requested skip Yahoo (2025-12-15)
            # df = self._fetch_fallback_yfinance_min(symbol, "HK")
            # if df is not None and not df.empty:
            #     self.logger.info(f"HK minute data fetched via yfinance: {len(df)} records")
            #     return df
            
            # FALLBACK: Try AkShare
            self.logger.warning(f"yfinance failed for HK {symbol}, trying AkShare...")
            code = symbol.replace('.hk', '').replace('.HK', '').zfill(5)
            # 限流
            self.rate_limiter.wait_if_needed(symbol, 'akshare')
            df = ak.stock_hk_hist_min_em(symbol=code, period=period)
            if df is not None and not df.empty:
                df = self.standardize_akshare_fields(df)
                self.logger.info(f"HK minute data fetched via AkShare: {len(df)} records")
                return df
            
            self.logger.error(f"Both yfinance and AkShare failed for HK {symbol}")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error fetching HK minute data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_cn_min_data(self, symbol: str, period: str = '1') -> pd.DataFrame:
        """
        Fetch CN minute data. Priority: yfinance (reliable) > AkShare (fallback)
        """
        try:
            self.logger.info(f"Fetching CN minute data for {symbol} (yfinance primary)...")
            
            # PRIMARY: Try yfinance first
            df = self._fetch_fallback_yfinance_min(symbol, "CN")
            if df is not None and not df.empty:
                self.logger.info(f"CN minute data fetched via yfinance: {len(df)} records")
                return df
            
            # FALLBACK: Try AkShare
            self.logger.warning(f"yfinance failed for CN {symbol}, trying AkShare...")
            code = symbol.replace('.sh', '').replace('.SH', '').replace('.sz', '').replace('.SZ', '').zfill(6)
            # 限流
            self.rate_limiter.wait_if_needed(symbol, 'akshare')
            df = ak.stock_zh_a_hist_min_em(symbol=code, period=period)
            if df is not None and not df.empty:
                df = self.standardize_akshare_fields(df)
                self.logger.info(f"CN minute data fetched via AkShare: {len(df)} records")
                return df
            
            self.logger.error(f"Both yfinance and AkShare failed for CN {symbol}")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error fetching CN minute data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_cn_spot_data(self, symbol: str) -> dict:
        """
        Fetch real-time spot data for a single CN stock to get indicators like Dividend Yield, PE, PB.
        Returns a dict with keys: price, open, high, low, volume, amount, pe, pb, dividend_yield, market_cap.
        """
        try:
            code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
            # Use stock_zh_a_spot_em for full market spot might be slow if fetching all, 
            # but AkShare/EM doesn't have a fast single-stock spot endpoint with indicators easily?
            # stock_individual_info_em gets static info.
            # stock_zh_a_spot_em() returns ALL stocks. Too slow (~5000 rows).
            # Alternative: stock_zh_a_hist_pre_min_em (realtime minute) doesn't have PE/Div.
            # Use 'stock_financial_abstract' for financial info? Only gives static.
            
            # BEST WAY: Use stock_zh_a_spot_em but filter? No, API downloads all.
            # OPTION 2: Use `stock_individual_info_em` for Name/Sector, but not dynamic price indicators.
            # OPTION 3: web scraping specific EM page. 
            # OPTION 4: AkShare has `stock_zh_index_spot_em`? No.
            
            # FASTEST for Single Stock Realtime with PE/PB:
            # Maybe just use `fetch_latest_data` (minute) for Price/Vol, 
            # and use a separate method for static/daily-update indicators like PE/Div?
            
            # For now, let's use the efficient approach:
            # If we need Dividend/PE, we might have to accept they are 'Daily' indicators.
            # `stock_zh_a_indicators` (PE/PB/Div history).
            
            # Let's try `stock_zh_a_spot_em` but cached? No.
            # Wait, `ak.stock_zh_a_spot_em` is surprisingly fast sometimes.
            # But let's check `ak.stock_zh_a_hist` (daily) - does headers have it? No.
            
            # Let's use `ak.stock_a_indicator_lg` (Legu)? No.
            
            # Let's fallback to scraping a lightweight endpoint if possible, or use yfinance for indicators?
            # yfinance info has 'dividendYield'.
            pass
        except:
            pass
        return {}

    def fetch_market_snapshot(self, market: str) -> dict:
        """
        Fetch a full market snapshot with caching (TTL 30s).
        Returns dict: {symbol_base: row_data}
        Currently only implements Stub or simple cache logic.
        """
        # For V4, we might not have a full market snapshot ready for US/HK.
        # So we return empty dict to force fallback to individual fetch.
        return {}

    def fetch_snapshot(self, symbol: str, market: str) -> dict:
        """
        Get a real-time snapshot including Valuation Indicators if possible.
        """
        try:
            # 1. Basic Price/Vol from Min Data (Fast & Reliable)
            base_data = self.fetch_latest_data(symbol, market)
            if not base_data: return None
            
            # 2. Indicators (PE, DIV)
            # For CN, we can try yfinance for indicators as a fallback, 
            # or use AkShare `stock_zh_a_valuation_baostock` (history).
            # Hack: Return base_data and let frontend use historical PE/Div from DB if today's is missing.
            # Ref: User complained Dividend is wrong. DB likely has None.
            # We NEED to fetch valid Dividend.
            
            # Try fetching "stock_zh_a_daily" (qfq) - does it have PE? No.
            # Try "stock_zh_a_daily_indicator" ?
            
            return base_data
        except Exception as e:
            self.logger.error(f"Snapshot error: {e}")
            return None

    def check_market_status(self, market: str) -> bool:
        """
        ⚠️ DEPRECATED: Use market_status.is_market_open() instead.
        
        Check if the market is currently open.
        Returns True if Open, False if Closed.
        """
        import warnings
        warnings.warn(
            "check_market_status() is deprecated. Use market_status.is_market_open() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        from market_status import is_market_open
        return is_market_open(market)
        from datetime import datetime, time
        import pytz

        now = datetime.now(pytz.timezone('Asia/Shanghai')) # User is likely in China
        
        current_time = now.time()

        if market == "CN":
            # Weekends
            if now.weekday() >= 5: return False
            
            # 9:30-11:30, 13:00-15:00
            morning_open = time(9, 30)
            morning_close = time(11, 30)
            afternoon_open = time(13, 0)
            afternoon_close = time(15, 0)
            return (morning_open <= current_time <= morning_close) or \
                   (afternoon_open <= current_time <= afternoon_close)

        elif market == "HK":
            # Weekends
            if now.weekday() >= 5: return False
            
            # 9:30-12:00, 13:00-16:00
            morning_open = time(9, 30)
            morning_close = time(12, 0)
            afternoon_open = time(13, 0)
            afternoon_close = time(16, 0)
            return (morning_open <= current_time <= morning_close) or \
                   (afternoon_open <= current_time <= afternoon_close)

        elif market == "US":
            # US Eastern Time: 9:30 - 16:00
            # Convert Shanghai 'now' to US/Eastern
            us_tz = pytz.timezone('US/Eastern')
            us_now = now.astimezone(us_tz)
            
            # US verify Weekday
            # US verify Weekday
            if us_now.weekday() >= 5: return False
            
            us_time = us_now.time()
            market_open = time(9, 30)
            market_close = time(16, 0)
            return (market_open <= us_time < market_close)  # 16:00已闭市

        return True # Default to Open if unknown

    def fetch_latest_data(self, symbol: str, market: str, save_db: bool = True, force_refresh: bool = False) -> dict:
        """
        Orchestrates fetching the absolute latest data.
        Strategy:
        1. Snapshot (All Markets) - fast, efficient.
        2. Database (If Market Closed & Cached)
        3. Realtime API (If Open/Forced)
        """
        try:
            # 0. Check valid market
            if market == 'Other':
                return None
            # Ensure necessary imports for DB operations
            from models import MarketDataDaily
            from database import create_db_and_tables
            from sqlmodel import Session, create_engine, select
            from datetime import datetime, timedelta, time as dtime # dtime for clarity with time objects
            import pytz
            import logging # For logging.info

            # Initialize engine if not already done (assuming self.engine might not exist yet)
            if not hasattr(self, 'engine') or self.engine is None:
                self.engine = create_engine("sqlite:///database.db")
                create_db_and_tables() # Ensure tables exist

            # ✅ 使用统一的市场状态模块
            from market_status import is_market_open
            is_open = is_market_open(market)
            is_trading_day = (datetime.now().weekday() < 5)  # Monday=0, Sunday=6
            reason = "Unknown" # Legacy support
            self.logger.info(f"Checking {symbol} ({market}): is_open={is_open}, is_trading_day={is_trading_day}")

            # ============================================================
            # 🎯 使用 DataOrchestrator 进行统一决策
            # ============================================================
            from data_orchestrator import DataOrchestrator
            from utils.symbol_utils import normalize_symbol_db
            
            orchestrator = DataOrchestrator()
            db_latest_date = orchestrator.get_db_latest_date(symbol, market)
            
            decision = orchestrator.decide_fetch_strategy(
                symbol=symbol,
                market=market,
                force_refresh=force_refresh,
                db_latest_date=db_latest_date
            )
            
            self.logger.info(
                f"[DataOrchestrator] {symbol} ({market}): "
                f"决策={decision.fetch_type}, 原因={decision.reason}"
            )
            
            # 如果决策是跳过,直接从数据库返回
            if decision.fetch_type == 'skip':
                self.logger.info(f"[跳过] {symbol}: {decision.reason}")
                # 从数据库返回最新数据
                from models import MarketSnapshot
                from database import engine
                
                with Session(engine) as session:
                    db_symbol = normalize_symbol_db(symbol, market)
                    snapshot = session.exec(
                        select(MarketSnapshot).where(
                            MarketSnapshot.symbol == db_symbol,
                            MarketSnapshot.market == market
                        )
                    ).first()
                    
                    if snapshot and snapshot.price and snapshot.price > 0:
                        return {
                            'symbol': snapshot.symbol,
                            'market': snapshot.market,
                            'price': snapshot.price,
                            'close': snapshot.price,
                            'open': snapshot.open or 0,
                            'high': snapshot.high or 0,
                            'low': snapshot.low or 0,
                            'prev_close': snapshot.prev_close,
                            'change': snapshot.change or 0,
                            'pct_change': snapshot.pct_change or 0,
                            'volume': snapshot.volume or 0,
                            'turnover': snapshot.turnover,
                            'date': snapshot.date,
                            'pe': snapshot.pe,
                            'pb': snapshot.pb,
                            'dividend_yield': snapshot.dividend_yield,
                            'market_cap': snapshot.market_cap
                        }
                    else:
                        self.logger.warning(f"[跳过] {symbol}: DB无有效数据,继续API请求")
            
            # 🔥 自动回填历史数据
            if decision.need_backfill_daily:
                self.logger.info(
                    f"[历史补充] {symbol}: {decision.backfill_date_range}, "
                    f"原因={decision.backfill_reason}"
                )
                try:
                    # 立即补充缺失的历史数据
                    backfill_result = self.backfill_missing_data(symbol, market, days=30)
                    if backfill_result.get('success'):
                        self.logger.info(
                            f"✅ [{symbol}] 历史数据补充成功: "
                            f"{backfill_result.get('records_fetched', 0)}条记录"
                        )
                    else:
                        self.logger.warning(
                            f"⚠️ [{symbol}] 历史数据补充失败: "
                            f"{backfill_result.get('message', '未知错误')}"
                        )
                except Exception as e:
                    self.logger.error(f"❌ [{symbol}] 历史数据补充异常: {e}")
            
            
            # --- 旧的HK指数特殊处理已移除，现在使用统一架构（Line 774+）---
            
            # ✅ FIX 2025-12-20: US Indices应该使用yfinance增量获取，不再路由到AkShare
            # 原因：AkShare的stock_us_daily会返回全量历史数据（5530条），
            # 而yfinance在Line 916配合HOTFIX period=5d只获取5天数据
            # 🔴 DISABLED: US Indices via AkShare routing (Line 612-665) 🔴
            # --- PRIORITY: US Indices via AkShare (避免被yahoo拉黑) ---
            # from symbols_config import is_index, get_akshare_symbol
            # if market == 'US' and is_index(symbol):
            #     self.logger.info(f"Routing US index {symbol} to AkShare...")
            #     
            #     # 限流：同symbol 10秒间隔，akshare源每分钟5请求
            #     wait_time = self.rate_limiter.wait_if_needed(symbol, 'akshare')
            #     if wait_time > 0:
            #         self.logger.info(f"Rate limit: waited {wait_time:.2f}s for {symbol}")
            #     
            #     try:
            #         import akshare as ak
            #         from datetime import datetime
            #         
            #         ak_symbol = get_akshare_symbol(symbol)  # ^DJI -> .DJI
            #         self.logger.info(f"Fetching {ak_symbol} via ak.stock_us_daily...")
            #         
            #         df = ak.stock_us_daily(symbol=ak_symbol, adjust="")
            #         if df is not None and not df.empty:
            #                 # 🔥 新架构：使用统一的ETL流程
            #                 # 不再直接保存到Daily/Snapshot，而是保存到RawMarketData
            #                 if save_db:
            #                     self.logger.info(f"Saving {symbol} to RawMarketData for ETL processing")
            #                     # save_to_db(symbol, market, period_data)
            #                     # period_data = {period: dataframe}
            #                     self.save_to_db(symbol, market, {'1d': df})
            #                 
            #                 # 构造返回字典（用于返回给调用者）
            #                 latest = df.iloc[-1]
            #                 result = {
            #                     'symbol': symbol,
            #                     'price': float(latest['close']),
            #                     'close': float(latest['close']),
            #                     'open': float(latest['open']),
            #                     'high': float(latest['high']),
            #                     'low': float(latest['low']),
            #                     'volume': int(latest['volume']) if latest['volume'] > 0 else 0,
            #                     'date': f"{latest['date'].strftime('%Y-%m-%d')} 16:00 美东",
            #                     'market': market,
            #                 }
            #                 
            #                 # 计算涨跌（用于返回值）
            #                 if len(df) >= 2:
            #                     prev = df.iloc[-2]
            #                     result['change'] = result['close'] - float(prev['close'])
            #                     result['pct_change'] = (result['change'] / float(prev['close'])) * 100 if prev['close'] > 0 else 0
            #                 
            #                 self.logger.info(f"✅ AkShare: {symbol} ${result['price']:.2f} (via ETL)")
            #                 return result
            #             else:
            #                 self.logger.warning(f"AkShare returned empty for {ak_symbol}")
            #         except Exception as ak_err:
            #             self.logger.error(f"AkShare failed for {symbol}: {ak_err}, falling back to yfinance")
            #             # Fall through to yfinance fallback

            # --- STRATEGY 1: Use Bulk Spot Snapshot (Preferred) ---
            # Extract basic code
            base_symbol = symbol.split('.')[0]
            if market == 'US':
                # Remove numeric prefix like "105." or "106."
                if '.' in symbol and symbol.split('.')[0].isdigit():
                     yahoo_symbol = symbol.split('.')[-1]
                else:
                     yahoo_symbol = symbol
                
                # Special case for Indices if needed, but standard stocks are just ticker
                pass
            
            # Fetch (or get cached) snapshot
            snapshot = self.fetch_market_snapshot(market)
            
            if snapshot and base_symbol in snapshot:
                row = snapshot[base_symbol]
                self.logger.info(f"Hit Snapshot for {symbol}")
                
                # Map fields
                try:
                    # EastMoney Logic (CN/HK/US now unified)
                    price = float(row.get('最新价', 0))
                    change = float(row.get('涨跌额', 0))
                    pct_change = float(row.get('涨跌幅', 0))
                    
                    vol_raw = row.get('成交量', 0)
                    vol = int(vol_raw) if vol_raw else 0
                    turnover = float(row.get('成交额', 0) or 0)
                    
                    open_p = float(row.get('今开', 0) or 0)
                    high_p = float(row.get('最高', 0) or 0)
                    low_p = float(row.get('最低', 0) or 0)
                    prev_c = float(row.get('昨收', 0) or 0)
                    
                    # Date - Live!
                    now_str = datetime.now(self.est_tz).strftime('%Y-%m-%d %H:%M')
                    if market == 'US':
                         now_str = datetime.now().strftime('%Y-%m-%d %H:%M') + " 美东(Live)"

                    return {
                        "symbol": symbol,
                        "market": market,
                        "price": price,
                        "close": price,
                        "change": change,
                        "pct_change": pct_change,
                        "volume": int(vol),
                        "turnover": turnover,
                        "date": now_str,
                        "open": open_p,
                        "high": high_p,
                        "low": low_p,
                        "prev_close": prev_c
                    }
                except Exception as map_err:
                    self.logger.error(f"Mapping snapshot failed for {symbol}: {map_err}")

            # --- STRATEGY 2: Fallback to Old Logic (Min/Daily) ---
            # If snapshot missing or symbol not in snapshot
            
            # 2. Database Strategy - IMPROVED for Lunch Break
            # Priority:
            # 1. If trading day (includes lunch break): Try to get today's minute data from DB first
            # 2. If not trading day OR force_refresh: Fetch from API
            # 3. If market closed and we have data: Return cached
            
            # Helper to check DB
            with Session(self.engine) as session:
                # Check daily data (MarketDataMinute table has been removed)
                latest_db = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol == symbol)
                    .order_by(MarketDataDaily.date.desc())
                    .limit(1)
                ).first()

                if latest_db:
                    # Logic: If Closed, and we have recent data (e.g. from today or yesterday), return it.
                    # Simple heuristic: If market closed, and we have ANY data from last 24h, good enough?
                    # Or compare date?
                    # Let's simplify: If not force_refresh AND not is_open: Return DB
                    # User requirement: "Refresh time... if Closed... return Last Close".
                    # Even if user pressed Refresh, if it's Closed and we have data, we shouldn't fetch.
                    
                    db_date_str = str(latest_db.date).split(' ')[0] # YYYY-MM-DD
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    
                    # If Market Closed (not even trading day) and we have data
                    if not is_trading_day and not force_refresh:
                        self.logger.info(f"Market Closed (not trading day). DB Record found: {db_date_str}. Returning Cached.")
                        # Convert DB model to Dict
                        # Fix 00:00 Time Display:
                        base_date = db_date_str
                        date_str = ""
                        if market == "CN":
                            date_str = f"{base_date} 15:00"
                        elif market == "HK":
                            date_str = f"{base_date} 16:00"
                        elif market == "US":
                            date_str = f"{base_date} 16:00:00" # Local ET close time usually. 
                        
                        # Ensure we populate MarketSnapshot even if debouncing
                        cached_data = {
                            "symbol": latest_db.symbol,
                            "price": latest_db.close, # In MarketData, close is price
                            "change": latest_db.change,
                            "pct_change": latest_db.pct_change,
                            "volume": latest_db.volume,
                            "market": latest_db.market,
                            "date": date_str, # Use formatted date_str
                            "pe": latest_db.pe,
                            "dividend_yield": latest_db.dividend_yield,
                            # Add other fields if needed, or rely on frontend fallbacks
                            "open": latest_db.open,
                            "high": latest_db.high,
                            "low": latest_db.low,
                            "close": latest_db.close,
                            "prev_close": latest_db.prev_close,
                             # Mark as cached
                            "data_source": "cache_db"
                        }
                        
                        # ✅ Snapshot由ETL管理，不在此处直接保存
                        # 如果Snapshot缺失，应通过ETL重建而非绕过ETL

                        return cached_data

            # 3. Fetch from API (If Open or DB Missing/Forced Refresh)
            self.logger.info(f"Fetching API for {symbol} (Force: {force_refresh}, Open: {is_open})")
            
            df = pd.DataFrame()
            
            # STRATEGY: 优先获取日线数据，失败才用分钟数据
            if market == "CN":
                # 1. 优先：日线数据
                try:
                    import akshare as ak
                    from symbols_config import get_akshare_symbol, is_index
                    
                    # ✅ 使用集中化的symbol映射
                    if is_index(symbol):
                        # 指数：使用get_akshare_symbol获取正确的代码
                        # 例如：000001.SS → sh000001 (上证指数)
                        akshare_code = get_akshare_symbol(symbol)
                        self.logger.info(f"Fetching CN index {symbol} using AkShare code: {akshare_code}")
                        df_daily = ak.stock_zh_index_daily(symbol=akshare_code)
                    else:
                        # 个股：提取代码
                        code = symbol.split('.')[0]
                        self.logger.info(f"Fetching CN stock {symbol} (code: {code})")
                        self.rate_limiter.wait_if_needed(symbol, 'akshare')
                        df_daily = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="")
                    
                    if df_daily is not None and not df_daily.empty:
                        # 只取最新一天的数据
                        df = df_daily.tail(1).copy()
                        # ✅ 使用统一的字段标准化
                        df = self.standardize_akshare_fields(df)
                        # ✅ 数据保持原始时间，不再强制修改
                        # 时间戳将由保存逻辑根据市场状态选择合适的表
                        
                        self.logger.info(f"✅ CN daily data fetched: {df['timestamp'].iloc[0]}")
                    else:
                        raise Exception("Daily data empty")
                        
                except Exception as daily_err:
                    # 2. Fallback：分钟数据
                    self.logger.warning(f"CN daily data failed ({daily_err}), falling back to minute data...")
                    df = self.fetch_cn_min_data(symbol, period='1')
                    
            elif market == "HK":
                # === HK市场：区分指数和个股 ===
                from symbols_config import is_index
                
                if is_index(symbol):
                    # --- HK指数分支 ---
                    self.logger.info(f"HK Index detected: {symbol}")
                    
                    # 判断市场状态（统一架构）
                    if is_open:
                        # 开市：获取实时数据
                        self.logger.info(f"HK market OPEN: fetching realtime for index {symbol}")
                        latest_data = self.fetch_hk_index_realtime(symbol)
                        
                    else:
                        # 闭市：获取日线数据并使用统一ETL流程
                        self.logger.info(f"HK market CLOSED: fetching daily for index {symbol}")
                        daily_df = self.fetch_hk_daily_data(symbol)
                        
                        if not daily_df.empty and save_db:
                            # 🔥 新架构：使用统一ETL流程
                            self.logger.info(f"Saving {symbol} to RawMarketData for ETL processing")
                            self.save_to_db(symbol, market, {'1d': daily_df})
                        
                        # 构造返回值（用于API响应）
                        if not daily_df.empty:
                            latest_row = daily_df.iloc[-1]
                            current_price = float(latest_row.get('收盘', latest_row.get('close', 0)))
                            
                            # 计算change和pct_change（用于返回值）
                            change = 0
                            pct_change = 0
                            if len(daily_df) >= 2:
                                prev_row = daily_df.iloc[-2]
                                prev_close = float(prev_row.get('收盘', prev_row.get('close', 0)))
                                if prev_close > 0:
                                    change = current_price - prev_close
                                    pct_change = (change / prev_close) * 100
                            
                            latest_data = {
                                'symbol': symbol,
                                'market': market,
                                'price': current_price,
                                'close': current_price,
                                'open': float(latest_row.get('开盘', latest_row.get('open', 0))),
                                'high': float(latest_row.get('最高', latest_row.get('high', 0))),
                                'low': float(latest_row.get('最低', latest_row.get('low', 0))),
                                'volume': int(latest_row.get('成交量', latest_row.get('volume', 0))),
                                'date': str(latest_row.get('timestamp', '')),  # ← 使用timestamp
                                'change': change,
                                'pct_change': pct_change
                            }
                        else:
                            latest_data = None
                    
                    # HK指数：已通过ETL处理，跳过后续df处理
                    df = None
                    skip_direct_save = True  # 标记：已通过ETL，跳过直接保存逻辑
                    
                else:
                    # --- HK个股分支（保持原有逻辑）---
                    self.logger.info(f"HK Stock: fetching minute data for {symbol}")
                    df = self.fetch_hk_min_data(symbol, period='1')
                
            elif market == "US":
                if is_open:
                    # 开市：分钟数据
                    self.logger.info(f"US Market OPEN: fetching minute data for {symbol}")
                    if symbol.startswith('^'):
                        df = pd.DataFrame()  # Indices skip AkShare
                    else:
                        symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                        df = self.fetch_us_min_data(symbol_min)
                else:
                    # 闭市：使用yfinance日线数据
                    self.logger.info(f"US Market CLOSED: fetching daily data via yfinance for {symbol}")
                    try:
                        df = self._fetch_fallback_yfinance(symbol, market)
                        if df is not None and not df.empty:
                            # yfinance返回的是日线数据，时间可能是00:00，设置为16:00 ET
                            if 'timestamp' in df.columns:
                                df['timestamp'] = pd.to_datetime(df['timestamp'])
                                # 检查是否为00:00，如果是则改为16:00
                                df['timestamp'] = df['timestamp'].apply(
                                    lambda x: x.replace(hour=16, minute=0, second=0) if x.hour == 0 else x
                                )
                            self.logger.info(f"✅ US daily data fetched via yfinance")
                    except Exception as e:
                        self.logger.error(f"US yfinance fallback failed: {e}")
                        df = pd.DataFrame()

            
            latest_data = None # Initialize to avoid UnboundLocalError

            if df is not None and not df.empty:
                # --- RULE 4: Write-Through ---
                # We save the latest data point as '1d' so it acts as the cached snapshot.
                # Use iloc[[-1]] to keep it as a DataFrame
                try:
                    last_row_df = df.iloc[[-1]].copy()
                    # Ensure Date is string or compatible for save_to_db logic
                    if save_db:
                        self.save_to_db(symbol, market, {'1d': last_row_df})
                        self.logger.info(f"Write-Through: Saved latest snapshot for {symbol}")
                    else:
                        self.logger.info(f"Write-Through: Skipped saving snapshot for {symbol} (save_db=False)")
                except Exception as w_err:
                    self.logger.error(f"Write-Through failed: {w_err}")
                
                # Get last row for return
                latest = df.iloc[-1]
                
                # Format Timestamp Explicitly
                time_val = latest.get('timestamp')  # ← 修复：使用timestamp
                dt_obj = None
                date_str = ""
                
                # OPTIMIZATION: If source already provided a formatted date, use it (e.g. from AkShare or previous step)
                if 'date' in latest and latest['date']:
                    date_str = str(latest['date'])
                    # Ensure seconds if missing
                    if len(date_str) == 16: # 2025-12-16 13:47
                         date_str += ":00"
                    elif len(date_str) == 10: # 2025-12-16
                         # If strictly date, we might want to check market status or leave as is?
                         # But for 1min data, it should have time.
                         pass
                    self.logger.info(f"Using pre-existing date field: {date_str}")
                else:
                    # 1. Parse into datetime object using time_val
                    if pd.api.types.is_datetime64_any_dtype(df['timestamp']) and hasattr(time_val, 'to_pydatetime'):
                         dt_obj = time_val.to_pydatetime()
                    else:
                         try:
                            dt_obj = pd.to_datetime(time_val).to_pydatetime()
                         except:
                            pass
                    
                    # 2. Timezone Conversion & Normalization (Crucial for US/CN/HK)
                    if dt_obj:
                        has_time_component = (dt_obj.hour != 0 or dt_obj.minute != 0)
                        
                        if market == "US":
                             # Heuristic: If time component exists (not 00:00)
                             if has_time_component:
                                 us_tz = pytz.timezone('US/Eastern')
                                 if dt_obj.tzinfo is None:
                                     dt_us = us_tz.localize(dt_obj)
                                 else:
                                     dt_us = dt_obj.astimezone(us_tz)
                                 date_str = dt_us.strftime('%Y-%m-%d %H:%M:%S')
                             else:
                                 # US Daily: Set to 16:00 ET
                                 dt_obj = dt_obj.replace(hour=16, minute=0, second=0)
                                 date_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                                 
                        elif market == "CN":
                            # CN Normalization: If 00:00:00, set to 15:00
                             if not has_time_component:
                                 dt_obj = dt_obj.replace(hour=15, minute=0, second=0)
                                 self.logger.info(f"CN Daily Normalization: 00:00 -> {dt_obj}")
                             date_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                             
                        elif market == "HK":
                             # HK Normalization: If 00:00:00, set to 16:00
                             if not has_time_component:
                                 dt_obj = dt_obj.replace(hour=16, minute=0, second=0)
                                 self.logger.info(f"HK Daily Normalization: 00:00 -> {dt_obj}")
                             date_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                             
                        else:
                             # Default
                             date_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                             
                        self.logger.info(f"Parsed DateStr: {date_str} (dt={dt_obj})")
                    else:
                        date_str = str(time_val)
                        self.logger.info(f"DEBUG: Failed to parse dt_obj. Raw: {time_val}")

                # Filter for the latest date in the dataframe
                time_col = 'timestamp'  # 统一使用timestamp
                latest_date_str = str(latest.get(time_col, '')).split(' ')[0]
                
                # Identify volume column
                vol_col = '成交量' if '成交量' in df.columns else 'volume'
                if vol_col not in df.columns: vol_col = None

                # Check if time column is datetime
                if time_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[time_col]):
                     # Filter rows with same date as latest row
                    latest_date_val = latest[time_col].date()
                    day_df = df[df[time_col].dt.date == latest_date_val]
                    total_vol = day_df[vol_col].sum() if vol_col else 0
                else:
                    try: 
                        total_vol = df[vol_col].sum() if vol_col else 0
                    except:
                        total_vol = latest.get(vol_col, 0) if vol_col else 0

                latest_data = {
                    "symbol": symbol,
                    "market": market,
                    "date": date_str,
                    "volume": int(total_vol), # Cumulative Volume
                    "open": float(latest.get('开盘') or latest.get('open') or 0),
                    "high": float(latest.get('最高') or latest.get('high') or 0),
                    "low": float(latest.get('最低') or latest.get('low') or 0),
                    "close": float(latest.get('收盘') or latest.get('close') or 0),
                    "price": float(latest.get('收盘') or latest.get('close') or 0) # Alias
                }
            
            # Merge with Yahoo Indicators (for Yield, PE, MarketCap)
            # This also serves as a Fallback if primary fetch failed (so latest_data might be None at start of this block)
            try:
                indicators = self.fetch_yahoo_indicators(symbol)
                if indicators:
                    # If primary fetch failed, try to construct latest_data from Yahoo
                    if latest_data is None:
                        # DEBUG
                        self.logger.info(f"DEBUG: latest_data is None, constructing from Yahoo for {symbol}")
                        # Yahoo has 'price', 'volume' (Daily), 'dividend_yield'
                        # We need 'date'
                        from datetime import datetime, timedelta
                        import pytz
                        
                        now = datetime.now(pytz.timezone('Asia/Shanghai'))
                        
                        if market == "US":
                            us_tz = pytz.timezone('US/Eastern')
                            us_now = now.astimezone(us_tz)
                            
                            # Logic: If Market is Closed (Weekend or outside 09:30-16:00), show Closing Time
                            if us_now.weekday() >= 5:
                                # Weekend -> Show last Friday
                                offset = us_now.weekday() - 4
                                last_close = us_now - timedelta(days=offset)
                                date_str = f"{last_close.strftime('%Y-%m-%d')} 16:00:00"
                            elif us_now.time() >= dtime(16, 0):
                                # Weekday after close -> Show Today 16:00
                                date_str = f"{us_now.strftime('%Y-%m-%d')} 16:00:00"
                            elif us_now.time() < dtime(9, 30):
                                # Weekday PRE-MARKET (before 09:30) -> Show Yesterday 16:00
                                last_close = us_now - timedelta(days=1)
                                # Handle Monday pre-market -> Show Friday
                                while last_close.weekday() >= 5:
                                    last_close = last_close - timedelta(days=1)
                                date_str = f"{last_close.strftime('%Y-%m-%d')} 16:00:00"
                            else:
                                # Market Open (09:30-16:00) -> Use current time
                                date_str = f"{us_now.strftime('%Y-%m-%d %H:%M:%S')}"
                        else:
                            date_str = now.strftime('%Y-%m-%d %H:%M:%S')
                        
                        latest_data = {
                            "symbol": symbol,
                            "market": market,
                            "date": date_str,
                            "volume": indicators.get('volume', 0),
                            "open": indicators.get('open', 0),
                            "high": indicators.get('dayHigh', indicators.get('high', 0)), # Yahoo info often uses dayHigh/dayLow
                            "low": indicators.get('dayLow', indicators.get('low', 0)),
                            "close": indicators.get('price', 0),
                            "price": indicators.get('price', 0)
                        }
                    
                    # Merge Indicators (PE, Div)
                    for k, v in indicators.items():
                         if k == 'volume': continue
                         # Don't overwrite existing valid data unless missing
                         if k not in latest_data or latest_data[k] is None or latest_data[k] == 0:
                            latest_data[k] = v
                    
                    self.logger.info(f"DEBUG: Post-Merge latest_data: {latest_data}")
                    
                    # FORCE Update Price for US Stocks from Yahoo (more realtime?)
                    if market == "US" and indicators.get('price'):
                         latest_data['price'] = indicators['price']
                         latest_data['close'] = indicators['price']
                         # Force update open if available to ensure correct change %
                         if indicators.get('open'): latest_data['open'] = indicators['open']
            
            except Exception as e:
                # self.logger.error(f"Yahoo Fallback Failed: {e}")
                pass

            # Fallback for Zero Price (Common in closed market for US/HK)
            if latest_data:
                # Check for data quality issues that require fallback
                # 1. Price is 0 (Critical missing)
                # 2. Change/PctChange is 0 (Likely closed market snapshot missing yesterday's reference)
                price_is_zero = latest_data.get('price', 0) == 0 and latest_data.get('close', 0) == 0
                change_is_zero = latest_data.get('change', 0) == 0 and latest_data.get('pct_change', 0) == 0
                
                if price_is_zero or change_is_zero:
                    reason = "Price is 0" if price_is_zero else "Change is 0"
                    self.logger.warning(f"Data incomplete ({reason}) for {symbol}. Attempting daily history fallback/repair.")
                    
                    try:
                         # Fetch 5 days of daily history to ensure we have 'Yesterday'
                         daily = None
                         if market == 'US':
                             daily = self.fetch_us_daily_data(self.to_akshare_us_symbol(symbol))
                         elif market == 'HK':
                             daily = self.fetch_hk_daily_data(symbol)
                         elif market == 'CN':
                             daily = self.fetch_cn_daily_data(symbol)
                         
                         
                         if daily is not None and not daily.empty:
                             # Ensure sorted by date!
                             if 'timestamp' in daily.columns:
                                 daily = daily.sort_values('timestamp')
                             
                             last_row = daily.iloc[-1]

                             # Map daily columns to latest_data format
                             # Robust Key Lookup for Close
                             valid_close = float(last_row.get('close') or last_row.get('Close') or last_row.get('收盘') or 0)

                             if valid_close > 0:
                                 # If original price was 0, use this. 
                                 # If original price existed but Change was 0, we trust Realtime Price, but use History for Change Calc?
                                 # Better to use History for Price too if we are falling back, to ensure consistency with Change.
                                 latest_data['close'] = valid_close
                                 latest_data['price'] = valid_close
                                 
                                 open_val = last_row.get('open') or last_row.get('Open') or last_row.get('开盘')
                                 if open_val: latest_data['open'] = float(open_val)
                                     
                                 high_val = last_row.get('high') or last_row.get('High') or last_row.get('最高')
                                 if high_val: latest_data['high'] = float(high_val)
                                     
                                 low_val = last_row.get('low') or last_row.get('Low') or last_row.get('最低')
                                 if low_val: latest_data['low'] = float(low_val)

                                 # Robust Volume Fetch
                                 vol = last_row.get('volume') or last_row.get('Volume') or last_row.get('成交量') or 0
                                 latest_data['volume'] = int(vol)
                                 
                                 # Robust Turnover Fetch/Calc
                                 tvr = last_row.get('turnover') or last_row.get('Turnover') or last_row.get('成交额')
                                 if tvr is None and latest_data.get('close') and latest_data.get('volume'):
                                     tvr = latest_data['close'] * latest_data['volume']
                                 if tvr: latest_data['turnover'] = float(tvr)

                                  
                                 # Use the historical date so user knows it's not live (ONLY if we don't have a better one)
                                 has_high_precision_time = latest_data.get('date') and len(str(latest_data['date'])) > 10
                                 if not has_high_precision_time:
                                     if 'timestamp' in last_row: latest_data['date'] = str(last_row['timestamp'])
                                     elif 'date' in last_row: latest_data['date'] = str(last_row['date'])
                                 
                                 # Attempt to extract indicators if present in history (rare)
                                 # 'pe', 'pb' usually not in candles, but let's try
                                 if 'pe' in last_row: latest_data['pe'] = float(last_row['pe'])
                                 

                    except Exception as fb_e:
                        self.logger.error(f"Daily fallback failed: {fb_e}")

                # If price_is_zero or change_is_zero, try to recalculate 'change' and 'pct_change'
                # This fixes the "+0.00%" issue for stocks like BABA (09988.hk)
                # This block should be after the daily fallback, as daily fallback might provide prev_close
                if latest_data:
                    # Check for zero data after fallback
                    price_is_zero = latest_data.get('price', 0) == 0 and latest_data.get('close', 0) == 0
                    change_is_zero = latest_data.get('change', 0) == 0 and latest_data.get('pct_change', 0) == 0

                    if price_is_zero or change_is_zero:
                        p_close = latest_data.get('prev_close', 0)
                        curr_price = latest_data.get('price', 0)
                        
                        if curr_price > 0 and p_close and p_close > 0:
                            recalc_change = curr_price - p_close
                            recalc_pct = (recalc_change / p_close) * 100
                            
                            if change_is_zero:
                                latest_data['change'] = recalc_change
                                latest_data['pct_change'] = recalc_pct
                                self.logger.info(f"Fixed 0% change for {symbol}: {recalc_pct:.2f}%")

                # If still zero price OR latest_data is None, try Fallback Min
                # Check safe access
                current_price = latest_data.get('price', 0) if latest_data else 0
                
                if current_price == 0:
                    self.logger.warning(f"Price still 0 for {symbol}. Attempting Yahoo minute fallback.")
                    try:
                        # Fetch 1 day of minute data from Yahoo
                        yf_symbol = self.to_yfinance_symbol(symbol, market)
                        import yfinance as yf
                        stock = yf.Ticker(yf_symbol)
                        hist = stock.history(period="1d", interval="1m")
                        
                        if not hist.empty:
                            last_minute_data = hist.iloc[-1]
                            # Initialize latest_data if None
                            if latest_data is None:
                                latest_data = {
                                    "symbol": symbol,
                                    "market": market,
                                    "date": last_minute_data.name.strftime('%Y-%m-%d %H:%M')
                                }

                            latest_data['price'] = float(last_minute_data['Close'])
                            latest_data['close'] = float(last_minute_data['Close'])
                            latest_data['open'] = float(last_minute_data['Open'])
                            latest_data['high'] = float(last_minute_data['High'])
                            latest_data['low'] = float(last_minute_data['Low'])
                            latest_data['volume'] = int(last_minute_data['Volume'])
                            latest_data['date'] = last_minute_data.name.strftime('%Y-%m-%d %H:%M')
                            self.logger.info(f"Yahoo minute fallback successful for {symbol}. Price: {latest_data['price']}")
                    except Exception as yf_min_e:
                        self.logger.error(f"Yahoo minute fallback failed for {symbol}: {yf_min_e}")


            # --- FINAL ENRICHMENT: Fetch Yahoo Indicators if still missing ---
            # This ensures PE, Dividend Yield, etc. are populated even if primary source lacks them.
            if latest_data:
                 # Check if we are missing key indicators
                 missing_indicators = False
                 for key in ['pe', 'dividend_yield', 'eps']:
                     if latest_data.get(key) is None:
                         missing_indicators = True
                         break
                 
                 if missing_indicators:
                     try:
                         # self.logger.info(f"Enriching {symbol} with Yahoo indicators...")
                         indicators = self.fetch_yahoo_indicators(symbol)
                         if indicators:
                             if not latest_data.get('pe') and indicators.get('pe'): 
                                 latest_data['pe'] = indicators.get('pe')
                             if not latest_data.get('dividend_yield') and indicators.get('dividend_yield'): 
                                 latest_data['dividend_yield'] = indicators.get('dividend_yield')
                             if not latest_data.get('eps') and indicators.get('eps'): 
                                 latest_data['eps'] = indicators.get('eps')
                             if not latest_data.get('market_cap') and indicators.get('market_cap'): 
                                 latest_data['market_cap'] = indicators.get('market_cap')
                             if not latest_data.get('pb') and indicators.get('pb'):
                                 latest_data['pb'] = indicators.get('pb')
                             if not latest_data.get('prev_close') and indicators.get('prev_close'):
                                 latest_data['prev_close'] = indicators.get('prev_close')

                     except Exception as ye:
                         self.logger.warning(f"Yahoo enrichment failed for {symbol}: {ye}")

            # --- RETRY CALCULATION: If Change is still 0, try calc using enriched prev_close ---
            if latest_data:
                price_is_zero = latest_data.get('price', 0) == 0 and latest_data.get('close', 0) == 0
                change_is_zero = latest_data.get('change', 0) == 0 and latest_data.get('pct_change', 0) == 0
                
                self.logger.info(f"DEBUG: Recalc Check - PriceZero:{price_is_zero}, ChangeZero:{change_is_zero}, PrevClose:{latest_data.get('prev_close')}, Price:{latest_data.get('price')}")

                if (price_is_zero or change_is_zero):
                    p_close = latest_data.get('prev_close', 0)
                    curr_price = latest_data.get('price', 0)
                    
                    if curr_price > 0 and p_close and p_close > 0:
                        recalc_change = curr_price - p_close
                        recalc_pct = (recalc_change / p_close) * 100
                        
                        if change_is_zero:
                            latest_data['change'] = recalc_change
                            latest_data['pct_change'] = recalc_pct
                            self.logger.info(f"Fixed 0% change for {symbol} (Post-Enrichment): {recalc_pct:.2f}%")

            # ✅ 所有数据已通过Line 890的save_to_db()走ETL流程
            # 不再需要直接保存到MarketDataDaily/MarketSnapshot

            # --- FINAL: Data Validation & Return ---
            if latest_data:
                # 数据验证和清理
                from data_validator import get_validator
                validator = get_validator()
                is_valid = validator.validate_and_log(symbol, latest_data, self.logger)
                
                if not is_valid:
                    self.logger.warning(f"Data quality issues for {symbol}, but returning anyway")
                
                latest_data = validator.sanitize_data(latest_data)
                return latest_data
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error fetching latest data for {symbol}: {e}")
        return None

                    
    def fetch_hk_index_realtime(self, symbol: str) -> dict:
        """
        HK指数实时数据获取（统一架构：只获取数据，不判断状态，不保存数据库）
        
        混合策略：
        - 主策略：AkShare spot_sina (实时快照)
        - 辅助：yfinance 1分钟数据
        
        Returns:
            dict with keys: symbol, market, price, close, open, high, low, 
                           change, pct_change, volume, date
            None if all sources fail
        """
        try:
            # === 主策略：AkShare实时快照 ===
            self.logger.info(f"Fetching HK index realtime (AkShare spot): {symbol}")
            
            try:
                df = ak.stock_hk_index_spot_sina()
                matches = df[df['代码'].str.upper() == symbol.upper()]
                
                if not matches.empty:
                    row = matches.iloc[0]
                    
                    # 转换为统一dict格式
                    from datetime import datetime
                    import pytz
                    hk_tz = pytz.timezone('Asia/Hong_Kong')
                    now = datetime.now(hk_tz)
                    
                    current_price = float(row['最新价'])
                    
                    # 🔥 修复：不信任API的涨跌额/涨跌幅，从数据库查询前一日收盘价计算
                    change = 0
                    pct_change = 0
                    prev_close = None
                    
                    try:
                        from database import engine
                        from sqlmodel import Session, select
                        
                        with Session(engine) as session:
                            prev_record = session.exec(
                                select(MarketDataDaily).where(
                                    MarketDataDaily.symbol == symbol,
                                    MarketDataDaily.market == 'HK'
                                ).order_by(MarketDataDaily.date.desc()).limit(1)
                            ).first()
                            
                            if prev_record and prev_record.close > 0:
                                prev_close = prev_record.close
                                change = current_price - prev_close
                                pct_change = (change / prev_close) * 100
                                self.logger.info(f"✅ HK Index {symbol}: calculated change from DB: {change:.2f} ({pct_change:.2f}%)")
                            else:
                                # Fallback: 使用今开作为参考（不准确但总比0好）
                                open_price = float(row['今开'])
                                if open_price > 0:
                                    change = current_price - open_price
                                    pct_change = (change / open_price) * 100
                                    self.logger.warning(f"HK Index {symbol}: using open as fallback: {change:.2f} ({pct_change:.2f}%)")
                    except Exception as calc_e:
                        self.logger.warning(f"Failed to calculate change for {symbol}: {calc_e}")
                    
                    result = {
                        'symbol': symbol,
                        'market': 'HK',
                        'price': current_price,
                        'close': current_price,
                        'open': float(row['今开']),
                        'high': float(row['最高']),
                        'low': float(row['最低']),
                        'change': change,
                        'pct_change': pct_change,
                        'prev_close': prev_close,
                        'volume': 0,  # 指数无成交量
                        'date': now.strftime('%Y-%m-%d %H:%M:%S'),
                        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    self.logger.info(f"✅ AkShare spot: {symbol} = {result['price']}")
                    return result
                    
            except Exception as e:
                self.logger.warning(f"AkShare spot failed for {symbol}: {e}")
            
            # === Fallback：yfinance分钟数据 ===
            self.logger.info(f"Falling back to yfinance minute for {symbol}")
            
            from symbols_config import get_yfinance_symbol
            import yfinance as yf
            
            yf_symbol = get_yfinance_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period='1d', interval='1m')
            
            if not hist.empty:
                last_row = hist.iloc[-1]
                last_time = hist.index[-1]
                current_price = float(last_row['Close'])
                
                # 🔧 修复：查询数据库获取前一日收盘价来计算涨跌幅
                prev_close = None
                change = 0
                pct_change = 0
                
                try:
                    from database import engine
                    from sqlmodel import Session, select
                    
                    with Session(engine) as session:
                        # 尝试从Daily表查询前一日收盘价
                        prev_record = session.exec(
                            select(MarketDataDaily).where(
                                MarketDataDaily.symbol == symbol,
                                MarketDataDaily.market == 'HK'
                            ).order_by(MarketDataDaily.date.desc()).limit(1)
                        ).first()
                        
                        if prev_record and prev_record.close > 0:
                            prev_close = prev_record.close
                            change = current_price - prev_close
                            pct_change = (change / prev_close) * 100
                            self.logger.info(f"✅ Calculated change for {symbol}: {change:.2f} ({pct_change:.2f}%)")
                        else:
                            # Fallback: 使用yfinance的open作为参考
                            if float(last_row['Open']) > 0:
                                prev_close = float(last_row['Open'])
                                change = current_price - prev_close
                                pct_change = (change / prev_close) * 100
                                self.logger.warning(f"Using open as prev_close for {symbol}: {change:.2f} ({pct_change:.2f}%)")
                except Exception as calc_e:
                    self.logger.warning(f"Failed to calculate change for {symbol}: {calc_e}")
                
                result = {
                    'symbol': symbol,
                    'market': 'HK',
                    'price': current_price,
                    'close': current_price,
                    'open': float(last_row['Open']),
                    'high': float(last_row['High']),
                    'low': float(last_row['Low']),
                    'volume': int(last_row['Volume']),
                    'date': last_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': last_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'prev_close': prev_close,
                    'change': change,
                    'pct_change': pct_change
                }
                
                self.logger.info(f"✅ yfinance minute fallback: {symbol} = {result['price']}")
                return result
            
            self.logger.error(f"Both AkShare and yfinance failed for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in fetch_hk_index_realtime: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def fetch_from_tencent(self, symbol: str) -> dict:
        """
        Fetch real-time snapshot from Tencent (Qt)
        Symbol should be prefixed, e.g. 'hkHSTECH', 'hkHSI', 'sh600519'
        """
        try:
            import requests
            url = f"http://qt.gtimg.cn/q={symbol}"
            # Use random UA to be safe
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=2)
            if resp.status_code != 200:
                return None
            
            content = resp.text.strip()
            # Format: v_hkHSTECH="100~恒生科技指数~HSTECH~5498.420~5638.050~5562.670~..."
            if '="' not in content:
                return None
                
            data_str = content.split('="')[1].strip('";')
            parts = data_str.split('~')
            
            if len(parts) < 30:
                return None
                
            # Parse (Standard GTimg format)
            # 1: Name 2: Code 3: Price 4: PrevClose 5: Open
            # 30: Time (YYYY/MM/DD HH:MM:SS) 31: Change 32: PctChange
            
            price = float(parts[3])
            prev_close = float(parts[4])
            open_p = float(parts[5])
            time_str = parts[30]
            # vol_str = parts[6] 
            # For HK Indices, parts[6] seems to be Turnover (money) or Volume (shares)?
            # Sina HSTECH: 56964428 (~56M)
            # Tencent HSTECH: 5696442.8498 (~5.6M) -> Maybe Lots? Or 1/100?
            # Usually users just want a relative magnitude.
            # Let's take parts[6] as Volume.
            vol_raw = float(parts[6]) if parts[6] else 0
            change = float(parts[31])
            pct_change = float(parts[32])
            
            return {
                "symbol": symbol, 
                "price": price,
                "close": price,
                "prev_close": prev_close,
                "open": open_p,
                "high": 0, 
                "low": 0,
                "change": change,
                "pct_change": pct_change,
                "volume": int(vol_raw), 
                "date": time_str,
                "market": "HK" if "hk" in symbol else "CN"
            }
            
        except Exception as e:
            self.logger.error(f"Tencent fetch failed for {symbol}: {e}")
            return None

    def fetch_cn_daily_data(self, symbol: str) -> pd.DataFrame:
        """
        CN日线数据：yfinance优先，AkShare备用
        """
        try:
            # === 优先使用 yfinance ===
            self.logger.info(f"Fetching CN daily data (yfinance primary): {symbol}")
            df = self._fetch_fallback_yfinance(symbol, "CN")
            
            if df is not None and not df.empty:
                self.logger.info(f"✅ yfinance CN daily: {len(df)} records for {symbol}")
                return df
            
            # === 备用：AkShare ===
            self.logger.warning(f"yfinance empty for CN {symbol}, trying AkShare...")
            code = symbol.replace('.sh', '').replace('.sz', '').replace('.SH', '').replace('.SZ', '').zfill(6)
            self.logger.info(f"Falling back to AkShare: {symbol} → {code}")
            
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if df is not None and not df.empty and '日期' in df.columns:
                df = self.standardize_akshare_fields(df)
                self.logger.info(f"✅ AkShare CN daily (fallback): {len(df)} records for {symbol}")
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error fetching CN daily data for {symbol}: {str(e)}")
            return pd.DataFrame()


    def fetch_hk_daily_data(self, symbol: str) -> pd.DataFrame:
        """
        HK日线数据：指数用yfinance（更稳定），个股用东方财富
        
        混合策略：
        - HK指数：主用yfinance，备用AkShare（因AkShare API不稳定）
        - HK个股：主用AkShare东方财富，备用yfinance
        """
        try:
            from symbols_config import is_index, get_akshare_symbol
            
            if is_index(symbol):
                # === HK指数：优先yfinance（更稳定） ===
                self.logger.info(f"Fetching HK index daily (yfinance primary): {symbol}")
                
                try:
                    df = self._fetch_fallback_yfinance(symbol, "HK")
                    if df is not None and not df.empty:
                        self.logger.info(f"✅ yfinance HK index daily: {len(df)} records for {symbol}")
                        return df
                except Exception as e:
                    self.logger.warning(f"yfinance failed for HK index {symbol}: {e}")
                
                # Fallback: AkShare (但已知不稳定)
                akshare_code = get_akshare_symbol(symbol)
                self.logger.info(f"Falling back to AkShare: {symbol} → {akshare_code}")
                
                try:
                    df = ak.stock_hk_index_daily_sina(symbol=akshare_code)
                    if df is not None and not df.empty:
                        df = self.standardize_akshare_fields(df)
                        
                        if 'prev_close' not in df.columns or df['prev_close'].isna().all():
                            df['prev_close'] = df['close'].shift(1)
                            self.logger.info(f"✅ 计算prev_close for {symbol} using shift()")
                        
                        self.logger.info(f"✅ AkShare HK index daily (fallback): {len(df)} records for {symbol}")
                        return df
                except Exception as e:
                    self.logger.error(f"AkShare also failed for {symbol} (code={akshare_code}): {e}")
                    return pd.DataFrame()  # 两个都失败，返回空
            
            else:
                # === HK个股：yfinance优先，AkShare备用 ===
                self.logger.info(f"Fetching HK stock daily (yfinance primary): {symbol}")
                
                # 优先使用 yfinance
                df = self._fetch_fallback_yfinance(symbol, "HK")
                if df is not None and not df.empty:
                    self.logger.info(f"✅ yfinance HK stock daily: {len(df)} records for {symbol}")
                    return df
                
                # 备用：AkShare东方财富API
                self.logger.warning(f"yfinance empty for HK stock {symbol}, trying AkShare...")
                code = symbol.replace('.hk', '').replace('.HK', '').zfill(5)
                self.logger.info(f"Falling back to AkShare: {symbol} → {code}")
                
                df = ak.stock_hk_hist(symbol=code, period="daily")
                
                if df is not None and not df.empty and '日期' in df.columns:
                    df = self.standardize_akshare_fields(df)
                    
                    # ✅ 计算prev_close（如果数据源没有提供）
                    if 'prev_close' not in df.columns or df['prev_close'].isna().all():
                        df['prev_close'] = df['close'].shift(1)
                        self.logger.info(f"✅ 计算prev_close for {symbol} using shift()")
                    
                    self.logger.info(f"✅ AkShare HK stock daily (fallback): {len(df)} records for {symbol}")
                    return df
                
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Error in fetch_hk_daily_data: {e}")
            return self._fetch_fallback_yfinance(symbol, "HK")

    def _get_latest_daily_date(self, symbol: str, market: str):
        """
        查询数据库中symbol的最新日期
        用于智能选择yfinance的period参数
        
        Returns:
            datetime or None: 最新日期，如果没有数据则返回None
        """
        try:
            from database import engine
            from models import MarketDataDaily
            from sqlmodel import Session, select
            from datetime import datetime
            
            with Session(engine) as session:
                stmt = select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol,
                    MarketDataDaily.market == market
                ).order_by(MarketDataDaily.timestamp.desc()).limit(1)
                
                latest_record = session.exec(stmt).first()
                
                if latest_record and latest_record.timestamp:
                    # timestamp字段是字符串格式 "YYYY-MM-DD HH:MM:SS"
                    return datetime.strptime(latest_record.timestamp[:10], '%Y-%m-%d')
                
                return None
        except Exception as e:
            self.logger.warning(f"Failed to get latest date for {symbol}: {e}")
            return None

    def to_akshare_us_symbol(self, symbol, for_minute=False):
        # symbol 可能是 105.msft、106.tsm、MSFT、TSM
        if for_minute:
            # 保留前缀，转小写
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.lower()
            if symbol.upper() == "TSM":
                return "106.tsm"
            # Default fallback assumption for US mapping if prefix missing
            return "105." + symbol.lower() 
        else:
            if symbol.startswith("105.") or symbol.startswith("106."):
                return symbol.split(".")[1].upper()
            return symbol.upper()

    def _fetch_fallback_yfinance(self, symbol: str, market: str) -> pd.DataFrame:
        import yfinance as yf
        try:
            # Use symbols_config for index symbol mapping (^NDX -> ^IXIC, ^SPX -> ^GSPC)
            from symbols_config import get_yfinance_symbol
            yf_symbol = get_yfinance_symbol(symbol)  # Will map if in config, otherwise returns original
            
            # Additional market-specific mappings for stocks (not indices)
            if yf_symbol == symbol:  # Not already mapped by config
                if market == "CN":
                    if symbol.endswith('.sh'):
                        yf_symbol = symbol.replace('.sh', '.SS')
                    elif symbol.endswith('.sz'):
                        yf_symbol = symbol.replace('.sz', '.SZ')
                elif market == "HK":
                    # HK stock symbols
                    if symbol.replace('.hk', '') == '800000':
                        yf_symbol = "^HSI"
                    elif symbol.replace('.hk', '') == '800700':
                        yf_symbol = "HSTECH.HK"
                    else:
                        code = symbol.replace('.hk', '')
                        if code.isdigit():
                            yf_symbol = f"{int(code):04d}.HK"
                        else:
                            yf_symbol = f"{code}.HK"
                elif market == "US":
                    # US stock symbols: strip suffix (.OQ, .N, etc)
                    if '.' in symbol and not symbol.startswith('^'):
                         yf_symbol = symbol.split('.')[0]


            # ⚠️ DEBUG: 进入fallback yfinance
            self.logger.info(f"[DEBUG] _fetch_fallback_yfinance: symbol={symbol}, market={market}, yf_symbol={yf_symbol}")
            self.logger.info(f"Fallback: fetching {yf_symbol} via yfinance...")
            stock = yf.Ticker(yf_symbol)
            
            # ✅ 智能period选择：根据数据缺口决定获取范围
            self.logger.info(f"[DEBUG] Calling _get_latest_daily_date for {symbol}")
            latest_date = self._get_latest_daily_date(symbol, market)
            self.logger.info(f"[DEBUG] latest_date result: {latest_date}")
            
            if latest_date:
                from datetime import datetime
                gap_days = (datetime.now() - latest_date).days
                
                # 根据缺口大小选择period
                if gap_days <= 5:
                    period = "5d"
                    self.logger.info(f"Gap {gap_days} days → using period=5d")
                elif gap_days <= 30:
                    period = "1mo"
                    self.logger.info(f"Gap {gap_days} days → using period=1mo")
                elif gap_days <= 90:
                    period = "3mo"
                    self.logger.info(f"Gap {gap_days} days → using period=3mo")
                else:
                    period = "1y"
                    self.logger.info(f"Gap {gap_days} days → using period=1y (large gap)")
            else:
                # 新symbol或无历史数据：默认1个月
                period = "1mo"
                self.logger.info(f"No existing data for {symbol} → using period=1mo")
            
            # ⚠️ HOTFIX: 强制使用5d绕过智能选择问题
            # 智能选择逻辑在async环境下未能生效，暂时使用固定5d确保增量更新
            period = "5d"
            self.logger.info(f"[HOTFIX] Forcing period=5d for incremental update")
            
            hist = stock.history(period=period)
            
            if hist.empty:
                self.logger.warning(f"yfinance fallback also empty for {yf_symbol}")
                return pd.DataFrame()
            
            # Reset index to get Date
            hist = hist.reset_index()
            
            # For US market during trading hours: filter out today's data
            # yfinance returns today's real-time price with incorrect timestamp (00:00)
            if market == "US":
                from datetime import datetime, time as dtime
                import pytz
                us_tz = pytz.timezone('US/Eastern')
                us_now = datetime.now(us_tz)
                
                # Check if market is open (9:30-16:00 ET, weekdays)
                is_open = (us_now.weekday() < 5 and 
                          dtime(9, 30) <= us_now.time() < dtime(16, 0))
                
                if is_open:
                    # Filter out today's data - it's real-time price with wrong timestamp
                    today_str = us_now.strftime('%Y-%m-%d')
                    initial_len = len(hist)
                    hist = hist[~hist['Date'].dt.strftime('%Y-%m-%d').eq(today_str)]
                    filtered = initial_len - len(hist)
                    if filtered > 0:
                        self.logger.info(f"US Market OPEN: filtered out {filtered} today's data (real-time price with incorrect timestamp)")
            
            # Rename columns to match what save_to_db expects (English keys also work: open, close, etc.)
            # But let's map Date -> 时间 just in case
            hist = hist.rename(columns={'Date': 'timestamp', 'Volume': 'volume', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'})
            hist['timestamp'] = pd.to_datetime(hist['timestamp'])
            
            # Ensure naive timezone and set time to 16:00 (market close)
            if pd.api.types.is_datetime64_any_dtype(hist['timestamp']):
                hist['timestamp'] = hist['timestamp'].dt.tz_localize(None)
                # yfinance返回的日线时间是00:00，应该改为16:00（收盘时间）
                hist['timestamp'] = hist['timestamp'].apply(
                    lambda x: x.replace(hour=16, minute=0, second=0) if x.hour == 0 else x
                )
                
            # Add turnover approx if missing
            if 'turnover' not in hist.columns:
                 # Estimate turnover = close * volume
                hist['turnover'] = hist['close'] * hist['volume']
            
            # Add date column in standardized format for US market
            hist['date'] = hist['timestamp'].apply(lambda x: x.strftime('%Y-%m-%d 16:00:00'))
            
            self.logger.info(f"Fallback success for {symbol}. Got {len(hist)} rows.")
            return hist
            
        except Exception as e:
            self.logger.error(f"Fallback failed for {symbol}: {e}")
            return pd.DataFrame()

    def _fetch_fallback_yfinance_min(self, symbol: str, market: str) -> pd.DataFrame:
        """
        Fallback: Use yfinance to fetch minute data (1d, 1m).
        """
        import yfinance as yf
        try:
            # 1. Adapt Symbol for Yahoo
            yf_symbol = symbol
            if market == 'HK':
                # Existing HK logic (00700 -> 0700.HK)
                code = symbol.replace('.HK', '').replace('.hk', '')
                try:
                    code_int = int(code)
                    yf_symbol = f"{code_int:04d}.HK"
                except:
                    yf_symbol = symbol
            elif market == 'CN':
                 # Existing CN logic
                 yf_symbol = symbol.replace('.sh', '.SS').replace('.SH', '.SS') \
                                   .replace('.sz', '.SZ').replace('.SZ', '.SZ')
            elif market == 'US':
                # NEW: Remove "105." prefix for US stocks
                if '.' in symbol and symbol.split('.')[0].isdigit():
                    yf_symbol = symbol.split('.')[-1]
            
            self.logger.info(f"Fallback (Min): fetching {yf_symbol} ...")
            ticker = yf.Ticker(yf_symbol)
            # Yahoo minute data limited to 7 days usually. 
            # period='1d', interval='1m' is standard for basic realtime.
            df = ticker.history(period="1d", interval="1m")
            
            if df.empty:
                self.logger.warning(f"Fallback (Min): {yf_symbol} returned empty DataFrame")
                return pd.DataFrame()
                
            # Formatting
            df = df.reset_index()
            
            # Handle column names - yfinance uses 'Datetime' for minute data
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'timestamp'})
            elif 'Date' in df.columns:
                df = df.rename(columns={'Date': 'timestamp'})
            
            # Rename price columns - 使用英文字段名以匹配ETL
            df = df.rename(columns={
                'Open': 'open', 
                'High': 'high', 
                'Low': 'low', 
                'Close': 'close', 
                'Volume': 'volume'
            })
            
            # Add turnover if missing
            if 'turnover' not in df.columns and 'close' in df.columns:
                df['turnover'] = df['close'] * df['volume']
            
            # Ensure TZ naive - properly handle timezone-aware datetime
            if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                # Check if timezone-aware
                if df['timestamp'].dt.tz is not None:
                    # Remove timezone by converting to naive datetime
                    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                
            self.logger.info(f"Fallback (Min): {yf_symbol} success, {len(df)} records")
            return df
        except Exception as e:

            self.logger.error(f"Fallback min error for {symbol}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return pd.DataFrame()

    def fetch_us_daily_data(self, symbol: str) -> pd.DataFrame:
        """
        US日线数据：yfinance优先，AkShare备用
        """
        try:
            # 标准化US股票代码：移除交易所后缀 (.OQ, .O, .N等)
            clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
            
            # === 优先使用 yfinance（所有US股票和指数） ===
            self.logger.info(f"Fetching US daily data (yfinance primary): {symbol}")
            df = self._fetch_fallback_yfinance(symbol, "US")
            
            if df is not None and not df.empty:
                self.logger.info(f"✅ yfinance US daily: {len(df)} records for {symbol}")
                return df
            
            # === 备用：AkShare（仅用于个股，不用于指数） ===
            if clean_symbol.startswith("^"):
                # 指数只用yfinance，不用AkShare
                self.logger.warning(f"yfinance failed for US index {symbol}, no AkShare fallback for indices")
                return pd.DataFrame()
            
            self.logger.warning(f"yfinance empty for US {symbol}, trying AkShare...")
            self.logger.info(f"Falling back to AkShare: {symbol} → {clean_symbol}")
            
            df = ak.stock_us_daily(symbol=clean_symbol)
            
            if df is not None and not df.empty and '日期' in df.columns:
                df = self.standardize_akshare_fields(df)
                # 只保留最近30天
                last_date = df['timestamp'].dt.date.max()
                first_date = last_date - pd.Timedelta(days=29)
                df = df[(df['timestamp'].dt.date >= first_date) & (df['timestamp'].dt.date <= last_date)]
                
                # ✅ 计算prev_close（如果数据源没有提供）
                if 'prev_close' not in df.columns or df['prev_close'].isna().all():
                    df['prev_close'] = df['close'].shift(1)
                    self.logger.info(f"✅ 计算prev_close for {symbol} using shift()")
                
                self.logger.info(f"✅ AkShare US daily (fallback): {len(df)} records for {symbol}")
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error fetching US daily data for {symbol}: {str(e)}")
            return pd.DataFrame()

    
    def save_to_db(self, symbol: str, market: str, period_data: dict) -> None:
        """
        NEW ETL PIPELINE:
        Fetch -> Raw Table -> ETL Service -> Prod Table
        """
        try:
            # ⚠️ DEBUG: 打印period_data长度
            for period, df in period_data.items():
                if df is not None and not df.empty:
                    self.logger.info(f"[DEBUG save_to_db] {symbol} {period}: {len(df)} records")
            
             # Normalize Symbol for DB
            db_symbol = normalize_symbol_db(symbol, market)
            
            from database import get_session
            from models import RawMarketData
            from etl_service import ETLService
            from field_normalizer import FieldNormalizer  # 导入字段标准化器
            
            gen = get_session()
            session = next(gen, None)
            
            if not session:
                self.logger.error("Could not get DB session")
                return

            try:
                # Iterate periods (1d, 1m, etc)
                for period, df in period_data.items():
                    if df is None or df.empty:
                        continue
                    
                    # ✅ P0+P2: 应用字段标准化
                    self.logger.info(f"Normalizing fields for {symbol} ({period})...")
                    df, norm_report = FieldNormalizer.normalize_dataframe(
                        df, 
                        source=None,  # 自动检测
                        data_type='minute' if 'm' in period else 'daily',
                        market=market
                    )
                    
                    # 记录标准化结果
                    if norm_report.get('warnings'):
                        self.logger.warning(f"Field normalization warnings for {symbol}: {norm_report['warnings']}")
                    
                    # Convert DF to JSON-serializable list of dicts
                    # Timestamps need string conversion
                    df_json = df.copy()
                    if 'timestamp' in df_json.columns:
                        df_json['date'] = df_json['timestamp'].astype(str)
                    elif 'timestamp' in df_json.columns:
                        df_json['date'] = df_json['timestamp'].astype(str)
                    
                    # Serialize
                    payload = df_json.to_json(orient='records')
                    
                    # 1. RAW INGESTION
                    raw = RawMarketData(
                        source="fetched",
                        symbol=db_symbol,
                        market=market,
                        period=period,
                        payload=payload,
                        processed=False
                    )
                    session.add(raw)
                    session.commit()
                    session.refresh(raw)
                    
                    # ✅ 2. TRIGGER ETL (Async via Queue)
                    # 旧模式: 同步ETL,阻塞用户响应(150秒)
                    # ETLService.process_raw_data(raw.id)
                    
                    # ✅ 新模式: 异步ETL,立即返回(5秒)
                    from etl_queue import etl_queue
                    etl_queue.enqueue(raw.id)
                    self.logger.info(f"✅ 数据已保存到Raw表 (raw_id={raw.id}), ETL任务已入队")
            
            except Exception as e:
                self.logger.error(f"Ingest/ETL Loop Error: {e}")
            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Critical error in save_to_db: {e}")


    def save_fund_flow(self, symbol: str):
        # 只采集A股资金流向
        if symbol.endswith('.sh') or symbol.endswith('.sz') or symbol.endswith('.bj'):
            stock = symbol[:6]
            market = "CN"
            try:
                # Proceeded dir logic
                market_dir = os.path.join(self.output_dir, "proceeded", market)
                os.makedirs(market_dir, exist_ok=True)
                
                fund_flow_df = ak.stock_individual_fund_flow(stock=stock, market=symbol[-2:])
                if fund_flow_df is not None and not fund_flow_df.empty:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{symbol}_{market}_fund_flow_{timestamp}_V4.xlsx"
                    filepath = os.path.join(market_dir, filename)
                    fund_flow_df.to_excel(filepath, index=False)
                    self.logger.info(f"资金流向已保存到 {filepath}")
            except Exception as e:
                self.logger.error(f"资金流向获取失败: {symbol}, 原因: {e}")


    def _get_market(self, symbol):
        symbol = symbol.upper()
        if symbol.startswith("105.") or symbol.startswith("106."):
            return "US"
        elif symbol.startswith("^"):
            return "US"
        elif symbol.endswith(".HK"):
            return "HK"
        elif symbol.endswith(".SH") or symbol.endswith(".SZ"):
            return "CN"
        # US Suffixes from EastMoney search
        elif any(symbol.endswith(s) for s in [".OQ", ".N", ".AM", ".O", ".K"]):
            return "US"
        # Plain US symbols (no dot) - naive check?
        # risky if overlaps with others, but usually 3-4 chars is US if not CN/HK.
        # Let's rely on suffixes for now as SearchBar seems to provide them.
        else:
            return "Other"

    def get_stock_name(self, symbol: str) -> str:
        market = self._get_market(symbol)
        name = symbol
        
        # Helper to fetch from Tencent (qt.gtimg.cn)
        def fetch_from_tencent(code_with_prefix):
            try:
                url = f"http://qt.gtimg.cn/q={code_with_prefix}"
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    # format: v_hk00005="100~汇丰控股~..."
                    content = resp.text
                    if '="' in content:
                        data_str = content.split('="')[1].strip('";')
                        parts = data_str.split('~')
                        if len(parts) > 2:
                            return parts[1] # Name is usually at index 1
            except Exception as e:
                self.logger.error(f"Tencent fetch error for {code_with_prefix}: {e}")
            return None

        try:
            if market == "CN":
                code = symbol.replace('.sh', '').replace('.sz', '').zfill(6)
                # Try Tencent first for speed? Or keep AkShare. 
                # AkShare is reliable for CN. Keep AkShare.
                df = ak.stock_individual_info_em(symbol=code)
                if df is not None and not df.empty:
                    row = df[df['item'] == '股票简称']
                    if not row.empty:
                        name = row.iloc[0]['value']
                        
            elif market == "HK":
                # Tencent format: hk00005
                code = symbol.replace('.hk', '')
                fetched = fetch_from_tencent(f"hk{code}")
                if fetched: name = fetched
                
            elif market == "US":
                # Tencent format: usAAPL
                # Our symbol: 105.aapl or just AAPL?
                # to_akshare_us_symbol format: "105.aapl"
                # Extract clean symbol
                clean_symbol = symbol.split(".")[-1].upper() # aapl -> AAPL
                fetched = fetch_from_tencent(f"us{clean_symbol}")
                if fetched: name = fetched
                
        except Exception as e:
            self.logger.error(f"Error getting name for {symbol}: {e}")
        return name

    def _is_daily_data_current(self, symbol: str, market: str) -> bool:
        """
        Check if we already have daily data for the 'current' trading day.
        """
        try:
            from database import engine
            from models import MarketDataDaily
            from sqlmodel import Session, select, func
            
            # Determine 'Expected' Date
            # Simple logic: 
            # CN/HK: Today's date (Asia/Shanghai)
            # US: Today's date (US/Eastern)
            # If market is Open, maybe we DON'T skip? 
            # User said "If already exists, don't duplicate". This usually refers to historical backfill.
            # But if today is trading, do we want to re-fetch to get close price updates?
            # User phrase: "marketdata_full, same date only save one. If exists, don't fetch."
            # This implies if we have a record for TODAY, we assume it's done?
            # Or maybe just for historical?
            # Let's be safe: If we have a record for TODAY, and market is CLOSED, definitely skip.
            # If market is OPEN, we might want to update? 
            # But let's follow instruction "If exists... don't fetch".
            
            now = datetime.now(pytz.timezone('Asia/Shanghai'))
            expected_date = now.date()
            
            if market == 'US':
                expected_date = now.astimezone(pytz.timezone('US/Eastern')).date()
            
            with Session(engine) as session:
                # Check for 1d record with Date starts with YYYY-MM-DD
                # Since date is String, use startswith
                date_prefix = expected_date.strftime("%Y-%m-%d")
                
                # Check directly
                statement = select(MarketDataDaily).where(
                    MarketDataDaily.symbol == normalize_symbol_db(symbol, market),
                    MarketDataDaily.market == market,
                    MarketDataDaily.date.startswith(date_prefix)
                )
                existing = session.exec(statement).first()
                
                if existing:
                    return True
                    
        except Exception as e:
            self.logger.error(f"Check existing failed for {symbol}: {e}")
            
        return False

    # NOTE: Modified fetch_all_stocks to accept an optional 'markets' filter and 'specific_symbols'
    def fetch_all_stocks(self, periods, target_markets=None, specific_symbols: list = None):
        import time, random
        target_list = specific_symbols if specific_symbols is not None else self.symbols
        self.logger.info(f"Starting to fetch data for {len(target_list)} stocks, periods: {periods}")
        
        consecutive_fails = 0
        
        for i, symbol in enumerate(target_list):
            # Safety: Random delay between requests
            if i > 0:
                time.sleep(random.uniform(1.0, 3.0))
            
            # Circuit Breaker
            if consecutive_fails >= 5:
                self.logger.warning("Circuit Breaker Triggered: Too many failures. Cooling down for 60s...")
                time.sleep(60)
                consecutive_fails = 0 # Reset

            market = self._get_market(symbol)
            if target_markets and market not in target_markets:
                continue
                
            # --- OPTIMIZATION: Skip if Daily Data Exists ---
            if self._is_daily_data_current(symbol, market):
                self.logger.info(f"Skipping Daily Fetch for {symbol}: Data for today already exists.")
                # We can still fetch minute data if needed, but usually 'fetch_all_stocks' is for sync
                # If minute data is needed, we proceed? 
                # User said "marketdata_full... same date only save one".
                # Let's skip DAILY fetch but maybe allow Minute?
                # But logic below mixes them.
                # Let's set a flag to skip daily part.
                skip_daily = True
            else:
                skip_daily = False
                
            period_data = {}

            if market == "US":
                symbol_daily = self.to_akshare_us_symbol(symbol, for_minute=False)
                symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                # 日线
                if not skip_daily:
                    daily_df = self.fetch_us_daily_data(symbol_daily)
                    if daily_df is not None and not daily_df.empty:
                        period_data['1d'] = daily_df
                        self.save_to_db(symbol, market, {'1d': daily_df}) # Save daily data
                # 分钟线
                df_1min = self.fetch_us_min_data(symbol_min)
                if df_1min is not None and not df_1min.empty:
                    period_data['1min'] = df_1min
                    self.save_to_db(symbol, market, {'1min': df_1min}) # Save minute data
            elif market == "CN":
                if not skip_daily:
                    daily_df = self.fetch_cn_daily_data(symbol)
                    if daily_df is not None and not daily_df.empty:
                        period_data['1d'] = daily_df
                        self.save_to_db(symbol, market, {'1d': daily_df}) # Save daily data
                else:
                    daily_df = None
                # Fund flow
                self.save_fund_flow(symbol) 
            elif market == "HK":
                if not skip_daily:
                    daily_df = self.fetch_hk_daily_data(symbol)
                    if daily_df is not None and not daily_df.empty:
                        period_data['1d'] = daily_df
                        self.save_to_db(symbol, market, {'1d': daily_df}) # Save daily data
                else: 
                    daily_df = None
            else:
                daily_df = None
                
            # CRITICAL FIX: Also fetch "Latest Snapshot" for Watchlist display (Real-time price)
            # Historical daily data often lags by 1 day or doesn't have intra-day 'change'.
            try:
                snapshot = self.fetch_latest_data(symbol, market, force_refresh=True)
                if snapshot:
                    # We inject this as a special updates to the DB directly, 
                    # ensuring the Watchlist has valid Price/Change.
                    # Since we are already creating period_data, we can't easily mix Dict snapshot with DataFrame history.
                    # Best to call a helper to save this snapshot.
                    from models import MarketDataDaily
                    from sqlmodel import select
                    from datetime import datetime
                    from database import get_session # Use get_session for consistency
                    
                    gen = get_session()
                    session = next(gen, None)
                    if not session:
                        self.logger.error("Could not get DB session for snapshot update")
                    else:
                        try:
                            stmt = select(MarketDataDaily).where(
                                MarketDataDaily.symbol == normalize_symbol_db(symbol, market),
                                MarketDataDaily.market == market
                            ).order_by(MarketDataDaily.date.desc())
                            existing = session.exec(stmt).first()
                            
                            # If no latest data, or snapshot is newer? 
                            # Just overwrite/update the latest 1d record to start with.
                            if not existing:
                                existing = MarketDataDaily(
                                    symbol=normalize_symbol_db(symbol, market), market=market, period='1d',
                                    date=snapshot['date'],
                                    open=snapshot['open'], high=snapshot['high'], low=snapshot['low'], close=snapshot['close'],
                                    volume=snapshot['volume'],
                                    pct_change=snapshot.get('pct_change'),
                                    change=snapshot.get('change'),
                                    updated_at=datetime.now()
                                )
                                session.add(existing)
                            else:
                                # Update fields
                                existing.close = snapshot['close']
                                existing.pct_change = snapshot.get('pct_change')
                                existing.change = snapshot.get('change')
                                existing.volume = snapshot['volume'] # Cumulative volume
                                existing.date = snapshot['date'] # Update Time to latest
                                existing.updated_at = datetime.now()
                                session.add(existing)
                            session.commit()
                            self.logger.info(f"Updated Snapshot for {symbol}")
                        except Exception as e:
                            session.rollback()
                            self.logger.error(f"Snapshot DB update failed: {e}")
                        finally:
                            session.close()

            except Exception as e:
                self.logger.error(f"Snapshot fetch failed in batch: {e}")


            # 各分钟线 (US logic in original code only loops if periods passed, but US calc above did 1min explicitly)
            # Original code logic:
            # For each period in periods:
            #   fetch min data
            
            for period in periods:
                df = None
                if market == "US" and period == "1":
                    # Already fetched above potentially, but let's follow logic
                    # Original code fetched 1min above for US regardless of 'periods' arg? 
                    # Actually original code:
                    # if market == "US": ... fetch 1min ... period_data['1min'] = ...
                    # then loop periods...
                    # if market == "US" and period == "1": fetch_us_min_data(symbol)
                    # It seems redundant or specific.
                    # Let's trust original logic but ensure we don't double fetch if 1min is already there.
                    if '1min' in period_data:
                        df = period_data['1min']
                    else:
                        symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                        df = self.fetch_us_min_data(symbol_min)
                        if df is not None and not df.empty:
                            df = self._fix_open_price(df)
                            period_data[f'{period}min'] = df
                            self.save_to_db(symbol, market, {f'{period}min': df}) # Save minute data

                elif market == "HK":
                    df = self.fetch_hk_min_data(symbol, period=period)
                    if df is not None and not df.empty:
                        df = self._fix_open_price(df)
                        period_data[f'{period}min'] = df
                        self.save_to_db(symbol, market, {f'{period}min': df}) # Save minute data
                elif market == "CN":
                    df = self.fetch_cn_min_data(symbol, period=period)
                    if df is not None and not df.empty:
                        df = self._fix_open_price(df)
                        period_data[f'{period}min'] = df
                        self.save_to_db(symbol, market, {f'{period}min': df}) # Save minute data
                
            # Saving to Excel is now separate from DB save, and uses period_data
            if period_data:
                self._save_stock_to_excel(symbol, market, period_data)

    def fetch_single_stock(self, symbol: str, periods=None):
        if periods is None:
            periods = ['1d', '1', '5']
            
        market = self._get_market(symbol)
        self.logger.info(f"Fetching single stock {symbol} ({market})...")
        
        period_data = {}

        # 1. Daily Data
        daily_df = None
        if market == "US":
            symbol_daily = self.to_akshare_us_symbol(symbol, for_minute=False)
            daily_df = self.fetch_us_daily_data(symbol_daily)
        elif market == "CN":
            daily_df = self.fetch_cn_daily_data(symbol)
        elif market == "HK":
            daily_df = self.fetch_hk_daily_data(symbol)
            
        if daily_df is not None and not daily_df.empty:
            period_data['1d'] = daily_df
            self.save_to_db(symbol, market, {'1d': daily_df}) # Save daily data

        # 2. Minute Data
        # Only fetch '1' and '5' for efficiency if not specified
        target_periods = [p for p in periods if p != '1d']
        
        for period in target_periods:
            df = None
            if market == "US":
                # For US minute, we use the specific symbol format if needed, or just symbol?
                # fetch_us_min_data uses 'symbol' argument and calls stock_us_hist_min_em(symbol=symbol)
                # We need to make sure we pass what it expects.
                # fetch_all_stocks passed 'symbol_min' for 1min? 
                # Let's check fetch_all_stocks again. 
                # It did: symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                # then self.fetch_us_min_data(symbol_min)
                symbol_min = self.to_akshare_us_symbol(symbol, for_minute=True)
                df = self.fetch_us_min_data(symbol_min)
            elif market == "HK":
                df = self.fetch_hk_min_data(symbol, period=period)
            elif market == "CN":
                df = self.fetch_cn_min_data(symbol, period=period)
            
            if df is not None and not df.empty:
                df = self._fix_open_price(df)
                period_data[f'{period}min'] = df
                self.save_to_db(symbol, market, {f'{period}min': df}) # Save minute data

        # 3. Save
        if period_data:
            # We skip Excel for single stock fetch to save time? Or keep it?
            # Creating excel for every single add might be slow. Let's start with DB only for speed.
            # self._save_stock_to_excel(symbol, market, period_data) 
            
            # Log counts
            counts = {k: len(v) for k, v in period_data.items()}
            self.logger.info(f"Single stock fetch success for {symbol}: {counts} records.")
            return True
        else:
            self.logger.warning(f"Single stock fetch returned NO data for {symbol}")
        return False

    def _save_stock_to_excel(self, symbol, market, period_data):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        market_dir = os.path.join(self.output_dir, market)
        os.makedirs(market_dir, exist_ok=True)
        filename = f"{symbol}_{market}_minute_data_{timestamp}_V4.xlsx"
        filepath = os.path.join(market_dir, filename)
        sheet_order = ['1d', '30min', '15min', '5min', '1min']
        ordered_keys = [k for k in sheet_order if k in period_data] + [k for k in period_data if k not in sheet_order]
        try:
            with pd.ExcelWriter(filepath) as writer:
                for period in ordered_keys:
                    df = period_data[period]
                    df.to_excel(writer, sheet_name=period, index=False)
            self.logger.info(f"Data for {symbol} saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save excel for {symbol}: {e}")

    def _fix_open_price(self, df):
        df = df.copy()
        open_col = "开盘"

        close_col = "收盘"
        if open_col in df.columns and close_col in df.columns:
            for i in range(1, len(df)):
                try:
                    if float(df.iloc[i][open_col]) == 0:
                        col_idx = df.columns.get_loc(open_col)
                        df.iloc[i, col_idx] = df.iloc[i-1][close_col]
                except Exception:
                    continue
        return df


    def to_akshare_us_symbol(self, s: str, for_minute: bool = False) -> str:
        """
        Convert potentially messy symbol to AkShare US format.
        Input: 'MSFT', '105.MSFT', 'MSFT.OQ'
        Output: '105.msft' (minute) or '105.MSFT' (daily)
        """
        s = s.upper() # Ensure upper first for comparisons
        # Clean suffix
        s_clean = s
        if s.endswith(".OQ") or s.endswith(".N") or s.endswith(".K"):
            s_clean = s.split('.')[0]
        
        s = s_clean
        prefix = "105." 
        
        # Already has prefix?
        if s.startswith("105.") or s.startswith("106."):
            if for_minute:
                return s.lower()
            return s.split(".")[1].upper()

        if s == "TSM": return "106.tsm" if for_minute else "TSM"
        
        if for_minute:
            return f"{prefix}{s.lower()}"
        else:
            return s

    def fetch_yahoo_indicators(self, symbol: str) -> dict:
        """
        Fetch supplementary indicators (PE, Dividend, etc.) and real-time quote from Yahoo Finance.
        Useful when AkShare lacks this specific metadata (like TTM Dividend Yield).
        """
        import yfinance as yf
        try:
            # Convert symbol to Yahoo format
            yf_symbol = symbol
            if symbol.endswith('.sh'):
                yf_symbol = symbol.replace('.sh', '.SS')
            elif symbol.endswith('.sz'):
                yf_symbol = symbol.replace('.sz', '.SZ')
            elif symbol.endswith('.hk'):
                try:
                    code = symbol.replace('.hk', '')
                    yf_symbol = f"{int(code):04d}.HK"
                except:
                    yf_symbol = symbol
            elif symbol.startswith('105.') or symbol.startswith('106.'):
                # US Stock
                yf_symbol = symbol.split('.')[-1].upper()
            elif symbol.startswith('^'):
                yf_symbol = symbol
            else:
                 # Clean US suffix like .OQ, .N for Yahoo
                 if symbol.endswith(".OQ") or symbol.endswith(".N"):
                     yf_symbol = symbol.split('.')[0]
            
            self.logger.info(f"Fetching Yahoo indicators for {yf_symbol}...")
            # 限流
            self.rate_limiter.wait_if_needed(symbol, 'yfinance')
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if not info:
                return {}
            
            return {
                "pe": info.get("trailingPE") or info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
                "prev_close": info.get("previousClose"),
                "currentPrice": info.get("currentPrice"),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"), # Alias for compatibility
                "open": info.get("open") or info.get("regularMarketOpen"),
                "high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "longName": info.get("longName"),
                "eps": info.get("trailingEps") or info.get("forwardEps")
            }
        except Exception as e:
            self.logger.error(f"Yahoo Fetch Failed: {e}")
            return {}

    # --- Refactor: New Async-Compatible Methods ---

    def get_db_snapshot(self, symbol: str, market: str):
        """
        Rule 3 & 4: Pure DB Read + Freshness Check.
        Returns: (data_dict, needs_update_bool)
        
        ✅ 修复：从MarketSnapshot表读取（而非MarketDataDaily）
        """
        from market_schedule import MarketSchedule
        from datetime import datetime, timedelta
        from sqlmodel import Session, select
        from models import MarketSnapshot
        
        with Session(self.engine) as session:
            # ✅ 从MarketSnapshot表读取
            latest_snapshot = session.exec(
                select(MarketSnapshot)
                .where(MarketSnapshot.symbol == normalize_symbol_db(symbol, market))
                .where(MarketSnapshot.market == market)
            ).first()
            
            if not latest_snapshot:
                return None, True 
            
            # Check Stale
            last_time = latest_snapshot.updated_at if latest_snapshot.updated_at else datetime.now() - timedelta(days=1)
            is_stale = MarketSchedule.is_stale(last_time, market, ttl_seconds=60)
            
            # Convert to dict
            data = {
                "symbol": latest_snapshot.symbol,
                "price": latest_snapshot.price,
                "change": latest_snapshot.change,
                "pct_change": latest_snapshot.pct_change,
                "volume": latest_snapshot.volume,
                "market": market,
                "date": latest_snapshot.date,
                "pe": latest_snapshot.pe,
                "dividend_yield": latest_snapshot.dividend_yield,
                "open": latest_snapshot.open,
                "high": latest_snapshot.high,
                "low": latest_snapshot.low,
                "prev_close": latest_snapshot.prev_close
            }
            return data, is_stale

    def sync_market_data(self, symbol: str, market: str):
        """
        Rule 4: API Fetch -> Write DB.
        Should be called by Background Task.
        """
        self.fetch_latest_data(symbol, market, force_refresh=True)

    async def close(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()

    def repair_daily_data(self, symbol: str, market: str) -> dict:
        """
        Verify and repair missing change/pct_change in MarketDataDaily.
        Returns dict with status and fixed_count.
        """
        try:
            from database import engine
            from models import MarketDataDaily
            from sqlmodel import select, col, Session
            
            with Session(engine) as session:

                db_symbol = normalize_symbol_db(symbol, market)
                fixed_count = 0
                
                # --- 1. MarketDataDaily Repair ---
                # Use ILIKE for case-insensitive match to find bad symbols
                records = session.exec(
                    select(MarketDataDaily)
                    .where(MarketDataDaily.symbol.ilike(db_symbol), MarketDataDaily.market == market)
                    .order_by(MarketDataDaily.date.asc())
                ).all()
                
                if records:
                    for i in range(len(records)):
                        curr = records[i]
                        is_modified = False
                        
                        # A. Fix Symbol Case
                        if curr.symbol != db_symbol:
                            curr.symbol = db_symbol
                            is_modified = True
                            fixed_count += 1
                            
                        # A2. Fix Timestamp for Market Close Accuracy
                        # CN -> 15:00, HK -> 16:00, US -> 16:00 (Check timezone)
                        try:
                             # Handle Date String
                             d_str = str(curr.date)
                             new_d_str = d_str
                             
                             if market == 'CN' and d_str.endswith('00:00:00'):
                                 new_d_str = d_str.replace('00:00:00', '15:00:00')
                             elif market == 'HK' and d_str.endswith('00:00:00'):
                                 new_d_str = d_str.replace('00:00:00', '16:00:00')
                             elif market == 'US':
                                 # US Complex logic: 
                                 # 1. If 00:00:00 -> Set to 16:00:00 (Same Day)
                                 if d_str.endswith('00:00:00'):
                                     new_d_str = d_str.replace('00:00:00', '16:00:00')
                                 # 2. If 04:00/05:00/06:00 -> Likely BJ time for next day -> Shift back to prev day 16:00
                                 elif ' 04:' in d_str or ' 05:' in d_str or ' 06:' in d_str:
                                     # Parse, subtract day, set 16:00
                                     dt = pd.to_datetime(d_str) - pd.Timedelta(days=1)
                                     new_d_str = dt.strftime('%Y-%m-%d 16:00:00')
                             
                             if new_d_str != d_str:
                                 curr.date = new_d_str
                                 is_modified = True
                                 fixed_count += 1
                        except Exception as date_e:
                            self.logger.error(f"Date repair failed for {curr.date}: {date_e}")

                        # B. Fix Missing Change/PctChange
                        needs_repair = (curr.change is None or curr.change == 0) and \
                                       (curr.pct_change is None or curr.pct_change == 0) and \
                                       (curr.close is not None and curr.close > 0)
                        
                        if needs_repair:
                            prev_close = None
                            if i > 0:
                                 if records[i-1].close and records[i-1].close > 0:
                                     prev_close = records[i-1].close
                            
                            if prev_close:
                                change_val = curr.close - prev_close
                                pct_val = (change_val / prev_close) * 100
                                
                                curr.change = round(change_val, 4)
                                curr.pct_change = round(pct_val, 4)
                                curr.updated_at = datetime.now()
                                is_modified = True
                                fixed_count += 1
                        
                        if is_modified:
                            session.add(curr)

                # --- 2. MarketDataMinute Repair (Symbol Only) ---
                # Minute data heavily relies on prev close for pct_change which is harder to track in bulk efficiently here.
                # We focus on fixing the Symbol case to ensure visibility.
                min_records = session.exec(
                    select(MarketDataMinute)
                    .where(MarketDataMinute.symbol.ilike(db_symbol), MarketDataMinute.market == market)
                ).all()
                
                min_fixed = 0
                if min_records:
                    for mm in min_records:
                        if mm.symbol != db_symbol:
                            mm.symbol = db_symbol
                            session.add(mm)
                            min_fixed += 1
                
                if fixed_count > 0 or min_fixed > 0:
                    session.commit()
                    self.logger.info(f"Repaired {fixed_count} daily + {min_fixed} minute records for {db_symbol}")
                    return {"status": "success", "fixed_daily": fixed_count, "fixed_minute": min_fixed, "symbol": db_symbol}
                else:
                    return {"status": "success", "fixed_count": 0, "symbol": db_symbol, "message": "No repairs needed"}
                
        except Exception as e:
            self.logger.error(f"Error repairing data for {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def repair_minute_data(self, symbol: str, market: str, date_filter: str = None) -> dict:
        """
        Repair missing change/pct_change in MarketDataMinute.
        Calculates change relative to PREVIOUS DAY'S CLOSE (not previous minute).
        
        Args:
            symbol: Stock symbol
            market: Market type (CN/HK/US)
            date_filter: Optional date filter (e.g., '2025-12-15%') to repair specific day
        
        Returns:
            dict with status and fixed_count
        """
        try:
            from database import engine
            from models import MarketDataDaily
            from sqlmodel import select, Session
            
            with Session(engine) as session:

                db_symbol = normalize_symbol_db(symbol, market)
                fixed_count = 0
                
                # Query minute records
                stmt = select(MarketDataMinute).where(
                    MarketDataMinute.symbol == db_symbol,
                    MarketDataMinute.market == market
                )
                
                # Apply date filter if provided
                if date_filter:
                    stmt = stmt.where(MarketDataMinute.date.like(date_filter))
                
                stmt = stmt.order_by(MarketDataMinute.date.asc())
                records = session.exec(stmt).all()
                
                if not records:
                    return {"status": "success", "message": "No records found", "fixed_count": 0}
                
                self.logger.info(f"Repairing {len(records)} minute records for {db_symbol}")
                
                # Group records by trading day
                from collections import defaultdict
                import pandas as pd
                
                records_by_day = defaultdict(list)
                for record in records:
                    day = str(record.date).split(' ')[0]  # Extract date part
                    records_by_day[day].append(record)
                
                # Process each trading day
                for day, day_records in records_by_day.items():
                    # Get previous trading day's close
                    stmt_daily = select(MarketDataDaily).where(
                        MarketDataDaily.symbol == db_symbol,
                        MarketDataDaily.market == market,
                        MarketDataDaily.date < day
                    ).order_by(MarketDataDaily.date.desc()).limit(1)
                    
                    prev_day_record = session.exec(stmt_daily).first()
                    
                    if not prev_day_record or not prev_day_record.close:
                        self.logger.warning(f"No previous day close found for {db_symbol} on {day}, skipping")
                        continue
                    
                    prev_day_close = prev_day_record.close
                    self.logger.info(f"Using prev_day_close={prev_day_close} for {db_symbol} on {day}")
                    
                    # Calculate change for all minute records of this day relative to prev_day_close
                    for record in day_records:
                        # Check if repair is needed
                        needs_repair = (record.change is None or record.pct_change is None) and \
                                       (record.close is not None and record.close > 0)
                        
                        if needs_repair and prev_day_close > 0:
                            change_val = record.close - prev_day_close
                            pct_val = (change_val / prev_day_close) * 100
                            
                            record.change = round(change_val, 4)
                            record.pct_change = round(pct_val, 4)
                            record.updated_at = datetime.now()
                            
                            session.add(record)
                            fixed_count += 1
                
                if fixed_count > 0:
                    session.commit()
                    self.logger.info(f"Repaired {fixed_count} minute records for {db_symbol}")
                
                return {
                    "status": "success",
                    "fixed_count": fixed_count,
                    "total_records": len(records)
                }
            
        except Exception as e:
            self.logger.error(f"repair_minute_data failed for {symbol}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}


    def save_snapshot(self, symbol: str, market: str, data: dict, source: str = 'mixed') -> bool:
        """
        ⚠️ DEPRECATED: This function bypasses ETL and should not be used.
        Use the unified ETL flow instead: save_to_db() → RawMarketData → ETL → MarketSnapshot
        
        保存市场快照到 MarketSnapshot 表（UPSERT逻辑防止重复）
        
        🔥 ETL职责：计算补全缺失的 change 和 pct_change
        
        Args:
            symbol: 股票代号
            market: 市场（CN, HK, US）
            data: 数据字典，必须包含 price, change, pct_change等
            source: 数据来源 ('akshare', 'yfinance', 'tencent', 'mixed')
        
        Returns:
            bool: 保存成功返回True
        """
        import warnings
        warnings.warn(
            "save_snapshot() is deprecated and bypasses ETL. Use save_to_db() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        try:
            from database import engine
            from sqlmodel import Session, select
            from models import MarketSnapshot, MarketDataDaily
            from datetime import datetime
            
            # 数据验证
            current_price = data.get('price') or data.get('close')
            if not current_price or current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}, skip saving")
                return False
            
            current_price = float(current_price)
            
            # 标准化symbol
            db_symbol = normalize_symbol_db(symbol, market)
            
            # === ETL计算补全：强制从前一日收盘价计算 ===
            change = data.get('change')
            pct_change = data.get('pct_change')
            prev_close = None
            
            # 判断是否需要计算
            needs_calculation = (change is None or change == 0) and (pct_change is None or pct_change == 0)
            
            if needs_calculation:
                self.logger.info(f"🔧 ETL: Computing change for {symbol} from previous day's close")
                
                # 🔥 只从MarketDataDaily表查询前一日收盘价（用户要求）
                with Session(engine) as temp_session:
                    prev_daily = temp_session.exec(
                        select(MarketDataDaily).where(
                            MarketDataDaily.symbol == db_symbol,
                            MarketDataDaily.market == market
                        ).order_by(MarketDataDaily.date.desc()).limit(1)
                    ).first()
                    
                    if prev_daily and prev_daily.close > 0:
                        prev_close = prev_daily.close
                        change = current_price - prev_close
                        pct_change = (change / prev_close) * 100
                        self.logger.info(f"✅ Calculated from previous daily close: {change:.2f} ({pct_change:.2f}%)")
                    else:
                        # 无法计算，保持为0
                        self.logger.warning(f"⚠️ Cannot calculate change for {symbol}: no previous daily close found")
                        change = 0
                        pct_change = 0
            
            # 确保change和pct_change有值（即使是0）
            change = float(change) if change is not None else 0.0
            pct_change = float(pct_change) if pct_change is not None else 0.0
            
            with Session(engine) as session:
                # UPSERT逻辑：查询是否存在
                existing = session.exec(
                    select(MarketSnapshot).where(
                        MarketSnapshot.symbol == db_symbol,
                        MarketSnapshot.market == market
                    )
                ).first()
                
                if existing:
                    # UPDATE - 更新现有记录
                    existing.price = current_price
                    existing.open = float(data.get('open', 0))
                    existing.high = float(data.get('high', 0))
                    existing.low = float(data.get('low', 0))
                    existing.prev_close = float(prev_close) if prev_close else None
                    existing.change = change
                    existing.pct_change = pct_change
                    existing.volume = int(data.get('volume', 0))
                    existing.turnover = float(data.get('turnover')) if data.get('turnover') else None
                    existing.pe = float(data.get('pe')) if data.get('pe') else None
                    existing.pb = float(data.get('pb')) if data.get('pb') else None
                    existing.dividend_yield = float(data.get('dividend_yield')) if data.get('dividend_yield') else None
                    existing.market_cap = float(data.get('market_cap')) if data.get('market_cap') else None
                    existing.date = str(data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    existing.data_source = source
                    existing.updated_at = datetime.now()
                    
                    session.add(existing)
                    self.logger.info(f"✅ Updated MarketSnapshot for {db_symbol} (change={change:.2f}, pct={pct_change:.2f}%)")
                else:
                    # INSERT - 创建新记录
                    new_snapshot = MarketSnapshot(
                        symbol=db_symbol,
                        market=market,
                        price=current_price,
                        open=float(data.get('open', 0)),
                        high=float(data.get('high', 0)),
                        low=float(data.get('low', 0)),
                        prev_close=float(prev_close) if prev_close else None,
                        change=change,
                        pct_change=pct_change,
                        volume=int(data.get('volume', 0)),
                        turnover=float(data.get('turnover')) if data.get('turnover') else None,
                        pe=float(data.get('pe')) if data.get('pe') else None,
                        pb=float(data.get('pb')) if data.get('pb') else None,
                        dividend_yield=float(data.get('dividend_yield')) if data.get('dividend_yield') else None,
                        market_cap=float(data.get('market_cap')) if data.get('market_cap') else None,
                        date=str(data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))),
                        data_source=source,
                        fetch_time=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    session.add(new_snapshot)
                    self.logger.info(f"✅ Inserted new MarketSnapshot for {db_symbol} (change={change:.2f}, pct={pct_change:.2f}%)")
                
                session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save snapshot for {symbol}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False




    def backfill_missing_data(self, symbol: str, market: str, days: int = None) -> dict:
        """
        智能回填缺失的历史数据
        
        Args:
            symbol: 股票代码
            market: 市场 ('CN', 'HK', 'US')
            days: 回填天数，None表示自动检测缺失范围
        """
        try:
            # 智能检测缺失范围
            if days is None:
                from database import engine
                from sqlmodel import Session, select
                from models import MarketDataDaily
                from datetime import datetime, timedelta
                
                with Session(engine) as session:
                    # 查询最新数据日期
                    latest = session.exec(
                        select(MarketDataDaily)
                        .where(MarketDataDaily.symbol == symbol)
                        .where(MarketDataDaily.market == market)
                        .order_by(MarketDataDaily.date.desc())
                        .limit(1)
                    ).first()
                    
                    if latest:
                        # 计算缺失天数
                        from datetime import datetime as dt
                        latest_date = latest.date
                        # 确保latest_date是datetime对象
                        if isinstance(latest_date, str):
                            latest_date = dt.fromisoformat(latest_date.replace(' ', 'T'))
                        today = datetime.now()
                        gap_days = (today - latest_date).days
                        
                        # 自动确定回填天数（最多90天）
                        days = min(max(gap_days + 5, 30), 90)
                        self.logger.info(f"  检测到缺失{gap_days}天，将回填{days}天")
                    else:
                        # 全新股票，全量下载所有历史数据
                        days = None  # None表示不限制，下载全部
                        self.logger.info(f"  新股票，全量下载所有历史数据")
            
            self.logger.info(f"🔄 开始回填 {symbol} ({market}) 最近{days}天数据")
            
            # 1. 获取完整历史数据
            df = None
            if market == 'CN':
                df = self.fetch_cn_daily_data(symbol)
            elif market == 'HK':
                df = self.fetch_hk_daily_data(symbol)
            elif market == 'US':
                df = self.fetch_us_daily_data(symbol)
            
            if df is None or df.empty:
                return {'success': False, 'message': '无法获取数据'}
            
            # 2. 筛选数据范围
            if days is None:
                # 全量下载，不限制
                self.logger.info(f"  全量下载: {len(df)} 条记录")
            else:
                # 只保留最近N天
                df = df.tail(days)
                self.logger.info(f"  筛选最近{days}天: {len(df)} 条记录")
            
            records_fetched = len(df)
            
            # 3. 保存到RawMarketData
            from models import RawMarketData
            from database import engine
            from sqlmodel import Session
            import json
            
            with Session(engine) as session:
                # 转换所有日期/时间列为字符串以支持JSON序列化
                df_json = df.copy()
                for col in df_json.columns:
                    if df_json[col].dtype == 'object' or 'timestamp' in col.lower() or 'date' in col.lower():
                        try:
                            df_json[col] = df_json[col].astype(str)
                        except:
                            pass
                
                payload = df_json.to_dict('records')
                raw = RawMarketData(
                    source='backfill',
                    symbol=symbol,
                    market=market,
                    period='1d',
                    payload=json.dumps(payload),
                    processed=0
                )
                session.add(raw)
                session.commit()
                session.refresh(raw)
                raw_id = raw.id
            
            # 4. 触发ETL处理
            from etl_service import ETLService
            ETLService.process_raw_data(raw_id)
            
            self.logger.info(f"✅ 回填完成: {symbol}")
            return {
                'success': True,
                'symbol': symbol,
                'records_fetched': records_fetched,
                'message': f'成功回填 {records_fetched} 条记录'
            }
            
        except Exception as e:
            self.logger.error(f"❌ 回填失败 {symbol}: {e}")
            return {'success': False, 'message': f'回填失败: {str(e)}'}
    
    # ============================================================
    # 🚀 异步并发支持 (方案1: 并行数据获取)
    # ============================================================
    
    async def fetch_latest_data_async(
        self,
        symbol: str,
        market: str,
        save_db: bool = True,
        force_refresh: bool = False
    ) -> Optional[dict]:
        """
        异步版本的fetch_latest_data
        
        包装同步函数运行在线程池中,支持并发调用
        
        Args:
            symbol: 股票代码
            market: 市场 (CN/HK/US)
            save_db: 是否保存到数据库
            force_refresh: 是否强制刷新
        
        Returns:
            数据字典,失败返回None
        
        性能优势:
            - 多个股票可以并发获取
            - 不阻塞主线程
            - 配合asyncio.gather可实现真正的并行
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        # 确保线程池存在
        if not hasattr(self, '_executor'):
            self._executor = ThreadPoolExecutor(max_workers=10)
        
        loop = asyncio.get_event_loop()
        
        # 在线程池中运行同步函数
        try:
            result = await loop.run_in_executor(
                self._executor,
                self.fetch_latest_data,
                symbol,
                market,
                save_db,
                force_refresh
            )
            return result
        except Exception as e:
            self.logger.error(f"Async fetch failed for {symbol}: {e}")
            return None

if __name__ == "__main__":
    pass

