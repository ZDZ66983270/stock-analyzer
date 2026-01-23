
import sys
import os
from datetime import datetime, timedelta
from sqlmodel import Session, select, func
import pandas as pd

# Add backend to path
sys.path.append('backend')
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import engine
from backend.models import Watchlist, MarketDataDaily
from backend.symbol_utils import parse_canonical_id

def check_fund_data():
    target_types = {'TRUST', 'FUND', 'ETF'}
    
    with Session(engine) as session:
        # Get all watchlist items
        assets = session.exec(select(Watchlist)).all()
        
        results = []
        
        print(f"📊 Scanning {len(assets)} assets for types: {target_types}...")
        
        for asset in assets:
            parts = parse_canonical_id(asset.symbol)
            asset_type = parts['type']
            
            if asset_type not in target_types:
                continue
                
            # Query Market Data Stats
            stmt = select(
                func.min(MarketDataDaily.timestamp),
                func.max(MarketDataDaily.timestamp),
                func.count(MarketDataDaily.id)
            ).where(MarketDataDaily.symbol == asset.symbol)
            
            min_ts, max_ts, count = session.exec(stmt).first()
            
            status = "✅ OK"
            if count == 0:
                status = "❌ No Data"
            else:
                last_date = datetime.strptime(str(max_ts)[:10], "%Y-%m-%d").date()
                days_gap = (datetime.now().date() - last_date).days
                if days_gap > 5:
                    status = f"⚠️ Outdated ({days_gap}d ago)"
            
            results.append({
                "Symbol": asset.symbol,
                "Name": asset.name,
                "Type": asset_type,
                "Status": status,
                "Count": count,
                "Last Date": str(max_ts)[:10] if max_ts else "N/A"
            })
            
    # Display
    if not results:
        print("No fund assets found in watchlist.")
        return
        
    df = pd.DataFrame(results)
    df = df.sort_values(by=["Type", "Status"])
    
    print("\n" + "="*80)
    print(" 🏥 Fund Data Health Check")
    print("="*80)
    print(df.to_string(index=False))
    print("="*80)
    
    # Summary
    missing = df[df['Status'].str.contains("No Data")]
    outdated = df[df['Status'].str.contains("Outdated")]
    
    if not missing.empty or not outdated.empty:
        print("\n⚠️  Issues Found:")
        if not missing.empty:
            print(f"   - Missing Data: {len(missing)} assets")
        if not outdated.empty:
            print(f"   - Outdated Data: {len(outdated)} assets")
    else:
        print("\n✅ All fund assets look healthy!")

if __name__ == "__main__":
    check_fund_data()
