"""
VERA Asynchronous ETL Task Queue (异步任务队列)
==============================================================================

本模块实现了一个轻量级的 ETL 任务分发系统，旨在使用单机线程池解决长耗时数据处理问题。
它采用“生产者-消费者”模型，确保前端 API 能够立即向用户返回响应。

核心逻辑:
========================================

I. 异步解耦 (Async Decoupling)
----------------------------------------
- **低延迟响应**: 将耗时约 150 秒的全量历史 ETL 任务推入后台。
- **性能红利**: API 响应时间从“分钟级”优化至“毫秒级”，显著提升用户体验。

II. 线程安全与单例 (Concurrency & Singleton)
----------------------------------------
- **Singleton Pattern**: 确保整个应用生命周期内只有一个任务调度器，避免资源冲突。
- **SQLite Optimization**: 针对 SQLite 的并发限制，通过单线程 Worker 顺序执行写密集型 ETL 任务，规避 `Database is locked` 错误。

III. 任务管理 (Task Management)
----------------------------------------
- **Daemon Thread**: 工作线程配置为守护线程，随主应用启动与退出。
- **Fault Tolerance**: 单个 ETL 任务的崩溃（异常捕获）不会导致整个工作线程退出。

作者: Antigravity
日期: 2026-01-23
"""
import threading
import queue
import logging
from typing import Optional
from etl_service import ETLService

logger = logging.getLogger(__name__)


class ETLQueue:
    """ETL任务队列（单例模式）"""
    
    _instance: Optional['ETLQueue'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.task_queue = queue.Queue(maxsize=1000)
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self._initialized = True
        
        logger.info("✅ ETLQueue initialized")
    
    def start(self):
        """启动工作线程"""
        if self.running:
            logger.warning("⚠️ ETLQueue already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="ETLQueueWorker"
        )
        self.worker_thread.start()
        logger.info("🚀 ETLQueue worker started")
    
    def stop(self):
        """停止工作线程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("🛑 ETLQueue worker stopped")
    
    def enqueue(self, raw_id: int, priority: int = 0):
        """
        添加ETL任务到队列
        
        Args:
            raw_id: RawMarketData记录ID
            priority: 优先级（暂未使用）
        """
        try:
            self.task_queue.put((raw_id, priority), block=False)
            queue_size = self.task_queue.qsize()
            logger.info(f"📥 ETL任务入队: raw_id={raw_id}, queue_size={queue_size}")
        except queue.Full:
            logger.error(f"❌ ETL队列已满，丢弃任务: raw_id={raw_id}")
    
    def _worker(self):
        """工作线程：持续处理队列中的任务"""
        logger.info("🔄 ETL工作线程启动")
        
        while self.running:
            try:
                # 阻塞等待任务（超时1秒检查running状态）
                raw_id, priority = self.task_queue.get(timeout=1)
                
                logger.info(f"🔧 开始处理ETL任务: raw_id={raw_id}")
                
                # 执行ETL处理
                try:
                    ETLService.process_raw_data(raw_id)
                    logger.info(f"✅ ETL任务完成: raw_id={raw_id}")
                except Exception as e:
                    logger.error(f"❌ ETL任务失败: raw_id={raw_id}, error={e}")
                
                self.task_queue.task_done()
                
            except queue.Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"❌ ETL工作线程异常: {e}")
        
        logger.info("🛑 ETL工作线程停止")
    
    def get_queue_size(self) -> int:
        """获取当前队列大小"""
        return self.task_queue.qsize()


# 全局单例
etl_queue = ETLQueue()
