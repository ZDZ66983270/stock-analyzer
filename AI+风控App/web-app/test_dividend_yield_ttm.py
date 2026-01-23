"""
测试 AkShare 股息率(TTM)获取接口
目标: 验证各接口返回的数据格式和可用性
"""

import akshare as ak
import yfinance as yf
from datetime import datetime

print("=" * 80)
print("股息率 TTM 数据获取测试")
print("=" * 80)
print(f"测试时间: {datetime.now()}")
print()

# ============================================================================
# 1. 测试 A股 - 同花顺接口 (推荐)
# ============================================================================
print("1️⃣ 测试 A股 - 同花顺接口 (stock_fhps_detail_ths)")
print("-" * 80)
try:
    cn_symbol = "600009"  # 上海机场
    df = ak.stock_fhps_detail_ths(symbol=cn_symbol)
    print(f"✅ 成功获取 {cn_symbol} 数据")
    print(f"   数据行数: {len(df)}")
    print(f"   列名: {df.columns.tolist()}")
    print()
    
    # 查看最新一期数据 (数据是倒序的,最新的在最后)
    if len(df) > 0:
        latest = df.iloc[-1]  # 最后一行是最新数据
        print("   最新一期分红数据:")
        print(f"   - 报告期: {latest.get('报告期', 'N/A')}")
        print(f"   - 分红总额: {latest.get('分红总额', 'N/A')}")
        print(f"   - 税前分红率: {latest.get('税前分红率', 'N/A')}")
        print(f"   - 股利支付率: {latest.get('股利支付率', 'N/A')}")
        print(f"   - 方案进度: {latest.get('方案进度', 'N/A')}")
        
        # 检查数据类型
        div_yield = latest.get('税前分红率')
        print(f"\n   税前分红率数据类型: {type(div_yield)}")
        print(f"   税前分红率原始值: {repr(div_yield)}")
        
        # 尝试解析百分比字符串
        if isinstance(div_yield, str) and div_yield != '--':
            try:
                # 移除百分号并转换为浮点数
                div_value = float(div_yield.replace('%', ''))
                print(f"   解析后的数值: {div_value} (即 {div_value}%)")
            except:
                print(f"   无法解析为数值")
        
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n")

# ============================================================================
# 2. 测试 A股 - 巨潮资讯接口
# ============================================================================
print("2️⃣ 测试 A股 - 巨潮资讯接口 (stock_dividend_cninfo)")
print("-" * 80)
try:
    cn_symbol = "600009"
    df = ak.stock_dividend_cninfo(symbol=cn_symbol)
    print(f"✅ 成功获取 {cn_symbol} 数据")
    print(f"   数据行数: {len(df)}")
    print(f"   列名: {df.columns.tolist()}")
    print()
    
    if len(df) > 0:
        latest = df.iloc[0]
        print("   最新一期分红数据:")
        print(f"   - 实施方案公告日期: {latest.get('实施方案公告日期', 'N/A')}")
        print(f"   - 分红类型: {latest.get('分红类型', 'N/A')}")
        print(f"   - 实施方案分红说明: {latest.get('实施方案分红说明', 'N/A')}")
        
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n")

# ============================================================================
# 3. 测试 港股 - 东方财富财务分析指标接口
# ============================================================================
print("3️⃣ 测试 港股 - 东方财富财务分析指标接口 (stock_financial_hk_analysis_indicator_em)")
print("-" * 80)
try:
    hk_symbol = "00700"  # 腾讯
    df = ak.stock_financial_hk_analysis_indicator_em(symbol=hk_symbol)
    print(f"✅ 成功获取 {hk_symbol} 数据")
    print(f"   数据行数: {len(df)}")
    print(f"   列名: {df.columns.tolist()}")
    print()
    
    if len(df) > 0:
        # 显示所有数据
        print("   所有财务指标:")
        for col in df.columns:
            print(f"   - {col}: {df[col].iloc[0] if len(df) > 0 else 'N/A'}")
        
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n")

# ============================================================================
# 4. 搜索港股相关的所有接口
# ============================================================================
print("4️⃣ 搜索 AkShare 中所有港股相关接口")
print("-" * 80)
try:
    hk_funcs = [attr for attr in dir(ak) if 'hk' in attr.lower()]
    print(f"找到 {len(hk_funcs)} 个港股相关接口:")
    
    # 筛选可能包含股息/分红的接口
    dividend_funcs = [f for f in hk_funcs if any(keyword in f.lower() for keyword in ['dividend', 'financial', 'indicator', 'payout'])]
    print(f"\n可能包含股息数据的接口 ({len(dividend_funcs)} 个):")
    for func in sorted(dividend_funcs):
        print(f"   - {func}")
        
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n")
print("=" * 80)
print("测试完成")
print("=" * 80)
