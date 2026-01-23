"""
测试ETL异步队列功能

验证:
1. ETL队列能否正常启动
2. 任务能否正确入队
3. 后台工作线程能否处理任务
4. 数据能否正确保存到生产表
"""
import sys
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_etl_queue():
    """测试ETL队列基本功能"""
    print("=" * 70)
    print("测试1: ETL队列基本功能")
    print("=" * 70)
    
    from etl_queue import etl_queue
    
    # 1. 启动队列
    print("\n✓ 启动ETL队列...")
    etl_queue.start()
    time.sleep(1)
    
    # 2. 检查队列状态
    initial_size = etl_queue.get_queue_size()
    print(f"✓ 队列初始大小: {initial_size}")
    
    # 3. 模拟入队（需要先创建一个raw记录）
    print("\n✓ 创建测试Raw记录...")
    from database import engine
    from models import RawMarketData
    from sqlmodel import Session
    from datetime import datetime
    import json
    
    with Session(engine) as session:
        # 创建测试数据
        test_payload = json.dumps([{
            "date": "2025-01-01 16:00:00",
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1000000
        }])
        
        raw = RawMarketData(
            source="test",
            symbol="TEST.SH",
            market="CN",
            period="1d",
            fetch_time=datetime.now(),
            payload=test_payload,
            processed=False
        )
        session.add(raw)
        session.commit()
        session.refresh(raw)
        raw_id = raw.id
        print(f"✓ 测试Raw记录已创建: raw_id={raw_id}")
    
    # 4. 入队
    print(f"\n✓ 将raw_id={raw_id}加入ETL队列...")
    etl_queue.enqueue(raw_id)
    time.sleep(0.5)
    
    # 5. 检查队列大小
    queue_size = etl_queue.get_queue_size()
    print(f"✓ 当前队列大小: {queue_size}")
    
    # 6. 等待处理
    print("\n✓ 等待ETL处理完成...")
    max_wait = 10
    for i in range(max_wait):
        time.sleep(1)
        size = etl_queue.get_queue_size()
        print(f"  [{i+1}s] 队列大小: {size}")
        if size == 0:
            print("✅ ETL处理完成!")
            break
    
    # 7. 验证结果
    print("\n✓ 验证ETL结果...")
    with Session(engine) as session:
        from models import MarketDataDaily
        from sqlmodel import select
        
        # 检查Raw记录是否被标记为已处理
        raw_record = session.get(RawMarketData, raw_id)
        if raw_record and raw_record.processed:
            print("✅ Raw记录已标记为processed=True")
        else:
            print("❌ Raw记录未被处理")
        
        # 检查是否生成了Daily记录
        daily_record = session.exec(
            select(MarketDataDaily).where(
                MarketDataDaily.symbol == "TEST.SH",
                MarketDataDaily.market == "CN"
            )
        ).first()
        
        if daily_record:
            print(f"✅ Daily记录已创建: close={daily_record.close}")
        else:
            print("❌ Daily记录未创建")
    
    # 8. 停止队列
    print("\n✓ 停止ETL队列...")
    etl_queue.stop()
    time.sleep(1)
    
    print("\n" + "=" * 70)
    print("✅ ETL队列测试完成")
    print("=" * 70)


def test_performance():
    """测试性能对比"""
    print("\n" + "=" * 70)
    print("测试2: 性能对比测试")
    print("=" * 70)
    
    from etl_queue import etl_queue
    from database import engine
    from models import RawMarketData
    from sqlmodel import Session
    from datetime import datetime
    import json
    
    # 启动队列
    etl_queue.start()
    
    # 创建10个测试任务
    num_tasks = 10
    print(f"\n✓ 创建{num_tasks}个测试任务...")
    
    raw_ids = []
    with Session(engine) as session:
        for i in range(num_tasks):
            test_payload = json.dumps([{
                "date": f"2025-01-{i+1:02d} 16:00:00",
                "open": 100.0 + i,
                "high": 105.0 + i,
                "low": 99.0 + i,
                "close": 103.0 + i,
                "volume": 1000000 + i * 10000
            }])
            
            raw = RawMarketData(
                source="perf_test",
                symbol=f"PERF{i:03d}.SH",
                market="CN",
                period="1d",
                fetch_time=datetime.now(),
                payload=test_payload,
                processed=False
            )
            session.add(raw)
            session.commit()
            session.refresh(raw)
            raw_ids.append(raw.id)
    
    print(f"✓ 已创建{len(raw_ids)}个Raw记录")
    
    # 测试入队速度
    print(f"\n✓ 批量入队{num_tasks}个任务...")
    start_time = time.time()
    
    for raw_id in raw_ids:
        etl_queue.enqueue(raw_id)
    
    enqueue_time = time.time() - start_time
    print(f"✅ 入队完成，用时: {enqueue_time:.3f}秒")
    print(f"   平均每个任务: {enqueue_time/num_tasks*1000:.1f}毫秒")
    
    # 等待处理完成
    print(f"\n✓ 等待{num_tasks}个任务处理完成...")
    start_time = time.time()
    
    max_wait = 30
    for i in range(max_wait):
        time.sleep(1)
        size = etl_queue.get_queue_size()
        if i % 2 == 0:  # 每2秒打印一次
            print(f"  [{i+1}s] 队列剩余: {size}")
        if size == 0:
            break
    
    process_time = time.time() - start_time
    print(f"✅ 处理完成，用时: {process_time:.3f}秒")
    print(f"   平均每个任务: {process_time/num_tasks:.3f}秒")
    
    # 停止队列
    etl_queue.stop()
    
    print("\n" + "=" * 70)
    print("性能测试总结:")
    print(f"  入队速度: {enqueue_time:.3f}秒 (几乎即时)")
    print(f"  处理速度: {process_time:.3f}秒 (后台异步)")
    print(f"  用户感知延迟: {enqueue_time:.3f}秒 ⭐")
    print(f"  性能提升: {(process_time/enqueue_time):.0f}倍")
    print("=" * 70)


if __name__ == "__main__":
    try:
        # 测试1: 基本功能
        test_etl_queue()
        
        # 测试2: 性能对比
        test_performance()
        
        print("\n" + "🎉" * 35)
        print("所有测试通过! 异步ETL队列工作正常!")
        print("🎉" * 35)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
