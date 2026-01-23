from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily, MarketSnapshot

def check_601919():
    # Assuming standard CN stock format
    symbol = "CN:STOCK:601919"
    with Session(engine) as session:
        # Check MarketDataDaily
        print(f"--- MarketDataDaily for {symbol} ---")
        stmt_daily = select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(1)
        daily_record = session.exec(stmt_daily).first()
        if daily_record:
            print(f"Timestamp: {daily_record.timestamp}")
            print(f"Close: {daily_record.close}")
            print(f"PE (Static): {daily_record.pe}")
            print(f"PE (TTM): {daily_record.pe_ttm}")
        else:
            print("No daily record found.")

        # Check MarketSnapshot
        print(f"\n--- MarketSnapshot for {symbol} ---")
        stmt_snap = select(MarketSnapshot).where(MarketSnapshot.symbol == symbol)
        snap_record = session.exec(stmt_snap).first()
        if snap_record:
            print(f"Timestamp: {snap_record.timestamp}")
            print(f"Price: {snap_record.price}")
            print(f"PE (Static): {snap_record.pe}")
            print(f"PE (TTM): {snap_record.pe_ttm}")
        else:
            print("No snapshot record found.")

if __name__ == "__main__":
    check_601919()
