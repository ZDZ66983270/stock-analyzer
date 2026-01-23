"""
Daily Incremental Update Script (每日增量更新脚本)
===============================================

功能说明:
1. 自动化执行每日行情同步流程：获取资产列表 -> 下载行情数据 -> 存入 Raw 表 -> 触发 ETL -> 更新高级指标。
2. 采用 yfinance Unified 策略，统一处理美股 (US)、港股 (HK) 和 A 股 (CN) 的行情下载。
3. 实现“智能跳过”逻辑：如果今日开盘已产生定型数据，则不重复下载，节省 API 额度。

核心逻辑与流程:
1. **符号转换 (Symbol Normalization)**:
   - 剥离 Canonical ID 前缀 (如 `US:STOCK:AAPL` -> `AAPL`)。
   - 应用市场规则补全后缀 (HK -> `.HK`, CN -> `.SS`/`.SZ`)。
   - 公式: `yf_symbol = normalize(canonical_id) + suffix_map(market)`
2. **下载策略**:
   - 下载过去 5 天的日线数据 (Period: 5d)，包含前复权处理 (auto_adjust=True)。
   - 目的: 覆盖周末和节假日，确保数据连续性。
3. **ETL 联动**:
   - 每下载一条 Raw 记录，立即调用 `ETLService.process_raw_data` 进行本地化清理和 `MarketSnapshot` 更新。
4. **指标同步**:
   - 执行完成后自动调用 `advanced_metrics.py` 以获取最新的 PE/PB/市值等数据。

作者: Antigravity
日期: 2026-01-23
"""
import sys
import os
import time
import json
import logging
from datetime import datetime
import pandas as pd
import yfinance as yf
from sqlmodel import Session, select

# 添加后端路径以导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine
from models import Watchlist, RawMarketData

