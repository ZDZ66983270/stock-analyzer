import pandas as pd
import os
import logging
from typing import Dict, Optional
from datetime import datetime

class ExcelExporter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 定义各周期sheet的标准字段顺序
        self.standard_columns = [
            'datetime', 'open', 'high', 'low', 'close', 'volume',
            'MA5', 'MA10', 'MA20',
            'MACD_DIF', 'MACD_DEA', 'MACD_HIST',
            'KDJ_K', 'KDJ_D', 'KDJ_J',
            'RSI6', 'RSI12', 'RSI24'
        ]
        
        # 定义资金流sheet的标准字段顺序
        self.fund_flow_columns = [
            'symbol', 'capital_inflow', 'capital_outflow', 'capital_netflow'
        ]
        
        # 输出目录
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def export_to_excel(self, 
                       stock_code: str, 
                       period_data: Dict[str, pd.DataFrame],
                       capital_flow_data: Optional[pd.DataFrame] = None) -> bool:
        """
        将股票数据导出到Excel文件
        
        Args:
            stock_code: 股票代码
            period_data: 不同周期的数据字典
            capital_flow_data: 资金流数据DataFrame
        
        Returns:
            bool: 是否成功导出
        """
        try:
            # 构建输出文件路径
            filename = f"{stock_code.replace('.', '_')}_all_periods.xlsx"
            filepath = os.path.join(self.output_dir, filename)
            
            # 创建ExcelWriter对象
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # 定义格式
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#D3D3D3',
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                # 导出各个周期的数据
                for period, df in period_data.items():
                    # 验证和修复列
                    df = self._validate_and_fix_columns(df, self.standard_columns)
                    
                    # 写入数据
                    sheet_name = period
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # 获取worksheet对象
                    worksheet = writer.sheets[sheet_name]
                    
                    # 设置列格式
                    self._format_worksheet(worksheet, df, header_format)
                
                # 导出资金流数据
                if capital_flow_data is not None:
                    # 验证和修复资金流数据的列
                    capital_flow_data = self._validate_and_fix_columns(
                        capital_flow_data, 
                        self.fund_flow_columns
                    )
                    
                    # 写入资金流数据
                    capital_flow_data.to_excel(writer, 
                                            sheet_name='capital_flow', 
                                            index=False)
                    
                    # 格式化资金流worksheet
                    worksheet = writer.sheets['capital_flow']
                    self._format_worksheet(worksheet, capital_flow_data, header_format)
            
            self.logger.info(f"成功导出数据到: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出Excel文件失败: {str(e)}")
            return False

    def _validate_and_fix_columns(self, 
                                df: pd.DataFrame, 
                                standard_columns: list) -> pd.DataFrame:
        """
        验证并修复DataFrame的列
        
        Args:
            df: 输入的DataFrame
            standard_columns: 标准列名列表
        
        Returns:
            pd.DataFrame: 修复后的DataFrame
        """
        try:
            # 创建新的DataFrame，包含所有标准列
            new_df = pd.DataFrame(columns=standard_columns)
            
            # 复制现有数据
            for col in standard_columns:
                if col in df.columns:
                    new_df[col] = df[col]
                else:
                    # 对于缺失的列，填充默认值
                    if col == 'datetime':
                        self.logger.warning(f"缺少datetime列")
                        if len(df) > 0:
                            new_df[col] = pd.NaT
                    elif col in ['open', 'high', 'low', 'close', 'volume']:
                        self.logger.warning(f"缺少{col}列，使用0填充")
                        new_df[col] = 0
                    else:
                        self.logger.warning(f"缺少{col}列，使用NaN填充")
                        new_df[col] = float('nan')
            
            return new_df
            
        except Exception as e:
            self.logger.error(f"验证和修复列失败: {str(e)}")
            return df

    def _format_worksheet(self, 
                         worksheet: 'xlsxwriter.worksheet.Worksheet',
                         df: pd.DataFrame,
                         header_format: 'xlsxwriter.format.Format') -> None:
        """
        格式化worksheet
        
        Args:
            worksheet: Excel worksheet对象
            df: 数据DataFrame
            header_format: 表头格式
        """
        try:
            # 设置列宽
            for idx, col in enumerate(df.columns):
                # datetime列
                if col == 'datetime':
                    worksheet.set_column(idx, idx, 20)
                # 数值列
                else:
                    worksheet.set_column(idx, idx, 12)
            
            # 设置表头格式
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
        except Exception as e:
            self.logger.error(f"格式化worksheet失败: {str(e)}") 