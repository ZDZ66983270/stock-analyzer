from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import MacroData

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tasks import fetch_market_data
from pydantic import BaseModel

# Scheduler Setup
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    
    # Schedule Jobs
    # 20:00 CN/HK
    scheduler.add_job(fetch_market_data, 'cron', hour=20, minute=0, args=['CN'])
    scheduler.add_job(fetch_market_data, 'cron', hour=20, minute=0, args=['HK'])
    # 10:00 US
    scheduler.add_job(fetch_market_data, 'cron', hour=10, minute=0, args=['US'])
    
    scheduler.start()
    print("Scheduler started...")
    yield
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

class SyncRequest(BaseModel):
    markets: list[str] = ['CN', 'HK', 'US']

@app.post("/api/sync-market")
async def sync_market(request: SyncRequest):
    """
    Manually trigger market sync.
    """
    print(f"Manual sync triggered for: {request.markets}")
    results = {}
    for market in request.markets:
        try:
            await fetch_market_data(market)
            results[market] = "Success"
        except Exception as e:
            results[market] = f"Failed: {str(e)}"
    
    return {"status": "completed", "details": results}


# Watchlist API
from models import Watchlist, MarketData

class WatchlistAddRequest(BaseModel):
    symbol: str


@app.get("/api/watchlist")
def get_watchlist(session: Session = Depends(get_session)):
    # Join Watchlist with latest MarketData AND latest AssetAnalysisHistory
    watchlist = session.exec(select(Watchlist)).all()
    results = []
    
    # Pre-fetch analyses to avoid N+1 (though loop is okay for small list)
    
    for item in watchlist:
        # 1. Market Data
        stmt_market = select(MarketData).where(
            MarketData.symbol == item.symbol
        ).order_by(MarketData.date.desc()).limit(1)
        latest_data = session.exec(stmt_market).first()
        
        # 2. Latest Analysis
        stmt_analysis = select(AssetAnalysisHistory).where(
            AssetAnalysisHistory.symbol == item.symbol
        ).order_by(AssetAnalysisHistory.created_at.desc()).limit(1)
        latest_analysis = session.exec(stmt_analysis).first()
        
        analysis_summary = None
        recommendation = None
        
        if latest_analysis:
            try:
                res_json = json.loads(latest_analysis.full_result_json)
                analysis_summary = res_json.get('summary', '')
                recommendation = res_json.get('recommendation', '')
                # Try to find a score if available, or infer from recommendation
            except:
                pass

        results.append({
            "id": item.id,
            "symbol": item.symbol,
            "market": item.market,
            "name": item.name or item.symbol,
            "price": latest_data.close if latest_data else None,
            "pct_change": ((latest_data.close - latest_data.open) / latest_data.open * 100) if latest_data and latest_data.open else 0,
            "analysis_summary": analysis_summary,
            "recommendation": recommendation
        })
    return results

@app.get("/api/latest-analysis/{symbol}")
def get_latest_analysis(symbol: str, session: Session = Depends(get_session)):
    stmt = select(AssetAnalysisHistory).where(
        AssetAnalysisHistory.symbol == symbol
    ).order_by(AssetAnalysisHistory.created_at.desc()).limit(1)
    analysis = session.exec(stmt).first()
    
    if not analysis:
        return {"status": "empty"}
        
    return {
        "status": "success",
        "data": json.loads(analysis.full_result_json),
        "created_at": analysis.created_at
    }

@app.post("/api/watchlist")
def add_to_watchlist(request: WatchlistAddRequest, session: Session = Depends(get_session)):
    try:
        # Check existing
        existing = session.exec(select(Watchlist).where(Watchlist.symbol == request.symbol)).first()
        if existing:
            # Idempotent success (don't error, just return existing)
            return {"status": "success", "message": "Already in watchlist", "data": existing}
        
        # Normalize Symbol and Market Inference
        s = request.symbol.lower().strip()
        market = "Other"
        final_symbol = request.symbol
        
        # CN Logic
        if s.endswith(".sh") or s.endswith(".sz"):
            market = "CN"
        elif s.isdigit() and len(s) == 6:
            # Infer market based on prefix
            if s.startswith("6"):
                final_symbol = f"{s}.sh"
                market = "CN"
            elif s.startswith("0") or s.startswith("3"):
                final_symbol = f"{s}.sz"
                market = "CN"
            elif s.startswith("4") or s.startswith("8"):
                final_symbol = f"{s}.bj" # Beijing
                market = "CN"
        # HK Logic
        elif s.endswith(".hk"):
            market = "HK"
        elif s.isdigit() and len(s) == 5:
             final_symbol = f"{s}.hk"
             market = "HK"
        # US Logic
        elif s.startswith("105.") or s.startswith("106."):
            market = "US"
        else:
            # Assume US if letters?
            if s.isalpha():
                market = "US"
        
        # Check existing with NORMALIZED symbol
        existing = session.exec(select(Watchlist).where(Watchlist.symbol == final_symbol)).first()
        if existing:
            return {"status": "success", "message": "Already in watchlist", "data": existing}
        
        # Fetch Name with normalized symbol
        name = final_symbol
        try:
            from data_fetcher import DataFetcher
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
        return {"status": "success", "data": new_item}
    except Exception as e:
        return {"status": "error", "message": str(e)}

