from sqlmodel import Session, select, func
from backend.database import engine
from backend.models import FinancialFundamentals

def check_counts():
    with Session(engine) as session:
        results = session.exec(
            select(FinancialFundamentals.symbol, func.count(FinancialFundamentals.id))
            .group_by(FinancialFundamentals.symbol)
        ).all()
        
        print(f"{'Symbol':<15} | {'Count'}")
        print("-" * 25)
        for sym, count in results:
            print(f"{sym:<15} | {count}")

if __name__ == "__main__":
    check_counts()
