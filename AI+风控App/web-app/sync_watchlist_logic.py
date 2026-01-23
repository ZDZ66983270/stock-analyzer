
import sys
import os
from datetime import datetime
from sqlmodel import Session, select, delete

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from database import engine
from models import Watchlist, Index

WATCHLIST_TARGETS = [
    # HK Stocks/ETFs
    {"symbol": "00005.HK", "name": "汇丰控股", "market": "HK"},
    {"symbol": "00700.HK", "name": "腾讯控股", "market": "HK"},
    {"symbol": "00998.HK", "name": "中信银行", "market": "HK"},
    {"symbol": "01919.HK", "name": "中远海控", "market": "HK"},
    {"symbol": "09988.HK", "name": "阿里巴巴-W", "market": "HK"},
    {"symbol": "02800.HK", "name": "盈富基金", "market": "HK"},
    {"symbol": "03033.HK", "name": "南方恒生科技", "market": "HK"},
    
    # US Stocks
    {"symbol": "AAPL", "name": "苹果", "market": "US"},
    {"symbol": "AMZN", "name": "亚马逊", "market": "US"},
    {"symbol": "BAC", "name": "美国银行", "market": "US"},
    {"symbol": "BTC", "name": "Grayscale Bitcoin Mini Trust", "market": "US"},
    {"symbol": "GOOG", "name": "谷歌-C", "market": "US"},
    {"symbol": "META", "name": "Meta Platforms", "market": "US"},
    {"symbol": "MSFT", "name": "微软", "market": "US"},
    {"symbol": "NVDA", "name": "英伟达", "market": "US"},
    {"symbol": "TSLA", "name": "特斯拉", "market": "US"},
    {"symbol": "TSM", "name": "台积电", "market": "US"},
    
    # US ETFs
    {"symbol": "DIA", "name": "道琼斯指数ETF", "market": "US"},
    {"symbol": "GLD", "name": "黄金现货SPDR", "market": "US"},
    {"symbol": "QQQ", "name": "纳指100ETF", "market": "US"},
    {"symbol": "SGOV", "name": "SGOV", "market": "US"},
    {"symbol": "SPY", "name": "标普500指数ETF", "market": "US"},
    {"symbol": "TLT", "name": "20年期以上国债ETF", "market": "US"},
    {"symbol": "USMV", "name": "美国最小波动率ETF", "market": "US"},
    {"symbol": "VTV", "name": "价值股ETF", "market": "US"},
    {"symbol": "VUG", "name": "成长股ETF", "market": "US"},
    {"symbol": "VYM", "name": "红利股ETF", "market": "US"},
    {"symbol": "XLB", "name": "基础材料ETF", "market": "US"},
    {"symbol": "XLC", "name": "通讯服务ETF", "market": "US"},
    {"symbol": "XLE", "name": "能源指数ETF", "market": "US"},
    {"symbol": "XLF", "name": "金融行业ETF", "market": "US"},
    {"symbol": "XLI", "name": "工业行业ETF", "market": "US"},
    {"symbol": "XLK", "name": "科技行业ETF", "market": "US"},
    {"symbol": "XLP", "name": "消费品指数ETF", "market": "US"},
    {"symbol": "XLRE", "name": "房地产行业ETF", "market": "US"},
    {"symbol": "XLU", "name": "公共事业指数ETF", "market": "US"},
    {"symbol": "XLV", "name": "医疗保健行业ETF", "market": "US"},
    {"symbol": "XLY", "name": "消费品指数SPDR", "market": "US"},
    {"symbol": "IWM", "name": "罗素2000指数ETF", "market": "US"},
    {"symbol": "BTC-USD", "name": "比特币", "market": "US"},
    
    # CN Stocks/ETFs
    {"symbol": "600030.SH", "name": "中信证券", "market": "CN"},
    {"symbol": "600309.SH", "name": "万华化学", "market": "CN"},
    {"symbol": "600536.SH", "name": "中国软件", "market": "CN"},
    {"symbol": "601519.SH", "name": "大智慧", "market": "CN"},
    {"symbol": "601919.SH", "name": "中远海控", "market": "CN"},
    {"symbol": "601998.SH", "name": "中信银行", "market": "CN"},
    {"symbol": "159662.SZ", "name": "航运ETF", "market": "CN"},
    {"symbol": "159751.SZ", "name": "港股通科技ETF", "market": "CN"},
    {"symbol": "159851.SZ", "name": "金融科技ETF", "market": "CN"},
    {"symbol": "159852.SZ", "name": "软件ETF", "market": "CN"},
    {"symbol": "512800.SH", "name": "银行ETF", "market": "CN"},
    {"symbol": "512880.SH", "name": "证券ETF", "market": "CN"},
    {"symbol": "513190.SH", "name": "港股通金融ETF", "market": "CN"},
    {"symbol": "516020.SH", "name": "化工ETF", "market": "CN"},
]

INDEX_TARGETS = [
    # HK Indices
    {"symbol": "HSCEI", "name": "恒生中国企业指数", "market": "HK"},
    {"symbol": "HSI", "name": "恒生指数", "market": "HK"},
    {"symbol": "HSTECH", "name": "恒生科技指数", "market": "HK"},
    
    # US Indices
    {"symbol": "DJI", "name": "道琼斯工业指数", "market": "US"},
    {"symbol": "NDX", "name": "纳斯达克100指数", "market": "US"},
    {"symbol": "SPX", "name": "标普500指数", "market": "US"},
    
    # CN Indices
    {"symbol": "000001.SH", "name": "上证指数", "market": "CN"},
    {"symbol": "000016.SH", "name": "上证50", "market": "CN"},
    {"symbol": "000300.SH", "name": "沪深300", "market": "CN"},
    {"symbol": "000905.SH", "name": "中证500", "market": "CN"},
]

def sync_tables():
    print("🚀 Starting Watchlist and Index synchronization...")
    
    with Session(engine) as session:
        # 1. Clear existing tables
        print("🗑️ Clearing existing Watchlist and Index tables...")
        session.exec(delete(Watchlist))
        session.exec(delete(Index))
        session.commit()
        
        # 2. Add Watchlist Targets
        print(f"📥 Adding {len(WATCHLIST_TARGETS)} items to Watchlist...")
        for target in WATCHLIST_TARGETS:
            item = Watchlist(
                symbol=target["symbol"],
                name=target["name"],
                market=target["market"],
                added_at=datetime.utcnow()
            )
            session.add(item)
        
        # 3. Add Index Targets
        print(f"📥 Adding {len(INDEX_TARGETS)} items to Index table...")
        for target in INDEX_TARGETS:
            item = Index(
                symbol=target["symbol"],
                name=target["name"],
                market=target["market"],
                added_at=datetime.utcnow()
            )
            session.add(item)
            
        session.commit()
        print("✅ Synchronization complete!")

if __name__ == "__main__":
    sync_tables()
