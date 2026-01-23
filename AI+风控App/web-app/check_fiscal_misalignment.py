
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals, Watchlist
from collections import defaultdict
import pandas as pd

def check_anomalies():
    print("Checking for Fiscal Year / Duplicate Annual Anomalies...")
    with Session(engine) as session:
        # Get all stocks
        all_assets = session.exec(select(Watchlist)).all()
        assets = [x for x in all_assets if ':STOCK:' in x.symbol]
        
        anomalies = []
        
        for asset in assets:
            # Get Annuals
            annuals = session.exec(select(FinancialFundamentals).where(
                FinancialFundamentals.symbol == asset.symbol,
                FinancialFundamentals.report_type == 'annual'
            ).order_by(FinancialFundamentals.as_of_date)).all()
            
            # Group by Year
            by_year = defaultdict(list)
            for r in annuals:
                # r.as_of_date is likely str "YYYY-MM-DD"
                y = int(str(r.as_of_date)[:4])
                by_year[y].append(r)
                
            # Check Duplicates
            for year, records in by_year.items():
                if len(records) > 1:
                    # Found duplicate annuals for same year
                    anomalies.append({
                        'Symbol': asset.symbol,
                        'Year': year,
                        'Issue': 'Duplicate Annuals',
                        'Dates': [str(r.as_of_date) for r in records],
                        'Divs': [r.dividend_amount for r in records]
                    })
            
            # Check Zero Annuals (Ghost)
            for r in annuals:
                if r.dividend_amount == 0 or r.dividend_amount is None:
                    # Check if standard payer (has other non-zero annuals)
                    has_payer_history = any((x.dividend_amount or 0) > 0 for x in annuals)
                    if has_payer_history and asset.symbol not in ['US:STOCK:TSLA', 'US:STOCK:AMZN']: # Exclude known non-payers
                         # Check if it looks like a "Ghost" (Dec 31 zero vs Mar 31 valid)
                         pass # Hard to verify without knowing context, but flag it
                         
                         anomalies.append({
                             'Symbol': asset.symbol,
                             'Year': int(str(r.as_of_date)[:4]),
                             'Issue': 'Zero Annual Div (Potential Ghost)',
                             'Date': str(r.as_of_date),
                             'Div': r.dividend_amount
                         })

        # Save
        if anomalies:
             df = pd.DataFrame(anomalies)
             df.to_csv('outputs/fiscal_anomalies.csv', index=False)
             print(f"Found {len(anomalies)} anomalies. Saved to outputs/fiscal_anomalies.csv")
             print(df.head(10).to_string())
        else:
             print("No anomalies found.")

if __name__ == "__main__":
    check_anomalies()
