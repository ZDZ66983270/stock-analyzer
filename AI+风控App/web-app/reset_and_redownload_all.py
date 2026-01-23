#!/usr/bin/env python3
"""
完整重置与重新下载流程 (Complete Reset & Re-download)
执行顺序：
1. 清空所有核心表（行情、财报、watchlist）
2. 从 symbols.txt 导入资产列表到 watchlist
3. 下载财报数据
4. 下载行情数据（ETL 自动计算 PE）
"""
import subprocess
import sys
import time
from pathlib import Path

# 添加 backend 路径
sys.path.append('backend')
from sqlmodel import Session, delete, select, func
from backend.database import engine
from backend.models import MarketDataDaily, MarketSnapshot, FinancialFundamentals, Watchlist, RawMarketData
from backend.symbol_utils import get_canonical_id
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResetAndRedownload")


def clear_all_tables():
    """清空所有核心表"""
    print(f"\n{'='*80}")
    print(f"🗑️  步骤 1: 清空所有核心表")
    print(f"{'='*80}")
    
    with Session(engine) as session:
        tables = [
            (MarketDataDaily, "行情日线数据"),
            (MarketSnapshot, "行情快照"),
            (RawMarketData, "原始数据"),
            (FinancialFundamentals, "财报数据"),
            (Watchlist, "观察列表")
        ]
        
        for model, name in tables:
            try:
                result = session.exec(delete(model))
                session.commit()
                logger.info(f"  ✅ 已清空 {name} 表")
            except Exception as e:
                logger.error(f"  ❌ 清空 {name} 表失败: {e}")
                session.rollback()
    
    # 统计剩余记录并确认
    print("\n📊 清空后各表状态:")
    with Session(engine) as session:
        for model, name in tables:
            count = session.exec(select(func.count()).select_from(model)).one()
            status = "✅ 空" if count == 0 else f"⚠️ 剩 {count} 条"
            print(f"  - {name:<10}: {status}")
            
    print("\n⚠️  请确认所有表已清空 (应全为'✅ 空')。")
    try:
        input("👉 按 Enter 键继续，或 Ctrl+C 退出... ")
    except KeyboardInterrupt:
        print("\n❌ 用户取消")
        sys.exit(0)


