"""
测试数据源 - 验证 HSTECH 和 CN ETF 的数据获取
"""
import sys
sys.path.append('backend')

import yfinance as yf
from backend.symbol_utils import get_yahoo_symbol

def test_symbol_conversion():
    """测试符号转换逻辑"""
    print("=" * 80)
    print("📝 符号转换测试")
    print("=" * 80)
    
    test_cases = [
        # (code, market, asset_type, expected_yf_symbol)
        ("HSTECH", "HK", "INDEX", "HSTECH.HK"),
        ("159662", "CN", "ETF", "159662.SZ"),
        ("159751", "CN", "ETF", "159751.SZ"),
        ("512800", "CN", "ETF", "512800.SS"),
        ("512880", "CN", "ETF", "512880.SS"),
    ]
    
    for code, market, asset_type, expected in test_cases:
        result = get_yahoo_symbol(code, market, asset_type)
        status = "✅" if result == expected else "❌"
        print(f"{status} {code:10} ({market}, {asset_type:5}) → {result:15} (期望: {expected})")
    
    print()

def test_data_fetch(symbol, yf_symbol, name):
    """测试单个资产的数据获取"""
    print(f"\n{'='*80}")
    print(f"📊 测试: {name} ({symbol} → {yf_symbol})")
    print(f"{'='*80}")
    
    try:
        ticker = yf.Ticker(yf_symbol)
        
        # 测试1: 获取最近5天数据
        print(f"\n1️⃣ 获取最近5天数据...")
        df_5d = ticker.history(period="5d", auto_adjust=True)
        
        if df_5d.empty:
            print(f"   ❌ 无数据")
            return False
        else:
            print(f"   ✅ 获取 {len(df_5d)} 条记录")
            print(f"   📅 日期范围: {df_5d.index[0].date()} → {df_5d.index[-1].date()}")
            
            # 显示最新数据
            latest = df_5d.iloc[-1]
            print(f"\n   最新数据 ({df_5d.index[-1].date()}):")
            print(f"   - 开盘: {latest['Open']:.2f}")
            print(f"   - 最高: {latest['High']:.2f}")
            print(f"   - 最低: {latest['Low']:.2f}")
            print(f"   - 收盘: {latest['Close']:.2f}")
            print(f"   - 成交量: {latest['Volume']:,.0f}")
        
        # 测试2: 获取历史数据范围
        print(f"\n2️⃣ 获取全量历史数据...")
        df_max = ticker.history(period="max", auto_adjust=True)
        
        if df_max.empty:
            print(f"   ❌ 无历史数据")
        else:
            print(f"   ✅ 历史数据: {len(df_max)} 条记录")
            print(f"   📅 历史范围: {df_max.index[0].date()} → {df_max.index[-1].date()}")
            
            # 计算数据年限
            years = (df_max.index[-1] - df_max.index[0]).days / 365.25
            print(f"   ⏱️  数据年限: {years:.1f} 年")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

def main():
    print("\n" + "=" * 80)
    print("🧪 数据源测试 - HSTECH & CN ETF")
    print("=" * 80)
    
    # 第一步: 测试符号转换
    test_symbol_conversion()
    
    # 第二步: 测试实际数据获取
    print("\n" + "=" * 80)
    print("📡 实际数据获取测试")
    print("=" * 80)
    
    test_assets = [
        ("HSTECH", "HSTECH.HK", "恒生科技指数"),
        ("159662", "159662.SZ", "军工ETF"),
        ("159751", "159751.SZ", "芯片ETF"),
        ("512800", "512800.SS", "银行ETF"),
        ("512880", "512880.SS", "证券ETF"),
    ]
    
    results = {}
    for symbol, yf_symbol, name in test_assets:
        success = test_data_fetch(symbol, yf_symbol, name)
        results[name] = success
        
        # 避免请求过快
        import time
        time.sleep(1)
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 测试结果总结")
    print("=" * 80)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
    print("=" * 80)

if __name__ == "__main__":
    main()
