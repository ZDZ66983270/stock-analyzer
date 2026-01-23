
from sqlmodel import create_engine, Session, select
from models import MarketDataDaily
from index_config import get_source_symbol

# Setup DB
engine = create_engine("sqlite:///database.db")

def check_us_indices():
    symbols = ['^DJI', '^NDX', '^SPX']
    
    with Session(engine) as session:
        print("=== Checking US Indices in DB ===")
        for sym in symbols:
            stmt = select(MarketDataDaily).where(
                MarketDataDaily.symbol == sym
            ).order_by(MarketDataDaily.date.desc()).limit(2) # Top 2
            
            recs = session.exec(stmt).all()
            for i, rec in enumerate(recs):
                print(f"[{sym}] #{i+1}: Date={rec.date} | Close={rec.close} | Change={rec.change} | Market={rec.market}")
                
            if not recs:
                print(f"[{sym}] NO DATA FOUND")
                
            # Check source mapping
            tencent_src = get_source_symbol(sym, 'tencent')
            yahoo_src = get_source_symbol(sym, 'yahoo')
            print(f"    Mapping -> Tencent: {tencent_src}, Yahoo: {yahoo_src}")

if __name__ == "__main__":
    check_us_indices()