def import_symbols_to_watchlist():
    """从 symbols.txt 导入资产列表到 watchlist（根据注释确定市场和类型）"""
    print(f"\n{'='*80}")
    print(f"📥 步骤 2: 从 symbols.txt 导入资产列表")
    print(f"{'='*80}")
    
    symbols_file = Path("imports/symbols.txt")
    
    if not symbols_file.exists():
        logger.warning(f"  ⚠️ {symbols_file} 不存在，跳过导入")
        return
    
    with Session(engine) as session:
        # 读取 symbols.txt
        with open(symbols_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 解析注释确定当前分类
        current_market = None
        current_type = None
        added_count = 0
        
        # =================================================================================================
        # 🔒 DO NOT MODIFY THIS SECTION / 请勿修改此部分代码 🔒
        # Use imports/symbols.txt layout to strictly identify Market and Type.
        # 根据 imports/symbols.txt 的布局严格识别市场和类型。
        # =================================================================================================
        
        # 注释模式映射
        section_patterns = {
            'A股指数 (CN Indices)': ('CN', 'INDEX'),
            '港股指数 (HK Indices)': ('HK', 'INDEX'),
            '美股指数 (US Indices)': ('US', 'INDEX'),
            'A股 (CN Stocks)': ('CN', 'STOCK'),
            'A股 ETF (CN ETFs)': ('CN', 'ETF'),
            '港股 (HK Stocks)': ('HK', 'STOCK'),
            '港股 ETF (HK ETFs)': ('HK', 'ETF'),
            '美股 (US Stocks)': ('US', 'STOCK'),
            '美股 ETF (US ETFs)': ('US', 'ETF'),
            '指数 (Indices)': (None, 'INDEX'),  # 保留兼容旧格式
            '加密货币 (Crypto)': ('CRYPTO', 'CRYPTO'),
        }
        
        for line in lines:
            line = line.strip()
            
            # 检查是否是分类注释
            if line.startswith('#'):
                for pattern, (market, asset_type) in section_patterns.items():
                    if pattern in line:
                        current_market = market
                        current_type = asset_type
                        break
                continue
            
            # 跳过空行
            if not line:
                continue
            
            # 如果没有设置当前分类，跳过
            if current_type is None:
                # logger.warning(f"  ⚠️ 跳过 {line}（未找到分类标题）") # 减少噪音
                continue
            
            code = line.split()[0]  # 只取第一个部分
            
            try:
                # 对于指数，需要根据代码判断市场
                if current_type == 'INDEX':
                    if code.isdigit() and len(code) == 6:
                        market = 'CN'
                    elif code in ['HSI', 'HSTECH', 'HSCC', 'HSCE']:
                        market = 'HK'
                    else:
                        market = 'US'
                else:
                    market = current_market
                
                # 获取典范 ID
                # 关键修复: 传递 current_type 以确保 DJI/NDX 被正确识别为 INDEX
                canonical_id, canonical_market = get_canonical_id(code, market, current_type)
                
                # 验证类型是否匹配
                expected_type = current_type
                actual_type = canonical_id.split(':')[1] if ':' in canonical_id else None
                
                if actual_type and actual_type != expected_type:
                    logger.warning(f"  ⚠️ 类型不匹配: {code} 期望={expected_type}, 实际={actual_type}")
                
                # 检查是否已存在
                existing = session.exec(
                    select(Watchlist).where(Watchlist.symbol == canonical_id)
                ).first()
                
                if existing:
                    logger.info(f"  ⏭️  {canonical_id} 已存在，跳过")
                    continue
                
                # 添加到 watchlist
                new_item = Watchlist(
                    symbol=canonical_id,
                    market=canonical_market,
                    name=code
                )
                session.add(new_item)
                added_count += 1
                logger.info(f"  ✅ 添加: {code} → {canonical_id} ({canonical_market}, {expected_type})")
                
            except Exception as e:
                logger.error(f"  ❌ 处理 {code} 失败: {e}")
                continue
        
        # =================================================================================================
        # 🔓 END OF CRITICAL SECTION / 关键部分结束 🔓
        # =================================================================================================
        
        session.commit()
        print(f"\n✅ 成功导入 {added_count} 个资产到 watchlist")
        
        # 列出当前所有资产并确认
        print("\n📋 当前 Watchlist 资产列表:")
        all_watchlists = session.exec(select(Watchlist).order_by(Watchlist.market, Watchlist.symbol)).all()
        print(f"{'ID':<5} | {'Symbol (Canonical)':<20} | {'Name':<10} | {'Market':<8}")
        print("-" * 50)
        for w in all_watchlists:
            print(f"{w.id:<5} | {w.symbol:<20} | {w.name:<10} | {w.market:<8}")
        print("-" * 50)
        print(f"总计: {len(all_watchlists)} 个资产")
        
        print("\n⚠️  请确认资产列表无误。下一步将开始下载财报和行情数据。")
        try:
            input("👉 按 Enter 键确认并开始下载，或 Ctrl+C 退出... ")
        except KeyboardInterrupt:
            print("\n❌ 用户取消")
            sys.exit(0)



def run_script(script_name, description):
    """执行 Python 脚本"""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"{'='*80}")
    try:
        result = subprocess.run(
            [sys.executable] + script_name.split(),
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✅ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("🔄 开始完整重置与重新下载流程")
    print("="*80)
    
    try:
        # 步骤 1: 清空所有表
        clear_all_tables()
        
        # 步骤 2: 从 symbols.txt 导入
        import_symbols_to_watchlist()
        
        # 步骤 3-5: 下载数据
        steps = [
            ("fetch_financials.py", "步骤 3: 下载财报数据"),
            ("download_full_history.py", "步骤 4: 下载行情数据"),
            ("fetch_valuation_history.py", "步骤 5: 获取A股/港股历史PE/PB数据"),
        ]
        
        for script, desc in steps:
            success = run_script(script, desc)
            if not success:
                print(f"\n⚠️ 流程在 '{desc}' 步骤失败，是否继续？")
                response = input("输入 'y' 继续，其他键退出: ")
                if response.lower() != 'y':
                    print("❌ 流程已中止")
                    return
            time.sleep(2)
        
        print("\n" + "="*80)
        print("🎉 完整重置与重新下载流程已完成！")
        print("="*80)
        print("\n📊 数据库现在包含：")
        print("  - 从 symbols.txt 导入的资产列表（典范 ID 格式）")
        print("  - 完整的财报数据")
        print("  - 完整的行情数据")
        print("  - A股/港股的历史PE/PB数据")
        print("\n💡 下一步：")
        print("  1. 运行ETL更新快照: python3 run_etl.py")
        print("  2. 或添加新资产: python3 add_new_asset_complete.py")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作（Ctrl+C）")
        print("流程已终止")
        sys.exit(1)


if __name__ == "__main__":
    main()
