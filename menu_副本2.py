import sys
import subprocess

def main_menu():
    while True:
        print("\n请选择一个操作：")
        print("1. 股票新高后回落分析，运行本地的 stock_highdrop.py")
        print("2. 股票对比，运行本地的 stock_index.py")
        print("3. 大选年指数分析，运行本地的 election_year.py")
        print("4. 获取分红和股息率，运行本地的 dividend_yield.py")
        print("5. 获取换手率，运行本地的 turnover_ratio.py")
        print("6. 12个月股价排序，运行本地的 month_comparison.py")
        print("7. 对比A股港股价差，运行本地的 CN & HK comparison.py")
        print("0. 退出，本程序关闭")

        choice = input("请输入选项（0/1/2/3/4/5/6/7）：")

        if choice == '1':
            print("正在运行股票新高后回落分析...")
            subprocess.run([sys.executable, "stock_highdrop.py"])  # 使用 sys.executable
        elif choice == '2':
            print("正在运行股票对比...")
            subprocess.run([sys.executable, "stock_index.py"])  # 使用 sys.executable
        elif choice == '3':
            print("正在运行大选年指数分析...")
            subprocess.run([sys.executable, "election_year.py"])  # 使用 sys.executable
        elif choice == '4':
            print("正在运行分红和股息率分析...")
            subprocess.run([sys.executable, "dividend_yield.py"])  # 使用 sys.executable
        elif choice == '5':
            print("正在运行换手率分析...")
            subprocess.run([sys.executable, "turnover_ratio.py"])  # 使用 sys.executable
        elif choice == '6':
            print("正在运行12个月股价排序分析...")
            subprocess.run([sys.executable, "month_comparison.py"])  # 使用 sys.executable
        elif choice == '7':
            print("正在对比A股港股价差...")
            subprocess.run([sys.executable, "CN & HK comparison.py"])  # 使用 sys.executable
        elif choice == '0':
            print("程序结束。")
            break
        else:
            print("无效输入，请重新选择。")

if __name__ == "__main__":
    main_menu()
