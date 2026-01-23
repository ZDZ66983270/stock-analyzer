#!/usr/bin/env python3
"""
深度测试：检查 TSM 数据源问题
对比数据库中的数据和 Yahoo Finance 实时数据
"""
import yfinance as yf
import pandas as pd
import sys
sys.path.insert(0, '.')

from sqlmodel import Session, select
from backend.database import engine
from backend.models import FinancialFundamentals

def test_tsm_data_source():
    print("=" * 70)
    print("TSM 数据源深度检查")
    print("=" * 70)
    
    # 1. 检查数据库中的数据
    print("\n📊 步骤 1: 检查数据库中的 TSM 数据")
    print("-" * 70)
    with Session(engine) as session:
        stmt = select(FinancialFundamentals).where(
            FinancialFundamentals.symbol.like('%TSM%')
        ).order_by(FinancialFundamentals.as_of_date.desc())
        
        db_records = session.exec(stmt).all()
        
        if db_records:
            print(f"✅ 数据库中找到 {len(db_records)} 条 TSM 记录")
            print(f"   最新记录日期: {db_records[0].as_of_date}")
            print(f"   数据源标记: {db_records[0].data_source}")
            print(f"   Symbol: {db_records[0].symbol}")
        else:
            print("❌ 数据库中未找到 TSM 数据")
    
    # 2. 测试不同的 ticker 符号
    print("\n📊 步骤 2: 测试不同的 Yahoo Finance ticker 符号")
    print("-" * 70)
    
    test_tickers = [
        "TSM",      # 美股 ADR
        "2330.TW",  # 台湾证交所
        "TSM.N",    # NYSE 明确标记
    ]
    
    for ticker_symbol in test_tickers:
        print(f"\n测试 ticker: {ticker_symbol}")
        try:
            ticker = yf.Ticker(ticker_symbol)
            
            # 测试基本信息
            info = ticker.info
            if info and 'symbol' in info:
                print(f"  ✅ 基本信息可用")
                print(f"     名称: {info.get('longName', 'N/A')}")
                print(f"     市场: {info.get('market', 'N/A')}")
                print(f"     币种: {info.get('currency', 'N/A')}")
            else:
                print(f"  ⚠️  基本信息不可用")
            
            # 测试财报数据
            financials = ticker.financials
            if not financials.empty:
                print(f"  ✅ 年度财报: {len(financials.columns)} 个报告期")
                print(f"     最新: {financials.columns[0].strftime('%Y-%m-%d')}")
            else:
                print(f"  ❌ 年度财报: 无数据")
            
            quarterly = ticker.quarterly_financials
            if not quarterly.empty:
                print(f"  ✅ 季度财报: {len(quarterly.columns)} 个报告期")
                print(f"     最新: {quarterly.columns[0].strftime('%Y-%m-%d')}")
            else:
                print(f"  ❌ 季度财报: 无数据")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
    
    # 3. 测试一个已知有效的美股ticker作为对照
    print("\n📊 步骤 3: 对照测试 - AAPL (已知有效)")
    print("-" * 70)
    try:
        aapl = yf.Ticker("AAPL")
        aapl_financials = aapl.financials
        if not aapl_financials.empty:
            print(f"✅ AAPL 年度财报: {len(aapl_financials.columns)} 个报告期")
            print(f"   最新: {aapl_financials.columns[0].strftime('%Y-%m-%d')}")
            print("   → Yahoo Finance API 工作正常")
        else:
            print("❌ AAPL 也无数据 - 可能是网络或 API 问题")
    except Exception as e:
        print(f"❌ AAPL 测试失败: {e}")
    
    # 4. 总结
    print("\n" + "=" * 70)
    print("📋 诊断结论")
    print("=" * 70)
    
    if db_records:
        print("✅ 数据库中有 TSM 数据，说明之前的 fetch_financials.py 成功运行")
        print(f"   数据源: {db_records[0].data_source}")
        print(f"   最新日期: {db_records[0].as_of_date}")
        print("\n💡 可能的情况：")
        print("   1. Yahoo Finance 对 TSM 的数据访问可能有延迟或限制")
        print("   2. 之前运行时数据可用，现在可能暂时不可用")
        print("   3. 需要使用特定的 ticker 符号（如 2330.TW）")
        print("   4. 数据已经在数据库中，无需重新获取")
    else:
        print("⚠️  数据库和 Yahoo Finance 都没有数据")
        print("   需要进一步调查数据获取流程")
    
    print("=" * 70)

if __name__ == "__main__":
    test_tsm_data_source()
