import sys
import os
from datetime import datetime
from sqlmodel import Session, select, func
from database import engine
from models import MarketDataDaily

def fix_history():
    print("Starting MarketDataDaily repair...")
    with Session(engine) as session:
        # 1. Get all symbols
        symbols = session.exec(select(MarketDataDaily.symbol).distinct()).all()
        print(f"Found {len(symbols)} symbols to check.")
        
        total_fixed = 0
        
        for sym in symbols:
            # Get all daily records for this symbol, sorted by date ASC
            records = session.exec(
                select(MarketDataDaily)
                .where(MarketDataDaily.symbol == sym)
                .order_by(MarketDataDaily.date.asc())
            ).all()
            
            if not records:
                continue
                
            print(f"Checking {sym} ({len(records)} records)...")
            
            # Iterate
            fixed_count = 0
            for i in range(len(records)):
                curr = records[i]
                
                # Check if needs repair
                needs_repair = (curr.change is None or curr.change == 0) and \
                               (curr.pct_change is None or curr.pct_change == 0) and \
                               (curr.close > 0)
                
                if needs_repair:
                    # Look for prev record
                    if i > 0:
                        prev = records[i-1]
                        if prev.close and prev.close > 0:
                            # Calculate
                            new_change = curr.close - prev.close
                            new_pct = (new_change / prev.close) * 100
                            
                            curr.change = round(new_change, 4)
                            curr.pct_change = round(new_pct, 4)
                            
                            session.add(curr)
                            fixed_count += 1
                    else:
                        # First record, cannot calc change from prev.
                        # Leave as 0 or None.
                        pass
                        
            if fixed_count > 0:
                print(f"  -> Fixed {fixed_count} records for {sym}")
                total_fixed += fixed_count
                
        session.commit()
        print(f"Repair Complete. Total records fixed: {total_fixed}")

if __name__ == "__main__":
    fix_history()
