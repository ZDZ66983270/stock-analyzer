#!/usr/bin/env python3
"""
测试符号别名映射
验证 800000 → HSI, 800700 → HSTECH
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from symbols_config import get_canonical_symbol
from utils.symbol_utils import normalize_symbol_db

# 测试用例
test_cases = [
    # (输入符号, 市场, 期望输出)
    ("800000", "HK", "HSI"),
    ("800700", "HK", "HSTECH"),
    ("HSI", "HK", "HSI"),
    ("HSTECH", "HK", "HSTECH"),
    ("00700.HK", "HK", "00700.HK"),
    ("TSLA", "US", "TSLA"),
]

print("=" * 80)
print("符号别名映射测试")
print("=" * 80)

passed = 0
failed = 0

for input_symbol, market, expected_output in test_cases:
    # 测试 get_canonical_symbol
    result1 = get_canonical_symbol(input_symbol)
    
    # 测试 normalize_symbol_db (应该包含别名映射)
    result2 = normalize_symbol_db(input_symbol, market)
    
    if result2 == expected_output:
        print(f"✅ PASS: '{input_symbol}' ({market}) → '{result2}'")
        passed += 1
    else:
        print(f"❌ FAIL: '{input_symbol}' ({market})")
        print(f"   期望: '{expected_output}'")
        print(f"   实际: '{result2}'")
        failed += 1

print("\n" + "=" * 80)
print(f"测试结果: {passed} 通过, {failed} 失败")
print("=" * 80)

if failed == 0:
    print("✅ 所有测试通过！别名映射正常工作。")
    sys.exit(0)
else:
    print("❌ 有测试失败！")
    sys.exit(1)
