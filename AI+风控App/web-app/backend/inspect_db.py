from sqlmodel import Session, select, create_engine
from models import MarketData

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

target_symbols = [
    "09988.hk", "00005.hk",
    "600309.sh",
    "TSLA", "MSFT",
    "^SPX", "^DJI", "^NDX",
    "000001.SS", "800000"
]

print(f"{'Symbol':<15} {'Market':<8} {'Price':<10} {'Change':<10} {'PctChange':<10} {'Updated':<20}")
print("-" * 80)

with Session(engine) as session:
    for sym in target_symbols:
        # Check explicit symbol first
        statement = select(MarketData).where(MarketData.symbol == sym).order_by(MarketData.updated_at.desc())
        results = session.exec(statement).all()
        
        if not results:
            # Try upper case
            statement = select(MarketData).where(MarketData.symbol == sym.upper()).order_by(MarketData.updated_at.desc())
            results = session.exec(statement).all()
            
        if results:
            latest = results[0]
            close_str = f"{latest.close:.2f}" if latest.close is not None else "--"
            change_str = f"{latest.change:.2f}" if latest.change is not None else "--"
            pct_str = f"{latest.pct_change:.2f}" if latest.pct_change is not None else "--"
            print(f"{latest.symbol:<15} {latest.market:<8} {close_str:<10} {change_str:<10} {pct_str:<10} {latest.updated_at}")
        else:
            print(f"{sym:<15} {'--':<8} {'--':<10} {'--':<10} {'--':<10} {'No Data'}")
