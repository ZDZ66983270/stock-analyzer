from sqlmodel import Session, select, create_engine
from models import StockInfo

def view_stock_info():
    sqlite_url = "sqlite:///database.db"
    engine = create_engine(sqlite_url)

    with Session(engine) as session:
        count = session.exec(select(StockInfo)).all()
        print(f"Total stocks in dictionary: {len(count)}")
        
        statement = select(StockInfo).limit(10)
        results = session.exec(statement).all()
        
        print(f"\nExample entries:")
        print(f"{'Symbol':<15} {'Name':<20} {'Market':<10}")
        print("-" * 50)
        for row in results:
            print(f"{row.symbol:<15} {row.name:<20} {row.market:<10}")

if __name__ == "__main__":
    view_stock_info()
