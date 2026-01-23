from sqlmodel import SQLModel
from backend.database import engine
from backend.models import *

print("Creating all tables...")
SQLModel.metadata.create_all(engine)
print("Done.")
