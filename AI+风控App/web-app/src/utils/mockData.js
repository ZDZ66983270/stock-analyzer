// Complete Mock Data for Offline Mode
// This allows the app to function without backend connectivity

export const mockMoutaiData = {
    // Basic Market Data
    symbol: '600519',
    market: 'SH',
    type: 'stock',
    name: '贵州茅台',
    price: 1725.50,
    prev_close: 1710.20,
    pct_change: 0.89,
    change: 15.30,
    open: 1715.00,
    high: 1732.80,
    low: 1710.50,
    volume: 32500,  // 万手
    turnover: 561000000,  // 元

    // Extended Info
    pe_ratio: 8.5,
    market_cap: 2170000000000,  // 2.17万亿
    dividend_yield: 1.85,
    buyback_ratio_1y: 0.12,

    // Analysis Result
    analysisResult: {
        stockCycle: '震荡',
        sectorCycle: '复苏',
        macroCycle: '衰退',
        signal_value: 1.5,  // -3 to +3
        total_score: 75,
        weighted_score: 82,
        model_details: [
            {
                name: '乔治·达格尼诺周期模型',
                signal: '看多 (Bullish)',
                score: 88,
                weight: 0.4,
                description: '库存周期触底回升，先行指标（信贷脉冲）转正。'
            },
            {
                name: '技术分析模型',
                signal: '中性 (Neutral)',
                score: 55,
                weight: 0.2,
                description: '日线MACD金叉但量能不足，此处需震荡消化套牢盘。',
                timeframe: '日线',
                details: {
                    macd: { dif: '12.5', dea: '10.8', bar: '1.7', conclusion: 'DIF上穿DEA形成金叉，红柱放大，短期（一周内）偏多' },
                    kdj: { k: '45.2', d: '42.8', j: '50.1', conclusion: 'KDJ三线向上发散，但仍处中位区域，观望为主' },
                    rsi: { rsi6: '58.5', rsi12: '60.2', rsi24: '63.5', conclusion: 'RSI多头排列，但未超买，中期（1-2月）可持续关注' }
                }
            },
            {
                name: '基本面相对估值',
                signal: '看多 (Bullish)',
                score: 92,
                weight: 0.3,
                description: '当前TTM PE分位数位于近10年5%分位，极具性价比。'
            },
            {
                name: '舆情分析',
                signal: '看空 (Bearish)',
                score: 45,
                weight: 0.1,
                description: '近期负面新闻较多，市场情绪偏谨慎。'
            }
        ],
        summary: '当前处于典型的磨底阶段，宏观流动性边际改善，估值处于历史低位。建议分批建仓，重点关注北向资金回流。',
        recommendation: '建议：分批建仓，重点关注北向资金回流',
        timestamp: new Date().toISOString()
    }
};

// BlackRock Fund Mock Data
export const mockBlackRockFund = {
    symbol: 'BGF-GSA',
    type: 'fund',
    market: 'US',
    name: '贝莱德全球基金',
    fullName: '贝莱德全球基金-系统分析环球股票高息基金（A6类-美元-每月派息-现金）',
    currency: 'USD',
    price: 9.28,
    change: 0.03,
    pct_change: 0.32,
    navDate: '2025-11-30',  // 净值日期
    assetSize: '125.6',     // 基金规模(亿)

    // 基金费用
    fees: {
        subscriptionFee: 3.00,  // 首次认购费
        managementFee: 1.50,    // 每年管理费(最高)
        minimumInvestment: 100, // 最低投资金额
        expenseRatio: 1.807     // 开支比率
    },

    // 股息资料
    dividendInfo: {
        asOfDate: '2025年11月30日',
        frequency: '每月',
        yieldRate: 7.33,  // %
        lastDividend: 0.06200,  // USD
        lastExDividendDate: '2025年11月28日',
        note: '股份收益率以过去12个月所派出的股息除以过去月结基金单位价格计算，以两个小数位显示。基金公司未必保证派发股息。'
    },

    // 风险回报概况
    performance: {
        asOfDate: '2025年11月30日',
        period: '3年',
        annualizedReturn: 13.89,  // %
        volatility: 12.5,  // %
        sharpeRatio: 0.95,
        maxDrawdown: -15.2  // %
    },

    // 基准指数对比
    benchmark: {
        name: 'MSCI World Index',
        nameZh: 'MSCI 世界指数',
        annualizedReturn: 11.20,  // %
        volatility: 14.2,  // %
        sharpeRatio: 0.72,
        maxDrawdown: -18.5  // %
    },

    // 额外基准指数（美元基金）
    additionalBenchmarks: [
        {
            name: 'S&P 500',
            nameZh: '标普500指数',
            annualizedReturn: 12.50,  // %
            volatility: 15.8,  // %
            sharpeRatio: 0.78,
            maxDrawdown: -19.2  // %
        },
        {
            name: 'Nasdaq 100',
            nameZh: '纳斯达克100指数',
            annualizedReturn: 15.30,  // %
            volatility: 18.5,  // %
            sharpeRatio: 0.82,
            maxDrawdown: -22.8  // %
        }
    ]
};

// Helper function to get mock data
export const getMockData = (symbol) => {
    if (symbol === '600519') {
        return mockMoutaiData;
    }
    if (symbol === 'BGF-GSA') {
        return mockBlackRockFund;
    }
    // Can add more symbols here
    return null;
};

// Check if we should use offline mode
export const isOfflineMode = () => {
    // Check if running on mobile (Capacitor)
    return window.Capacitor !== undefined;
};
