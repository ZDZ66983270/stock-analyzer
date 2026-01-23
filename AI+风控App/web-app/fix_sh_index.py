#!/usr/bin/env python3
import sys
sys.path.append('backend')
from download_full_history import download_full_history

print("🚀 启动针对性修复: 上证指数 (CN:INDEX:000001)...")
# 显式传递 INDEX 类型，触发我们在 symbol_utils.py 中写的修复逻辑
saved = download_full_history(
    canonical_id="CN:INDEX:000001",
    code="000001",
    market="CN",
    asset_type="INDEX"
)

if saved > 0:
    print(f"✅ 成功补全上证指数数据: {saved} 条记录")
else:
    print("❌ 补全失败，请检查网络或 yfinance 状态")
