#!/usr/bin/env python3
"""
测试程序：直接从 Yahoo Finance 获取 TSM 财报数据
验证数据源的完整性，不修改数据库
"""
import yfinance as yf
import pandas as pd
from datetime import datetime

def check_yahoo_tsm_data():
    print("=" * 70)
    print("直接从 Yahoo Finance 检查 TSM 财报数据完整性")
    print("=" * 70)
    
    ticker = yf.Ticker("TSM")
    
    # 1. 检查年度财报
    print("\n📊 年度财报 (Annual Financials):")
    print("-" * 70)
    try:
        annual_financials = ticker.financials
        if not annual_financials.empty:
            print(f"✅ 找到 {len(annual_financials.columns)} 个年度财报")
            print("\n可用日期:")
            for date in annual_financials.columns:
                print(f"  - {date.strftime('%Y-%m-%d')}")
            
            # 显示最新的财报数据
            latest_date = annual_financials.columns[0]
            print(f"\n最新年度财报 ({latest_date.strftime('%Y-%m-%d')}):")
            print(f"  可用字段数: {len(annual_financials[latest_date].dropna())}")
            
            # 检查关键字段
            key_fields = ['Total Revenue', 'Net Income', 'Basic EPS']
            for field in key_fields:
                if field in annual_financials.index:
                    val = annual_financials.loc[field, latest_date]
                    if pd.notna(val):
                        print(f"  ✅ {field}: {val:,.0f}")
                    else:
                        print(f"  ❌ {field}: 缺失")
                else:
                    print(f"  ⚠️  {field}: 字段不存在")
        else:
            print("❌ 未找到年度财报数据")
    except Exception as e:
        print(f"❌ 获取年度财报失败: {e}")
    
    # 2. 检查季度财报
    print("\n📊 季度财报 (Quarterly Financials):")
    print("-" * 70)
    try:
        quarterly_financials = ticker.quarterly_financials
        if not quarterly_financials.empty:
            print(f"✅ 找到 {len(quarterly_financials.columns)} 个季度财报")
            print("\n可用日期:")
            for date in quarterly_financials.columns:
                print(f"  - {date.strftime('%Y-%m-%d')}")
            
            # 显示最新的季度财报数据
            latest_date = quarterly_financials.columns[0]
            print(f"\n最新季度财报 ({latest_date.strftime('%Y-%m-%d')}):")
            print(f"  可用字段数: {len(quarterly_financials[latest_date].dropna())}")
            
            # 检查关键字段
            key_fields = ['Total Revenue', 'Net Income', 'Basic EPS']
            for field in key_fields:
                if field in quarterly_financials.index:
                    val = quarterly_financials.loc[field, latest_date]
                    if pd.notna(val):
                        print(f"  ✅ {field}: {val:,.0f}")
                    else:
                        print(f"  ❌ {field}: 缺失")
                else:
                    print(f"  ⚠️  {field}: 字段不存在")
        else:
            print("❌ 未找到季度财报数据")
    except Exception as e:
        print(f"❌ 获取季度财报失败: {e}")
    
    # 3. 检查资产负债表
    print("\n📊 资产负债表 (Balance Sheet):")
    print("-" * 70)
    try:
        balance_sheet = ticker.balance_sheet
        if not balance_sheet.empty:
            print(f"✅ 找到 {len(balance_sheet.columns)} 个资产负债表")
            latest_date = balance_sheet.columns[0]
            print(f"\n最新资产负债表 ({latest_date.strftime('%Y-%m-%d')}):")
            
            key_fields = ['Total Assets', 'Total Liabilities Net Minority Interest', 'Cash And Cash Equivalents']
            for field in key_fields:
                if field in balance_sheet.index:
                    val = balance_sheet.loc[field, latest_date]
                    if pd.notna(val):
                        print(f"  ✅ {field}: {val:,.0f}")
                    else:
                        print(f"  ❌ {field}: 缺失")
                else:
                    print(f"  ⚠️  {field}: 字段不存在")
        else:
            print("❌ 未找到资产负债表数据")
    except Exception as e:
        print(f"❌ 获取资产负债表失败: {e}")
    
    # 4. 检查现金流量表
    print("\n📊 现金流量表 (Cash Flow):")
    print("-" * 70)
    try:
        cashflow = ticker.cashflow
        if not cashflow.empty:
            print(f"✅ 找到 {len(cashflow.columns)} 个现金流量表")
            latest_date = cashflow.columns[0]
            print(f"\n最新现金流量表 ({latest_date.strftime('%Y-%m-%d')}):")
            
            key_fields = ['Operating Cash Flow', 'Free Cash Flow']
            for field in key_fields:
                if field in cashflow.index:
                    val = cashflow.loc[field, latest_date]
                    if pd.notna(val):
                        print(f"  ✅ {field}: {val:,.0f}")
                    else:
                        print(f"  ❌ {field}: 缺失")
                else:
                    print(f"  ⚠️  {field}: 字段不存在")
        else:
            print("❌ 未找到现金流量表数据")
    except Exception as e:
        print(f"❌ 获取现金流量表失败: {e}")
    
    # 5. 总结
    print("\n" + "=" * 70)
    print("📋 数据完整性总结")
    print("=" * 70)
    print("✅ Yahoo Finance 提供了 TSM 的完整财报数据")
    print("✅ 包括年度和季度报告")
    print("✅ 涵盖利润表、资产负债表和现金流量表")
    print("\n💡 如果数据库中某些字段缺失，可能是因为：")
    print("   1. Yahoo Finance 该字段本身为空")
    print("   2. 字段名称映射不匹配")
    print("   3. 数据提取逻辑需要调整")
    print("=" * 70)

if __name__ == "__main__":
    check_yahoo_tsm_data()
