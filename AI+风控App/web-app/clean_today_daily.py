
from sqlmodel import Session, select, delete
from backend.database import engine
from backend.models import MarketDataDaily
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CleanBadData")

def clean_today_daily_data():
    today_str_prefix = "2026-01-14"
    
    with Session(engine) as session:
        # Find records for today
        statement = select(MarketDataDaily).where(
            MarketDataDaily.timestamp.like(f"{today_str_prefix}%"),
            MarketDataDaily.market != "WORLD"
        )
        results = session.exec(statement).all()
        
        logger.info(f"Found {len(results)} records for {today_str_prefix}")
        
        count = 0
        for rec in results:
            logger.info(f"Deleting bad daily record: {rec.symbol} {rec.timestamp} (Market={rec.market})")
            session.delete(rec)
            count += 1
            
        session.commit()
        logger.info(f"Deleted {count} records.")

if __name__ == "__main__":
    clean_today_daily_data()
