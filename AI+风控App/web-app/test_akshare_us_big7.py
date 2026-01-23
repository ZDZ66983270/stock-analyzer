#!/usr/bin/env python3
"""
测试 AkShare 美股知名股票实时数据 - Big 7 + TSM 的 PE 比率
"""

import akshare as ak
import pandas as pd


def test_akshare_us_famous_stocks():
    """测试 AkShare 美股知名股票接口"""
    print("\n" + "="*80)
    print("AkShare 美股知名股票实时数据测试 - Big 7 + TSM")
    print("="*80 + "\n")
    
    # Big 7 + TSM 列表
    target_stocks = {
        'AAPL': '苹果',
        'MSFT': '微软',
        'GOOGL': '谷歌',
        'AMZN': '亚马逊',
        'META': 'Meta',
        'NVDA': '英伟达',
        'TSLA': '特斯拉',
        'TSM': '台积电'
    }
    
    print("目标股票:")
    for code, name in target_stocks.items():
        print(f"  {code:6s} - {name}")
    
    # 获取科技类股票数据
    print("\n正在调用 AkShare API...")
    
    try:
        df = ak.stock_us_famous_spot_em(symbol='科技类')
        
        print(f"✓ 成功获取 {len(df)} 只科技股数据\n")
        print(f"数据字段: {list(df.columns)}\n")
        
        # 检查市盈率字段
        if '市盈率' not in df.columns:
            print("❌ 数据不包含市盈率字段")
            return
        
        print("✅ 数据包含 '市盈率' 字段\n")
        
        # 筛选目标股票
        print("="*80)
        print("Big 7 + TSM 数据查找")
        print("="*80 + "\n")
        
        results = []
        
        for code, name_cn in target_stocks.items():
            # AkShare 返回的代码格式可能是 "105.MSFT" 这样的
            # 需要检查代码字段是否包含目标代码
            stock_data = df[df['代码'].str.contains(code, na=False)]
            
            if not stock_data.empty:
                row = stock_data.iloc[0]
                results.append({
                    '代码': code,
                    'AkShare代码': row['代码'],
                    'AkShare名称': row['名称'],
                    '中文名': name_cn,
                    '最新价($)': row['最新价'],
                    '涨跌幅(%)': row['涨跌幅'],
                    '市盈率': row['市盈率'],
                    '总市值($)': row['总市值']
                })
                print(f"✓ 找到 {code:6s} ({row['代码']:12s}) - {name_cn}")
            else:
                print(f"⚠️  未找到 {code:6s} - {name_cn}")
        
        if not results:
            print("\n❌ 未找到任何目标股票")
            print("\n前10只股票代码示例:")
            print(df[['代码', '名称']].head(10).to_string(index=False))
            return
        
        # 显示详细数据
        result_df = pd.DataFrame(results)
        
        print("\n" + "="*80)
        print(f"成功找到 {len(results)}/{len(target_stocks)} 只目标股票")
        print("="*80 + "\n")
        
        # 格式化显示
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.float_format', lambda x: f'{x:.2f}')
        
        print(result_df[['代码', '中文名', '最新价($)', '涨跌幅(%)', '市盈率', '总市值($)']].to_string(index=False))
        
        # PE 统计
        print("\n" + "="*80)
        print("PE 比率分析")
        print("="*80 + "\n")
        
        valid_pe = result_df[result_df['市盈率'] > 0]
        
        if len(valid_pe) > 0:
            print(f"有效 PE 数据: {len(valid_pe)}/{len(result_df)} 只")
            print(f"PE 范围: {valid_pe['市盈率'].min():.2f} - {valid_pe['市盈率'].max():.2f}")
            print(f"PE 平均: {valid_pe['市盈率'].mean():.2f}")
            print(f"PE 中位: {valid_pe['市盈率'].median():.2f}\n")
            
            # 按 PE 排序
            print("按 PE 从低到高排序:")
            sorted_pe = valid_pe.sort_values('市盈率')[['代码', '中文名', '市盈率']]
            print(sorted_pe.to_string(index=False))
        
        # 市值排名
        print("\n" + "="*80)
        print("市值排名 (单位: 万亿美元)")
        print("="*80 + "\n")
        
        result_df['市值(万亿$)'] = result_df['总市值($)'] / 1e12
        sorted_cap = result_df.sort_values('总市值($)', ascending=False)
        print(sorted_cap[['代码', '中文名', '市值(万亿$)', '市盈率']].to_string(index=False))
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_akshare_us_famous_stocks()
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
    print("\n💡 关键发现:")
    print("  1. AkShare 美股代码格式: '105.MSFT' (包含交易所前缀)")
    print("  2. 实时数据包含市盈率字段")
    print("  3. 适合获取美股的实时 PE 数据")
    print("  4. 但这是实时快照,不是历史每日数据")
    print()
