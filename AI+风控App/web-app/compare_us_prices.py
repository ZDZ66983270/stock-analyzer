
import sys
import os
import json
from sqlmodel import Session, select, func
import pandas as pd

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import engine
from backend.models import Watchlist, MarketDataDaily, MarketSnapshot, RawMarketData

def compare_prices():
    with Session(engine) as session:
        # Get all US Stocks
        stocks = session.exec(select(Watchlist).where(Watchlist.market == "US")).all()
        target_stocks = [s.symbol for s in stocks if ':STOCK:' in s.symbol]
        
        print(f"📊 Comparing Prices for {len(target_stocks)} US Stocks...")
        
        results = []
        
        for symbol in target_stocks:
            # 1. Daily
            daily = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(1)).first()
            daily_price = daily.close if daily else None
            daily_ts = daily.timestamp if daily else None
            
            # 2. Snapshot
            snap = session.exec(select(MarketSnapshot).where(MarketSnapshot.symbol == symbol)).first()
            snap_price = snap.price if snap else None
            snap_ts = snap.timestamp if snap else None
            
            # 3. Raw (Latest)
            # Raw table stores JSON payload. Need to parse.
            # Assuming 'close' or 'currentPrice' or similar in JSON.
            raw = session.exec(select(RawMarketData).where(RawMarketData.symbol == symbol).order_by(RawMarketData.fetch_time.desc()).limit(1)).first()
            raw_price = None
            raw_ts = raw.fetch_time if raw else None
            
            if raw and raw.payload:
                try:
                    data = json.loads(raw.payload)
                    # Handle VERA Wrapper structure {"data": [...]}
                    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                        items = data["data"]
                        if items:
                            last = items[-1]
                            raw_price = last.get('close') or last.get('Close')
                            # Raw timestamp inside data?
                            raw_data_ts = last.get('timestamp') or last.get('Date')
                            if raw_data_ts:
                                raw_ts = f"{raw.fetch_time} (Data: {raw_data_ts})"
                    
                    # Fallbacks
                    elif isinstance(data, list) and len(data) > 0:
                        last = data[-1]
                        raw_price = last.get('Close') or last.get('close')
                    elif isinstance(data, dict):
                         raw_price = data.get('Close') or data.get('close') or data.get('regularMarketPrice')
                except:
                    pass
            
            # Diff Check
            # Check if Snapshot == Daily
            diff_msg = ""
            if snap_price and daily_price:
                 if abs(snap_price - daily_price) > 0.01:
                     diff_msg = "⚠️ Diff"
            
            results.append({
                "Symbol": symbol,
                "Daily_Price": daily_price,
                "Daily_TS": daily_ts,
                "Snap_Price": snap_price,
                "Snap_TS": snap_ts,
                "Raw_Price": raw_price,
                "Raw_TS": str(raw_ts)[:19] if raw_ts else None,
                "Status": diff_msg
            })
            
    df = pd.DataFrame(results)
    if not df.empty:
        # Filter rows with Diff if many rows? Or show all?
        # User asked to "List all".
        
        print("\n" + "="*160)
        print(" 🇺🇸 US Stock Price Comparison (Raw vs Snapshot vs Daily)")
        print("="*160)
        print(f"{'Symbol':<15} | {'Daily Price':<12} {'Timestamp':<20} | {'Snap Price':<12} {'Timestamp':<20} | {'Raw Price':<12} {'Fetch Time':<20} | {'Status'}")
        print("-" * 160)
        
        for _, row in df.iterrows():
            d_p = f"{row['Daily_Price']:.2f}" if row['Daily_Price'] else "N/A"
            s_p = f"{row['Snap_Price']:.2f}" if row['Snap_Price'] else "N/A"
            r_p = f"{row['Raw_Price']:.2f}" if row['Raw_Price'] else "N/A"
            
            print(f"{row['Symbol']:<15} | {d_p:<12} {str(row['Daily_TS'])[:19]:<20} | {s_p:<12} {str(row['Snap_TS'])[:19]:<20} | {r_p:<12} {str(row['Raw_TS']):<20} | {row['Status']}")
            
        print("="*160)

if __name__ == "__main__":
    compare_prices()
