
import asyncio
import logging
from sqlmodel import Session, select, delete
from database import engine
from models import Watchlist, MarketData
from data_fetcher import DataFetcher
from datetime import datetime

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestFlow")

TEST_SYMBOL = "BIDU"
TEST_MARKET = "US"

async def test_single_flow():
    with Session(engine) as session:
        # 1. Cleanup
        logger.info(f"Cleaning up {TEST_SYMBOL}...")
        session.exec(delete(Watchlist).where(Watchlist.symbol == TEST_SYMBOL))
        session.exec(delete(MarketData).where(MarketData.symbol == TEST_SYMBOL))
        session.commit()
        
        # 2. Add
        logger.info(f"Adding {TEST_SYMBOL}...")
        wl = Watchlist(symbol=TEST_SYMBOL, market=TEST_MARKET, created_at=datetime.now())
        session.add(wl)
        session.commit()
        
    # 3. Targeted Fetch (Bypass jobs.py loop to avoid waiting for others)
    logger.info("Triggering Targeted Fetch...")
    fetcher = DataFetcher()
    # Force Refresh
    result = await asyncio.to_thread(fetcher.fetch_latest_data, TEST_SYMBOL, TEST_MARKET, force_refresh=True)
    
    logger.info(f"Fetch Result: {result}")
    
    # 4. Verify DB
    with Session(engine) as session:
        stmt = select(MarketData).where(
            MarketData.symbol == TEST_SYMBOL,
            MarketData.period == '1d'
        ).order_by(MarketData.date.desc())
        record = session.exec(stmt).first()
        
        if record:
            print("TEST_PASSED")
            print(f"Details: Price={record.close}, Vol={record.volume}")
        else:
            print("TEST_FAILED")

if __name__ == "__main__":
    asyncio.run(test_single_flow())
