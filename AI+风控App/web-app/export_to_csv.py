
import sys
import os
import pandas as pd
from sqlmodel import Session, select
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine
from models import MarketDataDaily, FinancialFundamentals

def main():
    print("\n--- [步骤]: 导出 CSV 数据 ---")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    with Session(engine) as session:
        try:
            # 1. 导出财报历史
            print("正在导出 financial_history.csv ...")
            fins = session.exec(select(FinancialFundamentals).order_by(FinancialFundamentals.symbol, FinancialFundamentals.as_of_date.desc())).all()
            if fins:
                fin_df = pd.DataFrame([f.model_dump() for f in fins])
                
                # Format numbers (scale to 100M if needed, though raw is safer for CSV. User preference in add_new_asset was scaled)
                # Let's keep consistency with add_new_asset_complete.py logic:
                num_cols = ['revenue_ttm', 'net_income_ttm', 'total_assets', 'total_liabilities', 'total_debt', 'cash_and_equivalents']
                for c in num_cols:
                    if c in fin_df.columns: 
                        # Check for non-null before division
                        fin_df[c] = fin_df[c].apply(lambda x: round(x / 100_000_000, 4) if pd.notnull(x) else x)
                
                fin_df.to_csv(f"{output_dir}/financial_history.csv", index=False, encoding='utf-8-sig')
                print(f"✅ 财报历史导出成功: {len(fin_df)} 条记录")
            else:
                print("⚠️ 无财报数据可导出")
            
            # 2. 导出日线表
            print("正在导出 market_daily.csv ...")
            # Export all daily data since it's a full download script result
            daily = session.exec(select(MarketDataDaily).order_by(MarketDataDaily.symbol, MarketDataDaily.timestamp.desc())).all()
            if daily:
                daily_df = pd.DataFrame([d.model_dump() for d in daily])
                daily_df.to_csv(f"{output_dir}/market_daily.csv", index=False, encoding='utf-8-sig')
                print(f"✅ 行情历史导出成功: {len(daily_df)} 条记录")
            else:
                print("⚠️ 无行情数据可导出")
                
            print(f"\n🏁 导出完成! 文件位于 {os.path.abspath(output_dir)}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")

if __name__ == "__main__":
    main()
