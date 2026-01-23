from sqlmodel import Session, delete
from database import engine
from models import MarketData

def clear_data():
    with Session(engine) as session:
        print("Cleaning MarketData table ONLY (preserving Watchlist)...")
        session.exec(delete(MarketData))
        session.commit()
    print("MarketData cleared.")

if __name__ == "__main__":
    clear_data()
