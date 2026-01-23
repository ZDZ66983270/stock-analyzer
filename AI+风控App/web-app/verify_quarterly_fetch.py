
import sys
import os
from sqlmodel import Session, select, delete
from backend.database import engine
from backend.models import FinancialFundamentals, Watchlist
from fetch_financials import fetch_yahoo_financials, upsert_financials
import pandas as pd
from datetime import datetime

def verify_quarterly():
    print("🧪 Testing Quarterly Financial Fetching...")
    
    test_symbols = [
        {'symbol': 'US:STOCK:AAPL', 'market': 'US'},
        {'symbol': 'HK:STOCK:00700', 'market': 'HK'},
        {'symbol': 'CN:STOCK:600519', 'market': 'CN'}
    ]
    
    with Session(engine) as session:
        for t in test_symbols:
            symbol = t['symbol']
            market = t['market']
            print(f"\n👉 Testing {symbol} ({market})...")
            
            # 1. Clear existing quarterly data for test
            session.exec(delete(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).where(FinancialFundamentals.report_type == 'quarterly'))
            session.commit()
            
            data_list = []
            
            if market == 'US' or market == 'HK':
                # Call Yahoo Quarterly
                print("   Calling fetch_yahoo_financials(quarterly)...")
                q_data = fetch_yahoo_financials(symbol, market=market, report_type='quarterly')
                data_list.extend(q_data)
                
            elif market == 'CN':
                print("   Skipping AkShare test here as it requires full main loop setup. Testing Yahoo fallback if needed.")
                # We can test Yahoo fallback for CN
                q_data = fetch_yahoo_financials(symbol, market='CN', report_type='quarterly')
                data_list.extend(q_data)

            if data_list:
                print(f"   ✅ Fetched {len(data_list)} quarterly records.")
                for d in data_list:
                    print(f"      - {d['as_of_date']} Report:{d['report_type']} Source:{d['data_source']} Rev:{d['revenue_ttm']}")
                    upsert_financials(session, d)
                session.commit()
                
                # Verify DB
                stored = session.exec(select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).where(FinancialFundamentals.report_type == 'quarterly')).all()
                print(f"   💾 Stored in DB: {len(stored)} records.")
            else:
                print("   ❌ No quarterly data fetched.")

if __name__ == "__main__":
    verify_quarterly()
