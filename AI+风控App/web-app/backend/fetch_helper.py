import asyncio
from sqlmodel import Session, select
from database import engine
from models import MarketSnapshot
from data_fetcher import DataFetcher, normalize_symbol_db
from datetime import datetime


async def fetch_and_save_single_stock(symbol: str, market: str):
    """
    Background Task: Fetch data for a single newly added stock.
    Uses MarketSnapshot architecture with automatic persistence.
    """
    print(f"[Background] Starting fetch for {symbol} ({market})...")
    try:
        fetcher = DataFetcher()
        
        # Use fetch_latest_data with save_db=True for automatic persistence
        # This will automatically save to MarketSnapshot via the unified flow
        latest = await asyncio.to_thread(
            fetcher.fetch_latest_data, 
            symbol, 
            market, 
            force_refresh=True,
            save_db=True  # ✅ Auto-save to MarketSnapshot
        )
        
        if latest:
            print(f"[Background] ✅ Successfully fetched and saved data for {symbol}")
            print(f"  → Price: {latest.get('price', 'N/A')}")
            print(f"  → Change: {latest.get('pct_change', 'N/A')}%")
            print(f"  → Date: {latest.get('date', 'N/A')}")
        else:
            print(f"[Background] ⚠️ No data returned for {symbol}")
            
    except Exception as e:
        print(f"[Background] ❌ Fetch failed for {symbol}: {e}")
        import traceback
        traceback.print_exc()
