
import sys
sys.path.append('.')
sys.path.append('backend')
from backend.database import engine, Session
from backend.models import MarketDataDaily
from fetch_valuation_history import fetch_us_valuation_history_fmp
from sqlmodel import select
from datetime import datetime
import pandas as pd

def test_derive_pe(symbol="US:STOCK:AAPL"):
    print(f"--- Deriving Daily PE for {symbol} ---")
    
    # 1. Fetch FMP History (simulating what we have)
    # We can fetch fresh or use what's in DB. Let's fetch fresh for explicit test.
    df_fmp = fetch_us_valuation_history_fmp(symbol, limit=5)
    if df_fmp is None or df_fmp.empty:
        print("No FMP data.")
        return

    print("\n[FMP Annual Data]")
    print(df_fmp[['date', 'pe']].head())
    
    # 2. Get Daily Price History from DB
    with Session(engine) as session:
        daily_recs = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == symbol)
            .where(MarketDataDaily.market == 'US')
            .order_by(MarketDataDaily.timestamp.asc()) # Oldest first
        ).all()
        
    if not daily_recs:
        print("No Daily Price data.")
        return
        
    # Convert to DataFrame
    data = []
    for r in daily_recs:
        data.append({
            'date': r.timestamp.split()[0],
            'close': r.close,
            'timestamp': r.timestamp
        })
    df_price = pd.DataFrame(data)
    df_price['date'] = pd.to_datetime(df_price['date'])
    
    # 3. Derive Daily PE
    # Logic: For each day, look for the MOST RECENT FMP record (before this day).
    # Use that FMP record's PE and Date to derive EPS.
    # EPS = Price_at_FMP_Date / PE_at_FMP_Date
    # PE_daily = Price_daily / EPS
    
    # Pre-process FMP data
    df_fmp['date'] = pd.to_datetime(df_fmp['date'])
    df_fmp = df_fmp.sort_values('date') # Oldest to newest
    
    print("\n[Derivation Logic]")
    
    derived_data = []
    
    # We iterate daily prices
    for _, row in df_price.iterrows():
        curr_date = row['date']
        
        # Find valid FMP report (latest one on or before current date)
        valid_reports = df_fmp[df_fmp['date'] <= curr_date]
        
        if valid_reports.empty:
            continue
            
        latest_report = valid_reports.iloc[-1]
        report_date = latest_report['date']
        report_pe = float(latest_report['pe'])
        
        # Determine Reference Price at Report Date
        # Better to look up the exact close price on that report date
        # (Since FMP PE is calculated using Price on that specific date)
        
        # Find close price on report_date
        # (This is an approximation using our own DB prices. FMP might use slightly diff price)
        ref_price_row = df_price[df_price['date'] == report_date]
        if ref_price_row.empty:
            # Fallback: find closest within 3 days
             ref_price_row = df_price[(df_price['date'] >= report_date) & (df_price['date'] <= report_date + pd.Timedelta(days=5))]
        
        if ref_price_row.empty:
            continue
            
        ref_price = ref_price_row.iloc[0]['close']
        
        # Calculate Implied EPS
        implied_eps = ref_price / report_pe
        
        # Calculate Current PE
        curr_pe = row['close'] / implied_eps
        
        derived_data.append({
            'date': curr_date.strftime('%Y-%m-%d'),
            'close': row['close'],
            'ref_report': report_date.strftime('%Y-%m-%d'),
            'ref_pe': round(report_pe, 2),
            'implied_eps': round(implied_eps, 2),
            'derived_pe': round(curr_pe, 2)
        })
        
    df_res = pd.DataFrame(derived_data)
    
    # Show Sample (Recent and Transition points)
    if not df_res.empty:
        print("\n[Derived Daily PE Sample]")
        print(df_res.tail(10))
        
        # Show specific transition near report date
        print("\n[Transition Example]")
        # Find where ref_report changes
        df_res['prev_ref'] = df_res['ref_report'].shift(1)
        transitions = df_res[df_res['ref_report'] != df_res['prev_ref']].dropna()
        if not transitions.empty:
            print(transitions.tail(2))
    else:
        print("No derived data.")

if __name__ == "__main__":
    test_derive_pe()
