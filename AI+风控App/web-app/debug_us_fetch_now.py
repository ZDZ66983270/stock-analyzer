
import logging
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock environment
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

from backend.data_fetcher import DataFetcher
from backend.database import engine
from sqlmodel import Session, select
from backend.models import MarketSnapshot

def test_fetch():
    print(f"--- Starting Manual Fetch Test at {datetime.now()} ---")
    fetcher = DataFetcher()
    
    # Force fresh fetch (ignore cache if possible, but fetcher logic handles debounce)
    # We can inspect the internal logic by calling fetch_latest_data
    
    symbol = "GOOG.OQ"
    print(f"Fetching {symbol}...")
    
    # We use a dummy session context if needed, but fetcher handles its own sessions usually
    # actually fetch_latest_data doesn't take session on self, it creates one internally for saving
    
    result = fetcher.fetch_latest_data(symbol, "US")
    
    print("\n--- Fetch Result ---")
    print(result)
    
    print("\n--- Checking DB after fetch ---")
    with Session(engine) as session:
        snap = session.exec(select(MarketSnapshot).where(MarketSnapshot.symbol == 'GOOG')).first()
        if snap:
            print(f"DB Date: {snap.date}")
            print(f"DB Price: {snap.price}")
            print(f"DB Updated: {snap.updated_at}")
        else:
            print("No snapshot found")

if __name__ == "__main__":
    test_fetch()
