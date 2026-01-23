
from sqlmodel import create_engine, Session, select, func
from models import Watchlist, StockInfo, MarketDataDaily

# Setup DB
engine = create_engine("sqlite:///database.db")

def inspect_indices():
    target_symbols = [
        '800000', '800700', 
        'HSI', 'HSTECH', 
        '^HSI', '^HSTECH',
        '800000.HK', '800700.HK'
    ]
    
    with Session(engine) as session:
        print("=== Watchlist Records ===")
        w_stmt = select(Watchlist).where(Watchlist.symbol.in_(target_symbols))
        w_res = session.exec(w_stmt).all()
        for w in w_res:
            print(f"Watchlist: {w.symbol} | name={w.name} | market={w.market}")
            
        print("\n=== StockInfo Records ===")
        s_stmt = select(StockInfo).where(StockInfo.symbol.in_(target_symbols))
        s_res = session.exec(s_stmt).all()
        for s in s_res:
            print(f"StockInfo: {s.symbol} | name={s.name}")

        print("\n=== MarketDataDaily Summary ===")
        for sym in target_symbols:
            stmt = select(func.count(MarketDataDaily.id)).where(MarketDataDaily.symbol == sym)
            count = session.exec(stmt).one()
            
            latest_stmt = select(MarketDataDaily).where(MarketDataDaily.symbol == sym).order_by(MarketDataDaily.date.desc()).limit(1)
            latest = session.exec(latest_stmt).first()
            
            if count > 0:
                print(f"Symbol: {sym:<10} | Count: {count:<4} | Latest: {latest.date} | Close: {latest.close} | Vol: {latest.volume}")
            else:
                pass # print(f"Symbol: {sym:<10} | Count: 0")

if __name__ == "__main__":
    inspect_indices()
