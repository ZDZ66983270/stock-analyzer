#!/usr/bin/env python3
"""
清空全库核心数据 (Clear All Data for Canonical Reset)
"""
import sys
import os
from sqlmodel import Session, delete

# 添加后端路径
sys.path.append('backend')
from database import engine
from models import Watchlist, Index, MarketDataDaily, MarketSnapshot, FinancialFundamentals, RawMarketData

def main():
    print("⚠️ 正在清空所有核心表数据...")
    with Session(engine) as session:
        # 1. 行情与快照
        session.exec(delete(MarketDataDaily))
        session.exec(delete(MarketSnapshot))
        session.exec(delete(RawMarketData))
        
        # 2. 财报
        session.exec(delete(FinancialFundamentals))
        
        # 3. 基础配置
        session.exec(delete(Watchlist))
        session.exec(delete(Index))
        
        session.commit()
    print("✅ 所有核心表已清空。系统已准备好接收典范 ID 格式的新数据。")

if __name__ == "__main__":
    main()
