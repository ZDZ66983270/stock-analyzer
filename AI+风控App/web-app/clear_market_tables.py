
import sys
import os
from sqlmodel import Session, delete, text

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine
from models import RawMarketData, MarketDataDaily, MarketSnapshot, FinancialFundamentals

def clear_tables():
    print("🧹 Cleaning up Market Data & Financials tables...")
    print("-" * 50)
    
    with Session(engine) as session:
        try:
            # 1. Clear RawMarketData
            print("Deleting RawMarketData...")
            session.exec(delete(RawMarketData))
            
            # 2. Clear MarketDataDaily
            print("Deleting MarketDataDaily...")
            session.exec(delete(MarketDataDaily))
            
            # 3. Clear MarketSnapshot
            print("Deleting MarketSnapshot...")
            session.exec(delete(MarketSnapshot))
            
            # 4. Clear FinancialFundamentals
            print("Deleting FinancialFundamentals...")
            session.exec(delete(FinancialFundamentals))
            
            session.commit()
            
            print("✅ All specified tables (Raw, Daily, Snapshot, Financials) cleared successfully.")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error clearing tables: {e}")

if __name__ == "__main__":
    clear_tables()
