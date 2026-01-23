#!/usr/bin/env python3
"""
调研 AkShare 港股季报数据可用性
测试不同的 AkShare 接口是否提供港股季报数据
"""
import akshare as ak
import pandas as pd

print("="*80)
print("AkShare 港股财报接口调研")
print("="*80)

# 测试股票: 腾讯 00700
test_symbol = "00700"

print(f"\n测试股票: {test_symbol} (腾讯控股)")

# 1. 当前使用的接口: stock_financial_hk_analysis_indicator_em (年度)
print("\n" + "="*80)
print("1. 当前接口: stock_financial_hk_analysis_indicator_em (年度)")
print("="*80)
try:
    df_annual = ak.stock_financial_hk_analysis_indicator_em(symbol=test_symbol, indicator="年度")
    print(f"✅ 成功获取数据")
    print(f"   行数: {len(df_annual)}")
    print(f"   列名: {list(df_annual.columns)}")
    print(f"\n   最近3条记录:")
    print(df_annual.head(3).to_string())
except Exception as e:
    print(f"❌ 失败: {e}")

# 2. 尝试季度接口
print("\n" + "="*80)
print("2. 尝试: stock_financial_hk_analysis_indicator_em (季度)")
print("="*80)
try:
    df_quarterly = ak.stock_financial_hk_analysis_indicator_em(symbol=test_symbol, indicator="季度")
    print(f"✅ 成功获取季度数据!")
    print(f"   行数: {len(df_quarterly)}")
    print(f"   列名: {list(df_quarterly.columns)}")
    print(f"\n   最近5条记录:")
    print(df_quarterly.head(5).to_string())
    
    # 检查日期格式
    if 'START_DATE' in df_quarterly.columns:
        print(f"\n   日期范围:")
        print(f"   最新: {df_quarterly['START_DATE'].iloc[0]}")
        print(f"   最旧: {df_quarterly['START_DATE'].iloc[-1]}")
        
    # 检查关键财务字段
    key_fields = ['OPERATE_INCOME', 'HOLDER_PROFIT', 'BASIC_EPS', 'DILUTED_EPS']
    print(f"\n   关键字段检查:")
    for field in key_fields:
        if field in df_quarterly.columns:
            print(f"   ✅ {field}: 存在")
        else:
            print(f"   ❌ {field}: 不存在")
            
except Exception as e:
    print(f"❌ 失败: {e}")

# 3. 尝试其他可能的港股财报接口
print("\n" + "="*80)
print("3. 探索其他可能的港股财报接口")
print("="*80)

# 3.1 stock_hk_profit_forecast_em
print("\n3.1 stock_hk_profit_forecast_em (利润预测)")
try:
    df = ak.stock_hk_profit_forecast_em(symbol=test_symbol)
    print(f"✅ 成功")
    print(f"   行数: {len(df)}, 列数: {len(df.columns)}")
    print(f"   列名: {list(df.columns)[:10]}")  # 只显示前10列
except Exception as e:
    print(f"❌ 失败: {e}")

# 3.2 stock_financial_hk_report_em
print("\n3.2 stock_financial_hk_report_em (财报)")
try:
    df = ak.stock_financial_hk_report_em(symbol=test_symbol)
    print(f"✅ 成功")
    print(f"   行数: {len(df)}, 列数: {len(df.columns)}")
    print(f"   列名: {list(df.columns)[:10]}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 4. 总结
print("\n" + "="*80)
print("总结")
print("="*80)
print("""
如果 stock_financial_hk_analysis_indicator_em 支持 indicator="季度"，
那么我们可以获取港股季报数据，用于更准确的 TTM 计算。

下一步:
1. 如果季度数据可用 → 修改 fetch_financials.py 添加季报获取
2. 如果不可用 → 继续使用年报，记录已知限制
""")
