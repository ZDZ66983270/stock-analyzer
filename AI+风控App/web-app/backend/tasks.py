from sqlmodel import Session, select, col
from database import engine, get_session
from models import Watchlist
from datetime import datetime, timedelta
import asyncio
from data_fetcher import DataFetcher
from market_schedule import MarketSchedule
import logging

logger = logging.getLogger(__name__)

async def fetch_market_data(market: str, force: bool = False) -> bool:
    """
    Fetch market data using the user's DataFetcher class.
    Unified Library: Includes both User Watchlist AND System Indices.
    Returns: True if successful (or nothing to do), False if critical failure.
    """
    logger.info(f"Starting daily market data sync for {market}...")
    
    try:
        # 1. Check Market Status
        is_open, reason = MarketSchedule.is_market_open(market)
        
        # 2. Prepare Target List (User + System)
        targets_set = set()
        
        # A) User Watchlist
        try:
            with Session(engine) as session:
                wl_items = session.exec(select(Watchlist).where(Watchlist.market == market)).all()
                for item in wl_items:
                    targets_set.add(item.symbol)
        except Exception as e:
            logger.error(f"Error reading watchlist: {e}")
            return False

        # B) System Indices (Unified Library)
        try:
            # Import inside function to avoid circular dependency if jobs.py imports tasks
            from jobs import load_unified_library
            sys_indices = load_unified_library()
            for idx in sys_indices:
                if idx.get("market") == market:
                    targets_set.add(idx["symbol"])
        except ImportError:
            logger.warning("Could not import load_unified_library from jobs.py")

        targets_list = list(targets_set)
        if not targets_list:
            logger.info(f"No symbols to sync for {market}.")
            return True

        specific_symbols = None
        
        # 3. Filter based on logic (Open vs Closed)
        if not is_open and not force:
            logger.info(f"Market {market} is CLOSED ({reason}). Checking for missing data items only.")
            
            # Check which ones are missing '1d' data for today/latest
            # Creating a session for checking
            with Session(engine) as session:
                # Optimized check: Find symbols that have a '1d' record 
                # Ideally we check date too, but for legacy compatibility we use existence first.
                # Actually, filtering by "Missing" is usually for *newly added* stocks.
                # If we want to strictly follow "Try to get data if missing", we compare lists.
                
                md_stmt = select(MarketData.symbol).where(
                    MarketData.symbol.in_(targets_list),
                    MarketData.period == '1d',
                    MarketData.market == market
                )
                existing = session.exec(md_stmt).all()
                existing_set = set(existing)
                
                specific_symbols = [s for s in targets_list if s not in existing_set]
                
            if not specific_symbols:
                logger.info(f"All {len(targets_list)} items have data. Skipping closed market sync.")
                return True
        else:
            # Market Open OR Force -> Sync All
            specific_symbols = targets_list

        if not specific_symbols:
            return True

        logger.info(f"Fetching data for {len(specific_symbols)} symbols in {market}...")

        # 4. Execute Fetch (Threaded)
        def run_fetcher():
            fetcher = DataFetcher()
            # fetch_all_stocks handles the specific_symbols filtering
            fetcher.fetch_all_stocks(
                periods=['1', '5', '15', '30'], 
                target_markets=[market],
                specific_symbols=specific_symbols
            )
            
        await asyncio.to_thread(run_fetcher)
        logger.info(f"Market data sync for {market} completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Critical error fetching data for {market}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def wrapper_daily_sync(market: str, scheduler=None):
    """
    Wrapper for daily sync with Retry Logic.
    If fails, schedules a retry in 1 hour (once).
    Also adds a random delay (1-10 mins) to avoid precise-time anti-scraping patterns.
    """
    import random
    # Delay 1 to 10 minutes (60s to 600s)
    delay_sec = random.randint(60, 600)
    logger.info(f"Scheduled Job Triggered for {market}. Safe-waiting for {delay_sec} seconds...")
    await asyncio.sleep(delay_sec)
    
    success = await fetch_market_data(market, force=True) # Force on daily schedule to ensure update
    
    if not success and scheduler:
        # Retry Logic
        retry_time = datetime.now() + timedelta(hours=1)
        logger.warning(f"Daily sync for {market} failed. Scheduling retry for {retry_time}...")
        
        scheduler.add_job(
            wrapper_daily_sync, 
            'date', 
            run_date=retry_time, 
            args=[market, None], # Pass scheduler=None to stop infinite retries
            name=f"retry_sync_{market}_{retry_time.timestamp()}"
        )

