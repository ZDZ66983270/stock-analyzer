
import sys
from sqlmodel import SQLModel
from backend.database import engine
# Import the model so SQLModel knows about it
from backend.models import FinancialFundamentals

def init_table():
    print("🚀 Initializing FinancialFundamentals table...")
    SQLModel.metadata.create_all(engine)
    print("✅ Table created (if it didn't exist).")

if __name__ == "__main__":
    sys.path.insert(0, ".")
    init_table()
