#!/usr/bin/env python3
"""
全面数据健康度扫描脚本
检查：
1. ETF 误标为 STOCK
2. 大小写不规范
3. HK 指数残留 0 前缀 (0HSCC, 0HSCE)
4. 代码去重检查
"""
import sys
sys.path.append('backend')
from database import engine
from sqlmodel import Session, text

def scan_health():
    print("🔍 开始全面数据健康度扫描...")
    print("="*60)
    
    issues_found = 0
    
    with Session(engine) as session:
        # 1.获取所有 symbol
        result = session.exec(text("SELECT DISTINCT symbol FROM marketdatadaily")).all()
        symbols = [r[0] for r in result]
        
        print(f"📊 扫描 {len(symbols)} 个唯一资产代码...")
        
        # 规则配置
        etf_keywords = ['ETF', '159', '510', '512', '513', '515', '516', '517', '588', '159', '3033', '2800', '3032', '3110']
        known_etfs = ['TLT', 'SPY', 'QQQ', 'DIA', 'IWM', 'GLD', 'VTV', 'VUG', 'XLB', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLU', 'XLV', 'XLY', 'SGOV', 'IBIT', 'USMV']
        
        for s in symbols:
            # 检查 1: 大小写
            if s != s.upper():
                print(f"❌ 大小写错误: {s}")
                issues_found += 1
            
            # 检查 2: HK 指数 0 前缀
            if '0HSCC' in s or '0HSCE' in s:
                print(f"❌ HK 指数残留 0 前缀: {s}")
                issues_found += 1
                
            # 检查 3: ETF 误标
            parts = s.split(':')
            if len(parts) == 3:
                market, type_, code = parts
                
                # 检查 STOCK 是否应该是 ETF
                if type_ == 'STOCK':
                    # A股 ETF 检查
                    if market == 'CN' and (code.startswith('15') or code.startswith('51') or code.startswith('56') or code.startswith('58')):
                         print(f"❌ 疑似 ETF 误标为 STOCK: {s}")
                         issues_found += 1
                    
                    # 港股 ETF 检查
                    if market == 'HK' and code in ['02800', '03033', '03110', '03437']:
                        print(f"❌ 疑似 ETF 误标为 STOCK: {s}")
                        issues_found += 1
                        
                    # 美股 ETF 检查
                    if market == 'US' and code in known_etfs:
                        print(f"❌ 疑似 ETF 误标为 STOCK: {s}")
                        issues_found += 1
                        
            # 检查 4: CRYPTO 格式
            if 'CRYPTO' in s and 'STOCK' in s:
                print(f"❌ CRYPTO 残留 STOCK 类型: {s}")
                issues_found += 1
                
    print("\n" + "="*60)
    if issues_found == 0:
        print("✅ 扫描完成：未发现异常！数据非常健康。")
    else:
        print(f"⚠️ 扫描完成：发现 {issues_found} 个异常项，请检查上方日志。")
    print("="*60)

if __name__ == "__main__":
    scan_health()
