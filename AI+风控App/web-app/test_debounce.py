"""
测试智能防抖功能
验证强制刷新时，闭市情况下是否跳过API调用
"""
import sys
sys.path.insert(0, 'backend')

from data_fetcher import DataFetcher
from datetime import datetime

print("=" * 80)
print("🧪 测试智能防抖 (Smart Debounce)")
print("=" * 80)

fetcher = DataFetcher()

# 测试场景：强制刷新 + 闭市 + 数据库已有最新数据
test_cases = [
    {"symbol": "HSI", "market": "HK", "desc": "港股恒指 (预期：防抖生效)"},
    {"symbol": "000001.SS", "market": "CN", "desc": "A股上证 (预期：防抖生效)"},
    {"symbol": "^SPX", "market": "US", "desc": "美股标普 (预期：防抖生效)"}
]

for case in test_cases:
    print(f"\n{'='*80}")
    print(f"测试: {case['desc']}")
    print(f"Symbol: {case['symbol']}, Market: {case['market']}")
    print(f"参数: force_refresh=True")
    print("-" * 80)
    
    try:
        result = fetcher.fetch_latest_data(
            symbol=case['symbol'],
            market=case['market'],
            force_refresh=True,  # 强制刷新
            save_db=False  # 不保存，仅测试
        )
        
        if result:
            print(f"✅ 返回成功")
            print(f"  价格: {result.get('price')}")
            print(f"  日期: {result.get('date')}")
            print(f"  涨跌幅: {result.get('pct_change', 0):.2f}%")
        else:
            print(f"❌ 返回为空")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n" + "=" * 80)
print("💡 查看日志中是否有 '✅ 防抖生效' 字样")
print("=" * 80)
