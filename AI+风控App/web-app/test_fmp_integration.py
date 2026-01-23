import sys
sys.path.append('backend')
from backend.database import engine, Session
from backend.models import MarketDataDaily
from fetch_valuation_history import fetch_us_valuation_history_fmp, save_us_historical_valuation_to_daily
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestFMP")

def test_aapl():
    symbol = "US:STOCK:AAPL"
    
    print(f"Testing FMP Integration for {symbol}...")
    
    # 1. Fetch
    df = fetch_us_valuation_history_fmp(symbol, limit=3)
    
    if df is None:
        print("❌ Fetch returned None")
        return
        
    print("✅ Fetch Result:")
    print(df)
    
    # 2. Save (Dry run or real save?)
    # We can try seeing if it matches existing dates.
    # To check matching, we need a DB session.
    
    with Session(engine) as session:
        count = save_us_historical_valuation_to_daily(symbol, df, session)
        print(f"✅ Saved/Updated {count} records in DB.")

if __name__ == "__main__":
    test_aapl()
