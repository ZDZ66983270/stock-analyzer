from sqlmodel import Session, select
from database import engine
from models import Watchlist

def check_watchlist():
    with Session(engine) as session:
        items = session.exec(select(Watchlist)).all()
        print(f"Total Watchlist Items: {len(items)}")
        for item in items:
            print(f"Symbol: {item.symbol}, Market: {item.market}, Name: {item.name}")

if __name__ == "__main__":
    check_watchlist()
