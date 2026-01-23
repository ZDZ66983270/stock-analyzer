import sys
import pandas as pd
import numpy as np
from sqlmodel import Session, select, update
from datetime import timedelta, datetime
from backend.database import engine
from backend.models import MarketDataDaily, FinancialFundamentals, Watchlist

def fetch_data_from_db(symbol, canonical_id):
    """
    Step 1: Data Preparation (Strictly from DB)
    """
    print(f"📦 Fetching DB data for {symbol}...")
    
    with Session(engine) as session:
        # A. Price
        query_price = select(MarketDataDaily).where(
            MarketDataDaily.symbol == canonical_id
        ).order_by(MarketDataDaily.timestamp)
        results = session.exec(query_price).all()
        data_price = [{'Date': pd.to_datetime(r.timestamp), 'Close': float(r.close)} for r in results]
        
        # B. Earnings (with EPS)
        query_fund = select(FinancialFundamentals).where(
            FinancialFundamentals.symbol == canonical_id
        ).order_by(FinancialFundamentals.as_of_date)
        results = session.exec(query_fund).all()
        # Filter for quarterly data only if possible, or use all and assume Quarterly if avail
        # For US stocks, 'as_of_date' behaves like fiscal end.
        data_earnings = []
        for r in results:
            if r.eps is not None:
                data_earnings.append({
                    'Fiscal_Date': pd.to_datetime(r.as_of_date),
                    'EPS_Raw': float(r.eps),
                    'Report_Type': r.report_type
                })
                
    df_price = pd.DataFrame(data_price)
    df_earnings = pd.DataFrame(data_earnings)
    
    return df_price, df_earnings

def calculate_pe_vera(df_price, df_earnings):
    """
    Step 2-4: Clean, Roll, Merge (VERA Protocol)
    """
    if df_price.empty or df_earnings.empty: return None

    # Filter for Quarterly data ideally? 
    # If mix of Annual/Quarterly, we need to be careful.
    # Yahoo fetch saves both. We should prioritize Quarterly for TTM calc.
    df_eps = df_earnings[df_earnings['Report_Type'] == 'quarterly'].copy()
    if df_eps.empty and not df_earnings.empty:
        # Fallback to whatever is there if labelled differently
        df_eps = df_earnings.copy()

    # Sort
    df_eps = df_eps.sort_values('Fiscal_Date')
    df_eps = df_eps.drop_duplicates(subset=['Fiscal_Date'], keep='last')

    # --- Step 2: TTM Calculation (Rolling 4Q) ---
    # Strict VERA: Sum of last 4 discrete quarters
    df_eps['EPS_TTM'] = df_eps['EPS_Raw'].rolling(window=4, min_periods=4).sum()
    
    # --- Step 3: Time Anchor ---
    # Approximate Report Date = Fiscal + 45 days
    # (In future, can scrape real report dates)
    df_eps['Report_Date'] = df_eps['Fiscal_Date'] + timedelta(days=45)
    
    # --- Step 4: Merge (AsOf Backward) ---
    df_price['Date'] = pd.to_datetime(df_price['Date']).dt.tz_localize(None)
    df_eps['Report_Date'] = pd.to_datetime(df_eps['Report_Date']).dt.tz_localize(None)

    df_price = df_price.sort_values('Date')
    df_eps = df_eps.sort_values('Report_Date')

    merged = pd.merge_asof(
        df_price,
        df_eps[['Report_Date', 'EPS_TTM']],
        left_on='Date',
        right_on='Report_Date',
        direction='backward',
        tolerance=pd.Timedelta(days=180) # If no earnings for 6 months, invalid
    )

    # Calculate PE
    merged['PE_TTM'] = merged['Close'] / merged['EPS_TTM']
    
    # Handle negative/invalid
    merged.loc[merged['EPS_TTM'] <= 0, 'PE_TTM'] = None
    merged.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    return merged

def save_to_db(canonical_id, df_result):
    """
    Step 5: Batch Update (Efficient)
    Updates MarketDataDaily.pe_ttm column.
    """
    print(f"💾 Saving {len(df_result)} PE records for {canonical_id}...")
    
    # Filter only valid PEs to save update calls
    valid_rows = df_result.dropna(subset=['PE_TTM'])
    
    if valid_rows.empty:
        print("   ⚠️ No valid PE data to save.")
        return

    # Bulk dictionary for update?
    # SQLAlchemy Core update is faster.
    # We iterate and update. For 3000 rows, batching might be needed if slow.
    # For now, simple loop with session.
    
    with Session(engine) as session:
        # Fetch existing IDs mapping to speed up?
        # Or just execute UPDATE marketdatadaily SET pe_ttm = :pe WHERE symbol = :sym AND timestamp = :ts
        
        # Prepare params list
        params = []
        for _, row in valid_rows.iterrows():
            params.append({
                's': canonical_id,
                'ts': row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
                'pe': row['PE_TTM']
            })
            
        # Bulk Update via statement
        # Note: 'timestamp' in DB is string YYYY-MM-DD HH:MM:SS
        # Ensure format matches exactly what is in DB.
        
        from sqlalchemy import text
        stmt = text("""
            UPDATE marketdatadaily 
            SET pe_ttm = :pe 
            WHERE symbol = :s AND timestamp = :ts
        """)
        
        # Execute in batches if needed, but 5000 is fine for SQLite
        try:
            session.connection().execute(stmt, params)
            session.commit()
            print("   ✅ Start Commited.")
        except Exception as e:
            print(f"   ❌ Save failed: {e}")

def process_stock(symbol, canonical_id):
    df_p, df_e = fetch_data_from_db(symbol, canonical_id)
    if df_p.empty: return
    
    df_final = calculate_pe_vera(df_p, df_e)
    
    if df_final is not None:
        save_to_db(canonical_id, df_final)
        
        # Show sample
        latest = df_final[df_final['PE_TTM'].notna()].tail(1)
        if not latest.empty:
            print(f"   👉 Latest PE ({latest['Date'].iloc[0].date()}): {latest['PE_TTM'].iloc[0]:.2f}")

def main():
    # 1. Get List of ALL Stocks
    with Session(engine) as session:
        stocks = session.exec(select(Watchlist)).all()
    
    print(f"🚀 Starting Batch PE Backfill for {len(stocks)} stocks (ALL Markets)...")
    
    for s in stocks:
        # Skip Indices, ETFs, Crypto, Funds
        if any(x in s.symbol for x in [':INDEX:', ':ETF:', ':CRYPTO:', ':TRUST:', ':FUND:']):
            continue
        
        process_stock(s.symbol.split(':')[-1], s.symbol)
        
    print("\n✅ Batch Backfill Complete.")

if __name__ == "__main__":
    main()
