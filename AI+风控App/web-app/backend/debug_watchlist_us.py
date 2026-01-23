from sqlmodel import create_engine, Session, select
from models import Watchlist, MarketData

engine = create_engine("sqlite:///database.db")

def inspect_us_stocks():
    with Session(engine) as session:
        # Check Watchlist
        print("\n--- Watchlist (US) ---")
        stmt = select(Watchlist).where(Watchlist.market == "US")
        items = session.exec(stmt).all()
        for item in items:
            print(f"Symbol: {item.symbol}, Name: {item.name}, Market: {item.market}")
            
            # Check MarketData
            md_stmt = select(MarketData).where(
                MarketData.symbol == item.symbol, 
                MarketData.period == '1d'
            ).order_by(MarketData.date.desc())
            md = session.exec(md_stmt).first()
            if md:
                print(f"  -> DB Price: {md.close}, Date: {md.date}, Updated: {md.updated_at}")
            else:
                print(f"  -> NO DATA in MarketData")

if __name__ == "__main__":
    inspect_us_stocks()
