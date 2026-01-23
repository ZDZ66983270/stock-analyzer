"""
ETL脚本：从历史数据仓库(MarketDataDaily)提取最新数据，填充到生产快照(MarketSnapshot)
- 计算涨跌幅（基于前一日收盘价）
- 数据验证和清洗
"""
import sys
sys.path.insert(0, 'backend')

from database import engine
from sqlmodel import Session, select
from models import MarketDataDaily, MarketSnapshot
from datetime import datetime


def run_etl_pipeline():
    print("=" * 80)
    print("🔄 ETL: 历史数据仓库 → 生产快照")
    print("=" * 80)
    
    success_count = 0
    fail_count = 0
    
    with Session(engine) as session:
        # 获取所有唯一的(symbol, market)组合
        result = session.exec(
            select(MarketDataDaily.symbol, MarketDataDaily.market)
            .distinct()
        )
        
        symbols = list(result.all())
        print(f"\n找到 {len(symbols)} 个标的需要处理\n")
        
        for idx, (symbol, market) in enumerate(symbols, 1):
            try:
                print(f"[{idx}/{len(symbols)}] {symbol} ({market})...", end=" ")
                
                # 1. 获取最新记录
                latest = session.exec(
                    select(MarketDataDaily)
                    .where(
                        MarketDataDaily.symbol == symbol,
                        MarketDataDaily.market == market
                    )
                    .order_by(MarketDataDaily.timestamp.desc())
                ).first()
                
                if not latest:
                    print("❌ 无数据")
                    fail_count += 1
                    continue
                
                # 2. 获取前一日收盘价（用于计算涨跌幅）
                prev_day = session.exec(
                    select(MarketDataDaily)
                    .where(
                        MarketDataDaily.symbol == symbol,
                        MarketDataDaily.market == market,
                        MarketDataDaily.timestamp < latest.timestamp
                    )
                    .order_by(MarketDataDaily.timestamp.desc())
                ).first()
                
                # 3. 计算涨跌幅
                if prev_day and prev_day.close > 0:
                    change = latest.close - prev_day.close
                    pct_change = (change / prev_day.close) * 100
                    prev_close = prev_day.close
                    calc_method = "计算"
                else:
                    # 如果没有前一日数据，使用原始值
                    change = latest.change or 0
                    pct_change = latest.pct_change or 0
                    prev_close = latest.prev_close
                    calc_method = "原始"
                
                # 4. UPSERT到MarketSnapshot
                existing = session.exec(
                    select(MarketSnapshot)
                    .where(
                        MarketSnapshot.symbol == symbol,
                        MarketSnapshot.market == market
                    )
                ).first()
                
                if existing:
                    # UPDATE
                    existing.price = latest.close
                    existing.open = latest.open
                    existing.high = latest.high
                    existing.low = latest.low
                    existing.prev_close = prev_close
                    existing.change = change
                    existing.pct_change = pct_change
                    existing.volume = latest.volume
                    existing.turnover = latest.turnover
                    existing.pe = latest.pe
                    # Fallback PE calculation if yfinance missing it but we have EPS
                    if (not existing.pe or existing.pe == 0) and latest.eps and latest.eps > 0:
                        existing.pe = latest.close / latest.eps
                        
                    existing.pb = latest.pb
                    existing.dividend_yield = latest.dividend_yield
                    existing.market_cap = latest.market_cap
                    existing.timestamp = latest.timestamp
                    existing.data_source = 'etl'
                    existing.updated_at = datetime.now()
                    session.add(existing)
                else:
                    # INSERT
                    current_pe = latest.pe
                    if (not current_pe or current_pe == 0) and latest.eps and latest.eps > 0:
                        current_pe = latest.close / latest.eps
                        
                    snapshot = MarketSnapshot(
                        symbol=symbol,
                        market=market,
                        price=latest.close,
                        open=latest.open,
                        high=latest.high,
                        low=latest.low,
                        prev_close=prev_close,
                        change=change,
                        pct_change=pct_change,
                        volume=latest.volume,
                        turnover=latest.turnover,
                        pe=current_pe,
                        pb=latest.pb,
                        dividend_yield=latest.dividend_yield,
                        market_cap=latest.market_cap,
                        timestamp=latest.timestamp, # ✅ Fixed: field name is timestamp, not date
                        data_source='etl',
                        fetch_time=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(snapshot)
                
                session.commit()
                print(f"✅ {calc_method} | 涨跌: {change:.2f} ({pct_change:.2f}%)")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 错误: {e}")
                session.rollback()
                fail_count += 1

    # 验证结果
    print("\n" + "=" * 80)
    print("📊 ETL完成统计")
    print("=" * 80)
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")

    with Session(engine) as session:
        count = session.exec(select(MarketSnapshot)).all()
        print(f"📸 MarketSnapshot表记录数: {len(count)}")

    print("=" * 80)

if __name__ == "__main__":
    run_etl_pipeline()

