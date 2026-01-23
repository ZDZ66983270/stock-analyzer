from sqlmodel import Session, select, delete
from database import engine
from models import MarketData

def clear_aapl():
    with Session(engine) as session:
        print("Deleting AAPL MarketData...")
        statement = delete(MarketData).where(MarketData.symbol.like("%AAPL%"))
        result = session.exec(statement)
        session.commit()
        print("AAPL data cleared.")

if __name__ == "__main__":
    clear_aapl()
