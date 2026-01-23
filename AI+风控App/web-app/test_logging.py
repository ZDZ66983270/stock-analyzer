"""
测试集中式日志系统
验证日志配置、写入和读取功能
"""
import sys
sys.path.insert(0, 'backend')

from logger_config import get_logger, read_logs

# 测试日志写入
print("=" * 80)
print("🧪 测试集中式日志系统")
print("=" * 80)

# 获取不同模块的logger
test_logger = get_logger("TestModule")
fetcher_logger = get_logger("DataFetcher")

# 写入不同级别的日志
print("\n📝 写入测试日志...")
test_logger.debug("这是debug日志")
test_logger.info("✅ 系统启动成功")
test_logger.warning("⚠️ 配置参数缺失，使用默认值")
fetcher_logger.info("🛡️ 防抖生效：数据已最新")
fetcher_logger.error("❌ API调用失败: timeout")

print("✅ 日志写入完成")

# 读取日志
print("\n📖 读取最近5条日志...")
logs = read_logs(limit=5)
for log in logs:
    print(f"  [{log['level']}] {log['timestamp']} - {log['message']}")

print("\n🔍 读取ERROR级别日志...")
error_logs = read_logs(limit=10, level='ERROR')
for log in error_logs:
    print(f"  [{log['level']}] {log['timestamp']} - {log['message']}")

print("\n✅ 日志系统测试完成！")
