import yfinance as yf
import csv
import os
import logging
import asyncio
from sqlmodel import Session, select
from models import Watchlist, MarketDataDaily
from database import engine
from datetime import datetime
import pandas as pd
from data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

def load_unified_library():
    """
    Load System Indices from ALL CSV files in market_data_library.
    Supports multiple files for scalability.
    """
    library_dir = os.path.join(os.path.dirname(__file__), 'market_data_library')
    indices = []
    
    if not os.path.exists(library_dir):
        logger.warning(f"Market Library directory not found at {library_dir}")
        return []

    # Scan all CSV files
    try:
        csv_files = [f for f in os.listdir(library_dir) if f.endswith('.csv') and not f.startswith('history_')]
        for filename in csv_files:
            file_path = os.path.join(library_dir, filename)
            try:
                # Use utf-8-sig to handle Excel-generated CSVs with BOM
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    for row in reader:
                        if row.get('symbol'):
                            indices.append({
                                "symbol": row['symbol'].strip(),
                                "market": row.get('market', 'US').strip(),
                                "name": row.get('name', '').strip()
                            })
                            count += 1
                    logger.info(f"Loaded {count} symbols from {filename}")
            except Exception as file_err:
                logger.error(f"Error reading library file {filename}: {file_err}")
                
    except Exception as e:
        logger.error(f"Error scanning market library: {e}")
        
    return indices

def import_csv_history(symbol: str):
    """
    On-demand import of CSV history for a specific symbol from market_data_library.
    """
    try:
        library_dir = os.path.join(os.path.dirname(__file__), 'market_data_library')
        file_path = os.path.join(library_dir, f"history_{symbol}.csv")
        
        if not os.path.exists(file_path):
            return False

        df = pd.read_csv(file_path)
        logger.info(f"Importing history for {symbol} from CSV ({len(df)} rows)...")

        # Determine Market (Simple heuristic or pass as arg)
        market = 'US'
        if symbol.endswith('.HK') or symbol.isdigit(): market = 'HK'
        if symbol.endswith('.SS') or symbol.endswith('.SZ') or symbol.startswith('sh') or symbol.startswith('sz'): market = 'CN'
        if symbol in ['800000', '800700']: market = 'HK'
        if symbol in ['000001.SS']: market = 'CN'

        with Session(engine) as session:
            # Check if we already have data to avoid dupes/slow writes
            # If DB has data, we assume it's populated.
            existing = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).limit(1)).first()
            if existing:
                logger.info(f"History already exists for {symbol}. Skipping CSV import.")
                return True

            for _, row in df.iterrows():
                try:
                    date_val = str(row.get('date') or row.get('日期') or row.get('Time') or row.get('时间'))
                    # Clean date string
                    if ' ' in date_val: 
                        date_val = date_val.split(' ')[0]
                    
                    # Append Market Close Time
                    if market == 'CN':
                        date_val = f"{date_val} 15:00"
                    elif market == 'HK':
                        date_val = f"{date_val} 16:00"
                    else:
                        # US: 16:00 Eastern Time (ignoring DST complexities for history for now)
                        date_val = f"{date_val} 16:00"
                    
                    price = float(row.get('close') or row.get('收盘') or 0)
                    if price == 0: continue
                    
                    md = MarketDataDaily(
                        symbol=symbol,
                        market=market,
                        date=date_val,
                        open=float(row.get('open') or row.get('开盘') or 0),
                        high=float(row.get('high') or row.get('最高') or 0),
                        low=float(row.get('low') or row.get('最低') or 0),
                        close=price,
                        volume=int(row.get('volume') or row.get('成交量') or 0),
                        updated_at=datetime.now()
                    )
                    session.add(md)
                except:
                    pass
            session.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to import history for {symbol}: {e}")
        return False

# Expose as a property or function result for compatibility
SYSTEM_INDICES = load_unified_library() # Initial load

async def update_market_data(market: str = None):
    """
    Unified Background Task to update Market Data.
    
    Args:
        market: Optional. Specify market to sync ('US', 'HK', 'CN').
                If None, sync all markets.
    
    Strategy:
    1. Skip on Sunday (non-trading day)
    2. Use DataFetcher for unified ETL pipeline
    3. Automatically triggers field normalization and WebSocket push
    """
    logger.info(f"Starting Market Data Sync for: {market or 'ALL markets'}")
    
    # 0. Check if today is Sunday - skip if so
    from datetime import datetime
    if datetime.now().weekday() == 6:  # Sunday = 6
        logger.info("Today is Sunday - skipping market data sync")
        return
    
    # 1. Prepare Target List (User + System)
    with Session(engine) as session:
        user_items = session.exec(select(Watchlist)).all()
        user_symbols = {item.symbol: item.market for item in user_items}
    
    system_indices = load_unified_library()
    targets = {}  # symbol -> market
    
    # Merge targets
    for s, m in user_symbols.items(): 
        targets[s] = m
    for idx in system_indices:
        if idx['symbol'] not in targets:
            targets[idx['symbol']] = idx['market']
    
    # Filter by market if specified
    if market:
        targets = {s: m for s, m in targets.items() if m == market}
        logger.info(f"Filtered to {market} market: {len(targets)} symbols")
    else:
        logger.info(f"Total Targets to Sync: {len(targets)} symbols across all markets")
    
    if not targets:
        logger.warning(f"No targets found for market: {market or 'ALL'}")
        return

    # 2. Use DataFetcher for ALL symbols (unified ETL pipeline)
    logger.info("=" * 60)
    logger.info("PHASE 1: Fetching Data via Unified Pipeline")
    logger.info("=" * 60)
    
    fetcher = DataFetcher()
    success_count = 0
    failure_count = 0
    
    # Group by market for logging
    from collections import defaultdict
    by_market = defaultdict(list)
    for sym, mkt in targets.items():
        by_market[mkt].append(sym)
    
    for mkt, symbols in by_market.items():
        logger.info(f"Fetching {len(symbols)} symbols for {mkt} market...")
        
        for symbol in symbols:
            try:
                # Use DataFetcher which handles:
                # - Field normalization (via FieldNormalizer)
                # - Save to RawMarketData
                # - Trigger ETL
                # - Save to MarketDataDaily
                # - Trigger WebSocket push
                result = await asyncio.to_thread(
                    fetcher.fetch_latest_data, 
                    symbol, 
                    mkt, 
                    force_refresh=True
                )
                
                if result:
                    success_count += 1
                    logger.info(f"✅ {symbol} ({mkt}) synced")
                else:
                    failure_count += 1
                    logger.warning(f"⚠️  {symbol} ({mkt}) returned no data (likely market closed)")
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"❌ {symbol} ({mkt}) failed: {e}")
    
    logger.info("=" * 60)
    logger.info(f"Sync Complete: ✅ {success_count} success, ❌ {failure_count} failed/empty")
    logger.info("=" * 60)



async def update_dividend_yields():
    logger.info("Placeholder for update_dividend_yields called.")
    pass
