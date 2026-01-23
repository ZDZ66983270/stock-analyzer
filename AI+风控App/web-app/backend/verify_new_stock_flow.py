
import asyncio
import logging
from sqlmodel import Session, select, delete
from database import engine
from models import Watchlist, MarketDataDaily
from jobs import update_market_data
from datetime import datetime

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestFlow")

TEST_SYMBOL = "BIDU"
TEST_MARKET = "US"

async def test_flow():
    with Session(engine) as session:
        # 1. Cleanup: Remove existing BIDU to ensure clean slate
        logger.info(f"Cleaning up {TEST_SYMBOL}...")
        session.exec(delete(Watchlist).where(Watchlist.symbol == TEST_SYMBOL))
        session.exec(delete(MarketDataDaily).where(MarketDataDaily.symbol == TEST_SYMBOL))
        session.commit()
        
        # 2. Simulate User Add
        logger.info(f"Simulating User Adding {TEST_SYMBOL}...")
        wl = Watchlist(symbol=TEST_SYMBOL, market=TEST_MARKET, created_at=datetime.now())
        session.add(wl)
        session.commit()
        
    # 3. Trigger Sync (Simulate Scheduler or API Call)
    logger.info("Triggering update_market_data()...")
    await update_market_data()
    
    # 4. Verify Result
    with Session(engine) as session:
        logger.info("Verifying MarketDataDaily...")
        # Check for 1d record
        stmt = select(MarketDataDaily).where(
            MarketDataDaily.symbol == TEST_SYMBOL,
            # MarketData.period == '1d' # Implicit
        ).order_by(MarketDataDaily.date.desc())
        
        record = session.exec(stmt).first()
        
        if record:
            logger.info(f"✅ SUCCESS! Found record for {TEST_SYMBOL}")
            logger.info(f"   Date: {record.date}")
            logger.info(f"   Price: {record.close}")
            logger.info(f"   Volume: {record.volume}")
            logger.info(f"   PE: {record.pe}")
            
            if record.close > 0:
                print("TEST_PASSED")
            else:
                print("TEST_FAILED: Price is 0")
        else:
            logger.error(f"❌ FAILED: No record found for {TEST_SYMBOL}")
            print("TEST_FAILED")

if __name__ == "__main__":
    asyncio.run(test_flow())
