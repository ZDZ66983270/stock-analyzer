import sys
import os
import pandas as pd
from sqlmodel import Session, select, func
from datetime import datetime

# 添加后端路径
sys.path.append('backend')
from database import engine
from models import MarketDataDaily, Watchlist, Index, FinancialFundamentals

def run_audit():
    print("🔍 开始数据质量深度审计 (v2.0)...")
    print("=" * 80)
    
    with Session(engine) as session:
        # 1. 基础配置统计
        watchlist = session.exec(select(Watchlist)).all()
        indices = session.exec(select(Index)).all()
        stocks = [w for w in watchlist if ":STOCK:" in w.symbol]
        etfs = [w for w in watchlist if ":ETF:" in w.symbol]
        
        print(f"📊 配置统计: 自选股={len(watchlist)} (个股={len(stocks)}, ETF={len(etfs)}), 指数={len(indices)}")
        print("-" * 80)

        # 2. 覆盖率与深度审计
        all_targets = watchlist + indices
        audit_results = []
        
        for item in all_targets:
            symbol = item.symbol
            # 统计行情
            q = select(
                func.count(MarketDataDaily.id),
                func.min(MarketDataDaily.timestamp),
                func.max(MarketDataDaily.timestamp),
                func.avg(MarketDataDaily.close)
            ).where(MarketDataDaily.symbol == symbol)
            
            count, start_date, end_date, avg_price = session.exec(q).one()
            
            # 统计估值填充 (已填充 PE 的比例)
            q_pe = select(func.count(MarketDataDaily.id)).where(
                MarketDataDaily.symbol == symbol,
                MarketDataDaily.pe != None
            )
            pe_count = session.exec(q_pe).one()
            pe_rate = (pe_count / count * 100) if count > 0 else 0
            
            # 统计财报条数
            q_fin = select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.symbol == symbol)
            fin_count = session.exec(q_fin).one()
            
            # 币种校验
            fin_sample = session.exec(select(FinancialFundamentals).where(FinancialFundamentals.symbol == symbol).limit(1)).first()
            currency = fin_sample.currency if fin_sample else "N/A"
            
            audit_results.append({
                "Symbol": symbol,
                "Name": item.name,
                "Market": item.market,
                "Count": count,
                "Start": str(start_date)[:10] if start_date else "N/A",
                "End": str(end_date)[:10] if end_date else "N/A",
                "AvgPrice": round(avg_price, 2) if avg_price else 0,
                "PERate": f"{pe_rate:.1f}%",
                "Fins": fin_count,
                "Currency": currency
            })

        df = pd.DataFrame(audit_results)
        
        # 3. 输出汇总与预警
        print("\n🚩 异常预警报告:")
        
        # 3.1 缺失行情
        missing = df[df['Count'] == 0]
        if not missing.empty:
            print(f"  ❌ 缺失行情标的 ({len(missing)}个):")
            for _, r in missing.iterrows():
                print(f"    - {r['Symbol']} ({r['Name']})")
        else:
            print("  ✅ 所有标的均有行情数据覆盖")

        # 3.2 深度不足 (历史数据少于 200 行的个股)
        shallow = df[(df['Count'] > 0) & (df['Count'] < 200) & (df['Symbol'].str.contains(":STOCK:"))]
        if not shallow.empty:
            print(f"  ⚠️ 行情深度较浅的个股 ({len(shallow)}个):")
            for _, r in shallow.iterrows():
                print(f"    - {r['Symbol']} ({r['Name']}): {r['Count']}行")

        # 3.3 指数价格校验 (重点: 000001)
        sh_index = df[df['Symbol'] == 'CN:INDEX:000001']
        if not sh_index.empty:
            price = sh_index.iloc[0]['AvgPrice']
            if price < 500:
                print(f"  ❌ 上证指数数据错误！当前均价 {price}，疑似仍为平安银行数据。")
            else:
                print(f"  ✅ 上证指数数据正位: 当前均价约为 {price}")

        # 3.4 汇率/币种风险点
        hk_cny = df[(df['Market'] == 'HK') & (df['Currency'] == 'CNY')]
        if not hk_cny.empty:
            print(f"  ℹ️ 港股财报币种提醒: 以下 {len(hk_cny)} 个标的财报为 CNY，计算 PE 时需核实 1.09 左右的汇率修正:")
            for _, r in hk_cny.iterrows():
                print(f"    - {r['Symbol']} ({r['Name']})")

        # 4. 详细清单 (抽样前 20 条或保存到日志)
        print("\n📋 数据审计详细清单 (前 30 条):")
        print(df.sort_values(by="Count", ascending=False).head(30).to_string(index=False))

        # 5. 总记录数验证
        total_daily = session.exec(select(func.count(MarketDataDaily.id))).one()
        print("-" * 80)
        print(f"🏁 审计完成! 数据库总行情记录数: {total_daily:,} 条")

if __name__ == "__main__":
    run_audit()
