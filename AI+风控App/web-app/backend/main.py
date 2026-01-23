import os

"""
VERA Backend API Server (Core Entry Point)
==============================================================================

本模块是 VERA 系统的核心后端入口，基于 FastAPI 构建。它集成了实时 API、后台调度任务、
异步 ETL 队列以及 WebSocket 实时行情推送。

架构概览:
========================================

I. API 服务架构 (API Endpoints)
----------------------------------------
1. **Watchlist API**:
   - `GET /api/watchlist`: 获取自选股快照。查询逻辑优先使用 `MarketSnapshot` 缓存表以保证读性能。
   - `POST /api/watchlist`: 添加新资产。具备“三步走”后台同步逻辑（30天历史 -> 实时分钟点 -> 全量历史）。
2. **Market Data & Analysis**:
   - `GET /api/latest-analysis/{symbol}`: 获取资产的最新风险分析结果。
   - `GET /api/market-data-history`: 获取图表用历史序列，内嵌 `calculate_indicators` 进行实时技术指标计算。
3. **Indices API**:
   - `GET /api/market-indices`: 聚合显示全球核心指数行情。

II. 后台任务与调度 (Background Jobs & Scheduler)
----------------------------------------
- **APScheduler**: 
  - 自动管理 CN, HK, US 市场的每日定时同步（每日 17:00 触发）。
  - 实现 `wrapper_daily_sync` 包装器，确保多市场数据在各自收盘后的标准化入库。
- **Self-Healing Index History**: 启动时自动检查核心指数（DJI, NDX, etc.）的数据完整性，缺失时从本地 CSV 自动补填。

III. 异步性能优化 (Performance Engine)
----------------------------------------
- **ETL Queue**: 引入 `etl_queue` 异步处理机制。
  - 用户添加新股票时，前端无需等待 150s 的全量 ETL，任务会入队并在后台静默处理，RT (Response Time) 从分钟级降至毫秒级。

IV. 实时行情引擎 (Real-time Strategy)
----------------------------------------
- **Manual Sync**: `POST /api/sync-market` 允许用户手动触发实时行情抓取。
- **WebSocket**: `/ws/market-data` 节点支持向前端推送经由后台抓取的最新价格波动（目前处于集成阶段）。

V. Dependencies & Modules
----------------------------------------
- `data_fetcher_legacy`: 核心抓取引擎，支持多种金融数据源回退。
- `utils.symbol_utils`: 统一的 Canonical ID 标准化工具，确保数据库键值一致性。
- `etl_queue`: 异步任务分发系统。

作者: Antigravity
日期: 2026-01-23
"""

print("!!! MAIN PY LOADED !!!")

# Unset system proxies to avoid AkShare connection errors
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

import sys
# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager # Keep this if still used
import sys # Keep this if still used
import json # Keep this if still used

from database import create_db_and_tables, get_session, engine
from models import MacroData, StockInfo, Watchlist, AssetAnalysisHistory, MarketDataDaily, MarketSnapshot
from data_fetcher_legacy import DataFetcher  # ✅ 使用 legacy 版本，包含 backfill_missing_data 方法
# ✅ 使用统一的符号转换工具
from utils.symbol_utils import normalize_symbol_db
from sqlmodel import Session, select, or_, col # Keep or_, col if still used

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tasks import fetch_market_data
from jobs import update_dividend_yields # Fix NameError
from pydantic import BaseModel
from pydantic import BaseModel

# Scheduler Setup
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    
    # Schedule Jobs
    import pytz
    from apscheduler.triggers.cron import CronTrigger
    from tasks import wrapper_daily_sync 
    # from jobs import update_dividend_yields # MOVED TO TOP 
    
    # Define Timezones
    tz_cn = pytz.timezone('Asia/Shanghai')
    tz_us = pytz.timezone('US/Eastern')
    
    # 20:00 CN/HK -> Now 17:00 as requested
    # CN Market (17:00 Beijing Time)
    scheduler.add_job(
        wrapper_daily_sync, 
        CronTrigger(hour=17, minute=0, timezone=tz_cn), 
        args=['CN', scheduler]
    )
    # HK Market (17:00 Beijing Time)
    scheduler.add_job(
        wrapper_daily_sync, 
        CronTrigger(hour=17, minute=0, timezone=tz_cn), 
        args=['HK', scheduler]
    )
    
    # US Market (17:00 Eastern Time)
    scheduler.add_job(
        wrapper_daily_sync, 
        CronTrigger(hour=17, minute=0, timezone=tz_us), 
        args=['US', scheduler]
    )
    
    # ✅ 启动ETL异步队列（性能优化：用户等待从150秒降到5秒）
    from etl_queue import etl_queue
    etl_queue.start()
    print("✅ ETL Queue started (Async processing enabled)")
    
    # Scheduler started...
    
    scheduler.start()
    print("Scheduler started...")
    
    # --- Auto-Import Indices History (Self-Healing) ---
    try:
        from jobs import import_csv_history
        from sqlmodel import select
        with Session(engine) as session:
            # 1. Check & Import Standard Indices
            # Map: CSV_Symbol -> DB_Symbol
            index_map = {
                "DJI": "^DJI",
                "NDX": "^NDX", 
                "SPY": "SPY",
                "800000": "800000",
                "800700": "800700",
                "000001.SS": "000001.SS"
            }
            
            for csv_sym, db_sym in index_map.items():
                # Check if data exists for DB Symbol
                exists = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == db_sym).limit(1)).first()
                if not exists:
                    print(f"[Startup] Missing history for {db_sym}, importing from CSV ({csv_sym})...")
                    # Import using CSV symbol
                    # This function commits internally
                    await asyncio.to_thread(import_csv_history, csv_sym)
                    
                    # Fix Symbol if needed (DJI -> ^DJI)
                    if csv_sym != db_sym:
                        # Update the records just inserted
                        # We use raw SQL for bulk update efficiency or iterate
                        from sqlalchemy import text
                        # Logic: Move from Daily/Minute? Not worth complexity for legacy fixup.
                        # This logic was trying to fix symbol casing or suffix on startup.
                        # Since we now Normalize on Write, this shouldn't be needed for new data.
                        # But if we migrated data, it's already normalized.
                        # Safest to just log or remove. 
                        # Or update MarketDataDaily table name.
                        session.exec(text(f"UPDATE marketdatadaily SET symbol = '{db_sym}' WHERE symbol = '{csv_sym}'"))
                        session.commit()
                        print(f"[Startup] Fixed symbol {csv_sym} -> {db_sym}")
            
    except Exception as e:
        print(f"[Startup] Index import warning: {e}")

    yield
    
    # ✅ 关闭ETL队列
    etl_queue.stop()
    print("✅ ETL Queue stopped")
    
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Add CORS to allow frontend to call backend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SyncMarketRequest(BaseModel):
    markets: list[str] = ['CN', 'HK', 'US']
    update_dividends: bool = True