# ==========================================
# 0. Result Tracker
# ==========================================
class ResultTracker:
    def __init__(self):
        self.results = []
        
    def add(self, symbol, market, status, message=""):
        self.results.append({
            "symbol": symbol,
            "market": market,
            "status": status,
            "message": message,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        
    def print_summary(self):
        print("\n" + "="*80)
        print(f"📊 每日更新详细报告 (Daily Update Report) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Group by Market
        by_market = {}
        for r in self.results:
            m = r['market'] or 'UNKNOWN'
            if m not in by_market: by_market[m] = {'ok': 0, 'fail': 0, 'skip': 0, 'details': []}
            
            if r['status'] == 'SUCCESS': by_market[m]['ok'] += 1
            elif r['status'] == 'FAILED': by_market[m]['fail'] += 1
            else: by_market[m]['skip'] += 1
            
            by_market[m]['details'].append(r)
            
        # Print Table Header
        print(f"{'Market':<8} | {'Symbol':<18} | {'Status':<10} | {'Message'}")
        print("-" * 80)
        
        total_ok, total_fail = 0, 0
        
        for market in sorted(by_market.keys()):
            stats = by_market[market]
            total_ok += stats['ok']
            total_fail += stats['fail']
            
            # Print details (Failed first, then Success)
            sorted_details = sorted(stats['details'], key=lambda x: (x['status'] == 'SUCCESS', x['symbol']))
            
            for item in sorted_details:
                # Colorize status
                status_str = item['status']
                if status_str == 'SUCCESS': status_icon = "✅ OK"
                elif status_str == 'FAILED': status_icon = "❌ FAIL"
                else: status_icon = "⏭️ SKIP"
                
                # Truncate message
                msg = item['message'][:40] + "..." if len(item['message']) > 40 else item['message']
                print(f"{market:<8} | {item['symbol']:<18} | {status_icon:<10} | {msg}")
            
            # Market Summary Line
            print(f"   >>> {market} Summary: ✅ {stats['ok']}  ❌ {stats['fail']}  ⏭️ {stats['skip']}")
            print("-" * 80)
            
        print("="*80)
        print(f"🏁 总计: 成功 {total_ok}  失败 {total_fail}")
        print("="*80)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DailyUpdate")

# ==========================================
# 1. 辅助函数
# ==========================================

def get_all_symbols_for_update():
    """
    获取所有需要更新的股票和指数（Watchlist + Index表）
    
    Returns:
        list of tuples: [(symbol, market), ...]
    """
    sys.path.insert(0, 'backend')
    from symbol_utils import get_all_symbols_to_update
    
    with Session(engine) as session:
        all_items = get_all_symbols_to_update(session)
    
    # 返回去重的 (symbol, market) 元组列表
    return list(set([(item['symbol'], item['market']) for item in all_items]))

from symbols_config import get_yfinance_symbol as get_yf_sym_config, get_canonical_symbol

def get_yfinance_symbol(symbol: str, market: str) -> str:
    """
    将内部 symbol 标准化为 yfinance 认可的 Ticker 格式
    优先使用 symbols_config.py 中的配置，其次使用通用规则
    """
    symbol = symbol.strip().upper()
    
    # 0. Strip Canonical ID prefix if present
    if ":" in symbol:
        symbol = symbol.split(":")[-1]
    
    # 1. 规范化别名 (e.g. 800700 -> HSTECH)
    canonical = get_canonical_symbol(symbol)
    
    # 2. 尝试从配置获取
    # config 返回的可能是本身(若无配置)，所以我们需要区分"有配置"和"默认"
    # 但 get_yfinance_symbol 实现是 config.get('yfinance_symbol', symbol)
    # 我们可以直接调用，如果它是指数，通常会有配置。
    config_yf = get_yf_sym_config(canonical)
    
    # 如果 config 返回的不等于 canonical，说明找到了特定配置 (或者就是 symbol 本身但我们确认一下)
    # 对于指数，如 ^DJI -> ^DJI, 000001.SS -> 000001.SS
    # 只有当它是配置表里的 Key 时，我们才信任它。
    # 如何判断是否在配置表？ get_yf_sym_config 内部是 dict.get
    # 简单策略：先查 Config。
    
    # 我们需要更明确的逻辑：如果是"已知指数/特殊品种" -> Use Config.
    # 如果是"普通个股" -> Use Generic Rule.
    
    # Hack: 检查 get_yf_sym_config 是否改变了 symbol，或者 symbol 是否在 symbols_config 的 Keys 里?
    # 由于不能直接访问 config dict，我们假设:
    # 如果 canonical 是指数 (含 .SS/.SZ 等)，config 应该能通过。
    
    if config_yf != canonical:
        # 发生了映射 (e.g. 800000 -> ^HSI, or Config has explicit definition)
        return config_yf
        
    # 特殊情况: 000001.SS 在 Config 里， get_yf_sym_config("000001.SS") returns "000001.SS"
    # 这时 config_yf == canonical，但它确实是 Config 管理的。
    # 为了避免 generic rules 误判 (虽然后面 generic 也会处理 .SS)
    # 我们可以稍微依赖 canonical 的格式.
    
    # 3. yfinance specific fix for SH
    if canonical.endswith(".SH"):
        return canonical.replace(".SH", ".SS")

    # 4. 通用规则 (Generic Stocks)
    # 如果已经包含后缀 (e.g. .HK, .SS, .SZ) -> 直接使用
    if "." in canonical:
        # Special handling for HK stocks (e.g. 09988.HK -> 9988.HK) - Yahoo prefers 4 digits
        if market == 'HK' and canonical.endswith('.HK'):
             code = canonical.split('.')[0]
             if code.isdigit():
                 return f"{int(code):04d}.HK"
        return canonical

    # 5. 根据市场规则补全
    if market == "US":
        return canonical
        
    elif market == "HK":
        if canonical.isdigit():
            return f"{int(canonical):04d}.HK"
        # 可能是未在 Config 中的指数?
        if canonical == "HSI": return "^HSI"
        if canonical == "HSTECH": return "^HSTECH"
        return f"{canonical}.HK"
        
    elif market == "CN":
        # A股规则
        if canonical.startswith("6") or canonical.startswith("5"):
            return f"{canonical}.SS"
        elif canonical.startswith("0") or canonical.startswith("3") or canonical.startswith("1"):
            return f"{canonical}.SZ"
        elif canonical.startswith("4") or canonical.startswith("8"):
            return f"{canonical}.BJ"
            
    return canonical

# ==========================================
# 2. 核心获取逻辑 (yfinance Unified)
# ==========================================

from etl_service import ETLService  # Added import

def fetch_and_save_unified(symbol: str, market: str) -> tuple[bool, str]:
    """
    统一获取逻辑：
    Returns: (Success, Message)
    """
    yf_symbol = get_yfinance_symbol(symbol, market)
    logger.info(f"🔄 Fetching [{market}] {symbol} -> yf: {yf_symbol}")
    
    try:
        # 强制下载最近5天，包含auto_adjust=True
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period="5d", interval="1d", auto_adjust=True)
        
        if df.empty:
            logger.warning(f"⚠️ No data found for {yf_symbol}")
            return False, f"No data (yf: {yf_symbol})"
            
        # 格式化数据
        df = df.reset_index()
        
        # 统一列名
        rename_map = {
            'Date': 'timestamp',
            'Datetime': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        df = df.rename(columns=rename_map)
        
        # 处理时间戳
        if 'timestamp' in df.columns:
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d')
        elif 'date' in df.columns: # Fallback
            df['timestamp'] = df['date'].dt.strftime('%Y-%m-%d')
            
        # 🛡️ SANITY CHECK
        if symbol == "000001.SS":
            last_close = df['close'].iloc[-1]
            if last_close < 1000:
                logger.error(f"❌ SANITY CHECK FAILED for {symbol}: Price {last_close} is too low for Index. Likely fetched Ping An Bank. Skipping.")
                return False, f"Sanity Check Failed (Low Price: {last_close})"
                
        # 转为 list of dicts
        records = df.to_dict(orient='records')
        
        # 构造 Payload
        payload = {
            "symbol": symbol,
            "market": market,
            "source": "yfinance",
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": records
        }
        
        # 存库 (返回 ID)
        record_id = save_payload_to_db(symbol, market, "yfinance", payload, period="1d")
        
        if record_id:
            # 立即触发 ETL: Raw -> Daily
            logger.info(f"⚡ Triggering ETL for Raw ID: {record_id}")
            ETLService.process_raw_data(record_id)
            return True, f"Saved Raw ID {record_id}"
        else:
            return False, "DB Save Failed"
        
    except Exception as e:
        logger.error(f"❌ Error fetching {symbol}: {str(e)}")
        return False, str(e)

def save_payload_to_db(symbol: str, market: str, source: str, payload: dict, period: str = '1d') -> int:
    """保存 Payload 到数据库, 返回记录 ID (None if failed)"""
    try:
        payload_json = json.dumps(payload)
        with Session(engine) as session:
            record = RawMarketData(
                symbol=symbol,
                market=market,
                source=source,
                period=period,
                fetch_time=datetime.now(),
                payload=payload_json,
                processed=False
            )
            session.add(record)
            session.commit()
            logger.info(f"✅ Saved {symbol} to RawMarketData (ID: {record.id})")
            # Must refresh to get ID if not immediately available on object? 
            # Session commit usually populates it.
            session.refresh(record)
            return record.id
    except Exception as e:
        logger.error(f"❌ Database error for {symbol}: {e}")
        return None

# ==========================================
# 3. 主执行流
# ==========================================

def run_daily_update():
    logger.info("🚀 Starting Daily Incremental Update (yfinance Unified)")
    
    # 获取所有需要更新的股票和指数（Watchlist + Index表）
    targets = get_all_symbols_for_update()
            
    logger.info(f"📋 Total targets: {len(targets)} (Watchlist + Index)")
    
    tracker = ResultTracker()
    
    success_count = 0
    fail_count = 0
    
    # 3. 遍历执行
    for symbol, market in targets:
        success, msg = fetch_and_save_unified(symbol, market)
        if success:
            success_count += 1
            tracker.add(symbol, market, "SUCCESS", msg)
        else:
            fail_count += 1
            tracker.add(symbol, market, "FAILED", msg)
            
        # 礼貌性延迟，避免触发Yahoo频控
        time.sleep(1.0)
        
    logger.info("-" * 40)
    logger.info(f"🏁 Update Finished: Success={success_count}, Failed={fail_count}")
    logger.info("-" * 40)
    
    # Print Detailed Report
    tracker.print_summary()
    
    # 4. 触发 ETL (如果可以)
    if success_count > 0:
        logger.info("🔧 Triggering ETL Pipeline...")
        try:
            # 尝试导入 run_etl
            import run_etl
            run_etl.run_etl_pipeline() 
        except Exception as e:
            logger.error(f"⚠️ ETL Trigger Failed: {e}")
            logger.info("👉 Please run 'python3 run_etl.py' manually.")
            
    # 5. Fetch Advanced Metrics (PE/PB/Cap)
    print("=" * 40)
    logger.info("📊 Fetching Advanced Metrics (PE/PB/Cap)...")
    try:
        from backend.advanced_metrics import update_all_metrics
        update_all_metrics()
        logger.info("✅ Advanced Metrics Updated.")
    except Exception as e:
        logger.error(f"⚠️ Advanced Metrics Update Failed: {e}")
    print("=" * 40)

if __name__ == "__main__":
    run_daily_update()
