
import os
import pandas as pd
import argparse
from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals, Watchlist

def export_formatted(target_symbol=None):
    print("🚀 Exporting formatted financials...")
    if target_symbol:
        print(f"🎯 Target Symbol: {target_symbol}")
    
    with Session(engine) as session:
        # Load all watchlist items for symbol mapping (includes stocks, ETFs, and indices)
        watchlist_items = session.exec(select(Watchlist)).all()
        
        # Map: identifying_key (Canonical ID or pure symbol) -> (Canonical ID, Name)
        key_to_meta = {}
        
        for item in watchlist_items:
            # item.symbol is Canonical ID
            meta = (item.symbol, item.name or item.symbol)
            key_to_meta[item.symbol] = meta
            
            # Also map pure symbol if available (e.g. 09988 from HK:STOCK:09988)
            pure_symbol = item.symbol.split(':')[-1]
            if pure_symbol not in key_to_meta:
                key_to_meta[pure_symbol] = meta

        # Fetch all financial fundamentals that have data
        stmt = select(FinancialFundamentals).where(
            (FinancialFundamentals.revenue_ttm != None) | 
            (FinancialFundamentals.total_assets != None)
        ).where(FinancialFundamentals.as_of_date != '2025-12-27') # Filter out TTM snapshot
        
        if target_symbol:
            stmt = stmt.where(FinancialFundamentals.symbol == target_symbol)
            
        stmt = stmt.order_by(FinancialFundamentals.symbol, FinancialFundamentals.as_of_date.desc())
        
        funds = session.exec(stmt).all()
        
        data = []
        for fund in funds:
            # Try to get Canonical ID and Name
            canonical_id, name = key_to_meta.get(fund.symbol, (fund.symbol, "Unknown"))
            
            # If still unknown and not in key_to_meta, we might want to skip or keep as is
            # For this task, we want everything in the export to be mapped correctly
            if name == "Unknown" and fund.symbol not in key_to_meta:
                continue
                
            row = fund.model_dump()
            row['symbol'] = canonical_id  # Update symbol to Canonical ID
            row['name'] = name
            data.append(row)
            
        df = pd.DataFrame(data)
        
        if df.empty:
            print("❌ No data found.")
            return

        # 1. Format Numbers (Convert to 亿 / 100 Million)
        # Fields to scale: revenue_ttm, net_income_ttm, total_assets, total_liabilities, total_debt, cash...
        scale_fields = ['revenue_ttm', 'net_income_ttm', 'operating_cashflow_ttm', 'total_assets', 'total_liabilities', 'total_debt', 'cash_and_equivalents']
        
        for col in scale_fields:
            if col in df.columns:
                # Divide by 100,000,000 (1亿), round to 2 decimals
                df[col] = df[col].apply(lambda x: round(x / 100000000, 2) if pd.notnull(x) else None)
                # Rename column
                df.rename(columns={col: f"{col.replace('_ttm', '')} (亿)"}, inplace=True)

        # Format Ratios (Round to 2 decimals)
        ratio_fields = ['debt_to_equity', 'dividend_yield', 'payout_ratio']
        for col in ratio_fields:
             if col in df.columns:
                df[col] = df[col].apply(lambda x: round(x, 2) if pd.notnull(x) else None)

        # Select and Reorder columns
        # name, symbol, as_of_date, currency, revenue, net_income, assets...
        cols_order = ['symbol', 'name', 'currency', 'as_of_date'] + \
                     [c for c in df.columns if '亿' in c] + \
                     ['debt_to_equity', 'dividend_yield']
        
        # Rename non-scaled TTM columns if any remain
        df.columns = [c.replace('_ttm', '') for c in df.columns]
        
        # Filter columns that actually exist
        final_cols = [c for c in cols_order if c in df.columns]
        df = df[final_cols]
        
        # 2. Fix Encoding (UTF-8-SIG for Excel)
        output_dir = "outputs"
        
        if target_symbol:
            safe_symbol = target_symbol.replace(':', '_')
            output_file = os.path.join(output_dir, f"financials_overview_{safe_symbol}.csv")
        else:
            output_file = os.path.join(output_dir, "financials_overview_v2.csv")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ Exported {len(df)} records to {output_file}")
        print("   (Numbers scaled to '亿', Encoding: utf-8-sig)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Financial Data')
    parser.add_argument('--symbol', type=str, help='Canonical ID to filter (e.g. US:STOCK:AAPL)')
    args = parser.parse_args()
    
    export_formatted(args.symbol)