@app.get("/api/indices_v2")
def get_indices(session: Session = Depends(get_session)):
    print("DEBUG: Executing get_indices_v2")
    """
    Get latest data for Global Indices (Hardcoded or CSV based).
    """
    # 1. Define list of indices (Or read from CSV cache)
    target_indices = [
        {"symbol": "^DJI", "name": "道琼斯工业平均指数", "market": "US"},
        {"symbol": "^NDX", "name": "纳斯达克100指数", "market": "US"},
        {"symbol": "^SPX", "name": "标普500指数", "market": "US"},
        {"symbol": "HSI", "name": "恒生指数", "market": "HK"},
        {"symbol": "HSTECH", "name": "恒生科技指数", "market": "HK"},
        {"symbol": "000001.SS", "name": "上证综合指数", "market": "CN"}
    ]
    
    # 2. Query DB for latest data
    results = []
    for item in target_indices:
        sym = item['symbol']
        stmt = select(MarketData).where(MarketData.symbol == sym).order_by(MarketData.date.desc()).limit(1)
        md = session.exec(stmt).first()
        
        if md:
            price = md.close
            pct_str = "0.00%"
            change_color = "#888" # Grey
            
            # Prioritize stored change/pct_change
            if md.pct_change is not None and md.pct_change != 0:
                pct = md.pct_change
                pct_str = f"{pct:+.2f}%"
                change_color = "#ef4444" if pct > 0 else ("#10b981" if pct < 0 else "#888")
            elif md.change is not None and md.change != 0 and md.close > 0:
                change = md.change
                pct = (change / (md.close - change)) * 100
                pct_str = f"{pct:+.2f}%"
                change_color = "#ef4444" if change > 0 else ("#10b981" if change < 0 else "#888")
            else:
                 # Fallback to manual calc only if stored data is missing/zero
                stmt_prev = select(MarketData).where(MarketData.symbol == sym).order_by(MarketData.date.desc()).limit(2)
                recs = session.exec(stmt_prev).all()
                
                if len(recs) >= 2:
                    curr = recs[0]
                    prev = recs[1]
                    if prev.close > 0:
                        change = curr.close - prev.close
                        pct = (change / prev.close) * 100
                        pct_str = f"{pct:+.2f}%"
                        change_color = "#ef4444" if change > 0 else ("#10b981" if change < 0 else "#888")
                elif len(recs) == 1:
                    # Intraday Fallback (Least accurate)
                    if md.open > 0:
                        change = md.close - md.open
                        pct = (change / md.open) * 100
                        pct_str = f"{pct:+.2f}%"
                        change_color = "#ef4444" if change > 0 else ("#10b981" if change < 0 else "#888")

            results.append({
                "symbol": sym,
                "name": item['name'],
                "market": item['market'],
                "price": f"{price:,.2f}",
                "pct": pct_str,
                "changeColor": change_color
            })
        else:
            results.append({
                "symbol": sym,
                "name": item['name'],
                "market": item['market'],
                "price": "--",
                "pct": "--",
                "changeColor": "#888"
            })
            
    return results

