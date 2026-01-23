import sys
import os

# 确保能找到 backend 模块
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from symbol_utils import get_canonical_id

def test_system_integrity():
    print("🧪 开始 Canonical ID 逻辑稳定性测试...")
    print("=" * 60)
    
    # 测试案例: (输入代码, 预期结果, 描述)
    test_cases = [
        ("TLT", "US:ETF:TLT", "美股债券 ETF (应正确识别为 ETF)"),
        ("000001", "CN:INDEX:000001", "上证指数 (应强制识别为 INDEX)"),
        ("HSI", "HK:INDEX:HSI", "恒生指数"),
        ("AAPL", "US:STOCK:AAPL", "美股个股"),
        ("600030", "CN:STOCK:600030", "A股个股"),
        ("DIA", "US:ETF:DIA", "美股指数 ETF"),
        ("BTC", "CRYPTO:STOCK:BTC", "加密货币"),
    ]
    
    all_pass = True
    for code, expected, desc in test_cases:
        actual, _ = get_canonical_id(code)
        if actual == expected:
            print(f"✅ [PASS] {code:10} -> {actual:20} | {desc}")
        else:
            print(f"❌ [FAIL] {code:10} -> 实际:{actual:20} | 预期:{expected:20} | {desc}")
            all_pass = False
    
    print("=" * 60)
    if all_pass:
        print("🎉 所有逻辑测试通过！系统现在可以安全运行 sync 或下载流程。")
    else:
        print("⚠️ 存在逻辑缺陷，请根据上述失败用例继续调整 symbol_utils.py。")

if __name__ == "__main__":
    test_system_integrity()
