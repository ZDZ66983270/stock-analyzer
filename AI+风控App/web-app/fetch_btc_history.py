
import yfinance as yf
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily

def fetch_and_process_btc():
    symbol = "BTC-USD"
    market = "CRYPTO" # Custom market tag
    print(f"🚀 Downloading 10 years of history for {symbol}...")
    
    # 1. Download data
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="10y", interval="1d")
    
    if df.empty:
        print("❌ Failed to download data from Yahoo Finance.")
        return

    print(f"✅ Downloaded {len(df)} rows. Processing ETL...")

    # 2. ETL Logic (Calculate prev_close, change, pct_change)
    df = df.sort_index()
    df['prev_close'] = df['Close'].shift(1)
    df['change'] = df['Close'] - df['prev_close']
    df['pct_change'] = (df['change'] / df['prev_close']) * 100
    
    # 3. Save to DB
    with Session(engine) as session:
        count = 0
        for timestamp, row in df.iterrows():
            # Format timestamp to string YYYY-MM-DD HH:MM:SS
            # Yahoo Crypto data is often UTC 00:00:00
            ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Upsert logic
            existing = session.exec(
                select(MarketDataDaily).where(
                    MarketDataDaily.symbol == symbol,
                    MarketDataDaily.market == market,
                    MarketDataDaily.timestamp == ts_str
                )
            ).first()
            
            if existing:
                existing.open = float(row['Open'])
                existing.high = float(row['High'])
                existing.low = float(row['Low'])
                existing.close = float(row['Close'])
                existing.volume = int(row['Volume'])
                existing.prev_close = float(row['prev_close']) if pd.notnull(row['prev_close']) else None
                existing.change = float(row['change']) if pd.notnull(row['change']) else None
                existing.pct_change = float(row['pct_change']) if pd.notnull(row['pct_change']) else None
                existing.updated_at = datetime.utcnow()
                session.add(existing)
            else:
                record = MarketDataDaily(
                    symbol=symbol,
                    market=market,
                    timestamp=ts_str,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    prev_close=float(row['prev_close']) if pd.notnull(row['prev_close']) else None,
                    change=float(row['change']) if pd.notnull(row['change']) else None,
                    pct_change=float(row['pct_change']) if pd.notnull(row['pct_change']) else None,
                    updated_at=datetime.utcnow()
                )
                session.add(record)
            count += 1
            if count % 500 == 0:
                session.commit()
                print(f"   Progress: {count} rows saved...")
        
        session.commit()
    
    print(f"🎉 Successfully saved/updated {count} records for {symbol} in MarketDataDaily.")

if __name__ == "__main__":
    fetch_and_process_btc()
