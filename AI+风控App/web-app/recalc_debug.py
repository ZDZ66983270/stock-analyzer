
import sys
import os
import pandas as pd
import bisect
from sqlmodel import Session, select
from sqlalchemy import text

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import engine
from backend.models import FinancialFundamentals, MarketDataDaily

def debug_pe(asset_id):
    with Session(engine) as session:
        # Fetch Fins
        fin_rows = session.exec(
            select(FinancialFundamentals.as_of_date, FinancialFundamentals.eps, FinancialFundamentals.report_type)
            .where(FinancialFundamentals.symbol == asset_id)
            .where(FinancialFundamentals.eps != None)
            .order_by(FinancialFundamentals.as_of_date)
        ).all()
        
        print(f"Found {len(fin_rows)} financials.")
        df_fin = pd.DataFrame(fin_rows, columns=['date', 'eps', 'report_type'])
        df_fin['date'] = pd.to_datetime(df_fin['date'])
        df_fin = df_fin.sort_values('date')
        print(df_fin)
        
        # Calc TTM
        df_q = df_fin[df_fin['report_type'] == 'quarterly'].copy()
        if not df_q.empty:
            df_q['ttm'] = df_q['eps'].rolling(4, min_periods=4).sum()
            print("\nQuarterly TTM:")
            print(df_q[['date', 'eps', 'ttm']])
        else:
             print("No quarterly data.")

        df_a = df_fin[df_fin['report_type'] == 'annual'].copy()
        if not df_a.empty:
            df_a['ttm'] = df_a['eps']
            print("\nAnnual TTM:")
            print(df_a[['date', 'eps', 'ttm']])

        ttm_series = pd.concat([df_q[['date', 'ttm']], df_a[['date', 'ttm']]]).dropna().sort_values('date')
        ttm_series = ttm_series.drop_duplicates(subset=['date'], keep='last')
        
        print("\nFinal TTM Series:")
        print(ttm_series)
        
        # Check against recent price
        last_price = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == asset_id).order_by(MarketDataDaily.timestamp.desc()).limit(1)).first()
        if last_price:
            t_date = str(last_price.timestamp)[:10]
            print(f"\nLast Price Date: {t_date}, Close: {last_price.close}")
            ttm_dates = ttm_series['date'].dt.strftime('%Y-%m-%d').tolist()
            idx = bisect.bisect_right(ttm_dates, t_date)
            print(f"Bisect Index: {idx}")
            if idx > 0:
                print(f"Index {idx-1} -> Date: {ttm_dates[idx-1]}, TTM: {ttm_series.iloc[idx-1]['ttm']}")
            else:
                print("Index 0 (No Match)")

if __name__ == "__main__":
    debug_pe("US:STOCK:AMZN")
