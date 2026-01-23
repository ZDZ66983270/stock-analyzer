import sys
sys.path.append('backend')
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily, FinancialFundamentals

def verify(symbol):
    print(f"--- Verifying {symbol} ---")
    with Session(engine) as session:
        # Get Financials
        fins = session.exec(select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).order_by(FinancialFundamentals.as_of_date)).all()
        print(f"Found {len(fins)} financial records.")
        for f in fins:
            print(f"  Date: {f.as_of_date}, NetInc: {f.net_income_ttm}, EPS_TTM: {f.eps_ttm}")

        # Get Daily Data (Sample)
        dailies = session.exec(select(MarketDataDaily).where(MarketDataDaily.symbol == symbol).order_by(MarketDataDaily.timestamp.desc()).limit(5)).all()
        print(f"Checking latest 5 daily records:")
        for d in dailies:
            print(f"  Date: {d.timestamp}, Close: {d.close}, PE: {d.pe}")
            # Try to match with fin
            # (Simple check: is PE roughly Close / EPS_TTM?)
            # Find relevant fin
            relevant_fin = None
            date_str = d.timestamp[:10]
            for f in sorted(fins, key=lambda x: x.as_of_date, reverse=True):
                if f.as_of_date <= date_str:
                    relevant_fin = f
                    break
            
            if relevant_fin and relevant_fin.eps_ttm:
                expected_pe = d.close / relevant_fin.eps_ttm
                diff = abs(d.pe - expected_pe) if d.pe else 999
                status = "✅" if diff < 1.0 else "❌" # Allow some margin
                print(f"     -> Expected PE ({d.close}/{relevant_fin.eps_ttm}) = {expected_pe:.2f} | Actual: {d.pe} {status}")
            else:
                print(f"     -> No relevant financial data found for date.")

if __name__ == "__main__":
    verify("US:STOCK:MSFT") # Use canonical ID if possible, or try raw if needed. 
    # backfill converts to canonical internally but uses what's in DB.
    # We should use MSFT or TSLA
    verify("US:STOCK:TSLA")
