
from sqlmodel import create_engine, Session, select
from models import MarketDataDaily
# Mock normalize_symbol_db
def normalize_symbol_db(symbol, market):
    # Simplified mock or import real one if possible
    # Let's import real one to be sure
    from main import normalize_symbol_db as real_norm
    return real_norm(symbol, market)

# Need to make sure main.py is importable
import sys
import os
sys.path.append(os.getcwd())

engine = create_engine("sqlite:///database.db")

def debug_indices():
    indices_map = {
        "HSI": "Constant",
        "HSTECH": "Tech",
        "000001.SS": "SSEC"
    }
    
    with Session(engine) as session:
        print("=== Debugging get_market_indices Logic ===")
        for sym, name in indices_map.items():
            # Logic from main.py
            mkt = "US"
            if sym.endswith(".SS"): mkt = "CN"
            elif sym.isdigit(): mkt = "HK"
            
            # Correction I suspect is needed:
            if sym in ['HSI', 'HSTECH']: mkt = 'HK' # This line IS MISSING in main.py
            
            print(f"Symbol: {sym} -> Inferred Market: {mkt}")
            
            # Since main.py MISSES the above line, let's test what HAPPENS with mkt="US" for HSI
            mkt_actual = "US"
            if sym.endswith(".SS"): mkt_actual = "CN"
            elif sym.isdigit(): mkt_actual = "HK"
            
            print(f"  [Main.py Logic] Inferred Market: {mkt_actual}")
            
            # Import normalize
            try:
                from main import normalize_symbol_db
                db_sym = normalize_symbol_db(sym, mkt_actual)
                print(f"  Normalized DB Symbol: {db_sym}")
                
                stmt = select(MarketDataDaily).where(
                    MarketDataDaily.symbol == db_sym,
                    MarketDataDaily.market.in_(['US', 'HK', 'CN'])
                ).order_by(MarketDataDaily.date.desc()).limit(1)
                
                latest = session.exec(stmt).first()
                if latest:
                     print(f"  -> Found Record: {latest.date} | Close: {latest.close} | Market: {latest.market}")
                else:
                     print(f"  -> NO RECORD FOUND")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    debug_indices()
