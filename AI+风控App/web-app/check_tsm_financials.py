
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals

def check_tsm():
    with Session(engine) as session:
        # Check TSM
        print("--- TSM Financials ---")
        rows = session.exec(select(FinancialFundamentals).where(FinancialFundamentals.symbol == "US:STOCK:TSM").order_by(FinancialFundamentals.as_of_date.desc()).limit(5)).all()
        for r in rows:
            print(f"Date: {r.as_of_date}, Type: {r.report_type}, EPS: {r.eps}, NetIncome: {r.net_income_ttm}, Currency: {r.currency}")

if __name__ == "__main__":
    check_tsm()
