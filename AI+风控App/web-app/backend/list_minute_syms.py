
from sqlmodel import create_engine, Session, select, func
from models import MarketDataMinute

engine = create_engine("sqlite:///database.db")

with Session(engine) as session:
    stmt = select(MarketDataMinute.symbol).distinct()
    syms = session.exec(stmt).all()
    print(f"Distinct MDMinute Symbols: {syms}")
    
    count = session.exec(select(func.count(MarketDataMinute.id))).one()
    print(f"Total Rows: {count}")
    
    if count > 0:
        first = session.exec(select(MarketDataMinute).limit(1)).first()
        print(f"Sample: {first.symbol} | Vol: {first.volume} | Date: {first.date}")
