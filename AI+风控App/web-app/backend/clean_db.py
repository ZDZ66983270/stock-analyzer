from sqlmodel import Session, delete
from database import engine
from models import Watchlist, MarketData

def clean_database():
    with Session(engine) as session:
        print("Cleaning Watchlist table...")
        session.exec(delete(Watchlist))
        
        print("Cleaning MarketData table...")
        session.exec(delete(MarketData))
        
        session.commit()
    print("Database cleanup complete. Watchlist and MarketData have been reset.")

if __name__ == "__main__":
    clean_database()
