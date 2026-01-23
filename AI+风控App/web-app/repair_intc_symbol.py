from sqlmodel import Session, create_engine, text
from backend.models import MarketDataDaily, MarketSnapshot, RawMarketData

engine = create_engine('sqlite:///backend/database.db')

def repair_intc():
    with Session(engine) as session:
        # 1. Update MarketDataDaily
        result = session.exec(text(
            "UPDATE marketdatadaily SET symbol = 'US:STOCK:INTC' WHERE symbol = 'INTC'"
        ))
        print(f"Updated MarketDataDaily: {result.rowcount} rows")
        
        # 2. Update MarketSnapshot
        result = session.exec(text(
            "UPDATE marketsnapshot SET symbol = 'US:STOCK:INTC' WHERE symbol = 'INTC'"
        ))
        print(f"Updated MarketSnapshot: {result.rowcount} rows")
        
        # 3. Update RawMarketData
        result = session.exec(text(
            "UPDATE rawmarketdata SET symbol = 'US:STOCK:INTC' WHERE symbol = 'INTC'"
        ))
        print(f"Updated RawMarketData: {result.rowcount} rows")
        
        session.commit()
        print("Done!")

if __name__ == "__main__":
    repair_intc()
