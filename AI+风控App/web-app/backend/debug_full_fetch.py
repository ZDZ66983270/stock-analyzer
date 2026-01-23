import os
import sys

# Unset proxy BEFORE any other imports to ensure requests/urllib pick it up
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

print("Proxy vars cleared.")

import pandas as pd
import akshare as ak
from data_fetcher import DataFetcher
from database import engine
from models import MarketData
from sqlmodel import Session, select

def debug_fetch():
    symbol = "600036.sh" # China Merchants Bank
    print(f"--- Debugging Fetch for {symbol} ---")
    
    fetcher = DataFetcher()
    
    # 1. Test Fetch CN Daily
    print("1. Calling fetch_cn_daily_data...")
    try:
        df = fetcher.fetch_cn_daily_data(symbol)
        if df is None or df.empty:
            print("ERROR: Fetch returned empty DataFrame!")
            # Try raw akshare call to see if it works
            code = "600036"
            print(f"   Trying raw ak.stock_zh_a_hist(symbol='{code}')...")
            raw_df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if raw_df is None or raw_df.empty:
                print("   Raw AkShare also returned empty!")
            else:
                print(f"   Raw AkShare OK: {len(raw_df)} rows. Columns: {raw_df.columns.tolist()}")
                print("   Last Row Raw:", raw_df.tail(1).to_dict('records'))
            return
    except Exception as e:
        print(f"ERROR calling fetch_cn_daily_data: {e}")
        return

    print(f"Fetch Success. Rows: {len(df)}")
    print("Columns:", df.columns.tolist())
    print("Last Row:")
    print(df.tail(1).to_dict('records'))

    # 2. Test Save to DB
    print("\n2. Calling save_to_db...")
    try:
        period_data = {'1d': df}
        # We need to mock the logger or just let it print
        fetcher.save_to_db(symbol, "CN", period_data)
        print("Save function executed without exception.")
    except Exception as e:
        print(f"ERROR calling save_to_db: {e}")

    # 3. Verify DB Content
    print("\n3. Verifying DB Content...")
    with Session(engine) as session:
        stmt = select(MarketData).where(MarketData.symbol == symbol).order_by(MarketData.date.desc()).limit(1)
        row = session.exec(stmt).first()
        if row:
            print(f"DB Record Found: Date={row.date}, Close={row.close}, Dividend={row.dividend_yield}")
            print(f"Volume={row.volume}, Turnover={row.turnover}")
        else:
            print("ERROR: No record found in DB after save!")

if __name__ == "__main__":
    debug_fetch()
