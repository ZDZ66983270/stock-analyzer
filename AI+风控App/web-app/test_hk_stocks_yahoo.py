#!/usr/bin/env python3
"""
测试多只港股从 Yahoo Finance 获取季报数据
"""
import yfinance as yf
import pandas as pd

# 测试股票列表
test_stocks = {
    "0700.HK": "腾讯控股",
    "9988.HK": "阿里巴巴-W", 
    "1810.HK": "小米集团-W",
    "0005.HK": "汇丰控股",
    "0998.HK": "中信银行"
}

print("="*100)
print("测试港股 Yahoo Finance 季报数据可用性")
print("="*100)

results = {}

for symbol, name in test_stocks.items():
    print(f"\n{'='*100}")
    print(f"测试: {symbol} - {name}")
    print(f"{'='*100}")
    
    try:
        ticker = yf.Ticker(symbol)
        
        # 1. 获取基本信息
        info = ticker.info
        current_price = info.get('currentPrice') or info.get('regularMarketPreviousClose')
        trailing_pe = info.get('trailingPE')
        trailing_eps = info.get('trailingEps')
        
        print(f"\n📊 基本信息:")
        print(f"   当前价格: {current_price}")
        print(f"   Trailing PE: {trailing_pe}")
        print(f"   Trailing EPS (官方): {trailing_eps}")
        
        # 2. 获取季报数据
        quarterly_is = ticker.quarterly_financials
        
        if quarterly_is is None or quarterly_is.empty:
            print(f"\n❌ 无季报数据")
            results[symbol] = {
                'name': name,
                'has_quarterly': False,
                'reason': '无季报数据'
            }
            continue
        
        print(f"\n✅ 季报数据: {quarterly_is.shape}")
        print(f"   季度数量: {len(quarterly_is.columns)}")
        print(f"   日期范围: {quarterly_is.columns[0]} 到 {quarterly_is.columns[-1]}")
        
        # 3. 检查最近4个季度的数据完整性
        print(f"\n   最近4个季度数据:")
        
        has_eps = False
        has_net_income = False
        has_revenue = False
        
        eps_values = []
        net_income_values = []
        revenue_values = []
        
        for i, col in enumerate(quarterly_is.columns[:4]):
            print(f"\n   Q{i+1}: {col}")
            
            # 检查 EPS
            eps_val = None
            for eps_field in ['Diluted EPS', 'Basic EPS', 'EPS']:
                if eps_field in quarterly_is.index:
                    eps_val = quarterly_is.loc[eps_field, col]
                    if pd.notnull(eps_val):
                        print(f"      ✅ EPS: {eps_val:.2f}")
                        eps_values.append(eps_val)
                        has_eps = True
                        break
            if eps_val is None or pd.isnull(eps_val):
                print(f"      ❌ EPS: N/A")
            
            # 检查净利润
            if 'Net Income' in quarterly_is.index:
                net_income = quarterly_is.loc['Net Income', col]
                if pd.notnull(net_income):
                    print(f"      ✅ 净利润: {net_income/1e9:.2f}亿")
                    net_income_values.append(net_income)
                    has_net_income = True
                else:
                    print(f"      ❌ 净利润: N/A")
            
            # 检查营收
            if 'Total Revenue' in quarterly_is.index:
                revenue = quarterly_is.loc['Total Revenue', col]
                if pd.notnull(revenue):
                    print(f"      ✅ 营收: {revenue/1e9:.2f}亿")
                    revenue_values.append(revenue)
                    has_revenue = True
                else:
                    print(f"      ❌ 营收: N/A")
        
        # 4. 计算 TTM
        print(f"\n   📈 TTM 计算:")
        
        ttm_eps = None
        if len(eps_values) == 4:
            ttm_eps = sum(eps_values)
            print(f"      ✅ TTM EPS (4季度相加): {ttm_eps:.2f}")
            
            if trailing_eps:
                diff_pct = abs(ttm_eps - trailing_eps) / trailing_eps * 100
                print(f"      对比 Yahoo 官方 ({trailing_eps:.2f}): 偏差 {diff_pct:.1f}%")
        else:
            print(f"      ❌ 无法计算 TTM EPS (只有 {len(eps_values)}/4 个季度有数据)")
        
        if len(net_income_values) == 4:
            ttm_income = sum(net_income_values)
            print(f"      ✅ TTM 净利润: {ttm_income/1e9:.2f}亿")
        else:
            print(f"      ⚠️ TTM 净利润不完整 (只有 {len(net_income_values)}/4 个季度)")
        
        # 5. 总结
        results[symbol] = {
            'name': name,
            'has_quarterly': True,
            'quarters_count': len(quarterly_is.columns),
            'has_eps': has_eps,
            'eps_complete': len(eps_values) == 4,
            'has_net_income': has_net_income,
            'net_income_complete': len(net_income_values) == 4,
            'has_revenue': has_revenue,
            'revenue_complete': len(revenue_values) == 4,
            'ttm_eps_calculated': ttm_eps,
            'ttm_eps_official': trailing_eps,
            'can_calculate_pe': ttm_eps is not None and current_price is not None
        }
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        results[symbol] = {
            'name': name,
            'has_quarterly': False,
            'reason': str(e)
        }

# 总结报告
print(f"\n\n{'='*100}")
print("总结报告")
print(f"{'='*100}\n")

print(f"{'股票':<15} {'季报':<8} {'EPS完整':<10} {'净利润完整':<12} {'可计算PE':<10}")
print("-"*100)

for symbol, data in results.items():
    name = data['name']
    has_q = "✅" if data.get('has_quarterly') else "❌"
    eps_ok = "✅" if data.get('eps_complete') else "❌" if data.get('has_eps') else "N/A"
    income_ok = "✅" if data.get('net_income_complete') else "⚠️" if data.get('has_net_income') else "N/A"
    can_pe = "✅" if data.get('can_calculate_pe') else "❌"
    
    print(f"{name:<15} {has_q:<8} {eps_ok:<10} {income_ok:<12} {can_pe:<10}")

print("\n结论:")
print("="*100)
print("""
1. 如果所有测试股票的 EPS 都完整 → Yahoo Finance 港股季报数据可用，优先使用
2. 如果部分股票 EPS 不完整 → 需要 Yahoo + AkShare 混合策略
3. 如果大部分股票都不行 → 继续使用 AkShare，但需要处理累计值问题
""")
