from sqlmodel import Session, select, create_engine
from models import MarketData

def view_data():
    sqlite_url = f"sqlite:///backend/database.db"
    engine = create_engine(sqlite_url)

    with Session(engine) as session:
        statement = select(MarketData).limit(20)
        results = session.exec(statement).all()
        
        if not results:
            print("Database is empty (or no MarketData records found).")
            return

        print(f"{'ID':<5} {'Symbol':<12} {'Market':<8} {'Period':<8} {'Date':<20} {'Close':<10} {'Volume':<10}")
        print("-" * 80)
        for row in results:
            print(f"{row.id:<5} {row.symbol:<12} {row.market:<8} {row.period:<8} {row.date:<20} {row.close:<10.2f} {row.volume:<10}")

if __name__ == "__main__":
    view_data()
