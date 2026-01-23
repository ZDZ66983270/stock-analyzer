#!/usr/bin/env python3
"""
DataOrchestrator 集成测试
测试fetch_latest_data是否正确使用DataOrchestrator进行决策
"""

import sys
sys.path.insert(0, '/Users/zhangzy/My Docs/Privates/22-AI编程/AI+风控App/web-app/backend')

from data_fetcher import DataFetcher
from data_orchestrator import DataOrchestrator
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_decision_logging():
    """测试决策日志是否正确输出"""
    print('=' * 70)
    print('测试1: 决策日志输出')
    print('=' * 70)
    
    fetcher = DataFetcher()
    
    # 测试几个不同市场的股票
    test_symbols = [
        ('TSLA', 'US'),
        ('600030.sh', 'CN'),
        ('09988.hk', 'HK')
    ]
    
    for symbol, market in test_symbols:
        print(f'\n测试 {symbol} ({market}):')
        try:
            # 这里只是触发决策,不实际获取数据
            # 我们通过查看日志来验证DataOrchestrator是否被调用
            result = fetcher.fetch_latest_data(
                symbol=symbol,
                market=market,
                save_db=False,  # 不保存,只测试决策
                force_refresh=False
            )
            
            if result:
                print(f'  ✅ 成功: 价格={result.get("price", "N/A")}')
            else:
                print(f'  ⚠️ 无结果')
                
        except Exception as e:
            print(f'  ❌ 异常: {e}')

def test_force_refresh_decision():
    """测试强制刷新时的决策"""
    print('\n' + '=' * 70)
    print('测试2: 强制刷新决策')
    print('=' * 70)
    
    fetcher = DataFetcher()
    
    symbol = 'TSLA'
    market = 'US'
    
    print(f'\n强制刷新 {symbol} ({market}):')
    try:
        result = fetcher.fetch_latest_data(
            symbol=symbol,
            market=market,
            save_db=False,
            force_refresh=True  # 强制刷新
        )
        
        if result:
            print(f'  ✅ 成功: 价格={result.get("price", "N/A")}')
        else:
            print(f'  ⚠️ 无结果')
            
    except Exception as e:
        print(f'  ❌ 异常: {e}')

def test_orchestrator_direct():
    """直接测试DataOrchestrator"""
    print('\n' + '=' * 70)
    print('测试3: DataOrchestrator直接调用')
    print('=' * 70)
    
    orchestrator = DataOrchestrator()
    
    test_cases = [
        ('TSLA', 'US', '2025-12-18'),
        ('600030.sh', 'CN', '2025-12-18'),
        ('09988.hk', 'HK', '2025-12-18')
    ]
    
    for symbol, market, db_date in test_cases:
        print(f'\n{symbol} ({market}):')
        
        decision = orchestrator.decide_fetch_strategy(
            symbol=symbol,
            market=market,
            force_refresh=False,
            db_latest_date=db_date
        )
        
        print(f'  决策: {decision.fetch_type}')
        print(f'  原因: {decision.reason}')
        print(f'  期望日期: {decision.expected_date}')
        
        if decision.need_backfill_daily:
            print(f'  需要补充: {decision.backfill_date_range}')
            print(f'  补充原因: {decision.backfill_reason}')

if __name__ == '__main__':
    print('\n' + '=' * 70)
    print('DataOrchestrator 集成测试')
    print('当前时间:', DataOrchestrator()._get_server_time().strftime('%Y-%m-%d %H:%M:%S %Z'))
    print('=' * 70)
    
    try:
        # 测试1: 决策日志
        test_decision_logging()
        
        # 测试2: 强制刷新
        test_force_refresh_decision()
        
        # 测试3: 直接调用
        test_orchestrator_direct()
        
        print('\n' + '=' * 70)
        print('✅ 所有测试完成')
        print('=' * 70)
        
    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
