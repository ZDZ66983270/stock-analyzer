"""
Script to clear all MARKET and FINANCIAL data tables while PRESERVING configuration (Watchlist, Index).
Target Tables to Clear:
- RawMarketData
- MarketDataDaily
- MarketSnapshot
- FinancialFundamentals
- DividendFact
- SplitFact
- AssetAnalysisHistory

Preserved Tables:
- Watchlist
- Index
- StockInfo (Metadata)
- MacroData (Macro indicators)
"""
import sys
import logging
sys.path.append('backend')

from database import engine
from sqlmodel import Session, select, delete
from models import (
    RawMarketData, MarketDataDaily, MarketSnapshot, 
    FinancialFundamentals, DividendFact, SplitFact, 
    AssetAnalysisHistory
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataCleaner")

def clear_table(session, model, table_name):
    try:
        count = session.exec(select(model)).all()
        logger.info(f"🗑️  Clearing {table_name}: Found {len(count)} records.")
        session.exec(delete(model))
        session.commit()
        logger.info(f"✅ {table_name} cleared.")
    except Exception as e:
        logger.error(f"❌ Failed to clear {table_name}: {e}")
        session.rollback()

def main():
    print("="*60)
    print("🧹 Starting Data Cleanup (Preserving Watchlist/Configuration)")
    print("="*60)
    
    with Session(engine) as session:
        clear_table(session, RawMarketData, "RawMarketData")
        clear_table(session, MarketDataDaily, "MarketDataDaily")
        clear_table(session, MarketSnapshot, "MarketSnapshot")
        clear_table(session, FinancialFundamentals, "FinancialFundamentals")
        clear_table(session, DividendFact, "DividendFact")
        clear_table(session, SplitFact, "SplitFact")
        clear_table(session, AssetAnalysisHistory, "AssetAnalysisHistory")

    print("\n" + "="*60)
    print("🎉 Cleanup Complete! All market/financial data has been wiped.")
    print("   Watchlist and Index configurations are preserved.")
    print("="*60)

if __name__ == "__main__":
    main()
