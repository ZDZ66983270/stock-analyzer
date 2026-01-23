
import logging
import sys
sys.path.append('backend')
from sqlmodel import Session, create_engine, select

from backend.models import RawMarketData, MarketDataDaily
from backend.etl_service import ETLService
from backend.market_status import is_market_open, get_market_time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ETLService")
logger.setLevel(logging.INFO)

engine = create_engine('sqlite:///backend/database.db')
raw_id = 176

print(f"--- Debugging Reprint ID {raw_id} ---")

# 1. Reset Processed
with Session(engine) as session:
    raw = session.get(RawMarketData, raw_id)
    raw.processed = False
    session.add(raw)
    session.commit()
    print("Reset processed = False")

# 2. Check Market Status
market = 'HK'
open_status = is_market_open(market)
market_time = get_market_time(market)
print(f"Market: {market}")
print(f"Is Open: {open_status}")
print(f"Market Time: {market_time}")

# 3. Process
print("Calling ETLService.process_raw_data...")
ETLService.process_raw_data(raw_id)
print("Done.")

# 4. Check Result
with Session(engine) as session:
    daily = session.exec(
        select(MarketDataDaily)
        .where(MarketDataDaily.symbol == 'HK:STOCK:09988')
        .order_by(MarketDataDaily.timestamp.desc())
    ).first()
    print(f"Final Daily Close: {daily.close}")
    print(f"Final Daily Time: {daily.timestamp}")
