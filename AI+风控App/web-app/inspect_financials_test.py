
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from database import engine
from sqlmodel import Session, select
from models import FinancialFundamentals

def inspect_financials_vera():
    symbol = "US:STOCK:AAPL" # Assuming AAPL is in watchlist and was fetched
    print(f"🕵️‍♀️ Inspecting Financials for {symbol}...")
    
    with Session(engine) as session:
        recs = session.exec(select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).order_by(FinancialFundamentals.as_of_date.desc()).limit(1)).all()
        if not recs:
            print("❌ No records found.")
            return

        rec = recs[0]
        print(f"📅 Date: {rec.as_of_date}")
        print(f"📄 Type: {rec.report_type}")
        print(f"💰 Net Income (Common): {rec.net_income_common_ttm}")
        print(f"📉 Shares (Diluted): {rec.shares_diluted}")
        print(f"🗓 Filing Date: {rec.filing_date}")
        
        if rec.net_income_common_ttm and rec.shares_diluted and rec.filing_date:
             print("✅ VERA Pro fields populated!")
        else:
             print("⚠️ VERA Pro fields missing or partial.")

if __name__ == "__main__":
    inspect_financials_vera()
