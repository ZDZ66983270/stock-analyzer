#!/usr/bin/env python3
"""
数据下载和 PE 回填批处理脚本
自动执行：
1. reset_and_redownload_all.py - 重置并下载所有数据
2. add_new_asset_complete.py - 添加新资产（如果有）
3. backfill_valuation_history.py - 回填历史 PE（需要用户确认）
"""
import subprocess
import sys
import os
from datetime import datetime

def run_script(script_name, description):
    """运行脚本并显示进度"""
    print("\n" + "="*80)
    print(f"📋 {description}")
    print("="*80)
    print(f"执行: python3 {script_name}")
    print("-"*80)
    
    try:
        result = subprocess.run(
            ["python3", script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            check=True,
            capture_output=False,
            text=True
        )
        print("-"*80)
        print(f"✅ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print("-"*80)
        print(f"❌ {description} 失败")
        print(f"错误: {e}")
        return False
    except Exception as e:
        print("-"*80)
        print(f"❌ {description} 执行出错")
        print(f"错误: {e}")
        return False


def confirm_action(prompt):
    """请求用户确认"""
    while True:
        response = input(f"\n{prompt} (y/n): ").strip().lower()
        if response in ['y', 'yes', '是']:
            return True
        elif response in ['n', 'no', '否']:
            return False
        else:
            print("请输入 y 或 n")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 数据下载和 PE 回填批处理")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 步骤 1: 重置并下载所有数据
    success = run_script(
        "reset_and_redownload_all.py",
        "步骤 1/3: 重置并下载所有历史数据（含 PE 自动计算）"
    )
    
    if not success:
        print("\n❌ 步骤 1 失败，批处理终止")
        sys.exit(1)
    
    # 步骤 2: 添加新资产
    success = run_script(
        "add_new_asset_complete.py",
        "步骤 2/3: 添加新资产到数据库"
    )
    
    if not success:
        print("\n⚠️ 步骤 2 失败，但继续执行")
    
    # 步骤 3: 回填历史 PE（需要确认）
    print("\n" + "="*80)
    print("📋 步骤 3/3: 回填历史 PE 数据")
    print("="*80)
    print("说明:")
    print("  - 此步骤会重新计算所有历史数据的 PE 值")
    print("  - 通过 ETL 重新处理，符合架构规则")
    print("  - 如果步骤 1 已成功，通常不需要运行此步骤")
    print("  - 只在需要修复历史 PE 数据时运行")
    print("-"*80)
    
    if confirm_action("是否执行步骤 3（回填历史 PE）？"):
        success = run_script(
            "backfill_valuation_history.py",
            "步骤 3/3: 回填历史 PE 数据"
        )
        
        if not success:
            print("\n⚠️ 步骤 3 失败")
    else:
        print("\n⏭️ 跳过步骤 3")
    
    # 完成
    print("\n" + "="*80)
    print("✅ 批处理完成")
    print("="*80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    print("\n📊 下一步:")
    print("  1. 检查数据完整性")
    print("  2. 验证 PE 计算准确性")
    print("  3. 启动应用程序")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断批处理")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 批处理执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
