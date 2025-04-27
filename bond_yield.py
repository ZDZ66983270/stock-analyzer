import datetime
from dateutil.relativedelta import relativedelta

def calculate_target_yield():
    print("\n=== 国债目标基准收益率计算器 ===\n")
    
    try:
        # 获取用户输入
        duration = float(input("请输入国债的久期（年）: "))
        coupon_rate = float(input("请输入票面利率（%）: ")) / 100
        
        # 获取到期日
        maturity_date_str = input("请输入到期日 (格式：YYYY-MM-DD): ")
        maturity_date = datetime.datetime.strptime(maturity_date_str, "%Y-%m-%d").date()
        
        current_price = float(input("请输入当前市场价格（元）: "))
        current_benchmark = float(input("请输入当前基准收益率（%）: ")) / 100
        target_profit = float(input("请输入目标获利百分比（%）: ")) / 100
        
        # 计算到期时间（年）
        today = datetime.date.today()
        years_to_maturity = (maturity_date - today).days / 365
        
        # 计算目标价格
        target_price = current_price * (1 + target_profit)
        
        # 使用久期公式反推所需的收益率变动
        # ΔP/P ≈ -D * Δy
        # 其中：ΔP/P 是价格变动比例，D是久期，Δy是收益率变动
        
        price_change_ratio = (target_price - current_price) / current_price
        required_yield_change = -price_change_ratio / duration
        
        target_benchmark = current_benchmark + required_yield_change
        
        # 输出结果
        print("\n=== 计算结果 ===")
        print(f"当前价格: {current_price:.2f}元")
        print(f"目标价格: {target_price:.2f}元")
        print(f"当前基准收益率: {current_benchmark*100:.2f}%")
        print(f"目标基准收益率: {target_benchmark*100:.2f}%")
        print(f"需要收益率变动: {required_yield_change*100:.2f}%")
        
    except ValueError as e:
        print(f"\n错误：输入格式不正确 - {str(e)}")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")

if __name__ == "__main__":
    while True:
        calculate_target_yield()
        
        choice = input("\n是否继续计算？(Y/N): ").upper()
        if choice != 'Y':
            break
    
    print("\n感谢使用国债目标基准收益率计算器！")
