#!/usr/bin/env python3
"""
测试 yfinance 日线数据接口是否包含 EPS 字段
"""
import yfinance as yf
import pandas as pd

# 测试多个市场的代表性股票
test_symbols = [
    ("AAPL", "US - 苹果"),
    ("00700.HK", "HK - 腾讯"),
    ("600030.SS", "CN - 中信证券"),
]

print("=" * 80)
print("测试 yfinance 日线数据 (history) 接口是否包含 EPS")
print("=" * 80)

for symbol, desc in test_symbols:
    print(f"\n📊 测试标的: {symbol} ({desc})")
    print("-" * 80)
    
    try:
        ticker = yf.Ticker(symbol)
        
        # 1. 测试 history 接口（日线数据）
        print("\n1️⃣ history() 接口 - 获取最近5天数据:")
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            print(f"   返回列: {list(hist.columns)}")
            print(f"   数据形状: {hist.shape}")
            
            # 检查是否有 EPS 列
            if 'EPS' in hist.columns or 'Eps' in hist.columns or 'eps' in hist.columns:
                print("   ✅ history 接口包含 EPS 列!")
                print(f"   EPS 样本数据:\n{hist[['Close', 'EPS']].head()}")
            else:
                print("   ❌ history 接口不包含 EPS 列")
                print(f"   最新数据样本:\n{hist.tail(2)}")
        else:
            print("   ⚠️  未获取到数据")
        
        # 2. 测试 info 接口（基本信息）
        print("\n2️⃣ info 接口 - 查找 EPS 相关字段:")
        info = ticker.info
        
        eps_fields = {k: v for k, v in info.items() if 'eps' in k.lower()}
        
        if eps_fields:
            print("   ✅ info 接口包含 EPS 相关字段:")
            for key, value in eps_fields.items():
                print(f"      {key}: {value}")
        else:
            print("   ❌ info 接口未找到 EPS 相关字段")
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")

print("\n" + "=" * 80)
print("测试结论:")
print("=" * 80)
print("""
如果 history() 接口不包含 EPS，说明：
1. yfinance 的日线数据接口本身不提供 EPS
2. EPS 需要从 ticker.info 或财报数据中获取
3. 当前 ETL 流程无法从日线数据中提取 EPS（因为数据源就没有）

建议方案：
- 方案A: 从 ticker.info['trailingEps'] 获取最新 EPS，定期更新
- 方案B: 从财报数据计算 EPS = 净利润 / 流通股数
- 方案C: 使用专门的财务数据接口（如 AkShare 的财务指标接口）
""")
