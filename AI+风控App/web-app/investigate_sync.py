
from sqlmodel import SQLModel, Session, select, create_engine
from backend.models import MarketDataDaily, RawMarketData
from backend.database import engine

def investigate():
    with Session(engine) as session:
        print("\n=== 4. Production Library (MarketDataDaily - US Stocks) ===")
        stmt_md = select(MarketDataDaily).where(MarketDataDaily.symbol.in_(['TSLA', 'MSFT', 'TSLA.OQ', 'MSFT.OQ', '105.TSLA', '105.MSFT'])).order_by(MarketDataDaily.updated_at.desc())
        mds = session.exec(stmt_md).all()
        
        if mds:
            for md in mds:
                print(f"Sym: {md.symbol} | Date: {md.date} | Close: {md.close} | Updated: {md.updated_at}")
        else:
            print("No MarketDataDaily found.")

        print("\n=== 5. Raw Library (RawMarketData - US Stocks) ===")
        stmt_raw = select(RawMarketData).where(RawMarketData.symbol.in_(['TSLA', 'MSFT', 'TSLA.OQ', 'MSFT.OQ', '105.TSLA', '105.MSFT'])).order_by(RawMarketData.fetch_time.desc()).limit(5)
        raws = session.exec(stmt_raw).all()
        if raws:
            for r in raws:
                print(f"ID: {r.id} | Sym: {r.symbol} | Source: {r.source} | Period: {r.period} | FetchTime: {r.fetch_time}")
                print(f"   Payload Sample: {r.payload[:200]}...") 
        else:
            print("No RawMarketData found for US stocks.")

if __name__ == "__main__":
    investigate()
