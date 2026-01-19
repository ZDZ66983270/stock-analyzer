# utils/i18n.py
"""
VERA 系统中英文翻译模块
提供代码层英文标识符到用户友好的中英文显示转换
"""

TRANSLATIONS = {
    # D-states (个股回撤状态)
    "D0": "未形成完整回撤结构",
    "D1": "正常波动期",
    "D2": "结构中性",
    "D3": "深度博弈",
    "D4": "早期反弹",
    "D5": "中期修复",
    "D6": "大部分修复",
    
    # I-states (指数回撤状态)
    "I0": "未形成完整回撤结构",
    "I1": "正常波动期",
    "I2": "结构中性",
    "I3": "博弈区",
    "I4": "敏感阶段",
    "I5": "脆弱阶段",
    "I6": "深度危机",
    
    # Path Risk Levels
    "LOW": "低风险",
    "MID": "中性",
    "HIGH": "高风险",
    
    # Position Zones
    "Peak": "阶段高点",
    "Upper": "上部区域",
    "Middle": "中部区域",
    "Lower": "下部区域",
    "Trough": "阶段低点",
    "Unknown": "未知",
    
    # Market Regime Labels
    "Healthy Differentiation": "健康分化",
    "Systemic Compression": "系统性压缩",
    "Systemic Stress": "系统性压力",
    "Crisis Mode": "危机模式",
    "Selective Market": "选择性市场",
    
    # Amplification Levels
    "Low": "低",
    "Medium": "中等",
    "High": "高",
    "Extreme": "极端",
    
    # Alpha Headroom
    "None": "无",
    
    # Sector Alignment
    "aligned": "同步",
    "negative_divergence": "负向偏离",
    "positive_divergence": "正向偏离",
    
    # Volatility Regime
    "STABLE": "稳定",
    "ELEVATED": "升高",
    "VOLATILE": "波动",
    
    # Valuation Status
    "Overvalued": "高估",
    "Undervalued": "低估",
    "Fair": "合理",
    "Premium": "高估",
    "Discount": "低估",

    # GICS Sectors
    "Energy": "能源",
    "Materials": "原材料",
    "Industrials": "工业",
    "Consumer Discretionary": "可选消费",
    "Consumer Staples": "必需消费",
    "Health Care": "医疗保健",
    "Financials": "金融",
    "Information Technology": "信息技术",
    "Communication Services": "通信服务",
    "Utilities": "公用事业",
    "Real Estate": "房地产",

    # HK Sectors (Custom)
    "HK Tech Leaders": "港股科技龙头",
    "HK Blue Chips": "港股蓝筹",

    # Market Indices
    "^GSPC": "标普500",
    "^NDX": "纳斯达克100",
    "^DJI": "道琼斯工业",
    "HSI": "恒生指数",
    "HSTECH": "恒生科技",
    "000300": "沪深300",
    
    # Quality Levels
    "STRONG": "强",
    "MODERATE": "中等",
    "WEAK": "弱",
}


def translate(key: str, format: str = "bilingual") -> str:
    """
    翻译英文代码为中文或中英双语显示
    
    Args:
        key: 英文标识符 (如 "D2", "HIGH", "Peak")
        format: 显示格式
            - "bilingual": 中英双语 "D2 (结构中性)"
            - "zh_only": 仅中文 "结构中性"
            - "en_only": 仅英文 "D2"
    
    Returns:
        格式化后的字符串
    """
    if key is None:
        return "-"
    
    zh = TRANSLATIONS.get(str(key), None)
    
    if format == "zh_only":
        return zh if zh else str(key)
    elif format == "en_only":
        return str(key)
    elif format == "bilingual":
        if zh:
            return f"{key} ({zh})"
        else:
            return str(key)
    else:
        return str(key)


def get_translation(key: str) -> str:
    """
    获取纯中文翻译（快捷方法）
    
    Args:
        key: 英文标识符
    
    Returns:
        中文翻译，如不存在则返回原key
    """
    return TRANSLATIONS.get(str(key), str(key))


