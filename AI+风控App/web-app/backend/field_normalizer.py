"""
数据验证和字段标准化工具
Data Validation and Field Standardization Utilities
"""

import pandas as pd
import logging
from typing import Tuple, Dict, List, Optional
from field_mapping import (
    get_mapping_for_source,
    detect_source_from_columns,
    CHINESE_TO_ENGLISH_MAPPING,
    get_required_fields,
    STANDARD_FIELDS
)

logger = logging.getLogger("FieldNormalizer")


class FieldNormalizer:
    """字段标准化器 - 将不同数据源的字段统一为标准格式"""
    
    @staticmethod
    def normalize_dataframe(
        df: pd.DataFrame, 
        source: Optional[str] = None,
        data_type: Optional[str] = None,
        market: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        标准化DataFrame的字段名
        
        Args:
            df: 原始DataFrame
            source: 数据源 ('yfinance', 'akshare_cn', 'akshare_hk', 'akshare_us')
            data_type: 数据类型 ('daily', 'minute', 'spot')
            market: 市场 ('CN', 'HK', 'US') - 用于自动检测时辅助判断
        
        Returns:
            (标准化后的DataFrame, 验证报告)
        """
        if df is None or df.empty:
            return df, {"status": "empty", "message": "Empty DataFrame"}
        
        original_columns = df.columns.tolist()
        report = {
            "status": "success",
            "original_columns": original_columns,
            "actions": [],
            "warnings": [],
        }
        
        # 1. 自动检测数据源（如果未指定）
        if source is None or data_type is None:
            detected_source, detected_type = detect_source_from_columns(original_columns)
            
            if source is None:
                source = detected_source
                report["actions"].append(f"Auto-detected source: {source}")
            
            if data_type is None:
                data_type = detected_type
                report["actions"].append(f"Auto-detected type: {data_type}")
        
        # 2. 获取映射规则
        mapping = get_mapping_for_source(source, data_type)
        
        # 3. 如果没有专用映射，尝试通用中文转英文
        if not mapping:
            # 检查是否有中文字段
            chinese_fields = [col for col in original_columns if col in CHINESE_TO_ENGLISH_MAPPING]
            if chinese_fields:
                mapping = CHINESE_TO_ENGLISH_MAPPING
                report["actions"].append(f"Using generic Chinese-to-English mapping for {len(chinese_fields)} fields")
        
        # 4. 应用映射
        if mapping:
            # ✅ 修复：避免重复列名
            # 1. 先检查哪些映射会导致冲突（目标列已存在）
            # 2. 对于冲突的情况，删除源列（中文列），保留目标列（英文列）
            rename_dict = {}
            columns_to_drop = []
            
            for source_col, target_col in mapping.items():
                if source_col in df.columns:
                    if target_col in df.columns and source_col != target_col:
                        # 冲突：目标列已存在，删除源列
                        columns_to_drop.append(source_col)
                        report["actions"].append(f"Dropped duplicate column '{source_col}' ('{target_col}' already exists)")
                    else:
                        # 安全：可以重命名
                        rename_dict[source_col] = target_col
            
            # 删除冲突的源列
            if columns_to_drop:
                df = df.drop(columns=columns_to_drop)
            
            # 执行安全的重命名
            if rename_dict:
                df = df.rename(columns=rename_dict)
                report["actions"].append(f"Mapped {len(rename_dict)} columns")
                report["mapped_fields"] = rename_dict
        else:
            report["warnings"].append("No mapping found, DataFrame unchanged")
        
        # 5. 验证必需字段
        required = get_required_fields(data_type)
        if required:
            missing = [f for f in required if f not in df.columns]
            if missing:
                report["status"] = "warning"
                report["warnings"].append(f"Missing required fields: {missing}")
            else:
                report["actions"].append(f"All {len(required)} required fields present")
        
        # 6. 标准化时间字段
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # 移除时区信息（如果有）
                if df['timestamp'].dt.tz is not None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                report["actions"].append("Timestamp standardized")
            except Exception as e:
                report["warnings"].append(f"Timestamp conversion failed: {e}")
        
        report["final_columns"] = df.columns.tolist()
        
        logger.info(f"Field normalization: {report['status']} - {len(report['actions'])} actions, {len(report['warnings'])} warnings")
        
        return df, report
    
    @staticmethod
    def validate_data_quality(df: pd.DataFrame, data_type: str = 'daily') -> Dict:
        """
        验证数据质量
        
        Returns:
            质量报告字典
        """
        report = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "null_counts": {},
            "zero_counts": {},
            "quality_score": 100.0,
            "issues": []
        }
        
        if df.empty:
            report["quality_score"] = 0
            report["issues"].append("DataFrame is empty")
            return report
        
        # 检查空值
        null_counts = df.isnull().sum()
        report["null_counts"] = null_counts[null_counts > 0].to_dict()
        
        # 检查关键字段的零值
        price_fields = ['open', 'high', 'low', 'close', 'price']
        for field in price_fields:
            if field in df.columns:
                zero_count = (df[field] == 0).sum()
                if zero_count > 0:
                    report["zero_counts"][field] = int(zero_count)
                    report["issues"].append(f"{field} has {zero_count} zero values")
        
        # 计算质量分数
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        if total_cells > 0:
            completeness = ((total_cells - null_cells) / total_cells) * 100
            report["quality_score"] = round(completeness, 2)
        
        # 检查异常值
        if 'close' in df.columns:
            # 检查是否有负值
            negative_count = (df['close'] < 0).sum()
            if negative_count > 0:
                report["issues"].append(f"Found {negative_count} negative close prices")
                report["quality_score"] -= 10
        
        return report


# ============================================
# 便捷函数
# ============================================

def normalize_yfinance_daily(df: pd.DataFrame) -> pd.DataFrame:
    """快捷方法：标准化yfinance日线数据"""
    normalized_df, _ = FieldNormalizer.normalize_dataframe(df, source='yfinance', data_type='daily')
    return normalized_df


def normalize_yfinance_minute(df: pd.DataFrame) -> pd.DataFrame:
    """快捷方法：标准化yfinance分钟数据"""
    normalized_df, _ = FieldNormalizer.normalize_dataframe(df, source='yfinance', data_type='minute')
    return normalized_df


def normalize_akshare_cn(df: pd.DataFrame, data_type: str = 'spot') -> pd.DataFrame:
    """快捷方法：标准化akshare CN数据"""
    normalized_df, _ = FieldNormalizer.normalize_dataframe(df, source='akshare_cn', data_type=data_type)
    return normalized_df


def auto_normalize(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """快捷方法：自动检测并标准化"""
    return FieldNormalizer.normalize_dataframe(df)
