"""
VERA Data Orchestrator (中央数据决策大脑)
==============================================================================

本模块是 VERA 系统数据感知层的“调度中枢”。它不直接抓取数据，而是根据市场状态与现有数据库
新鲜度，动态决定每一次获取任务的优先级、类型与范围。

职责范围:
========================================

I. 智能获取策略 (Dynamic Strategy Decision)
----------------------------------------
- **状态感知**: 结合 `market_status`，自动识别全球市场的“交易中”、“午休”、“已闭市”或“非交易日”状态。
- **差异决策**: 
  - 交易中 → 获取分钟级实时快照。
  - 闭市后（首小时内）→ 获取行情终值并触发 Daily ETL。
  - 非交易日/闭市后（已同步）→ 跳过冗余请求。

II. 数据完整性自愈 (Integrity Self-Healing)
----------------------------------------
- **Gap Detection**: 启动抓取前，自动扫描 `MarketDataDaily` 缺口。
- **Automatic Backfill**: 为新加入或长期未同步的资产自动规划“三段式回填”：初始下载(1年) → 追赶同步(7天) → 实时补足。

III. 时区与准入校验 (Timezone & Guardrails)
----------------------------------------
- **多时区统一**: 将 US (ET), HK (HKT) 时间统一转换为服务器基准时间进行逻辑判定。
- **DB Freshness**: 设置严格的“准入日期”校验，防止旧数据覆盖新快照。

作者: Antigravity
日期: 2026-01-23
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class FetchDecision:
    """数据获取决策结果"""
    should_fetch: bool  # 是否需要获取数据
    fetch_type: Literal['minute', 'daily', 'skip']  # 获取类型
    reason: str  # 决策原因
    expected_date: Optional[str] = None  # 期望的数据日期 (YYYY-MM-DD)
    
    # 新增:历史数据补充
    need_backfill_daily: bool = False  # 是否需要补充历史日线数据
    backfill_date_range: Optional[Tuple[str, str]] = None  # 补充日期范围 (start_date, end_date)
    backfill_reason: Optional[str] = None  # 补充原因


class DataOrchestrator:
    """
    中央数据获取决策器
    
    核心方法:
    - decide_fetch_strategy: 决定数据获取策略
    - check_db_freshness: 检查数据库数据新鲜度
    """
    
    def __init__(self):
        self.logger = logger
        # 服务器时区 (北京时间)
        import pytz
        self.server_tz = pytz.timezone('Asia/Shanghai')
    
    def _get_server_time(self) -> datetime:
        """
        获取服务器当前时间 (带时区)
        
        Returns:
            datetime: 服务器当前时间 (北京时间)
        """
        now = datetime.now(self.server_tz)
        self.logger.debug(f"服务器时间: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        return now
    
    def _get_server_date(self) -> str:
        """
        获取服务器当前日期 (YYYY-MM-DD)
        
        Returns:
            str: 当前日期
        """
        return self._get_server_time().strftime('%Y-%m-%d')
    
    def check_data_gaps(self, symbol: str, market: str) -> dict:
        """
        检测数据完整性，返回缺口信息和建议的回填策略
        
        Args:
            symbol: 股票代码
            market: 市场 (CN/HK/US)
        
        Returns:
            dict: 缺口分析结果
            {
                'has_gap': bool,
                'gap_type': str,  # 'empty', 'recent_missing', 'large_gap'
                'action': str,    # 'initial_backfill', 'catch_up', 'full_backfill'
                'days_needed': int,
                'latest_date': str,
                'expected_date': str
            }
        """
        try:
            from database import engine
            from models import MarketDataDaily
            from sqlmodel import Session, select
            from datetime import datetime, timedelta
            
            with Session(engine) as session:
                # 查询最新记录
                stmt = select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol,
                    MarketDataDaily.market == market
                ).order_by(MarketDataDaily.timestamp.desc()).limit(1)
                
                latest_record = session.exec(stmt).first()
                
                expected_date = self._get_expected_date(market, 
                    self._is_trading_day(market), 
                    False  # 假设闭市检查
                )
                
                # 情况1: 完全没有数据
                if not latest_record:
                    return {
                        'has_gap': True,
                        'gap_type': 'empty',
                        'action': 'initial_backfill',
                        'days_needed': 365,  # 初始下载1年
                        'latest_date': None,
                        'expected_date': expected_date,
                        'message': f'{symbol} 无历史数据，需要初始回填'
                    }
                
                # 情况2: 有数据，检查缺口
                latest_date = latest_record.timestamp[:10]  # YYYY-MM-DD
                latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
                expected_dt = datetime.strptime(expected_date, '%Y-%m-%d')
                
                gap_days = (expected_dt - latest_dt).days
                
                # 情况2a: 数据是最新的
                if gap_days <= 1:
                    return {
                        'has_gap': False,
                        'gap_type': 'up_to_date',
                        'action': 'none',
                        'days_needed': 0,
                        'latest_date': latest_date,
                        'expected_date': expected_date,
                        'message': f'{symbol} 数据最新'
                    }
                
                # 情况2b: 最近几天缺失
                if gap_days <= 7:
                    return {
                        'has_gap': True,
                        'gap_type': 'recent_missing',
                        'action': 'catch_up',
                        'days_needed': gap_days,
                        'latest_date': latest_date,
                        'expected_date': expected_date,
                        'message': f'{symbol} 缺失最近{gap_days}天数据'
                    }
                
                # 情况2c: 大缺口
                return {
                    'has_gap': True,
                    'gap_type': 'large_gap',
                    'action': 'backfill',
                    'days_needed': min(gap_days, 365),  # 最多回填1年
                    'latest_date': latest_date,
                    'expected_date': expected_date,
                    'message': f'{symbol} 有{gap_days}天数据缺口，建议后台回填'
                }
                
        except Exception as e:
            self.logger.error(f"check_data_gaps failed for {symbol}: {e}")
            return {
                'has_gap': False,
                'gap_type': 'error',
                'action': 'none',
                'days_needed': 0,
                'message': f'检查失败: {str(e)}'
            }

    def decide_fetch_strategy(
        self,
        symbol: str,
        market: str,
        force_refresh: bool = False,
        db_latest_date: Optional[str] = None
    ) -> FetchDecision:
        """
        核心决策函数:决定是否需要获取数据以及获取类型
        
        Args:
            symbol: 股票代码
            market: 市场 (CN/HK/US)
            force_refresh: 是否强制刷新
            db_latest_date: 数据库中最新数据的日期 (YYYY-MM-DD格式)
        
        Returns:
            FetchDecision: 决策结果
        
        决策规则:
        1. 开市中 → 获取分钟数据
        2. 闭市 + 交易日 + DB无今天数据 → 获取日线数据
        3. 闭市 + 交易日 + DB有今天数据 → 跳过
        4. 闭市 + 非交易日 + DB有最新数据 → 跳过
        5. 闭市 + 非交易日 + DB数据过旧 → 获取日线数据
        """
        # ✅ 使用market_status模块准确判断市场状态
        from market_status import is_market_open
        
        # 1. 判断市场状态
        is_open = is_market_open(market)
        is_trading_day = self._is_trading_day(market)  # 传递market参数
        
        # 2. 获取期望的数据日期
        expected_date = self._get_expected_date(market, is_trading_day, is_open)
        
        # 3. 检查数据库新鲜度
        db_is_fresh = self._check_db_freshness(db_latest_date, expected_date)
        
        self.logger.info(
            f"[决策] {symbol} ({market}): "
            f"开市={is_open}, 交易日={is_trading_day}, "
            f"期望日期={expected_date}, DB日期={db_latest_date}, "
            f"DB新鲜={db_is_fresh}, 强制={force_refresh}"
        )
        
        # 4. 应用决策规则
        
        decision = None
        
        # 4. 应用决策规则
        
        # 规则0: 强制刷新 (最高优先级)
        if force_refresh:
            fetch_type = 'minute' if is_open else 'daily'
            decision = FetchDecision(
                should_fetch=True,
                fetch_type=fetch_type,
                reason=f"强制刷新 requested (Market Open={is_open})",
                expected_date=expected_date
            )
            
            # 即使是强制刷新，检查历史补充逻辑依然有价值（如果是开盘）
            if is_open:
                last_trading_day = self._get_last_trading_day()
                if db_latest_date and db_latest_date < last_trading_day:
                    decision.need_backfill_daily = True
                    decision.backfill_date_range = (db_latest_date, last_trading_day)
                    decision.backfill_reason = f"DB缺少 {db_latest_date} 到 {last_trading_day} 期间的历史daily数据"

        # 规则1: 开市中 → 获取分钟数据 (同时检查是否需要补充历史daily)
        elif is_open:
            decision = FetchDecision(
                should_fetch=True,
                fetch_type='minute',
                reason=f"市场开盘中,获取分钟数据",
                expected_date=expected_date
            )
            
            # 检查是否需要补充历史daily数据
            last_trading_day = self._get_last_trading_day()
            
            if db_latest_date and db_latest_date < last_trading_day:
                decision.need_backfill_daily = True
                decision.backfill_date_range = (db_latest_date, last_trading_day)
                decision.backfill_reason = f"DB缺少 {db_latest_date} 到 {last_trading_day} 期间的历史daily数据(仅交易日)"
                self.logger.info(f"⚠️ 开市中同时需要补充历史数据: {decision.backfill_date_range}")

        # 规则2: 闭市 + 交易日 + DB无今天数据 → 获取日线数据
        elif is_trading_day and not db_is_fresh:
            decision = FetchDecision(
                should_fetch=True,
                fetch_type='daily',
                reason=f"交易日闭市,DB数据不是最新({db_latest_date} vs {expected_date}),获取日线数据",
                expected_date=expected_date
            )
        
        # 规则3: 闭市 + 交易日 + DB有今天数据 → 跳过
        elif is_trading_day and db_is_fresh:
            decision = FetchDecision(
                should_fetch=False,
                fetch_type='skip',
                reason=f"交易日闭市,DB已有最新数据({db_latest_date}),跳过获取",
                expected_date=expected_date
            )
        
        # 规则4: 闭市 + 非交易日 + DB有最新数据 → 跳过
        elif not is_trading_day and db_is_fresh:
            decision = FetchDecision(
                should_fetch=False,
                fetch_type='skip',
                reason=f"非交易日,DB已有最新数据({db_latest_date}),跳过获取",
                expected_date=expected_date
            )
        
        # 规则5: 闭市 + 非交易日 + DB数据过旧 → 获取日线数据
        elif not is_trading_day and not db_is_fresh:
            decision = FetchDecision(
                should_fetch=True,
                fetch_type='daily',
                reason=f"非交易日但DB数据过旧({db_latest_date} vs {expected_date}),获取日线数据",
                expected_date=expected_date
            )
        
        # 默认:跳过
        else:
            decision = FetchDecision(
                should_fetch=False,
                fetch_type='skip',
                reason="未匹配任何规则,默认跳过",
                expected_date=expected_date
            )
            
        # 🔥 输出统一的决策日志 (WARNING级别确保可见)
        log_icon = "✅" if decision.should_fetch else "⏭️"
        backfill_msg = f", 补充历史={decision.backfill_date_range}" if decision.need_backfill_daily else ""
        
        self.logger.warning(
            f"{log_icon} [DataOrchestrator决策] {symbol} ({market}): "
            f"类型={decision.fetch_type}, "
            f"原因={decision.reason}"
            f"{backfill_msg}"
        )
        
        return decision
    
    def _is_trading_day(self, market: str) -> bool:
        """
        判断今天是否是交易日
        
        ✅ 使用market_status模块的统一逻辑
        基于服务器时间和市场时区判断
        
        Args:
            market: 市场代码
        
        Returns:
            bool: True=交易日, False=非交易日
        """
        from market_status import get_market_time
        
        # 获取市场当地时间
        market_time = get_market_time(market)
        
        # 周一到周五为交易日
        is_trading = market_time.weekday() < 5
        
        self.logger.info(
            f"{market}市场: 当地时间={market_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"星期{market_time.weekday()}({'交易日' if is_trading else '非交易日'})"
        )
        
        return is_trading
    
    def _get_expected_date(self, market: str, is_trading_day: bool, is_open: bool = False) -> str:
        """
        获取期望的最新数据日期 - 分市场决策
        
        Args:
            market: 市场
            is_trading_day: 是否是交易日
            is_open: 市场是否开市
        
        Returns:
            期望日期 (YYYY-MM-DD格式)
        
        决策逻辑:
        
        **开市中**: 期望今天(正在生成今天的数据)
        
        **CN市场** (北京时间):
        - 交易时间: 9:30-15:00
        - 决策:
          - 开市中 → 期望今天
          - 交易日 + 15:00后 → 期望今天
          - 交易日 + 15:00前 → 期望昨天
          - 非交易日 → 期望最近交易日
        
        **HK市场** (香港时间 = 北京时间):
        - 交易时间: 9:30-16:00
        - 决策:
          - 开市中 → 期望今天
          - 交易日 + 16:00后 → 期望今天
          - 交易日 + 16:00前 → 期望昨天
          - 非交易日 → 期望最近交易日
        
        **US市场** (美东时间):
        - 交易时间: 9:30-16:00 ET
        - 决策:
          - 开市中 → 期望今天
          - 闭市 → 期望昨天
        """
        # 使用服务器时间
        now = self._get_server_time()
        today = now.strftime('%Y-%m-%d')
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        beijing_hour = now.hour
        
        # 如果市场开市,总是期望今天的数据
        if is_open:
            self.logger.info(f"{market}市场: 开市中, 期望今天 {today}")
            return today
        
        if market == 'CN':
            # CN市场决策
            if is_trading_day:
                # 交易日:15:00后期望今天,15:00前期望昨天
                if beijing_hour >= 15:
                    self.logger.info(f"CN市场: 交易日{beijing_hour}:00 >= 15:00, 期望今天 {today}")
                    return today
                else:
                    self.logger.info(f"CN市场: 交易日{beijing_hour}:00 < 15:00, 期望昨天 {yesterday}")
                    return yesterday
            else:
                # 非交易日:期望最近交易日
                last_trading = self._get_last_trading_day()
                self.logger.info(f"CN市场: 非交易日, 期望最近交易日 {last_trading}")
                return last_trading
        
        elif market == 'HK':
            # HK市场决策
            if is_trading_day:
                # 交易日:16:00后期望今天,16:00前期望昨天
                if beijing_hour >= 16:
                    self.logger.info(f"HK市场: 交易日{beijing_hour}:00 >= 16:00, 期望今天 {today}")
                    return today
                else:
                    self.logger.info(f"HK市场: 交易日{beijing_hour}:00 < 16:00, 期望昨天 {yesterday}")
                    return yesterday
            else:
                # 非交易日:期望最近交易日
                last_trading = self._get_last_trading_day()
                self.logger.info(f"HK市场: 非交易日, 期望最近交易日 {last_trading}")
                return last_trading
        
        elif market == 'US':
            # US市场决策 (考虑时区)
            # 美东时间 = 北京时间 - 13小时 (冬令时)
            # 美股收盘时间: 美东16:00 = 北京次日5:00
            # 美股开盘时间: 美东9:30 = 北京22:30
            
            if beijing_hour >= 22:
                # 北京时间22:00后 → 美股开盘中 → 期望今天
                self.logger.info(f"US市场: 北京{beijing_hour}:00 >= 22:00, 美股开盘中, 期望今天 {today}")
                return today
            elif beijing_hour >= 5:
                # 北京时间5:00-22:00 → 美股已收盘 → 期望昨天
                self.logger.info(f"US市场: 北京{beijing_hour}:00在5:00-22:00之间, 美股已收盘, 期望昨天 {yesterday}")
                return yesterday
            else:
                # 北京时间0:00-5:00 → 美股还在交易 → 期望昨天
                self.logger.info(f"US市场: 北京{beijing_hour}:00 < 5:00, 美股还在交易, 期望昨天 {yesterday}")
                return yesterday
        
        # 默认:今天
        return today
    
    def _get_last_trading_day(self) -> str:
        """
        获取最近的交易日
        简化版:往前推到最近的工作日
        """
        # 使用服务器时间
        now = self._get_server_time()
        days_back = 0
        
        while True:
            check_date = now - timedelta(days=days_back)
            if check_date.weekday() < 5:  # 工作日
                return check_date.strftime('%Y-%m-%d')
            days_back += 1
            if days_back > 7:  # 防止无限循环
                return now.strftime('%Y-%m-%d')
    
    def _check_db_freshness(
        self,
        db_latest_date: Optional[str],
        expected_date: str
    ) -> bool:
        """
        检查数据库数据是否新鲜
        
        Args:
            db_latest_date: 数据库最新数据日期 (YYYY-MM-DD)
            expected_date: 期望的数据日期 (YYYY-MM-DD)
        
        Returns:
            True if 数据库数据是最新的, False otherwise
        """
        if not db_latest_date:
            return False
        
        # 提取日期部分(去除时间)
        db_date_only = db_latest_date.split(' ')[0] if ' ' in db_latest_date else db_latest_date
        
        return db_date_only == expected_date
    
    def get_db_latest_date(self, symbol: str, market: str) -> Optional[str]:
        """
        从数据库获取最新数据日期 - 同时检查Daily和Snapshot表
        
        Args:
            symbol: 股票代码
            market: 市场
        
        Returns:
            最新数据日期 (YYYY-MM-DD格式), 如果没有数据返回 None
        
        策略:
        1. 检查 MarketSnapshot 表(实时快照)
        2. 检查 MarketDataDaily 表(日线数据)
        3. 返回两者中较新的日期
        """
        try:
            from sqlmodel import Session, select, create_engine
            from models import MarketSnapshot, MarketDataDaily
            from utils.symbol_utils import normalize_symbol_db
            
            engine = create_engine('sqlite:///database.db')
            
            with Session(engine) as session:
                db_symbol = normalize_symbol_db(symbol, market)
                
                # 1. 检查 MarketSnapshot 表
                snapshot = session.exec(
                    select(MarketSnapshot).where(
                        MarketSnapshot.symbol == db_symbol,
                        MarketSnapshot.market == market
                    )
                ).first()
                
                snapshot_date = None
                if snapshot and snapshot.date:
                    date_str = str(snapshot.date)
                    snapshot_date = date_str.split(' ')[0] if ' ' in date_str else date_str
                    self.logger.info(f"Snapshot表: {symbol} 最新日期 = {snapshot_date}")
                
                # 2. 检查 MarketDataDaily 表
                daily = session.exec(
                    select(MarketDataDaily).where(
                        MarketDataDaily.symbol == db_symbol,
                        MarketDataDaily.market == market
                    ).order_by(MarketDataDaily.date.desc())
                ).first()
                
                daily_date = None
                if daily and daily.date:
                    date_str = str(daily.date)
                    daily_date = date_str.split(' ')[0] if ' ' in date_str else date_str
                    self.logger.info(f"Daily表: {symbol} 最新日期 = {daily_date}")
                
                # 3. 返回较新的日期
                if snapshot_date and daily_date:
                    # 比较两个日期,返回较新的
                    latest = max(snapshot_date, daily_date)
                    self.logger.info(f"DB最新日期: {symbol} = {latest} (Snapshot:{snapshot_date}, Daily:{daily_date})")
                    return latest
                elif snapshot_date:
                    self.logger.info(f"DB最新日期: {symbol} = {snapshot_date} (仅Snapshot)")
                    return snapshot_date
                elif daily_date:
                    self.logger.info(f"DB最新日期: {symbol} = {daily_date} (仅Daily)")
                    return daily_date
                else:
                    self.logger.info(f"DB无数据: {symbol}")
                    return None
                
        except Exception as e:
            self.logger.error(f"获取DB最新日期失败: {e}")
            return None


# 便捷函数
def decide_fetch(
    symbol: str,
    market: str,
    force_refresh: bool = False
) -> FetchDecision:
    """
    便捷函数:快速决策
    
    Usage:
        decision = decide_fetch('TSLA', 'US', force_refresh=True)
        if decision.should_fetch:
            # 获取数据
            pass
    """
    orchestrator = DataOrchestrator()
    db_latest_date = orchestrator.get_db_latest_date(symbol, market)
    return orchestrator.decide_fetch_strategy(symbol, market, force_refresh, db_latest_date)