import pandas as pd
import numpy as np

def calculate_indicators(data_list):
    if not data_list or len(data_list) < 2:
        return []
    
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
        def get_val(key):
            val = indicators.get(key)
            return float(val) if val is not None and not np.isnan(val) else None
            
        results.append({
            "date": item.date,
            "open": item.open,
            "high": item.high,
            "low": item.low,
            "close": item.close,
            "volume": item.volume,
            "pct_change": get_val('pct_change'),
            "macd": get_val('macd'),
            "diff": get_val('hist'), # often called diff in China
            "dea": get_val('signal'),
            "rsi": get_val('rsi'),
            "k": get_val('k'),
            "d": get_val('d'),
            "j": get_val('j')
        })
    return results

@app.get("/api/market-data/{symbol}")
def get_market_data_history(symbol: str, session: Session = Depends(get_session)):
    """
    Get historical data for a symbol with calculated indicators.
    """
    try:
        stmt = select(MarketData).where(
            MarketData.symbol == symbol
        ).order_by(MarketData.date.asc())
        data = session.exec(stmt).all()
        
        if not data:
            return {"status": "empty", "data": []}

        # Calculate Indicators
        try:
            formatted = calculate_indicators(data)
        except Exception as calc_err:
            print(f"Indicator calculation failed: {calc_err}")
            # Fallback to basic data
            formatted = []
            for row in data:
                formatted.append({
                    "date": row.date,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume
                })

        return {"status": "success", "data": formatted}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/api/watchlist/{symbol}")
def delete_from_watchlist(symbol: str, session: Session = Depends(get_session)):
    try:
        # Need to handle potential URL encoding or plain string
        item = session.exec(select(Watchlist).where(Watchlist.symbol == symbol)).first()
        if not item:
            return {"status": "error", "message": "Not found"}
        
        session.delete(item)
        session.commit()
        return {"status": "success", "message": f"Deleted {symbol}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def read_root():
    return {"message": "AI Risk App Backend is Running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

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

class FetchStockRequest(BaseModel):
    symbol: str

@app.post("/api/fetch-stock")
def fetch_stock_sync(request: FetchStockRequest, session: Session = Depends(get_session)):
    """
    Synchronously fetch stock data (and add to watchlist).
    Prioritizes adding to watchlist, then attempts data fetch.
    """
    # 1. Normalize & Market Inference
    try:
        s = request.symbol.lower().strip()
        market = "Other"
        final_symbol = request.symbol
        
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
    saved_name = final_symbol
    try:
        existing = session.exec(select(Watchlist).where(Watchlist.symbol == final_symbol)).first()
        if not existing:
            # Try to fetch Name (Best Effort)
            try:
                from data_fetcher import DataFetcher
                fetcher = DataFetcher()
                fetched_name = fetcher.get_stock_name(final_symbol)
                if fetched_name:
                    saved_name = fetched_name
            except Exception as e:
                print(f"Name fetch failed (continuing): {e}")
            
            new_item = Watchlist(symbol=final_symbol, market=market, name=saved_name)
            session.add(new_item)
            session.commit()
            session.refresh(new_item)
        else:
            saved_name = existing.name
    except Exception as e:
        print(f"Watchlist add failed: {e}")
        # If we can't save to watchlist, we generally can't proceed well, but let's try data fetch anyway?
        # No, report error.
        return {"status": "error", "message": f"Database error: {e}"}

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
            stmt = select(MarketData).where(
                MarketData.symbol == final_symbol
            ).order_by(MarketData.date.asc())
            data = session.exec(stmt).all()
            for row in data:
                formatted_data.append({
                    "date": row.date,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume
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
