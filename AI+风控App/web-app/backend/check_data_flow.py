
from sqlmodel import create_engine, Session, select
from models import MarketDataDaily
from data_fetcher import DataFetcher
from index_config import get_source_symbol

# Setup DB
engine = create_engine("sqlite:///database.db")

def check_flow():
    fetcher = DataFetcher()
    symbols = ['HSI', 'HSTECH']
    
    with Session(engine) as session:
        print("=== 1. Checking Download Source (Live Tencent) ===")
        for sym in symbols:
            # internal -> source
            src_sym = get_source_symbol(sym, 'tencent')
            print(f"[{sym}] Fetching from {src_sym}...")
            
            # Fetch
            data = fetcher.fetch_from_tencent(src_sym)
            if data:
                print(f"  Result: Price={data.get('price')} | Change={data.get('change')} | Pct={data.get('pct_change')} | Date={data.get('date')}")
            else:
                print("  Result: None")
                
        print("\n=== 2. Checking Production Database (MarketDataDaily) ===")
        for sym in symbols:
            stmt = select(MarketDataDaily).where(
                MarketDataDaily.symbol == sym
            ).order_by(MarketDataDaily.date.desc()).limit(1)
            
            rec = session.exec(stmt).first()
            if rec:
                print(f"[{sym}] DB Record: Price={rec.close} | Change={rec.change} | Pct={rec.pct_change} | Date={rec.date}")
            else:
                print(f"[{sym}] DB Record: None")

if __name__ == "__main__":
    check_flow()
