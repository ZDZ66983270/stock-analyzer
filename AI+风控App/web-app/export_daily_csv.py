
import sys
import os
import csv
import argparse
from datetime import datetime
from sqlmodel import Session, select
import pandas as pd

# Add backend to path
sys.path.insert(0, 'backend')
from database import engine
from models import MarketDataDaily

OUTPUT_DIR = "outputs"

def export_daily_data(target_symbol=None):
    # Determine output file
    if target_symbol:
        safe_symbol = target_symbol.replace(':', '_')
        output_file = os.path.join(OUTPUT_DIR, f"market_data_daily_{safe_symbol}.csv")
    else:
        output_file = os.path.join(OUTPUT_DIR, "market_data_daily_full.csv")
    
    print(f"🚀 Starting export of MarketDataDaily to {output_file}...")
    if target_symbol:
        print(f"🎯 Target Symbol: {target_symbol}")
    
    # Ensure directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    try:
        # Check connection
        with Session(engine) as session:
            # Query all data or filtered data
            query = select(MarketDataDaily)
            
            if target_symbol:
                query = query.where(MarketDataDaily.symbol == target_symbol)
            
            query = query.order_by(MarketDataDaily.timestamp.desc())
            
            results = session.exec(query).all()
            
            if not results:
                print("⚠️ No data found in MarketDataDaily table.")
                return
            
            print(f"📊 Found {len(results)} records. Converting to CSV...")
            
            # Convert to list of dicts
            data = []
            for row in results:
                data.append(row.model_dump())
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # 1. Define logical Column Order
            cols_order = [
                'symbol', 'market', 'timestamp', 
                'open', 'high', 'low', 'close', 'volume', 
                'change', 'pct_change', 
                'pe', 'pe_ttm', 'pb', 'ps', 'dividend_yield', 'market_cap', 
                'turnover', 'eps', 'updated_at'
            ]
            # Filter to only existing columns
            cols_to_use = [c for c in cols_order if c in df.columns]
            # Add any other columns at the end
            remaining_cols = [c for c in df.columns if c not in cols_to_use and c != 'id']
            df = df[cols_to_use + remaining_cols]
            
            # 2. Format Data for Readability
            # Round prices/metrics to 2-3 decimal places
            float_cols_2 = ['open', 'high', 'low', 'close', 'change', 'pct_change', 'pe', 'pe_ttm', 'pb', 'ps', 'eps', 'dividend_yield']
            for col in float_cols_2:
                if col in df.columns:
                    df[col] = df[col].round(3)

            # Format Market Cap and Volume to specific format if needed
            # Accessing .values to avoid index issues if any
            if 'market_cap' in df.columns:
                 # Fill NaNs with 0 to allow int conversion, or keep as is. 
                 # Better to just apply formatting to non-nulls.
                 df['market_cap'] = df['market_cap'].apply(lambda x: '{:.0f}'.format(x) if pd.notnull(x) else '')
            
            if 'volume' in df.columns:
                 df['volume'] = df['volume'].apply(lambda x: '{:.0f}'.format(x) if pd.notnull(x) else '')

            # Save to CSV
            df.to_csv(output_file, index=False, encoding='utf-8-sig') # utf-8-sig for Excel compatibility
            
            print(f"✅ Successfully exported to {output_file}")
            print(f"   Rows: {len(df)}")
            print(f"   Columns: {list(df.columns)}")
            
    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Daily Market Data')
    parser.add_argument('--symbol', type=str, help='Canonical ID to filter (e.g. US:STOCK:AAPL)')
    args = parser.parse_args()
    
    export_daily_data(args.symbol)
