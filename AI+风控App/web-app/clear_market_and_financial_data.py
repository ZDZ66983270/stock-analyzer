#!/usr/bin/env python3
"""
清空三张行情数据表 (Raw, Daily, Snapshot) 和财务报表 (FinancialFundamentals)
保留 Watchlist 和 Index 基础表
"""
import sys
import os
from sqlmodel import Session, delete

# 添加后端路径
sys.path.append('backend')
from database import engine
from models import MarketDataDaily, MarketSnapshot, RawMarketData, FinancialFundamentals

def main():
    print("🗑️ 正在清空行情与财务核心数据表...")
    print("="*60)
    
    with Session(engine) as session:
        # 1. 行情相关表
        print("📦 清空 RawMarketData...")
        session.exec(delete(RawMarketData))
        
        print("📊 清空 MarketDataDaily...")
        session.exec(delete(MarketDataDaily))
        
        print("📸 清空 MarketSnapshot...")
        session.exec(delete(MarketSnapshot))
        
        # 2. 财务报表
        print("📑 清空 FinancialFundamentals...")
        session.exec(delete(FinancialFundamentals))
        
        session.commit()
        
    print("="*60)
    print("✅ 清理完成！行情表与财务表已完全重置。")
    print("💡 基础配置表 (Watchlist, Index) 已保留。")

if __name__ == "__main__":
    main()
