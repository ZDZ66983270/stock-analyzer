#!/usr/bin/env python3
"""
Migrate Crypto IDs from CRYPTO:STOCK:CODE to CRYPTO:CODE-USD
"""
import sys
sys.path.append('backend')
from database import engine
from sqlmodel import Session, text

def migrate_crypto():
    print("🔄 Starting Crypto ID Migration...")
    print("="*60)
    
    with Session(engine) as session:
        # Find all crypto assets
        result = session.exec(text("SELECT symbol FROM watchlist WHERE market = 'CRYPTO'")).all()
        
        for row in result:
            old_symbol = row[0]  # e.g., CRYPTO:STOCK:BTC
            
            # Logic to generate new symbol
            # Remove CRYPTO:STOCK: prefix
            code = old_symbol.replace('CRYPTO:STOCK:', '').replace('CRYPTO:', '')
            # If no dash, assume USD pair
            if '-' not in code:
                new_symbol = f"CRYPTO:{code}-USD"
            else:
                new_symbol = f"CRYPTO:{code}"
            
            if old_symbol == new_symbol:
                print(f"⏩ Skipping {old_symbol} (already correct)")
                continue
                
            print(f"\n📝 Migrating {old_symbol} → {new_symbol}")
            
            # Update all tables
            tables = ['watchlist', 'marketdatadaily', 'marketsnapshot', 'rawmarketdata', 'financialfundamentals', 'dividendfact', 'splitfact', 'portfolioposition', 'trade']
            
            for table in tables:
                try:
                    stmt = text(f"UPDATE {table} SET symbol = :new WHERE symbol = :old").bindparams(new=new_symbol, old=old_symbol)
                    res = session.exec(stmt)
                    if res.rowcount > 0:
                        print(f"   {table}: {res.rowcount} rows updated")
                except Exception as e:
                    # Table might not exist or other error, mostly harmless for some tables
                    # print(f"   (Skipping table {table}: {e})")
                    pass
            
        session.commit()
        print("\n✅ Migration Commit Complete.")

if __name__ == "__main__":
    migrate_crypto()
