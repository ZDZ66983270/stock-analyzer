#!/usr/bin/env python3
"""
测试 Yahoo Finance 港股季报数据
"""
import yfinance as yf
import pandas as pd

print("="*80)
print("测试 Yahoo Finance 港股季报数据")
print("="*80)

ticker = yf.Ticker("0700.HK")  # 腾讯

print("\n1. 测试年报数据...")
print("-"*80)
try:
    annual_is = ticker.financials
    print(f"✅ 年报损益表: {annual_is.shape if annual_is is not None and not annual_is.empty else 'Empty'}")
    if annual_is is not None and not annual_is.empty:
        print(f"   日期范围: {annual_is.columns[0]} 到 {annual_is.columns[-1]}")
        print(f"   共 {len(annual_is.columns)} 年")
        
        # 检查关键字段
        key_fields = ['Total Revenue', 'Net Income', 'Diluted EPS', 'Basic EPS']
        for field in key_fields:
            if field in annual_is.index:
                print(f"   ✅ {field}: 存在")
                # 显示最新值
                latest_val = annual_is.loc[field, annual_is.columns[0]]
                print(f"      最新值 ({annual_is.columns[0]}): {latest_val}")
except Exception as e:
    print(f"❌ 年报损益表失败: {e}")

print("\n2. 测试季报数据...")
print("-"*80)
try:
    quarterly_is = ticker.quarterly_financials
    print(f"✅ 季报损益表: {quarterly_is.shape if quarterly_is is not None and not quarterly_is.empty else 'Empty'}")
    if quarterly_is is not None and not quarterly_is.empty:
        print(f"   日期范围: {quarterly_is.columns[0]} 到 {quarterly_is.columns[-1]}")
        print(f"   共 {len(quarterly_is.columns)} 个季度")
        
        # 显示最近4个季度
        print(f"\n   最近4个季度:")
        for i, col in enumerate(quarterly_is.columns[:4]):
            print(f"\n   Q{i+1}: {col}")
            
            # 关键指标
            if 'Total Revenue' in quarterly_is.index:
                revenue = quarterly_is.loc['Total Revenue', col]
                print(f"      营收: {revenue/1e9:.2f}亿" if pd.notnull(revenue) else "      营收: N/A")
            
            if 'Net Income' in quarterly_is.index:
                net_income = quarterly_is.loc['Net Income', col]
                print(f"      净利润: {net_income/1e9:.2f}亿" if pd.notnull(net_income) else "      净利润: N/A")
            
            # 尝试找 EPS
            eps_fields = ['Diluted EPS', 'Basic EPS', 'EPS']
            eps_val = None
            for eps_field in eps_fields:
                if eps_field in quarterly_is.index:
                    eps_val = quarterly_is.loc[eps_field, col]
                    if pd.notnull(eps_val):
                        print(f"      EPS ({eps_field}): {eps_val:.2f}")
                        break
        
        # 计算 TTM
        print(f"\n   📊 TTM 计算 (最近4个季度):")
        if 'Net Income' in quarterly_is.index:
            ttm_income = 0
            for col in quarterly_is.columns[:4]:
                val = quarterly_is.loc['Net Income', col]
                if pd.notnull(val):
                    ttm_income += val
            print(f"      TTM 净利润: {ttm_income/1e9:.2f}亿")
        
        # TTM EPS
        eps_found = False
        for eps_field in eps_fields:
            if eps_field in quarterly_is.index:
                ttm_eps = 0
                count = 0
                for col in quarterly_is.columns[:4]:
                    val = quarterly_is.loc[eps_field, col]
                    if pd.notnull(val):
                        ttm_eps += val
                        count += 1
                if count == 4:
                    print(f"      TTM EPS ({eps_field}): {ttm_eps:.2f}")
                    eps_found = True
                    break
        
        if not eps_found:
            print(f"      ⚠️ 无法计算 TTM EPS (缺少 EPS 字段)")
            
except Exception as e:
    print(f"❌ 季报损益表失败: {e}")

print("\n3. 测试资产负债表...")
print("-"*80)
try:
    quarterly_bs = ticker.quarterly_balance_sheet
    print(f"✅ 季报资产负债表: {quarterly_bs.shape if quarterly_bs is not None and not quarterly_bs.empty else 'Empty'}")
    if quarterly_bs is not None and not quarterly_bs.empty:
        print(f"   共 {len(quarterly_bs.columns)} 个季度")
except Exception as e:
    print(f"❌ 季报资产负债表失败: {e}")

print("\n4. 测试现金流量表...")
print("-"*80)
try:
    quarterly_cf = ticker.quarterly_cashflow
    print(f"✅ 季报现金流量表: {quarterly_cf.shape if quarterly_cf is not None and not quarterly_cf.empty else 'Empty'}")
    if quarterly_cf is not None and not quarterly_cf.empty:
        print(f"   共 {len(quarterly_cf.columns)} 个季度")
except Exception as e:
    print(f"❌ 季报现金流量表失败: {e}")

print("\n5. 获取股票信息...")
print("-"*80)
try:
    info = ticker.info
    print(f"✅ 股票信息获取成功")
    
    # 关键信息
    key_info = {
        'trailingPE': 'Trailing PE',
        'trailingEps': 'Trailing EPS',
        'currentPrice': '当前价格',
        'currency': '币种',
        'financialCurrency': '财报币种'
    }
    
    for key, label in key_info.items():
        val = info.get(key)
        if val:
            print(f"   {label}: {val}")
            
except Exception as e:
    print(f"❌ 股票信息失败: {e}")

print("\n" + "="*80)
print("总结")
print("="*80)
print("""
如果 Yahoo Finance 能提供港股季报数据:
✅ 优点: 数据是离散的季度值（非累计），更适合 TTM 计算
✅ 优点: 与美股使用相同的数据源，逻辑统一
✅ 优点: 数据质量通常较高

下一步:
1. 如果 Yahoo 季报可用 → 优先使用 Yahoo，AkShare 作为备份
2. 如果 Yahoo 季报不可用 → 继续使用 AkShare，但需要处理累计值问题
""")
