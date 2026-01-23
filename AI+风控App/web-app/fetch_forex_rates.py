
import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from sqlmodel import Session, select
from backend.models import ForexRate
from backend.database import engine

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_forex_history(pair_symbol: str, from_curr: str, to_curr: str, days: int = 365*5):
    """
    Fetch historical forex rates from Yahoo Finance.
    pair_symbol: e.g., 'CNY=X' for USD/CNY (rate 1 USD = x CNY)
    """
    logger.info(f"Fetching history for {pair_symbol} ({from_curr}->{to_curr})...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        df = yf.download(pair_symbol, start=start_date, end=end_date, progress=False)
        if df.empty:
            logger.warning(f"No data found for {pair_symbol}")
            return

        # Handle yfinance multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            # If 'Close' is at top level
            if 'Close' in df.columns.get_level_values(0):
               df = df.xs('Close', axis=1, level=0, drop_level=True)
        
        # If we still have multi-level columns (e.g. from single ticker download structure change), flatten it or take first col
        if isinstance(df.columns, pd.MultiIndex):
             df.columns = df.columns.get_level_values(0)

        # Ensure we have a straightforward DF with just rate or just one column
        if len(df.columns) > 1 and 'Close' in df.columns:
            df = df[['Close']]
        
        records_to_add = []
        with Session(engine) as session:
            for date_idx, row in df.iterrows():
                # date_idx should be Timestamp
                date_str = date_idx.strftime('%Y-%m-%d')
                
                # row might be a Series (if multiple cols) or scalar (if one col? No, iterrows always yields Series)
                # If df has 1 column, row is a Series with name=index, value=column value
                if len(row) >= 1:
                    rate_val = float(row.iloc[0])
                else:
                    continue
                
                # Check existence
                existing = session.exec(
                    select(ForexRate).where(
                        ForexRate.date == date_str,
                        ForexRate.from_currency == from_curr,
                        ForexRate.to_currency == to_curr
                    )
                ).first()
                
                if existing:
                    existing.rate = rate_val
                    existing.updated_at = datetime.utcnow()
                    session.add(existing)
                else:
                    new_rate = ForexRate(
                        date=date_str,
                        from_currency=from_curr,
                        to_currency=to_curr,
                        rate=rate_val
                    )
                    session.add(new_rate)
            
            session.commit()
            logger.info(f"Updated {len(records_to_add) if records_to_add else 'rows'} for {pair_symbol}")

    except Exception as e:
        logger.error(f"Error fetching {pair_symbol}: {e}")

def main():
    # Define pairs to fetch
    # Yahoo Tickers:
    # CNY=X -> USD to CNY rate (1 USD = ~7.2 CNY)
    # HKD=X -> USD to HKD rate (1 USD = ~7.8 HKD)
    
    # We primarily need:
    # USD -> CNY (for visualizing US assets in CNY? Or normalizing?)
    # Usually we need to convert everything to a base currency if we were aggregating,
    # but for PE calculation, we need to convert Market Cap currency to Financial Reporting currency if they differ.
    # Case 1: Stock Price in HKD, Financials in CNY (common for H-shares). Need CNY -> HKD or HKD -> CNY.
    # Case 2: Stock Price in USD, Financials in CNY (US listed Chinese ADs). Need CNY -> USD.
    
    # Let's verify what 'CNY=X' gives. It gives CNY per USD.
    # So Rate(USD->CNY) = 'CNY=X'.
    # Rate(CNY->USD) = 1 / 'CNY=X'.
    
    # Strategy: Store canonical pairs.
    # USD/CNY (from='USD', to='CNY')
    # USD/HKD (from='USD', to='HKD')
    
    pairs = [
        ('CNY=X', 'USD', 'CNY'),
        ('HKD=X', 'USD', 'HKD'),
        # Add others if needed, e.g. CNH=X for offshore, but CNY is standard.
    ]
    
    for ticker, from_c, to_c in pairs:
        fetch_forex_history(ticker, from_c, to_c)

if __name__ == "__main__":
    main()
