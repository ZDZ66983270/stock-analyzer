from sqlmodel import Session, select
from database import engine
from models import MarketData
from datetime import datetime
import asyncio
from data_fetcher import DataFetcher

async def fetch_market_data(market: str):
    """
    Fetch market data using the user's DataFetcher class.
    This runs the fetch_all_stocks method which saves to Excel.
    
    Args:
        market: 'CN', 'HK', or 'US' - acts as a filter for the fetch operation.
    """
    print(f"Starting market data sync for {market}...")
    
    # Run the synchronous DataFetcher in a thread to avoid blocking the async event loop
    try:
        def run_fetcher():
            fetcher = DataFetcher()
            # The fetcher reads symbols from symbols_V4.txt
            # We filter by the requested market
            fetcher.fetch_all_stocks(periods=['1', '5', '15', '30'], target_markets=[market])
            
        await asyncio.to_thread(run_fetcher)
        print(f"Market data sync for {market} completed.")
        
    except Exception as e:
        print(f"Error fetching data for {market}: {str(e)}")
