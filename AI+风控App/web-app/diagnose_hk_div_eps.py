
import pandas as pd
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals, Watchlist

def diagnose():
    with Session(engine) as session:
        # 1. Get List (HK + US for reference)
        all_assets = session.exec(select(Watchlist).where(Watchlist.market.in_(['HK', 'US']))).all()
        assets = [x for x in all_assets if ':STOCK:' in x.symbol]
        target_symbols = [a.symbol for a in assets]
        
        print(f"Diagnosing {len(target_symbols)} stocks (HK+US)...")
        
        records = []
        for sym in target_symbols:
            # Fetch financials
            fins = session.exec(select(FinancialFundamentals).where(
                FinancialFundamentals.symbol == sym
            ).order_by(FinancialFundamentals.as_of_date.desc())).all()
            
            for f in fins:
                records.append({
                    'Market': sym.split(':')[0],
                    'Symbol': sym.split(':')[-1],
                    'Date': f.as_of_date,
                    'Type': f.report_type,
                    'DividendAmount': f.dividend_amount,
                    'EPS': f.eps,
                    'PayoutRatio_Calc': (f.dividend_amount / f.eps if f.eps and f.dividend_amount else None)
                })
        
        df = pd.DataFrame(records)
        if df.empty:
            print("No Records Found.")
            return

        # Sort
        df = df.sort_values(['Market', 'Symbol', 'Date'], ascending=[True, True, False])
        
        # Save
        out_path = 'outputs/hk_us_div_eps_check.csv'
        df.to_csv(out_path, index=False)
        print(f"✅ Diagnosis saved to {out_path}")
        
        # Print Sample (Tencent, Alibaba, HSBC, Tesla)
        print("\n--- Sample: Tencent (00700) ---")
        print(df[df['Symbol'] == '00700'].head(5).to_string(index=False))
        
        print("\n--- Sample: HSBC (00005) ---")
        print(df[df['Symbol'] == '00005'].head(5).to_string(index=False))

        print("\n--- Sample: Alibaba (09988) ---")
        print(df[df['Symbol'] == '09988'].head(5).to_string(index=False))

        print("\n--- Sample: Tesla (TSLA) ---")
        print(df[df['Symbol'] == 'TSLA'].head(5).to_string(index=False))

if __name__ == "__main__":
    diagnose()
