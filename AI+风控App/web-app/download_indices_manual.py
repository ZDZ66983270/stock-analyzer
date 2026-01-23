"""
批量下载所有指数的历史数据
"""
import sys
sys.path.insert(0, 'backend')

from data_fetcher_legacy import DataFetcher

indices = [
    ("^DJI", "US", "道琼斯"),
    ("^NDX", "US", "纳斯达克100"),
    ("^SPX", "US", "标普500"),
    ("HSI", "HK", "恒生指数"),
    ("HSTECH", "HK", "恒生科技"),
    ("000001.SS", "CN", "上证指数"),
]

fetcher = DataFetcher()

print("="*60)
print("批量下载指数数据")
print("="*60)

success_count = 0
fail_count = 0
failed_items = []

for symbol, market, name in indices:
    print(f"\n[{indices.index((symbol, market, name)) + 1}/{len(indices)}] {name} ({symbol})...", end=" ")
    
    try:
        result = fetcher.backfill_missing_data(symbol, market, days=30)
        
        if result and result.get('success'):
            records = result.get('records_fetched', 0)
            print(f"✅ {records}条记录")
            success_count += 1
        else:
            msg = result.get('message', '未知错误') if result else '返回None'
            print(f"❌ {msg}")
            fail_count += 1
            failed_items.append(f"{name} ({symbol})")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)[:50]}")
        fail_count += 1
        failed_items.append(f"{name} ({symbol})")

print("\n" + "="*60)
print("下载完成统计")
print("="*60)
print(f"✅ 成功: {success_count}/{len(indices)}")
print(f"❌ 失败: {fail_count}/{len(indices)}")

if failed_items:
    print(f"\n失败列表:")
    for item in failed_items:
        print(f"  - {item}")

print("\n🎉 批量下载完成！")
