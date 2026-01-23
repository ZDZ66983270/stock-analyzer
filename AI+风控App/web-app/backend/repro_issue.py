import asyncio
import os
import sys
# Unset proxies
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

from data_fetcher import DataFetcher
from main import search_stocks
from sqlmodel import Session, select
from database import engine

def test_fetch_crash():
    print("--- Testing Fetch 600309.sh ---")
    fetcher = DataFetcher()
    try:
        # Simulate what /api/market-data does?
        # No, the screenshot shows GET /api/market-data/600309.sh 500
        # That endpoint calls `get_market_data_history`.
        # But wait, 500 could be in `main.py` formatting OR `data_fetcher` saving?
        # The user says "No date".
        # Let's try fetching data using DataFetcher first.
        
        # 1. Fetch CN Daily
        df = fetcher.fetch_cn_daily_data("600309.sh")
        print(f"Fetch Result type: {type(df)}")
        if df is not None:
             print(f"Rows: {len(df)}")
             print(df.tail(1))
             
             # 2. Try Save to DB (this is where conversion errors often happen)
             print("Attempting save_to_db...")
             fetcher.save_to_db("600309.sh", "CN", {"1d": df})
             print("Save successful")
             
    except Exception as e:
        print("CRASH during Fetch/Save:")
        import traceback
        traceback.print_exc()

def test_search_apple():
    print("\n--- Testing Search 'Apple' ---")
    # We need a session for search_stocks
    with Session(engine) as session:
        try:
            # Mocking dependency
            results = search_stocks(q="Apple", session=session)
            print("Search Results:")
            import json
            print(json.dumps(results, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Search failed: {e}")

if __name__ == "__main__":
    test_fetch_crash()
    test_search_apple()
