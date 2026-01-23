import sys
import os
import pandas as pd
from sqlmodel import Session, select, func
from datetime import datetime

# Add backend to path
sys.path.append('backend')
from database import engine
from models import Watchlist, Index, MarketDataDaily, FinancialFundamentals

def get_duration_report():
    with Session(engine) as session:
        # 1. 获取配置清单
        watchlist = session.exec(select(Watchlist)).all()
        indices = session.exec(select(Index)).all()
        
        config_targets = {}
        for item in watchlist:
            config_targets[item.symbol] = {'source': 'Watchlist', 'name': item.name, 'market': item.market}
        for item in indices:
            config_targets[item.symbol] = {'source': 'Index', 'name': item.name, 'market': item.market}
            
        # 2. 获取实际存在于行情表中的标的清单
        all_market_symbols = session.exec(select(MarketDataDaily.symbol).distinct()).all()
        all_fin_symbols = session.exec(select(FinancialFundamentals.symbol).distinct()).all()
        
        all_seen_symbols = set(all_market_symbols) | set(all_fin_symbols) | set(config_targets.keys())
        
        results = []
        for sym in all_seen_symbols:
            cfg = config_targets.get(sym, {'source': 'Extra (Not in Config)', 'name': 'Unknown', 'market': 'Unknown'})
            
            # 行情统计
            daily_stats = session.exec(
                select(
                    func.count(MarketDataDaily.id),
                    func.min(MarketDataDaily.timestamp),
                    func.max(MarketDataDaily.timestamp)
                ).where(MarketDataDaily.symbol == sym)
            ).first()
            
            count_daily = daily_stats[0] or 0
            start_date = (daily_stats[1] or "N/A").split(' ')[0]
            end_date = (daily_stats[2] or "N/A").split(' ')[0]
            
            # 财务统计
            fin_count = session.exec(
                select(func.count(FinancialFundamentals.id)).where(FinancialFundamentals.symbol == sym)
            ).one()
            
            # 计算时长感官
            duration_desc = "0 days"
            if count_daily > 0 and daily_stats[1] and daily_stats[2]:
                try:
                    d1 = datetime.strptime(start_date, "%Y-%m-%d")
                    d2 = datetime.strptime(end_date, "%Y-%m-%d")
                    diff = d2 - d1
                    years = diff.days / 365.25
                    if years >= 1:
                        duration_desc = f"{years:.1f} years"
                    else:
                        duration_desc = f"{diff.days} days"
                except:
                    duration_desc = "Unknown"

            results.append({
                'Symbol': sym,
                'Name': cfg['name'],
                'Market': cfg['market'],
                'Source': cfg['source'],
                'Daily Count': count_daily,
                'Start': start_date,
                'End': end_date,
                'Duration': duration_desc,
                'Fin Count': fin_count,
                'In Config': 'Yes' if sym in config_targets else '❌ Removed'
            })
            
        df = pd.DataFrame(results)
        # 排序：配置优先，然后市场，然后代码
        df['sort_rank'] = df['In Config'].apply(lambda x: 0 if x == 'Yes' else 1)
        df = df.sort_values(by=['sort_rank', 'Market', 'Symbol'])
        
        print("\n" + "="*125)
        print(f"{'Symbol':<25} | {'Name':<12} | {'Mkt':<4} | {'Daily':<6} | {'Start Date':<10} | {'End Date':<10} | {'Duration':<10} | {'Fin':<4} | {'Sync'}")
        print("-" * 125)
        
        for _, row in df.iterrows():
            name = (row['Name'] or "N/A")[:12]
            print(f"{row['Symbol']:<25} | {name:<12} | {row['Market']:<4} | {row['Daily Count']:<6} | {row['Start']:<10} | {row['End']:<10} | {row['Duration']:<10} | {row['Fin Count']:<4} | {row['In Config']}")
            
        print("="*125)
        
        # 统计汇总
        missing_in_db = [s for s, v in config_targets.items() if s not in set(all_market_symbols)]
        extra_in_db = set(all_market_symbols) - set(config_targets.keys())
        
        print(f"\n📈 数据摘要:")
        print(f"   - 配置清单总数: {len(config_targets)}")
        print(f"   - 行情表标的总数: {len(all_market_symbols)}")
        print(f"   - 财务表标的总数: {len(all_fin_symbols)}")
        print(f"   - ⚠️ 配置中有但行情缺失: {len(missing_in_db)} 个")
        if missing_in_db:
            print(f"     缺失明细: {', '.join(missing_in_db[:10])}...")
        print(f"   - ⚠️ 行情中有但配置已删: {len(extra_in_db)} 个")
        
if __name__ == "__main__":
    get_duration_report()