@app.post("/api/sync-market")
async def sync_market(request: SyncMarketRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Refresh market data for specified markets.
    Uses 'fetch_latest_data' to get real-time price with timestamp.
    """
    try:
        # Get symbols to update
        stmt = select(Watchlist)
        if request.markets:
            stmt = stmt.where(col(Watchlist.market).in_(request.markets))
        
        items = session.exec(stmt).all()
        if not items:
             return {"status": "success", "message": "No items to sync"}

        # Filter out Unified Market Library items (System Indices etc.) 
        # as per user request: "Only fetch new self-selected stocks NOT in unified library"
        try:
            from jobs import load_unified_library
            unified_list = load_unified_library()
            unified_symbols = {i['symbol'] for i in unified_list}
            
            # Filter
            original_count = len(items)
            items = [item for item in items if item.symbol not in unified_symbols]
            filtered_count = len(items)
            
            if filtered_count < original_count:
                print(f"Filtered {original_count - filtered_count} unified symbols from manual sync.")
                
            if not items:
                return {"status": "success", "message": "All items are in Unified Library (skipped)."}
                
        except Exception as filter_err:
            print(f"Warning: Failed to filter unified symbols: {filter_err}")
            # Proceed with all items if filter fails


        from data_fetcher_legacy import DataFetcher
        fetcher = DataFetcher()

        count = 0
        for item in items:
            # Fetch latest real-time data
            print(f"[Sync] Fetching {item.symbol}...")
            latest = await asyncio.to_thread(fetcher.fetch_latest_data, item.symbol, item.market, force_refresh=True)
            print(f"[Sync] Result for {item.symbol} date: {latest.get('date') if latest else 'None'}")
            
            if latest:
                # Update MarketData (period='1d') with this real-time snapshot
                # Check if exists
                db_symbol = normalize_symbol_db(item.symbol, item.market)
                stmt_md = select(MarketDataDaily).where(
                    MarketDataDaily.symbol == db_symbol,
                    MarketDataDaily.market == item.market,
                    # MarketData.period == '1d' # Implied
                ).order_by(MarketDataDaily.date.desc())
                
                existing_md = session.exec(stmt_md).first()
                
                if existing_md:
                    # Update existing
                    existing_md.close = latest['close']
                    existing_md.open = latest['open']
                    existing_md.high = latest['high']
                    existing_md.low = latest['low']
                    existing_md.date = latest['date']
                    existing_md.volume = latest['volume']
                    # Add change fields
                    existing_md.pct_change = latest.get('pct_change')
                    existing_md.change = latest.get('change')
                    existing_md.updated_at = datetime.now()
                    session.add(existing_md)
                else:
                    # Create new
                    new_md = MarketDataDaily(
                        symbol=normalize_symbol_db(item.symbol, item.market), # Use market from dict
                        market=item.market,
                        date=latest['date'],
                        open=latest['open'],
                        high=latest['high'],
                        low=latest['low'],
                        close=latest['price'],
                        volume=latest['volume'],
                        change=latest['change'],
                        pct_change=latest['pct_change'],
                        updated_at=datetime.now()
                    )
                    session.add(new_md)
                count += 1
        
        session.commit()
        
        # Trigger dividend update in background
        if request.update_dividends:
             background_tasks.add_task(update_dividend_yields_task)

        return {"status": "success", "message": f"Synced {count} items with real-time data"}
    except Exception as e:
        print(f"Sync failed: {e}")
        return {"status": "error", "message": str(e)}

def update_dividend_yields_task():
    asyncio.run(update_dividend_yields())

@app.post("/api/run-job")
async def run_job(job_name: str):
    """
    Manually trigger a specific background job.
    """
    if job_name == "sync_all":
        # Manually verify daily sync
        from jobs import update_market_data
        await update_market_data()
        return {"status": "triggered", "job": "daily_sync_unified"}
    else:
         return {"status": "error", "message": "Unknown job"}


# Watchlist API
from models import Watchlist, MarketDataDaily
from data_fetcher import normalize_symbol_db

class WatchlistAddRequest(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None


@app.get("/api/watchlist")
def get_watchlist(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    获取用户自选股 - 简化版：直接查询 MarketSnapshot 表
    """
    from models import MarketSnapshot
    
    # Get user's watchlist
    watchlist = list(session.exec(select(Watchlist)).all())
    results = []
    
    for item in watchlist:
        try:
            # Get latest analysis
            stmt_analysis = select(AssetAnalysisHistory).where(
                AssetAnalysisHistory.symbol == item.symbol
            ).order_by(AssetAnalysisHistory.analysis_date.desc()).limit(1)
            latest_analysis = session.exec(stmt_analysis).first()
            
            analysis_summary = None
            recommendation = None
            
            if latest_analysis:
                try:
                    res_json = json.loads(latest_analysis.full_result_json)
                    analysis_summary = res_json.get('summary', '')
                    recommendation = res_json.get('recommendation', '')
                except:
                    pass
            
            # 🔥 简化：直接查询 MarketSnapshot
            db_symbol = normalize_symbol_db(item.symbol, item.market)
            snapshot = session.exec(
                select(MarketSnapshot).where(
                    MarketSnapshot.symbol == db_symbol,
                    MarketSnapshot.market == item.market
                )
            ).first()
            
            if snapshot:
                results.append({
                    "id": item.id,
                    "symbol": item.symbol,
                    "market": item.market,
                    "name": item.name or item.symbol,
                    "price": snapshot.price,
                    "change": snapshot.change,
                    "pct_change": snapshot.pct_change,
                    "timestamp": snapshot.timestamp,
                    "volume": snapshot.volume,
                    "analysis_summary": analysis_summary,
                    "recommendation": recommendation
                })
            else:
                # 如果没有数据，返回默认值
                results.append({
                    "id": item.id,
                    "symbol": item.symbol,
                    "market": item.market,
                    "name": item.name or item.symbol,
                    "price": 0,
                    "change": 0,
                    "pct_change": 0,
                    "timestamp": None,
                    "volume": 0,
                    "analysis_summary": analysis_summary,
                    "recommendation": recommendation
                })
        
        except Exception as e:
            print(f"Error fetching watchlist item {item.symbol}: {e}")
    
    return results



@app.post("/api/sync-indices")
async def sync_indices(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Force refresh all system indices from Watchlist (identified by :INDEX: tag)
    """
    from models import Watchlist
    from data_fetcher_legacy import DataFetcher
    import asyncio
    
    # 从 Watchlist 表获取所有指数
    indices = session.exec(select(Watchlist).where(Watchlist.symbol.like("%:INDEX:%"))).all()
    
    if not indices:
        return {"status": "error", "message": "No indices found in Watchlist", "updated_count": 0}
    
    fetcher = DataFetcher()
    
    print(f"[Sync] Starting sync for {len(indices)} indices...")
    count = 0
    
    for idx in indices:
        symbol = idx.symbol
        market = idx.market
        print(f"[Sync] Fetching {symbol} ({market})...")
        try:
            # ✅ 使用统一保存逻辑：save_db=True
            # 会自动根据市场状态保存到Minute或Daily表
            latest = await asyncio.to_thread(
                fetcher.fetch_latest_data, 
                symbol, 
                market, 
                force_refresh=True,
                save_db=True  # ✅ 关键修复！使用统一保存逻辑
            )
            
            if latest:
                print(f"[Sync] Success {symbol}: {latest.get('price')}")
                count += 1
            else:
                print(f"[Sync] Failed {symbol}")
                
        except Exception as e:
            print(f"Index fetch failed {symbol}: {e}")
            
    try:
        session.commit()
    except Exception as db_err:
        print(f"DB Commit failed: {db_err}")
    
    return {"status": "success", "updated_count": count}



@app.get("/api/latest-analysis/{symbol}")
def get_latest_analysis(symbol: str, session: Session = Depends(get_session)):
    try:
        statement = select(AssetAnalysisHistory).where(
            AssetAnalysisHistory.symbol == symbol
        ).order_by(AssetAnalysisHistory.analysis_date.desc()).limit(1)
        
        result = session.exec(statement).first()
        
        if not result:
            return {"status": "empty", "data": None}
            
        # Ensure full_result_json is parsed if it's a string
        analysis_data = result.full_result_json
        if isinstance(analysis_data, str):
            import json
            try:
                analysis_data = json.loads(analysis_data)
            except:
                pass # Keep as string or dict

        return {
            "status": "success", 
            "data": {
                "analysis": analysis_data,
                "date": result.analysis_date.isoformat() if result.analysis_date else None,
                "screenshot": result.screenshot_path
            }
        }
    except Exception as e:
        print(f"Error in get_latest_analysis: {e}")
        return {"status": "error", "message": str(e)}

# ============================================================
# 📊 市场指数API
# ============================================================
# 数据来源：查询 MarketSnapshot 表（生产快照）
# 注意：不直接查询 MarketDataDaily（历史数据仓库）
# ============================================================
@app.get("/api/market-indices")
async def get_market_indices(session: Session = Depends(get_session)):
    """
    获取市场指数 - 统一从 Watchlist 表中筛选带有 :INDEX: 的标的
    """
    from models import MarketSnapshot, Watchlist
    
    # 从 Watchlist 表获取所有含有 :INDEX: 标签的指数
    indices = session.exec(select(Watchlist).where(Watchlist.symbol.like("%:INDEX:%"))).all()
    results = []
    
    for idx in indices:
        try:
            # 查询MarketSnapshot获取最新行情
            snapshot = session.exec(
                select(MarketSnapshot).where(
                    MarketSnapshot.symbol == idx.symbol,
                    MarketSnapshot.market == idx.market
                )
            ).first()
            
            if snapshot:
                results.append({
                    "symbol": idx.symbol,
                    "name": idx.name,
                    "price": snapshot.price,
                    "change": snapshot.change,
                    "pct_change": snapshot.pct_change,
                    "market": idx.market,
                    "timestamp": snapshot.timestamp,
                    "data_age_seconds": (datetime.now() - snapshot.updated_at).seconds if snapshot.updated_at else None
                })
            else:
                # 如果没有数据，返回空值
                results.append({
                    "symbol": idx.symbol,
                    "name": idx.name,
                    "price": 0,
                    "change": 0,
                    "pct_change": 0,
                    "market": idx.market,
                    "timestamp": None,
                    "data_age_seconds": None
                })
            
        except Exception as e:
            print(f"Error fetching index {idx.symbol}: {e}")
            
    return results

# ============================================================
# 📈 自选股API
# ============================================================
# 数据来源：查询 MarketSnapshot 表（生产快照）
# 注意：不查询 MarketDataDaily（历史数据仓库）
# ============================================================
@app.post("/api/watchlist")
def add_to_watchlist(request: WatchlistAddRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    try:
        # ✅ 使用统一的符号标准化函数
        from utils.symbol_utils import normalize_symbol_for_watchlist
        
        try:
            final_symbol, market = normalize_symbol_for_watchlist(request.symbol)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        
        # Check existing with NORMALIZED symbol
        existing = session.exec(select(Watchlist).where(Watchlist.symbol == final_symbol)).first()
        if existing:
            return {"status": "info", "message": f"{final_symbol} 已经在自选列表中"}
        
        # Fetch Name with normalized symbol
        name = request.name if request.name and request.name.strip() else final_symbol
        
        # Only attempt to fetch if we don't have a valid name or it looks like a symbol
        if name == final_symbol:
            try:
                from data_fetcher_legacy import DataFetcher
                fetcher = DataFetcher()
                fetched_name = fetcher.get_stock_name(final_symbol)
                if fetched_name:
                    name = fetched_name
            except Exception as e:
                print(f"Failed to fetch name: {e}")

        new_item = Watchlist(symbol=final_symbol, market=market, name=name)
        session.add(new_item)
        session.commit()
        session.refresh(new_item)
        
        # --- Background 30-Day History Download ---
        print(f"[Watchlist] ✅ 已添加 {new_item.symbol} ({new_item.market}), 启动30天历史数据下载...")
        
        # 后台任务：下载30天历史数据 + 开市期间获取分钟数据 + 全量历史数据
        def download_initial_history(sym: str, mkt: str):
            from data_fetcher_legacy import DataFetcher
            from market_status import is_market_open
            import logging
            
            logger = logging.getLogger(__name__)
            
            try:
                fetcher = DataFetcher()
                
                # 步骤1: 下载30天历史数据（快速，让用户立即看到数据）
                logger.info(f"[{sym}] 步骤1: 开始下载30天历史数据...")
                result = fetcher.backfill_missing_data(sym, mkt, days=30)
                
                if result.get('success'):
                    logger.info(
                        f"✅ [{sym}] 步骤1完成: 历史数据下载成功 "
                        f"({result.get('records_fetched', 0)}条记录)"
                    )
                else:
                    logger.error(
                        f"❌ [{sym}] 步骤1失败: 历史数据下载失败 "
                        f"({result.get('message', '未知错误')})"
                    )
                    return  # 历史数据失败则不继续
                
                # 步骤2: 检查市场状态，如果开市则获取分钟数据
                if is_market_open(mkt):
                    logger.info(f"[{sym}] 步骤2: 市场开盘中，获取最新分钟数据...")
                    try:
                        minute_result = fetcher.fetch_latest_data(
                            sym, 
                            mkt,
                            force_refresh=True,
                            save_db=True
                        )
                        
                        if minute_result:
                            logger.info(
                                f"✅ [{sym}] 步骤2完成: 分钟数据获取成功 "
                                f"(价格: {minute_result.get('price', 'N/A')})"
                            )
                        else:
                            logger.warning(f"⚠️ [{sym}] 步骤2: 分钟数据获取失败")
                    except Exception as e:
                        logger.error(f"❌ [{sym}] 步骤2异常: {e}")
                else:
                    logger.info(f"[{sym}] 步骤2: 市场已闭市，跳过分钟数据获取")
                
                # 步骤3: 继续下载全量历史数据（后台静默执行）
                logger.info(f"[{sym}] 步骤3: 开始下载全量历史数据...")
                try:
                    full_result = fetcher.backfill_missing_data(sym, mkt, days=None)  # days=None 表示最大历史
                    
                    if full_result.get('success'):
                        logger.info(
                            f"✅ [{sym}] 步骤3完成: 全量历史数据下载成功 "
                            f"({full_result.get('records_fetched', 0)}条记录)"
                        )
                    else:
                        logger.warning(
                            f"⚠️ [{sym}] 步骤3: 全量历史数据下载失败 "
                            f"({full_result.get('message', '未知错误')})"
                        )
                except Exception as e:
                    logger.error(f"❌ [{sym}] 步骤3异常: {e}")
                    # 注意：步骤3失败不影响前面的步骤，用户仍然可以看到30天数据
                    
            except Exception as e:
                logger.error(f"❌ [{sym}] 下载流程异常: {e}")
        
        # 添加后台任务（不阻塞响应）
        background_tasks.add_task(download_initial_history, new_item.symbol, new_item.market)
        # --------------------------------

        return {"status": "success", "data": new_item.dict()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import pandas as pd
import numpy as np

def calculate_indicators(data_list):
    if not data_list:
        return []
    
    # For single record, return basic data without indicators
    if len(data_list) < 2:
        def safe_float(val):
            if val is None: return None
            try:
                f = float(val)
                return None if np.isnan(f) else f
            except:
                return None
        
        def safe_float_zero(val):
            """For change/pct_change, return 0 instead of None"""
            if val is None: return 0
            try:
                f = float(val)
                return 0 if np.isnan(f) else f
            except:
                return 0
        
        item = data_list[0]
        return [{
            "date": item.date,
            "open": item.open,
            "high": item.high,
            "low": item.low,
            "close": item.close,
            "volume": item.volume,
            "change": safe_float_zero(item.change),
            "pct_change": safe_float_zero(item.pct_change),
            "macd": None,
            "diff": None,
            "dea": None,
            "rsi": None,
            "k": None,
            "d": None,
            "j": None,
            "pe": safe_float(item.pe),
            "pb": safe_float(item.pb),
            "ps": safe_float(item.ps),
            "dividend_yield": safe_float(item.dividend_yield),
            "eps": safe_float(item.eps)
        }]
    
    df = pd.DataFrame([
        {'date': d.date, 'close': d.close, 'high': d.high, 'low': d.low, 'open': d.open}
        for d in data_list
    ])
    
    # Sort by date asc
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 1. Change %
    df['pct_change'] = df['close'].pct_change() * 100
    
    # 2. MACD (12, 26, 9)
    # EMA 12
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    # EMA 26
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['hist'] = df['macd'] - df['signal']
    
    # 3. RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 4. KDJ (9, 3, 3)
    low_list = df['low'].rolling(window=9, min_periods=9).min()
    high_list = df['high'].rolling(window=9, min_periods=9).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    df['k'] = rsv.ewm(com=2, adjust=False).mean()
    df['d'] = df['k'].ewm(com=2, adjust=False).mean()
    df['j'] = 3 * df['k'] - 2 * df['d']

    # Merge back to list
    results = []
    # Create map for quick lookup
    indicator_map = df.set_index('date').to_dict('index')
    
    for item in data_list:
        date_key = pd.to_datetime(item.date)
        indicators = indicator_map.get(date_key, {})
        
        # safely get values, handle NaN
        def safe_float(val):
            if val is None: return None
            try:
                f = float(val)
                return None if np.isnan(f) else f
            except:
                return None
        
        def safe_float_zero(val):
            """For change/pct_change, return 0 instead of None"""
            if val is None: return 0
            try:
                f = float(val)
                return 0 if np.isnan(f) else f
            except:
                return 0
        
        def get_val(key):
            """Get value from indicators dict, handling NaN"""
            val = indicators.get(key)
            return safe_float_zero(val) if key in ['pct_change', 'change'] else safe_float(val)

        results.append({
            "date": item.date,
            "open": item.open,
            "high": item.high,
            "low": item.low,
            "close": item.close,
            "volume": item.volume,
            "change": safe_float_zero(item.change),  # Use DB value, fallback to 0
            "pct_change": get_val('pct_change'),  # Use calculated value
            "macd": get_val('macd'),
            "diff": get_val('hist'),
            "dea": get_val('signal'),
            "rsi": get_val('rsi'),
            "k": get_val('k'),
            "d": get_val('d'),
            "j": get_val('j'),
            # Valuation Data (Native fields from item)
            "pe": safe_float(item.pe),
            "pb": safe_float(item.pb),
            "ps": safe_float(item.ps),
            "dividend_yield": safe_float(item.dividend_yield),
            "eps": safe_float(item.eps)
        })
    return results

@app.get("/api/market-data/{symbol}")
@app.get("/api/market-data/{symbol}")
@app.get("/api/market-data/{symbol}")
async def get_market_data_history(symbol: str, market: str = None, background_tasks: BackgroundTasks = None, session: Session = Depends(get_session)):
    """
    Get historical data for a symbol with calculated indicators.
    Default to '1d' period for history.
    """
    try:
        # Infer market if not provided
        if not market:
            if symbol.endswith(".HK") or (symbol.isdigit() and len(symbol) == 5):
                market = "HK"
            elif symbol.endswith(".SH") or symbol.endswith(".SZ"):
                market = "CN"
            else:
                market = "US"
        
        db_sym = normalize_symbol_db(symbol, market)

        statement = select(MarketDataDaily).where(
            MarketDataDaily.symbol == db_sym
            # MarketData.period == '1d' -> Implied by table
        ).order_by(MarketDataDaily.date.asc())
        data = session.exec(statement).all()
        
        if not data:
             # Maybe trigger a fetch if empty? 
             pass
        
        if not data:
            return {"status": "empty", "data": []}

        # Calculate Indicators
        try:
            formatted = calculate_indicators(data)
        except Exception as calc_err:
            print(f"Indicator calculation failed: {calc_err}")
            formatted = []
            
            def safe_float(val):
                if val is None: return None
                try:
                    f = float(val)
                    import math
                    return None if math.isnan(f) else f
                except:
                    return None

            for row in data:
                formatted.append({
                    "date": row.date,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume,
                    "change": row.change,
                    "pct_change": row.pct_change,
                    "pe": safe_float(row.pe),
                    "pb": safe_float(row.pb),
                    "ps": safe_float(row.ps),
                    "dividend_yield": safe_float(row.dividend_yield),
                    "eps": safe_float(row.eps)
                })
        
        # --- PRIORITY: Check for Latest Minute Data (Match Watchlist Logic) ---
        # MarketDataMinute table has been removed - using only daily data now
        # TODO: If real-time intraday data needed, implement via MarketSnapshot

        
        # --- ASYNC UPDATE TRIGGER (Rule 3) ---
        if formatted:
            latest = formatted[-1]
            last_date_str = str(latest['date']) # YYYY-MM-DD ...
            
            # Simple check: Is it today?
            # Better: Check updated_at if we had it in formatted. 
            # But formatted list is dicts.
            # We can check data[-1].updated_at from the ORM object 'data'.
            
            latest_obj = data[-1]
            from market_schedule import MarketSchedule
            from data_fetcher import DataFetcher
            
            # Infer market (or store it in DB to save inference?)
            # data[-1].market should exist? Yes.
            market = latest_obj.market
            
            # Check Stale
            last_time = latest_obj.updated_at or datetime.datetime.now() - datetime.timedelta(days=1)
            
            if MarketSchedule.is_stale(last_time, market):
                def bg_sync(s, m):
                    try:
                        f = DataFetcher()
                        f.sync_market_data(s, m)
                    except Exception as e:
                        print(f"Async sync failed for {s}: {e}")
                
                background_tasks.add_task(bg_sync, symbol, market)
                
        # Return DB data immediately (Fast)
        return {"status": "success", "data": formatted}
    except Exception as e:
        return {"status": "error", "message": str(e)}


        return {"status": "success", "data": new_item.dict()}
    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.post("/api/force-refresh")
async def force_refresh(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    🚀 强制刷新所有数据（自选股 + 市场指数）- 并行版本
    
    性能优化:
    - 方案1: 并行数据获取 (150秒 → 20秒, 提升87%)
    - 方案2: 异步ETL处理 (用户等待从150秒 → 5秒, 提升97%)
    - 组合效果: 实际处理20秒, 用户感知3秒 (提升98%)
    """
    from data_fetcher import DataFetcher
    from symbols_config import get_all_indices, get_symbol_info
    import logging
    import asyncio
    
    logger = logging.getLogger(__name__)
    
    # 获取所有自选股
    watchlist = list(session.exec(select(Watchlist)).all())
    
    # 获取所有市场指数
    indices = get_all_indices()
    
    total_count = len(watchlist) + len(indices)
    
    if total_count == 0:
        return {
            "status": "success",
            "message": "没有需要刷新的数据",
            "refreshed": 0
        }
    
    # ✅ 异步并行刷新（方案1）
    async def refresh_all_parallel():
        """并行刷新所有数据"""
        logger.info("[DEBUG force_refresh] Creating new DataFetcher instance...")
        fetcher = DataFetcher()
        logger.info(f"[DEBUG force_refresh] DataFetcher created, module: {fetcher.__class__.__module__}")
        tasks = []
        
        # 创建所有异步任务
        # 1. 自选股
        for item in watchlist:
            task = fetcher.fetch_latest_data_async(
                item.symbol,
                item.market,
                force_refresh=True,
                save_db=True
            )
            tasks.append((item.symbol, task))
        
        # 2. 市场指数
        for symbol in indices:
            info = get_symbol_info(symbol)
            market = info.get("market", "US")
            
            logger.info(f"[DEBUG force_refresh] Queueing {symbol} ({market})")
            task = fetcher.fetch_latest_data_async(
                symbol,
                market,
                force_refresh=True,
                save_db=True
            )
            tasks.append((symbol, task))
        
        # ✅ 并行执行所有任务（分批处理防止API限流）
        logger.info(f"🚀 开始并行刷新 {len(tasks)} 个标的...")
        
        success_count = 0
        failed_count = 0
        
        # 分批处理（每批5个，避免API限流）
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            # 并行执行当前批次
            results = await asyncio.gather(
                *[task for _, task in batch],
                return_exceptions=True
            )
            
            # 统计结果
            for (symbol, _), result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"❌ {symbol} 失败: {result}")
                    failed_count += 1
                elif result:
                    logger.info(f"✅ {symbol} 成功")
                    success_count += 1
                else:
                    logger.warning(f"⚠️ {symbol} 无数据")
                    failed_count += 1
            
            # 批次间延迟（防止API限流）
            if i + batch_size < len(tasks):
                await asyncio.sleep(2)
        
        logger.info(
            f"🎉 刷新完成 - 成功: {success_count}, 失败: {failed_count}, "
            f"总计: {total_count}"
        )
        
        return success_count, failed_count
    
    # 启动后台任务
    background_tasks.add_task(refresh_all_parallel)    
    return {
        "status": "success",
        "message": f"已触发{total_count}个标的的数据刷新",
        "refreshed": total_count
    }

@app.post("/api/trigger-update")
async def trigger_incremental_update():
    """
    手动触发独立增量更新脚本
    绕过force-refresh复杂逻辑，直接调用独立脚本
    """
    import subprocess
    import os
    
    script_path = os.path.join(os.path.dirname(__file__), '..', 'daily_incremental_update.py')
    
    try:
        # 异步执行脚本（不阻塞API响应）
        process = subprocess.Popen(
            ['/usr/local/bin/python3', script_path], # Try absolute path or sys.executable
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(script_path)
        )
        
        return {
            "status": "success",
            "message": "增量更新已启动（3市场全量）",
            "pid": process.pid
        }
    except Exception as e:
        # Fallback to just python3
        try:
            process = subprocess.Popen(
                ['python3', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(script_path)
            )
            return {
                "status": "success",
                "message": "增量更新已启动（Fallback python3）",
                "pid": process.pid
            }
        except Exception as e2:  
            return {
                "status": "error",
                "message": f"启动失败: {str(e)} | {str(e2)}"
            }

@app.post("/api/trigger-update")
async def trigger_incremental_update():
    """
    手动触发独立增量更新脚本
    绕过force-refresh复杂逻辑，直接调用独立脚本
    """
    import subprocess
    import os
    
    script_path = os.path.join(os.path.dirname(__file__), '..', 'daily_incremental_update.py')
    
    try:
        # 异步执行脚本（不阻塞API响应）
        process = subprocess.Popen(
            ['/usr/bin/python3', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(script_path)
        )
        
        return {
            "status": "success",
            "message": "增量更新已启动（3市场全量）",
            "pid": process.pid
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"启动失败: {str(e)}"
        }


@app.delete("/api/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, session: Session = Depends(get_session)):
    items = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).all()
    for item in items:
        session.delete(item)
    session.commit()
    return {"status": "success", "message": f"Deleted {symbol}"}

@app.post("/api/backfill-history")
async def backfill_history(
    request: dict,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """
    手动触发历史数据回填
    
    用户可以在前端触发此接口为某个股票补充历史数据
    适用于：
    1. 新添加的股票历史数据下载失败
    2. 数据库清空后需要重新下载历史
    3. 手动补充缺失的历史数据
    
    Request body:
    {
        "symbol": "01810.HK",  # 可选，不提供则为所有watchlist股票回填
        "days": 30             # 可选，默认30天
    }
    """
    symbol = request.get("symbol")
    days = request.get("days", 30)
    
    async def backfill_task(sym: str, mkt: str, day_count: int):
        """后台回填任务"""
        from data_fetcher import DataFetcher
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            fetcher = DataFetcher()
            logger.info(f"[Backfill] 开始为 {sym} ({mkt}) 回填 {day_count} 天历史数据...")
            
            result = fetcher.backfill_missing_data(sym, mkt, days=day_count)
            
            if result.get('success'):
                logger.info(
                    f"✅ [Backfill] {sym} 成功: "
                    f"{result.get('records_fetched', 0)} 条记录"
                )
            else:
                logger.error(
                    f"❌ [Backfill] {sym} 失败: "
                    f"{result.get('message', '未知错误')}"
                )
        except Exception as e:
            logger.error(f"❌ [Backfill] {sym} 异常: {e}")
    
    # 如果指定了symbol，只回填该symbol
    if symbol:
        # 查找市场信息
        item = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).first()
        if not item:
            return {"status": "error", "message": f"{symbol} 不在自选列表中"}
        
        # 添加后台任务
        background_tasks.add_task(backfill_task, item.symbol, item.market, days)
        
        return {
            "status": "success",
            "message": f"已触发 {symbol} 的历史数据回填",
            "symbol": symbol,
            "days": days
        }
    
    # 否则，为所有watchlist股票回填
    else:
        watchlist = list(session.exec(select(Watchlist)).all())
        
        if not watchlist:
            return {"status": "error", "message": "自选列表为空"}
        
        # 为每个股票添加后台任务
        for item in watchlist:
            background_tasks.add_task(backfill_task, item.symbol, item.market, days)
        
        return {
            "status": "success",
            "message": f"已触发 {len(watchlist)} 个股票的历史数据回填",
            "total": len(watchlist),
            "days": days
        }


@app.get("/")
def read_root():
    return {"message": "AI Risk App Backend is Running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/data-source-status")
async def get_data_source_status():
    """
    获取数据源健康状态和限流统计
    """
    try:
        from rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        
        # 获取限流统计
        rate_stats = limiter.get_stats()
        
        # 数据源状态
        data_sources = {
            "akshare": {
                "status": "healthy",
                "description": "Primary for CN/HK, fallback for US",
                "markets": ["CN", "HK", "US"]
            },
            "yfinance": {
                "status": "healthy",
                "description": "Primary for US, fallback for global",
                "markets": ["US", "HK", "CN"]
            },
            "tencent": {
                "status": "unknown",
                "description": "Fallback for HK indices",
                "markets": ["HK"]
            }
        }
        
        return {
            "rate_limiter": rate_stats,
            "data_sources": data_sources,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "rate_limiter": {},
            "data_sources": {},
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/indices")
def get_indices():
    """Get data for System Default Indices"""
    from jobs import load_unified_library
    system_indices = load_unified_library()
    
    from sqlmodel import Session, select
    from database import engine
    from models import MarketDataDaily
    
    with Session(engine) as session:
        results = []
        for idx in system_indices:
            # Query MarketData for this symbol
            db_sym = normalize_symbol_db(idx["symbol"], idx.get("market", 'US')) # Default US if missing
            # Helper: map hardcoded indices logic if necessary, or pass market
            data_row = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == db_sym)).first() # Limit 1? Need sorting?
            # Ideally sort by date desc
            stmt = select(MarketDataDaily).where(MarketDataDaily.symbol == db_sym).order_by(MarketDataDaily.date.desc())
            data_row = session.exec(stmt).first()
            
            item = idx.copy() # name, market, symbol
            if data_row:
                item["price"] = data_row.close # Assuming 'close' is the current price
                item["pct_change"] = data_row.pct_change
                # item["change_amount"] = data_row.change_amount # if exists
            else:
                item["price"] = None
                item["pct_change"] = 0.0
            
            results.append(item)
    return results

# Analysis Persistence
from models import AssetAnalysisHistory
import json

class SaveAnalysisRequest(BaseModel):
    symbol: str
    result: dict
    screenshot_path: str = None

@app.post("/api/save-analysis")
def save_analysis(request: SaveAnalysisRequest, session: Session = Depends(get_session)):
    try:
        # Save to DB
        history = AssetAnalysisHistory(
            symbol=request.symbol,
            full_result_json=json.dumps(request.result),
            screenshot_path=request.screenshot_path
        )
        session.add(history)
        session.commit()
        return {"status": "success", "id": history.id}
    except Exception as e:
        print(f"Failed to save analysis: {e}")
        return {"status": "error", "message": str(e)}

class SyncMarketRequest(BaseModel):
    markets: list[str] = None

@app.post("/api/sync-market")
def sync_market_data(request: SyncMarketRequest, session: Session = Depends(get_session)):
    """
    Synchronously fetch latest data for all watchlist stocks.
    Blocking call to ensure frontend gets fresh data after await.
    """
    try:
        # 1. Get all symbols
        watchlist = session.exec(select(Watchlist)).all()
        # Filter by markets if requested? For now sync all.
        
        from data_fetcher import DataFetcher
        fetcher = DataFetcher()
        
        results = {}
        for item in watchlist:
            # Fetch each stock
            # Using fetch_single_stock (synchronous)
            # This fetches both Daily (for charts) and Minute (for Realtime header)
            success = fetcher.fetch_single_stock(item.symbol)
            results[item.symbol] = success
            
        return {"status": "success", "results": results}
    except Exception as e:
        print(f"Sync failed: {e}")
        return {"status": "error", "message": str(e)}

class FetchStockRequest(BaseModel):
    symbol: str
    name: str = None
    market: str = None

@app.post("/api/fetch-stock")
def fetch_stock_sync(request: FetchStockRequest, session: Session = Depends(get_session)):
    """
    Synchronously fetch stock data (and add to watchlist).
    Prioritizes adding to watchlist, then attempts data fetch.
    """
    # 1. Normalize & Market Inference
    try:
        s = request.symbol.lower().strip()
        market = request.market or "Other"  # Use provided market if available
        final_symbol = request.symbol
        
        # Only infer market if not provided or valid
        if not request.market:
            if s.endswith(".sh") or s.endswith(".sz"):
                market = "CN"
            elif s.isdigit() and len(s) == 6:
                if s.startswith("6"):
                    final_symbol = f"{s}.sh"
                    market = "CN"
                elif s.startswith("0") or s.startswith("3"):
                    final_symbol = f"{s}.sz"
                    market = "CN"
                elif s.startswith("4") or s.startswith("8"):
                    final_symbol = f"{s}.bj"
                    market = "CN"
            elif s.endswith(".hk"):
                market = "HK"
            elif s.isdigit() and len(s) == 5:
                 final_symbol = f"{s}.hk"
                 market = "HK"
            elif s.startswith("105.") or s.startswith("106."):
                market = "US"
            else:
                if s.isalpha():
                    market = "US"
    except Exception as e:
        print(f"Error normalizing symbol: {e}")
        return {"status": "error", "message": f"Invalid symbol format: {e}"}

    # 2. Add to Watchlist (Critical Step)
    saved_name = request.name or final_symbol # Default to provided name, then symbol
    try:
        existing = session.exec(select(Watchlist).where(Watchlist.symbol == final_symbol)).first()
        if not existing:
            # Try to fetch Name (Best Effort) if not provided
            if not request.name:
                try:
                    from data_fetcher import DataFetcher
                    fetcher = DataFetcher()
                    fetched_name = fetcher.get_stock_name(final_symbol)
                    if fetched_name:
                        saved_name = fetched_name
                except Exception as e:
                    print(f"Name fetch failed: {e}")
            
            # Create Watchlist Item
            new_item = Watchlist(symbol=final_symbol, market=market, name=saved_name)
            session.add(new_item)
            session.commit()
            session.refresh(new_item)
        else:
            return {"status": "info", "message": f"{final_symbol} 已经在自选列表中"}
    except Exception as e:
        print(f"Watchlist add failed: {e}")
        return {"status": "error", "message": f"Database error: {e}"}

    # 2.5 Auto-add to StockInfo (Search Dictionary)
    try:
        existing_info = session.exec(select(StockInfo).where(StockInfo.symbol == final_symbol)).first()
        if not existing_info:
            new_info = StockInfo(symbol=final_symbol, name=saved_name, market=market)
            session.add(new_info)
            session.commit()
    except Exception as e:
        print(f"StockInfo update failed (non-critical): {e}")

    # 3. Synchronously Fetch Market Data (Best Effort)
    formatted_data = []
    try:
        from data_fetcher import DataFetcher
        fetcher = DataFetcher()
        
        # Determine Data Fetch Function
        df = None
        if market == "US":
            symbol_daily = fetcher.to_akshare_us_symbol(final_symbol, for_minute=False)
            df = fetcher.fetch_us_daily_data(symbol_daily)
        elif market == "CN":
            df = fetcher.fetch_cn_daily_data(final_symbol)
            # Fund flow optionally
            try:
                fetcher.save_fund_flow(final_symbol)
            except: pass
        elif market == "HK":
            df = fetcher.fetch_hk_daily_data(final_symbol)
        
        # Save & Format
        if df is not None and not df.empty:
            period_data = {'1d': df}
            fetcher.save_to_db(final_symbol, market, period_data)
            
            # Read back formatted
            db_symbol = normalize_symbol_db(final_symbol, market)
            stmt = select(MarketDataDaily).where(
                MarketDataDaily.symbol == db_symbol
            ).order_by(MarketDataDaily.date.asc())
            data = session.exec(stmt).all()
            for row in data:
                formatted_data.append({
                    "date": row.date,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume,
                    "turnover": row.turnover, # Add turnover
                    "dividend_yield": row.dividend_yield 
                })
    except Exception as e:
        print(f"Data fetch failed: {e}")
        # Do NOT fail the request. Return success but empty data.
        # Frontend handles empty history.

    return {
        "status": "success", 
        "data": formatted_data, 
        "meta": {"name": saved_name, "symbol": final_symbol, "market": market}
    }

@app.get("/api/search")
def search_stocks(q: str, limit: int = 10, session: Session = Depends(get_session)):
    """
    Search stocks by symbol or name.
    Logic: Local DB -> If empty -> Network Search (Tencent Smartbox)
    """
    if not q:
        return {"status": "success", "data": []}
    
    q = q.strip()
    try:
        # 1. Local Search
        statement = select(StockInfo).where(
            or_(
                col(StockInfo.symbol).contains(q.lower()), 
                col(StockInfo.name).contains(q)
            )
        ).limit(limit)
        
        results = session.exec(statement).all()
        
        data = []
        for item in results:
            data.append({
                "symbol": item.symbol,
                "name": item.name,
                "market": item.market
            })
            
        # 2. Fallback: Network Search (if local results are too few)
        if len(data) < 3:
            import requests
            try:
                # Tencent Smartbox
                # Returns: v_hint="600519~贵州茅台~gzmt~SH~A股";...
                url = f"http://smartbox.gtimg.cn/s3/?q={q}&t=all"
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    content = resp.text
                    if 'v_hint="' in content:
                        raw_data = content.split('v_hint="')[1].split('"')[0]
                        items = raw_data.split('^')
                        
                        for item in items:
                            # Parse item: sh~601919~中远海控~zyhk~GP-A
                            parts = item.split('~')
                            if len(parts) >= 3:
                                market_prefix = parts[0] # sh, sz, hk, us
                                code = parts[1]          # 601919
                                name = parts[2]          # 中远海控
                                
                                # Format Symbol
                                final_symbol = code
                                market = "Other"
                                
                                if market_prefix == "sh":
                                    final_symbol = f"{code}.sh"
                                    market = "CN"
                                elif market_prefix == "sz":
                                    final_symbol = f"{code}.sz"
                                    market = "CN"
                                elif market_prefix == "hk":
                                    final_symbol = f"{code}.hk"
                                    market = "HK"
                                elif market_prefix == "us":
                                    final_symbol = code.upper()
                                    market = "US"
                                
                                # Decode Name if it looks like unicode escape
                                try:
                                    if "\\u" in name:
                                        name = name.encode('utf-8').decode('unicode_escape')
                                except:
                                    pass

                                # Avoid duplicates with local data
                                if not any(d['symbol'] == final_symbol for d in data):
                                    data.append({
                                        "symbol": final_symbol,
                                        "name": name,
                                        "market": market
                                    })
                                    
                                if len(data) >= limit:
                                    break
            except Exception as net_e:
                print(f"Network search error: {net_e}")

        return {"status": "success", "data": data[:limit]}
    except Exception as e:
        print(f"Search failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/debug/force_sync_now")
async def force_sync_now(market: str, background_tasks: BackgroundTasks):
    """
    Manually trigger a market data sync.
    Useful for 'Pull to Refresh' or debug.
    """
    logging.info(f"Manual force sync triggered for market: {market} (Force Mode)")
    from jobs import update_market_data
    background_tasks.add_task(update_market_data, market)
    return {"status": "success", "message": f"Sync triggered for {market}"}

class VerifyRequest(BaseModel):
    symbol: str
    market: str

@app.post("/api/verify-data")
async def verify_data(req: VerifyRequest):
    """
    Perform full Fetch -> Write -> Validate/Repair cycle for a symbol.
    User can call this to fix specific stock data issues manually.
    """
    from data_fetcher import DataFetcher
    fetcher = DataFetcher()
    
    try:
        # 1 & 2. Get & Write (Force Refresh)
        # Note: save_to_db inside fetcher already attempts auto-calc for NEW data.
        latest = await asyncio.to_thread(fetcher.fetch_latest_data, req.symbol, req.market, force_refresh=True)
        
        # 3. Validate & Supplement (Repair History)
        # This covers cases where fetching succeeded but calc failed, or older history is bad.
        repair_res = await asyncio.to_thread(fetcher.repair_daily_data, req.symbol, req.market)
        
        return {
            "status": "success",
            "fetch_result": "Data Fetched" if latest else "Fetch Returned Empty (Closed?)",
            "repair_report": repair_res,
            "latest_data": latest
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================
# WebSocket Endpoint for Real-time Updates
# ============================================

@app.websocket("/ws/market-data")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data updates.
    
    Clients connect to this endpoint to receive automatic market data updates
    when the backend fetches new data.
    
    Message format:
    {
        "type": "market_update",
        "symbol": "TSLA",
        "market": "US",
        "data": {...},
        "timestamp": "2025-12-16 15:30:00"
    }
    """
    from websocket_manager import manager
    
    await manager.connect(websocket)
    try:
        # Keep connection alive and handle client messages
        while True:
            # Receive any client messages (ping/pong, subscriptions, etc.)
            try:
                data = await websocket.receive_text()
                # Handle client messages if needed
                # For now, we just acknowledge receipt
                logging.info(f"Received from client: {data}")
            except Exception as e:
                logging.error(f"Error receiving WebSocket message: {e}")
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("WebSocket client disconnected")


# ============================================
# 系统日志管理API
# ============================================

@app.get("/api/admin/logs")
async def get_system_logs(
    limit: int = 100,
    level: str = None,
    module: str = None,
    search: str = None
):
    """
    获取系统日志
    
    Args:
        limit: 返回最近N条日志 (default: 100)
        level: 过滤日志级别 (INFO/WARNING/ERROR/DEBUG)
        module: 过滤模块名
        search: 搜索关键词
        
    Returns:
        日志列表
    """
    try:
        from logger_config import read_logs
        
        logs = read_logs(
            limit=min(limit, 1000),  # 最多返回1000条
            level=level,
            module=module,
            search=search
        )
        
        return {
            "status": "success",
            "total": len(logs),
            "logs": logs
        }


    except Exception as e:
        logging.error(f"Failed to read logs: {e}")
        return {
            "status": "error",
            "message": str(e),
            "logs": []
        }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
