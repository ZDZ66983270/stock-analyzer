from fastapi import FastAPI, BackgroundTasks, Depends
from sqlmodel import Session, select
from database import get_session
from models import Watchlist
from data_fetcher import DataFetcher
import logging

app = FastAPI()  # Mock app for context, not running

def sync_market_logic(session: Session):
    # 1. Get all symbols
    watchlist = session.exec(select(Watchlist)).all()
    symbols = [item.symbol for item in watchlist]
    
    # 2. Fetch synchronously
    fetcher = DataFetcher()
    results = {}
    for symbol in symbols:
        try:
            # We use fetch_single_stock which wraps daily+minute fetching
            success = fetcher.fetch_single_stock(symbol)
            results[symbol] = "Success" if success else "Failed"
        except Exception as e:
            results[symbol] = f"Error: {e}"
            
    return results
