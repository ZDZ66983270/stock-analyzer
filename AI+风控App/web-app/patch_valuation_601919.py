from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily
from fetch_valuation_history import fetch_cn_valuation_history, save_cn_valuation_to_daily

def patch_601919():
    symbol = "CN:STOCK:601919"
    print(f"Patching valuation for {symbol}...")
    
    # Fetch Data
    df = fetch_cn_valuation_history(symbol)
    if df is not None:
        with Session(engine) as session:
            count = save_cn_valuation_to_daily(symbol, df, session)
            session.commit()
            print(f"Updated {count} records.")
    else:
        print("Failed to fetch valuation data.")

if __name__ == "__main__":
    patch_601919()
