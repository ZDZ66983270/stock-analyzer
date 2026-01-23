#!/usr/bin/env python3
"""
详细检查HK和CN指数的数据
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from sqlmodel import Session, select
from database import engine
from models import MarketDataDaily

def check_hk_cn_indices():
    """检查HK和CN指数的详细数据"""
    
    print("=" * 100)
    print("HK和CN指数详细数据检查")
    print("=" * 100)
    
    with Session(engine) as session:
        # HK指数
        print("\n【恒生指数 (HSI)】最近5条记录:")
        print("-" * 100)
        hsi_records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'HSI')
            .order_by(MarketDataDaily.date.desc())
            .limit(5)
        ).all()
        
        for r in hsi_records:
            print(f"日期: {r.date}")
            print(f"  收盘: {r.close}, 涨跌额: {r.change}, 涨跌幅: {r.pct_change}%")
            print(f"  prev_close: {r.prev_close}")
            print()
        
        print("\n【恒生科技 (HSTECH)】最近5条记录:")
        print("-" * 100)
        hstech_records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == 'HSTECH')
            .order_by(MarketDataDaily.date.desc())
            .limit(5)
        ).all()
        
        for r in hstech_records:
            print(f"日期: {r.date}")
            print(f"  收盘: {r.close}, 涨跌额: {r.change}, 涨跌幅: {r.pct_change}%")
            print(f"  prev_close: {r.prev_close}")
            print()
        
        # CN指数
        print("\n【上证指数 (000001.SS)】最近5条记录:")
        print("-" * 100)
        ssec_records = session.exec(
            select(MarketDataDaily)
            .where(MarketDataDaily.symbol == '000001.SS')
            .order_by(MarketDataDaily.date.desc())
            .limit(5)
        ).all()
        
        for r in ssec_records:
            print(f"日期: {r.date}")
            print(f"  收盘: {r.close}, 涨跌额: {r.change}, 涨跌幅: {r.pct_change}%")
            print(f"  prev_close: {r.prev_close}")
            print()
        
        # 计算正确的涨跌幅
        print("\n" + "=" * 100)
        print("正确值计算:")
        print("=" * 100)
        
        if len(hsi_records) >= 2:
            latest = hsi_records[0]
            prev = hsi_records[1]
            correct_change = latest.close - prev.close
            correct_pct = (correct_change / prev.close) * 100 if prev.close else 0
            print(f"\n【HSI 2025-12-16】")
            print(f"  当前记录: close={latest.close}, change={latest.change}, pct_change={latest.pct_change}%")
            print(f"  前一天: close={prev.close}")
            print(f"  ✅ 正确值: change={correct_change:.2f}, pct_change={correct_pct:.2f}%")
        
        if len(hstech_records) >= 2:
            latest = hstech_records[0]
            prev = hstech_records[1]
            correct_change = latest.close - prev.close
            correct_pct = (correct_change / prev.close) * 100 if prev.close else 0
            print(f"\n【HSTECH 2025-12-16】")
            print(f"  当前记录: close={latest.close}, change={latest.change}, pct_change={latest.pct_change}%")
            print(f"  前一天: close={prev.close}")
            print(f"  ✅ 正确值: change={correct_change:.2f}, pct_change={correct_pct:.2f}%")
        
        if len(ssec_records) >= 2:
            latest = ssec_records[0]
            prev = ssec_records[1]
            correct_change = latest.close - prev.close
            correct_pct = (correct_change / prev.close) * 100 if prev.close else 0
            print(f"\n【000001.SS 2025-12-18】")
            print(f"  当前记录: close={latest.close}, change={latest.change}, pct_change={latest.pct_change}%")
            print(f"  前一天: close={prev.close}")
            print(f"  ✅ 正确值: change={correct_change:.2f}, pct_change={correct_pct:.2f}%")

if __name__ == "__main__":
    try:
        check_hk_cn_indices()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