def get_legend_text(category: str) -> str:
    """
    生成完整的 Tooltip 图例说明
    
    Args:
        category: 类别 ("D_STATE", "I_STATE", "PATH_RISK", "VOL_REGIME")
        
    Returns:
        格式化的图例字符串 (Markdown-like)
    """
    if category == "D_STATE":
        return (
            "个股状态定义 (D-States):\n\n"
            "• D0 (未形成结构): 历史数据不足或处于绝对高点\n\n"
            "• D1 (正常波动): 回撤 < 15%\n\n"
            "• D2 (结构中性): 回撤 15-25%，多空平衡\n\n"
            "• D3 (深度博弈): 回撤 > 35%，处于谷底博弈区\n\n"
            "• D4 (早期反弹): 出现触底反弹 (Recovery > 0%)，但仍脆弱\n\n"
            "• D5 (中期修复): 修复进度 > 30%，脱离最危险区域\n\n"
            "• D6 (大部分修复): 修复进度 > 95%，结构重启但未创新高"
        )
    elif category == "I_STATE":
        return (
            "指数状态定义 (I-States):\n\n"
            "• I0 (未形成结构): 处于历史高点附近\n\n"
            "• I1 (正常波动): 回撤 < 10%\n\n"
            "• I2 (结构中性): 回撤 10-20%\n\n"
            "• I3 (博弈区): 回撤 20-30%\n\n"
            "• I4 (敏感阶段): 回撤 30-45%\n\n"
            "• I5 (脆弱阶段): 回撤 45-60%\n\n"
            "• I6 (深度危机): 回撤 > 60%"
        )
    elif category == "PATH_RISK":
        return (
            "路径结构风险 (Path Risk):\n\n"
            "基于回撤状态 (D-State) 的结构化风险映射：\n\n"
            "• LOW (低风险): 对应 D0/D1/D6。底部结构扎实或处于强势区间，上涨阻力较小。\n\n"
            "• MID (中性): 对应 D2/D3。处于中间区域，存在一定套牢盘，多空博弈为主。\n\n"
            "• HIGH (高风险): 对应 D4/D5。处于反弹敏感区或脆弱修复期，上方临近密集套牢区，阻力较大。"
        )
    elif category == "VOL_REGIME":
        return (
            "波动体制 (Volatility Regime):\n\n"
            "• STABLE (稳定): 波动率低于历史中枢，市场情绪平稳，适合顺势交易。\n\n"
            "• ELEVATED (升高): 波动率开始放大，市场出现分歧，建议降低仓位。\n\n"
            "• VOLATILE (剧烈): 极高波动，市场恐慌或狂热，风险收益比极差。"
        )
    elif category == "AMPLIFICATION":
        return (
            "波动放大器 (Amplification):\n\n"
            "• Low (低): 个股与市场波动同步，无额外风险放大。\n\n"
            "• Medium (中): 波动率略高于市场，存在一定的贝塔放大效应。\n\n"
            "• High (高): 显著的高波动特征，往往意味着拥挤交易或情绪化定价。\n\n"
            "• Extreme (极端): 极度危险的波动状态，价格行为可能脱离基本面。"
        )
    elif category == "REGIME":
        return (
            "市场体制 (Market Regime):\n\n"
            "• Healthy Differentiation (健康分化): 个股走势主要由各自基本面驱动，相关性低，是理想的选股环境。\n\n"
            "• Selective Market (选择性市场): 市场宽度收窄，只有部分板块或个股上涨，选股难度增加。\n\n"
            "• Systemic Stress (系统性压力): 宏观因子主导市场，个股普遍下跌，相关性急剧上升。\n\n"
            "• Crisis Mode (危机模式): 市场流动性枯竭或极度恐慌，所有资产遭到无差别抛售。"
        )
    elif category == "STYLE_BIAS":
        return (
            "风格偏离 (Style Bias):\n\n"
            "衡量该个股相对于市场整体风格的偏向性：\n\n"
            "• 成长 (Growth): 相对于大盘表现出的高成长特征（如科技、医药）。\n\n"
            "• 价值 (Value): 相对于大盘表现出的低估值特征（如金融、能源）。\n\n"
            "数值表示偏离程度，正值越大代表该风格特征越明显。"
        )
    elif category == "DIVIDEND_SAFETY":
        return (
            "分红安全性 (Dividend Safety):\n\n"
            "• STRONG (强): 派息率健康 (<65%)，现金流充裕，且有长期分红增长记录。\n\n"
            "• MEDIUM (中): 派息率适中 (65-90%)，或是分红历史存在一定波动，但整体可控。\n\n"
            "• WEAK (弱): 派息率过高 (>90%) 或现金流覆盖不足，存在削减分红的风险。"
        )
    elif category == "EARNINGS_CYCLE":
        return (
            "盈利周期 (Earnings Cycle):\n\n"
            "• E1 (高速成长): EPS 增速 > 20%，处于业绩爆发期。\n\n"
            "• E2 (稳健增长): EPS 增速 5-20%，处于成熟稳定期。\n\n"
            "• E3 (困境反转): 增速由负转正，或出现显著的经营拐点。\n\n"
            "• E4 (增速放缓): 增速降至 0-5%，增长动能减弱。\n\n"
            "• E5 (亏损/下滑): 业绩负增长或处于亏损状态，基本面承压。\n\n"
            "• E6 (早期复苏): 亏损幅度收窄或短期财务指标改善，尚未完全确立增长趋势。"
        )

    return ""
