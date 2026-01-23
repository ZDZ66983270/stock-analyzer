from sqlmodel import Session, text
from backend.database import engine
from backend.models import FinancialFundamentals

def main():
    print("🗑️ Dropping FinancialFundamentals table to apply schema change...")
    with Session(engine) as session:
        # SQLite drop table
        session.exec(text("DROP TABLE IF EXISTS financialfundamentals"))
        session.commit()
    
    print("🆕 Recreating tables...")
    from sqlmodel import SQLModel
    # This will recreate the table with the new schema
    SQLModel.metadata.create_all(engine)
    print("✅ Schema update complete (eps_ttm added).")

if __name__ == "__main__":
    main()
