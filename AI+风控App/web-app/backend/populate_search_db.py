from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import StockInfo
import akshare as ak
import pandas as pd

def populate_stock_info():
    create_db_and_tables()
    
    print("Fetching all A-shares from AkShare...")
    try:
        # columns: 序号, 代码, 名称, ...
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            print("Failed to fetch stock list.")
            return

        print(f"Fetched {len(df)} stocks. Saving to DB...")
        
        with Session(engine) as session:
            # clear existing? No, maybe upsert. 
            # For simplicity, clear first to avoid duplicates if re-run
            # session.exec("DELETE FROM stockinfo") # unsafe
            
            count = 0
            for _, row in df.iterrows():
                try:
                    code = str(row['代码'])
                    name = str(row['名称'])
                    
                    # Determine market/symbol
                    market = "CN"
                    symbol = code
                    if code.startswith("6"):
                        symbol = f"{code}.sh"
                    elif code.startswith("0") or code.startswith("3"):
                        symbol = f"{code}.sz"
                    elif code.startswith("4") or code.startswith("8"):
                        symbol = f"{code}.bj"
                    
                    # Check existing
                    existing = session.exec(select(StockInfo).where(StockInfo.symbol == symbol)).first()
                    if not existing:
                        new_info = StockInfo(symbol=symbol, name=name, market=market)
                        session.add(new_info)
                        count += 1
                        
                    if count % 100 == 0:
                        session.commit()
                        print(f"Processed {count}...")
                except:
                    continue
            session.commit()
            print(f"Done. Added {count} new stocks to Search DB.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    populate_stock_info()
