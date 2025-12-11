import os
import pandas as pd
from datetime import datetime, timedelta
import glob
import re
from dateutil.parser import parse

def get_market_from_filename(filename):
    """从文件名获取市场类型"""
    filename = filename.upper()
    if "_US_" in filename or filename.endswith("_US.XLSX") or "_US." in filename:
        return "US"
    elif "_HK_" in filename or filename.endswith("_HK.XLSX") or "_HK." in filename:
        return "HK"
    elif "_CN_" in filename or filename.endswith("_CN.XLSX") or "_CN." in filename:
        return "CN"
    elif ".US_" in filename or ".US." in filename:
        return "US"
    elif ".HK_" in filename or ".HK." in filename:
        return "HK"
    elif ".CN_" in filename or ".CN." in filename:
        return "CN"
    else:
        return "Other"

def process_file(input_path, output_dir, start_date, end_date):
    """处理单个文件，提取指定日期范围的日线数据"""
    try:
        # 读取Excel文件
        xls = pd.ExcelFile(input_path)
        
        # 检查是否有1d sheet
        if '1d' not in xls.sheet_names:
            print(f"文件 {input_path} 中没有日线数据")
            return
        
        # 读取日线数据
        df = xls.parse('1d')
        
        # 确保时间列存在
        if '时间' not in df.columns:
            print(f"文件 {input_path} 中没有时间列")
            return
        
        # 转换时间列为datetime
        df['时间'] = pd.to_datetime(df['时间'])
        
        # 过滤日期范围
        mask = (df['时间'].dt.date >= start_date) & (df['时间'].dt.date <= end_date)
        df_filtered = df[mask]
        
        if df_filtered.empty:
            print(f"文件 {input_path} 在指定日期范围内没有数据")
            return
        
        # 获取市场类型
        market = get_market_from_filename(os.path.basename(input_path))
        
        # 创建输出目录
        market_output_dir = os.path.join(output_dir, market)
        os.makedirs(market_output_dir, exist_ok=True)
        
        # 生成输出文件名
        base_name = os.path.basename(input_path)
        name_without_ext = os.path.splitext(base_name)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name_without_ext}_daily_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{timestamp}.xlsx"
        output_path = os.path.join(market_output_dir, output_filename)
        
        # 保存数据
        df_filtered.to_excel(output_path, index=False)
        print(f"已保存到: {output_path}")
        
    except Exception as e:
        print(f"处理文件 {input_path} 时出错: {str(e)}")

def main():
    # 获取用户输入的开始日期
    while True:
        start_date_str = input("请输入开始日期 (YYYY-MM-DD，默认为一年前): ").strip()
        if not start_date_str:
            # 默认设置为一年前
            start_date = datetime.now().date() - timedelta(days=365)
            break
        try:
            start_date = parse(start_date_str).date()
            break
        except:
            print("日期格式无效，请使用YYYY-MM-DD格式")
    
    # 设置结束日期为今天
    end_date = datetime.now().date()
    
    print(f"\n处理日期范围: {start_date} 至 {end_date}")
    
    # 设置输入输出目录
    input_base_dir = "output_V4"
    output_base_dir = "proceeded_V4"
    
    # 确保输出目录存在
    os.makedirs(output_base_dir, exist_ok=True)
    
    # 处理每个市场目录
    for market in ['US', 'HK', 'CN']:
        market_input_dir = os.path.join(input_base_dir, market)
        if not os.path.exists(market_input_dir):
            print(f"目录不存在: {market_input_dir}")
            continue
            
        print(f"\n处理{market}市场数据...")
        
        # 获取所有Excel文件
        excel_files = glob.glob(os.path.join(market_input_dir, "*.xlsx"))
        
        if not excel_files:
            print(f"在 {market_input_dir} 中没有找到Excel文件")
            continue
            
        # 处理每个文件
        for file_path in excel_files:
            print(f"\n处理文件: {os.path.basename(file_path)}")
            process_file(file_path, output_base_dir, start_date, end_date)
    
    print("\n处理完成！")

if __name__ == "__main__":
    main() 