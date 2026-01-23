
import sys
import os
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Watchlist

def diagnose():
    print("Diagnosing symbols in Watchlist...")
    with Session(engine) as session:
        # Check specific symbols
        targets = ['000001', '000300', '000858']
        
        for t in targets:
            results = session.exec(select(Watchlist).where(Watchlist.symbol.like(f'%{t}%'))).all()
            for r in results:
                print(f"Code: {t} -> Symbol: '{r.symbol}' Type: {type(r.symbol)} Name: {r.name}")

if __name__ == "__main__":
    diagnose()
