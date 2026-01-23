
from sqlmodel import Session, select, create_engine
from models import MarketData

# Adjust path if needed
engine = create_engine("sqlite:///database.db")

with Session(engine) as session:
    statement = select(MarketData).where(MarketData.symbol == "600536.sh").order_by(MarketData.updated_at.desc()).limit(1)
    results = session.exec(statement).all()
    
    if results:
        data = results[0]
        print(f"Symbol: {data.symbol}")
        print(f"Date: {data.date}")
        print(f"Volume (saved in DB): {data.volume}")
        print(f"Source: {data.source if hasattr(data, 'source') else 'Unknown'}")
    else:
        print("No data found for 600536")
