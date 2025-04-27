import pandas as pd
import os
from datetime import datetime

def split_excel_by_department(main_file):
    # 读取Excel文件的所有sheet名称
    excel_file = pd.ExcelFile(main_file)
    sheet_names = excel_file.sheet_names
    
    print("所有sheet名称：", sheet_names)
    
    # 跳过第一个sheet，从第二个sheet开始处理
    all_data = []
    for sheet_name in sheet_names[1:]:  # 从索引1开始（第二个sheet）
        print(f"正在处理sheet: {sheet_name}")
        df = pd.read_excel(main_file, sheet_name=sheet_name)
        all_data.append(df)
    
    # 合并所有sheet的数据
    if all_data:
        df = pd.concat(all_data, ignore_index=True)
        
        # 打印合并后的列名
        print("\n合并后的所有列名：")
        print(df.columns.tolist())
        
        # 使用"发票抬头"列获取唯一值
        if '发票抬头' in df.columns:
            companies = df['发票抬头'].unique()
            print("\n找到的发票抬头：")
            print(companies)
            
            # 获取日期范围
            min_date = df['日期'].min()
            max_date = df['日期'].max()
            date_range = f"{min_date.strftime('%Y%m%d')}至{max_date.strftime('%Y%m%d')}"
            
            # 为每个公司创建对应的文件
            for company in companies:
                company_data = df[df['发票抬头'] == company]
                
                # 创建各类文件
                file_types = {
                    'split': f"样本-(拆分){company}-({date_range}).xlsx",
                    'domestic_flight': f"样本-{company}-国内机票对账单.xlsx",
                    'domestic_hotel': f"样本-{company}-国内酒店.xlsx",
                    'hotel_statement': f"样本-{company}-国内酒店对账单.xlsx",
                    'expense_share': f"样本-{company}-机票、酒店费用分摊表.xlsx",
                    'cost_share': f"样本-费用分摊表.xlsx"
                }
                
                # 根据不同类型筛选数据并保存
                for file_type, file_name in file_types.items():
                    filtered_data = filter_data(company_data, file_type)
                    if not filtered_data.empty:
                        filtered_data.to_excel(file_name, index=False)
                        print(f"已创建文件: {file_name}")
        else:
            print("\n错误：在Excel文件中找不到'发票抬头'列")
            print("可用的列名有：", df.columns.tolist())
    else:
        print("没有找到有效的数据sheet")

def filter_data(data, file_type):
    """根据不同文件类型筛选数据"""
    if file_type == 'split':
        return data  # 全部数据
    elif file_type == 'domestic_flight':
        return data[data['类型'] == '国内机票']
    elif file_type == 'domestic_hotel':
        return data[data['类型'] == '国内酒店']
    elif file_type == 'hotel_statement':
        return data[data['类型'].isin(['国内酒店', '对账单'])]
    elif file_type == 'expense_share':
        return data[data['类型'].isin(['机票', '酒店', '费用分摊'])]
    elif file_type == 'cost_share':
        return data[data['类型'] == '费用分摊']
    
    return pd.DataFrame()  # 返回空DataFrame

# 使用文件
main_file = "样本-主表_副本.xlsx"
split_excel_by_department(main_file)
