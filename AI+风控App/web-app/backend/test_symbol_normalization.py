#!/usr/bin/env python3
"""
测试符号标准化统一性
验证 normalize_symbol_for_watchlist 函数
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from utils.symbol_utils import normalize_symbol_for_watchlist

# 测试用例
test_cases = [
    # (输入, 期望输出符号, 期望市场)
    # CN市场
    ("600519", "600519.SH", "CN"),
    ("600519.sh", "600519.SH", "CN"),
    ("600519.SH", "600519.SH", "CN"),
    ("000001", "000001.SZ", "CN"),
    ("000001.sz", "000001.SZ", "CN"),
    ("300750", "300750.SZ", "CN"),
    
    # HK市场
    ("00700", "00700.HK", "HK"),
    ("00700.hk", "00700.HK", "HK"),
    ("00700.HK", "00700.HK", "HK"),
    ("09988", "09988.HK", "HK"),
    
    # US市场
    ("TSLA", "TSLA", "US"),
    ("tsla", "TSLA", "US"),
    ("AAPL", "AAPL", "US"),
    ("aapl", "AAPL", "US"),
    ("MSFT", "MSFT", "US"),
    ("^SPX", "^SPX", "US"),
    ("^DJI", "^DJI", "US"),
]

print("=" * 80)
print("符号标准化测试")
print("=" * 80)

passed = 0
failed = 0

for input_symbol, expected_symbol, expected_market in test_cases:
    try:
        result_symbol, result_market = normalize_symbol_for_watchlist(input_symbol)
        
        if result_symbol == expected_symbol and result_market == expected_market:
            print(f"✅ PASS: '{input_symbol}' → '{result_symbol}' ({result_market})")
            passed += 1
        else:
            print(f"❌ FAIL: '{input_symbol}'")
            print(f"   期望: '{expected_symbol}' ({expected_market})")
            print(f"   实际: '{result_symbol}' ({result_market})")
            failed += 1
            
    except Exception as e:
        print(f"❌ ERROR: '{input_symbol}' - {e}")
        failed += 1

print("\n" + "=" * 80)
print(f"测试结果: {passed} 通过, {failed} 失败")
print("=" * 80)

if failed == 0:
    print("✅ 所有测试通过！")
    sys.exit(0)
else:
    print("❌ 有测试失败！")
    sys.exit(1)
