from sqlmodel import Session, select
from database import get_session, engine
from models import MarketData, Watchlist

def inspect_msft():
    with Session(engine) as session:
        # Check Watchlist
        w_items = session.exec(select(Watchlist).where(Watchlist.symbol.ilike('%MSFT%'))).all()
        print(f"Watchlist Matches: {[i.symbol for i in w_items]}")
        
        # Check MarketData
        m_items = session.exec(select(MarketData).where(MarketData.symbol.ilike('%MSFT%')).order_by(MarketData.date.desc()).limit(5)).all()
        print(f"MarketData Matches ({len(m_items)}):")
        for m in m_items:
            print(f"Symbol: {m.symbol} | Date: {m.date} | Close: {m.close}")

if __name__ == "__main__":
    inspect_msft()
