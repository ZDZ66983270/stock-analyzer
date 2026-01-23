import pandas as pd
from data_fetcher import DataFetcher
from sqlmodel import Session, select, create_engine
from models import MarketData
from datetime import datetime
import os

# --- Configuration ---
# Save to market_data_library relative to backend
LIBRARY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "market_data_library")
if not os.path.exists(LIBRARY_DIR):
    os.makedirs(LIBRARY_DIR)
CSV_FILE = os.path.join(LIBRARY_DIR, "fetched_stocks.csv")
DB_FILE = "database.db"  # Use relative path or absolute if needed
DB_URL = f"sqlite:///{DB_FILE}"
# Override DB connection if needed (ensure backend/database.py matches)
# engine = create_engine(DB_URL) 
# Use backend's engine to be safe?
# But importing from database.py requires proper path if running from root vs backend.
# If running inside backend dir:
from database import engine

fetcher = DataFetcher()

# Target Stocks
symbols = [
    ("09988.hk", "HK"),
    ("00005.hk", "HK"),
    ("600309.sh", "CN"),
    ("TSLA", "US"),
    ("MSFT", "US")
]

print("--- 1. Fetching Data (InMemory) ---")
results = []
for symbol, market in symbols:
    print(f"Fetching {symbol}...")
    try:
        # save_db=False prevents auto-write
        data = fetcher.fetch_latest_data(symbol, market, force_refresh=True, save_db=False)
        if data:
            results.append(data)
            print(f"  Got price: {data.get('price')} change: {data.get('change')}")
        else:
            print(f"  Failed to get data for {symbol}")
    except Exception as e:
        print(f"  Error fetching {symbol}: {e}")

if not results:
    print("No data fetched. Exiting.")
    exit()

print(f"\n--- 2. Saving to CSV ({CSV_FILE}) ---")
df = pd.DataFrame(results)
# Flatten or select columns relevant for DB
# Ensure 'date' is string
df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
print(f"Saved {len(df)} records to {CSV_FILE}")

print("\n--- 3. Importing CSV to Database ---")
# Reload to simulate 'check'
df_import = pd.read_csv(CSV_FILE)

with Session(engine) as session:
    for _, row in df_import.iterrows():
        symbol = row['symbol']
        market = row['market']
        
        print(f"Processing {symbol} in DB...")
        
        # Find existing '1d' record
        statement = select(MarketData).where(
            MarketData.symbol == symbol,
            MarketData.market == market,
            MarketData.period == '1d'
        )
        md = session.exec(statement).first()
        
        if not md:
            print(f"  Creating NEW record for {symbol}")
            md = MarketData(
                symbol=symbol,
                market=market,
                period='1d',
                updated_at=datetime.now()
            )
        else:
            print(f"  Updating EXISTING record for {symbol}")
            md.updated_at = datetime.now()

        # Update Fields
        # Handle NaN from CSV
        def get_val(r, k, type_func=float):
            val = r.get(k)
            if pd.isna(val) or val == '--': return None
            try:
                return type_func(val)
            except:
                return None

        # Price
        price = get_val(row, 'price') or get_val(row, 'close')
        if price: md.close = price
        
        md.open = get_val(row, 'open') or md.open
        md.high = get_val(row, 'high') or md.high
        md.low = get_val(row, 'low') or md.low
        md.volume = int(get_val(row, 'volume') or 0)
        
        # Change
        change = get_val(row, 'change')
        if change is not None: md.change = change
        
        pct = get_val(row, 'pct_change')
        if pct is not None: md.pct_change = pct
        
        # Indicators
        pe = get_val(row, 'pe')
        if pe: md.pe = pe
        
        dy = get_val(row, 'dividend_yield')
        if dy: md.dividend_yield = dy

        eps = get_val(row, 'eps')
        if eps: md.eps = eps
        
        # mc = get_val(row, 'market_cap')
        # if mc: md.market_cap = mc

        # Date
        date_str = row.get('date')
        if not pd.isna(date_str): md.date = str(date_str)
        
        session.add(md)
    
    session.commit()
    print("DB Commit Successful")

print("\nDone.")
