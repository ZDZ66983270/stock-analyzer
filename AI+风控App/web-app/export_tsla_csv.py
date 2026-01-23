
import os
import pandas as pd
from sqlmodel import Session, select
from backend.database import engine
from backend.models import MarketDataDaily

def export_tsla():
    print("🚀 Exporting Tesla (TSLA) history...")
    
    with Session(engine) as session:
        statement = select(MarketDataDaily).where(
            MarketDataDaily.symbol == "TSLA"
        ).order_by(MarketDataDaily.timestamp.desc())
        
        results = session.exec(statement).all()
        
        if not results:
            print("❌ No data found for TSLA.")
            return

        # Convert to list of dicts
        data = [row.model_dump() for row in results]
        df = pd.DataFrame(data)
        
        # Select and reorder columns
        cols = ['symbol', 'market', 'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'change', 'pct_change', 'pe', 'pb', 'market_cap']
        
        # Ensure columns exist
        existing_cols = [c for c in cols if c in df.columns]
        df = df[existing_cols]
        
        # Export
        output_dir = "outports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, "tsla_history.csv")
        df.to_csv(output_file, index=False)
        
        print(f"✅ Exported {len(df)} records to {output_file}")

if __name__ == "__main__":
    export_tsla()
