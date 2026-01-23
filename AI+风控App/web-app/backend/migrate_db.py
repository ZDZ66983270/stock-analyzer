from sqlmodel import SQLModel, create_engine, Session, select
from models import MarketData, MarketDataDaily, MarketDataMinute
import database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def normalize_symbol(symbol: str, market: str) -> str:
    """
    Standardize symbol format:
    - US: Strip suffixes like .OQ, .QQ, .N (e.g. TSLA.OQ -> TSLA)
    - CN/HK: Keep as is for now (usually numerical like 00700.hk)
    """
    if market == 'US':
        if '.' in symbol:
            # Check if suffix is exchange code (OQ, N, etc)
            base = symbol.split('.')[0]
            # Ensure we don't accidentally strip legit dots (e.g. BRK.B)
            # But for now, user mainly has TSLA.OQ, MSFT.OQ
            return base
    return symbol

def migrate():
    engine = database.engine
    SQLModel.metadata.create_all(engine) # Create new tables

    with Session(engine) as session:
        # Fetch all legacy data
        logger.info("Fetching legacy data...")
        legacy_data = session.exec(select(MarketData)).all()
        logger.info(f"Found {len(legacy_data)} rows to migrate.")

        daily_count = 0
        minute_count = 0
        
        for row in legacy_data:
            # 1. Normalize Symbol
            std_symbol = normalize_symbol(row.symbol, row.market)
            
            # 2. Map to New Model
            if row.period == '1d':
                # Check for existing to avoid duplicates (naive check)
                exists = session.exec(select(MarketDataDaily).where(
                    MarketDataDaily.symbol == std_symbol,
                    MarketDataDaily.market == row.market,
                    MarketDataDaily.date == row.date
                )).first()
                
                if exists:
                    # Overwrite if newer? Or skip?
                    # Let's assume we want to keep the latest version if duplicate exists
                    continue

                new_row = MarketDataDaily(
                    symbol=std_symbol,
                    market=row.market,
                    date=row.date,
                    open=row.open,
                    high=row.high,
                    low=row.low,
                    close=row.close,
                    volume=row.volume,
                    turnover=row.turnover,
                    change=row.change,
                    pct_change=row.pct_change,
                    prev_close=row.prev_close,
                    pe=row.pe,
                    pb=row.pb,
                    ps=row.ps,
                    dividend_yield=row.dividend_yield,
                    eps=row.eps,
                    updated_at=row.updated_at
                )
                session.add(new_row)
                daily_count += 1
            
            else:
                # Minute Data
                exists = session.exec(select(MarketDataMinute).where(
                    MarketDataMinute.symbol == std_symbol,
                    MarketDataMinute.market == row.market,
                    MarketDataMinute.period == row.period,
                    MarketDataMinute.date == row.date
                )).first()
                
                if exists:
                    continue

                new_row = MarketDataMinute(
                    symbol=std_symbol,
                    market=row.market,
                    period=row.period,
                    date=row.date,
                    open=row.open,
                    high=row.high,
                    low=row.low,
                    close=row.close,
                    volume=row.volume,
                    turnover=row.turnover,
                    updated_at=row.updated_at
                )
                session.add(new_row)
                minute_count += 1

            if (daily_count + minute_count) % 1000 == 0:
                logger.info(f"Processed {daily_count + minute_count} rows...")
                session.commit()

        session.commit()
        logger.info(f"Migration Complete. Daily: {daily_count}, Minute: {minute_count}")

if __name__ == "__main__":
    confirm = input("This will migrate data to new tables. Type 'yes' to proceed: ")
    if confirm.lower() == 'yes':
        migrate()
    else:
        print("Cancelled.")
