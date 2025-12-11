import React, { useState, useEffect } from 'react';
import ImageUploadArea from './ImageUploadArea';
import { analyzeAsset } from '../utils/mockAI';
import { getMockData } from '../utils/mockData';
import { getColorConvention, getChangeColor, getPerformanceColor } from '../utils/colorUtils';

const FundDetailView = ({ asset, onBack }) => {
    const [fundData, setFundData] = useState(null);
    const [colorConvention, setColorConvention] = useState('chinese');
    const [analyzing, setAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [enabledModels, setEnabledModels] = useState({
        dagnino: true,           // 乔治·达格尼诺周期模型
        styleDrift: true,        // 基金风格漂移分析
        feeEfficiency: true,     // 费用效率分析
        concentration: true,     // 持仓集中度分析
        trackingError: true,     // 跟踪误差分析
        flowAnalysis: true       // 资金流向分析
    });

    useEffect(() => {
        // Load color convention
        const convention = getColorConvention();
        setColorConvention(convention);

        if (asset && asset.symbol) {
            // Load mock fund data
            const mockData = getMockData(asset.symbol);
            if (mockData) {
                setFundData(mockData);
            }
        }
    }, [asset]);

    const handleAnalyze = async () => {
        setAnalyzing(true);
        try {
            // Call real AI analysis
            const result = await analyzeAsset(asset.symbol);

            // Inject real context if available
            if (asset.name) result.name = asset.name;
            result.symbol = asset.symbol;
            result.price = asset.price; // Use latest price

            // Save to backend
            try {
                await fetch('http://localhost:8000/api/save-analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        symbol: asset.symbol,
                        result: result,
                        screenshot_path: null
                    })
                });
            } catch (saveErr) {
                console.error("Failed to save analysis", saveErr);
            }

            setAnalysisResult(result);

            // Scroll to result
            setTimeout(() => {
                document.getElementById('analysis-result')?.scrollIntoView({ behavior: 'smooth' });
            }, 100);

        } catch (e) {
            console.error("Analysis failed", e);
            alert("分析服务暂时不可用");
        } finally {
            setAnalyzing(false);
        }
    };

    console.log('FundDetailView rendered, asset:', asset);
    console.log('Fund Data:', fundData);

    if (!asset) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#fff' }}>
                <h2>错误：未选择基金</h2>
                <button
                    onClick={onBack}
                    style={{
                        marginTop: '1rem',
                        padding: '0.5rem 1rem',
                        background: 'var(--accent-primary)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    返回
                </button>
            </div>
        );
    }

    const data = fundData || asset;

    return (
        <div style={{ padding: '1rem', paddingTop: 'max(1rem, env(safe-area-inset-top))', paddingBottom: '6rem' }}>
            {/* Header / Nav */}
            <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                <button
                    onClick={onBack}
                    style={{
                        background: 'rgba(255,255,255,0.1)',
                        border: 'none',
                        color: 'var(--text-secondary)',
                        padding: '0.5rem',
                        borderRadius: '50%',
                        width: '36px',
                        height: '36px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer'
                    }}
                >
                    &larr;
                </button>
                <div style={{ flex: 1 }}>
                    <h1 style={{ margin: 0, fontSize: '1.2rem', lineHeight: '1.4' }}>
                        {data.fullName || data.name || data.symbol}
                    </h1>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {data.symbol} • {data.market} • 基金
                    </span>
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

                {/* SECTION 1: Basic Information */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                        基础行情
                    </h3>

                    {/* Price and Volume/Turnover Layout */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        {/* Left: Price Section */}
                        <div>
                            <div style={{ fontSize: '2.2rem', fontWeight: 'bold', color: getChangeColor(data.pct_change, colorConvention), lineHeight: 1, marginBottom: '0.5rem' }}>
                                {data.currency} {data.price ? data.price.toFixed(2) : '--.--'}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                                <span style={{ fontSize: '1rem', color: getChangeColor(data.pct_change, colorConvention), fontWeight: '600' }}>
                                    {data.pct_change > 0 ? '+' : ''}{data.pct_change ? data.pct_change.toFixed(2) : '0.00'}%
                                </span>
                                <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                                    {data.change ? `${data.change > 0 ? '+' : ''}${data.change.toFixed(2)}` : ''}
                                </span>
                            </div>
                        </div>

                        {/* Right: NAV Date & Asset Size Stacked */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', alignItems: 'flex-end' }}>
                            {/* NAV Date */}
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>净值日期</div>
                                <div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '500' }}>
                                    {data.navDate || '2025-11-30'}
                                </div>
                            </div>

                            {/* Asset Size */}
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>基金规模</div>
                                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '500' }}>
                                    {data.assetSize || '--'}亿
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* SECTION 2: Dividend Information */}
                {data.dividendInfo && (
                    <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                        <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                            股息资料
                        </h3>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                            截至 {data.dividendInfo.asOfDate}
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem 0.5rem', marginBottom: '1rem' }}>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>预期派股息次数</div>
                                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>{data.dividendInfo.frequency}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>股息收益率</div>
                                <div style={{ fontSize: '1rem', color: 'var(--accent-primary)', fontWeight: 'bold' }}>{data.dividendInfo.yieldRate}%</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>上次派息(单位)</div>
                                <div style={{ fontSize: '1rem', color: '#fff' }}>{data.currency} {data.dividendInfo.lastDividend.toFixed(5)}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>上次除息日期</div>
                                <div style={{ fontSize: '1rem', color: '#fff' }}>{data.dividendInfo.lastExDividendDate}</div>
                            </div>
                        </div>

                        {data.dividendInfo.note && (
                            <div style={{
                                fontSize: '0.7rem',
                                color: 'var(--text-muted)',
                                lineHeight: '1.4',
                                padding: '0.8rem',
                                background: 'rgba(255,255,255,0.02)',
                                borderRadius: 'var(--radius-sm)',
                                borderLeft: '2px solid rgba(255,255,255,0.1)'
                            }}>
                                {data.dividendInfo.note}
                            </div>
                        )}
                    </div>
                )}

                {/* SECTION 2.5: Fund Fees */}
                {data.fees && (
                    <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                        <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                            基金费用
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem 0.5rem' }}>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>首次认购费</div>
                                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>{data.fees.subscriptionFee}%</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>每年管理费(最高)</div>
                                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>{data.fees.managementFee}%</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>最低投资金额</div>
                                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>{data.currency} {data.fees.minimumInvestment}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>开支比率</div>
                                <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>{data.fees.expenseRatio}%</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* SECTION 3: Performance / Risk-Return Profile */}
                {data.performance && (
                    <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                        <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                            风险回报概况
                        </h3>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                            截至 {data.performance.asOfDate}
                        </div>

                        {/* Period Selector */}
                        <div style={{ marginBottom: '1rem' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>时间周期</div>
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                {['1年', '3年', '5年', '10年', '成立至今'].map(period => (
                                    <div
                                        key={period}
                                        style={{
                                            padding: '0.4rem 0.8rem',
                                            borderRadius: '4px',
                                            fontSize: '0.8rem',
                                            cursor: 'pointer',
                                            background: period === data.performance.period ? 'var(--accent-primary)' : 'rgba(255,255,255,0.05)',
                                            color: period === data.performance.period ? '#fff' : 'var(--text-secondary)',
                                            border: `1px solid ${period === data.performance.period ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)'}`,
                                            transition: 'all 0.2s'
                                        }}
                                        onClick={() => alert(`切换到${period}周期（功能开发中）`)}
                                    >
                                        {period}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Annualized Return */}
                        <div style={{
                            background: 'rgba(255,255,255,0.03)',
                            padding: '1.5rem',
                            borderRadius: 'var(--radius-sm)',
                            textAlign: 'center',
                            border: '1px solid rgba(255,255,255,0.05)'
                        }}>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>年度化回报率</div>
                            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>
                                {data.performance.annualizedReturn}%
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
                                {data.performance.period}
                            </div>
                        </div>
                    </div>
                )}

                {/* SECTION 3.5: Benchmark Comparison */}
                {data.benchmark && data.performance && (
                    <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                        <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                            与基准指数对比
                        </h3>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                            基准：{data.benchmark.nameZh} ({data.benchmark.name})
                        </div>

                        {/* Comparison Table */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                        <th style={{ textAlign: 'left', padding: '0.5rem 0', color: 'var(--text-muted)', fontWeight: '500' }}>指标</th>
                                        <th style={{ textAlign: 'right', padding: '0.5rem 0', color: 'var(--text-muted)', fontWeight: '500' }}>基金</th>
                                        <th style={{ textAlign: 'right', padding: '0.5rem 0', color: 'var(--text-muted)', fontWeight: '500' }}>基准</th>
                                        <th style={{ textAlign: 'right', padding: '0.5rem 0', color: 'var(--text-muted)', fontWeight: '500' }}>差异</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {/* Annualized Return */}
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>年度化回报率</td>
                                        <td style={{ padding: '0.8rem 0', textAlign: 'right', color: 'var(--accent-primary)', fontWeight: '600' }}>
                                            {data.performance.annualizedReturn}%
                                        </td>
                                        <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                            {data.benchmark.annualizedReturn}%
                                        </td>
                                        <td style={{
                                            padding: '0.8rem 0',
                                            textAlign: 'right',
                                            color: (data.performance.annualizedReturn - data.benchmark.annualizedReturn) > 0 ? '#ef4444' : '#10b981',
                                            fontWeight: '600'
                                        }}>
                                            {(data.performance.annualizedReturn - data.benchmark.annualizedReturn) > 0 ? '+' : ''}
                                            {(data.performance.annualizedReturn - data.benchmark.annualizedReturn).toFixed(2)}%
                                        </td>
                                    </tr>

                                    {/* Volatility */}
                                    {data.performance.volatility && data.benchmark.volatility && (
                                        <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>波动率</td>
                                            <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                                {data.performance.volatility}%
                                            </td>
                                            <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                                {data.benchmark.volatility}%
                                            </td>
                                            <td style={{
                                                padding: '0.8rem 0',
                                                textAlign: 'right',
                                                color: (data.performance.volatility - data.benchmark.volatility) < 0 ? '#ef4444' : '#10b981',
                                                fontWeight: '600'
                                            }}>
                                                {(data.performance.volatility - data.benchmark.volatility) > 0 ? '+' : ''}
                                                {(data.performance.volatility - data.benchmark.volatility).toFixed(1)}%
                                            </td>
                                        </tr>
                                    )}

                                    {/* Sharpe Ratio */}
                                    {data.performance.sharpeRatio && data.benchmark.sharpeRatio && (
                                        <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>夏普比率</td>
                                            <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                                {data.performance.sharpeRatio.toFixed(2)}
                                            </td>
                                            <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                                {data.benchmark.sharpeRatio.toFixed(2)}
                                            </td>
                                            <td style={{
                                                padding: '0.8rem 0',
                                                textAlign: 'right',
                                                color: (data.performance.sharpeRatio - data.benchmark.sharpeRatio) > 0 ? '#ef4444' : '#10b981',
                                                fontWeight: '600'
                                            }}>
                                                {(data.performance.sharpeRatio - data.benchmark.sharpeRatio) > 0 ? '+' : ''}
                                                {(data.performance.sharpeRatio - data.benchmark.sharpeRatio).toFixed(2)}
                                            </td>
                                        </tr>
                                    )}

                                    {/* Max Drawdown */}
                                    {data.performance.maxDrawdown && data.benchmark.maxDrawdown && (
                                        <tr>
                                            <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>最大回撤</td>
                                            <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                                {data.performance.maxDrawdown}%
                                            </td>
                                            <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                                {data.benchmark.maxDrawdown}%
                                            </td>
                                            <td style={{
                                                padding: '0.8rem 0',
                                                textAlign: 'right',
                                                color: (data.performance.maxDrawdown - data.benchmark.maxDrawdown) > 0 ? '#ef4444' : '#10b981',
                                                fontWeight: '600'
                                            }}>
                                                {(data.performance.maxDrawdown - data.benchmark.maxDrawdown) > 0 ? '+' : ''}
                                                {(data.performance.maxDrawdown - data.benchmark.maxDrawdown).toFixed(1)}%
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Performance Chart - Dual Line */}
                        <div style={{ paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.8rem' }}>
                                累计收益对比（近3年）
                            </div>
                            <div style={{ height: '120px', width: '100%', position: 'relative' }}>
                                <svg width="100%" height="100%" viewBox="0 0 300 120" preserveAspectRatio="none">
                                    <defs>
                                        <linearGradient id="fundGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.2" />
                                            <stop offset="100%" stopColor="var(--accent-primary)" stopOpacity="0" />
                                        </linearGradient>
                                    </defs>

                                    {/* Benchmark Line (Gray) - Lower performance */}
                                    <path
                                        d="M0,80 L30,75 L60,70 L90,65 L120,60 L150,58 L180,55 L210,52 L240,50 L270,48 L300,45"
                                        fill="none"
                                        stroke="#71717a"
                                        strokeWidth="2"
                                        strokeDasharray="4,2"
                                    />

                                    {/* Fund Line (Primary Color) - Higher performance */}
                                    <path
                                        d="M0,75 L30,68 L60,62 L90,55 L120,50 L150,45 L180,42 L210,38 L240,35 L270,32 L300,30"
                                        fill="none"
                                        stroke="var(--accent-primary)"
                                        strokeWidth="2.5"
                                    />
                                    <path
                                        d="M0,75 L30,68 L60,62 L90,55 L120,50 L150,45 L180,42 L210,38 L240,35 L270,32 L300,30 V120 H0 Z"
                                        fill="url(#fundGradient)"
                                        stroke="none"
                                    />
                                </svg>

                                {/* Legend */}
                                <div style={{ position: 'absolute', top: '5px', right: '5px', display: 'flex', gap: '1rem', fontSize: '0.7rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                        <div style={{ width: '16px', height: '2px', background: 'var(--accent-primary)' }}></div>
                                        <span style={{ color: 'var(--text-muted)' }}>基金</span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                        <div style={{ width: '16px', height: '2px', background: '#71717a', borderTop: '2px dashed #71717a' }}></div>
                                        <span style={{ color: 'var(--text-muted)' }}>基准</span>
                                    </div>
                                </div>

                                {/* Y-axis labels */}
                                <div style={{ position: 'absolute', top: '5px', left: '2px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>+45%</div>
                                <div style={{ position: 'absolute', bottom: '5px', left: '2px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>0%</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* SECTION 3.6: Additional Benchmarks (for USD funds) */}
                {data.additionalBenchmarks && data.additionalBenchmarks.length > 0 && data.performance && (
                    <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                        <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                            其他主要指数对比
                        </h3>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                            美元基金常用基准：{data.additionalBenchmarks.map(b => b.nameZh).join('、')}
                        </div>

                        {/* Comparison Table */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                        <th style={{ textAlign: 'left', padding: '0.5rem 0', color: 'var(--text-muted)', fontWeight: '500' }}>指标</th>
                                        <th style={{ textAlign: 'right', padding: '0.5rem 0', color: 'var(--text-muted)', fontWeight: '500' }}>基金</th>
                                        {data.additionalBenchmarks.map((benchmark, idx) => (
                                            <th key={idx} style={{ textAlign: 'right', padding: '0.5rem 0', color: 'var(--text-muted)', fontWeight: '500', fontSize: '0.75rem' }}>
                                                {benchmark.name}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {/* Annualized Return */}
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>年度化回报率</td>
                                        <td style={{ padding: '0.8rem 0', textAlign: 'right', color: 'var(--accent-primary)', fontWeight: '600' }}>
                                            {data.performance.annualizedReturn}%
                                        </td>
                                        {data.additionalBenchmarks.map((benchmark, idx) => {
                                            const diff = data.performance.annualizedReturn - benchmark.annualizedReturn;
                                            return (
                                                <td key={idx} style={{ padding: '0.8rem 0', textAlign: 'right' }}>
                                                    <div style={{ color: '#fff' }}>{benchmark.annualizedReturn}%</div>
                                                    <div style={{
                                                        fontSize: '0.75rem',
                                                        color: diff > 0 ? '#ef4444' : '#10b981',
                                                        fontWeight: '600'
                                                    }}>
                                                        ({diff > 0 ? '+' : ''}{diff.toFixed(2)}%)
                                                    </div>
                                                </td>
                                            );
                                        })}
                                    </tr>

                                    {/* Volatility */}
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>波动率</td>
                                        <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                            {data.performance.volatility}%
                                        </td>
                                        {data.additionalBenchmarks.map((benchmark, idx) => {
                                            const diff = data.performance.volatility - benchmark.volatility;
                                            return (
                                                <td key={idx} style={{ padding: '0.8rem 0', textAlign: 'right' }}>
                                                    <div style={{ color: '#fff' }}>{benchmark.volatility}%</div>
                                                    <div style={{
                                                        fontSize: '0.75rem',
                                                        color: diff < 0 ? '#ef4444' : '#10b981',
                                                        fontWeight: '600'
                                                    }}>
                                                        ({diff > 0 ? '+' : ''}{diff.toFixed(1)}%)
                                                    </div>
                                                </td>
                                            );
                                        })}
                                    </tr>

                                    {/* Sharpe Ratio */}
                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>夏普比率</td>
                                        <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                            {data.performance.sharpeRatio.toFixed(2)}
                                        </td>
                                        {data.additionalBenchmarks.map((benchmark, idx) => {
                                            const diff = data.performance.sharpeRatio - benchmark.sharpeRatio;
                                            return (
                                                <td key={idx} style={{ padding: '0.8rem 0', textAlign: 'right' }}>
                                                    <div style={{ color: '#fff' }}>{benchmark.sharpeRatio.toFixed(2)}</div>
                                                    <div style={{
                                                        fontSize: '0.75rem',
                                                        color: diff > 0 ? '#ef4444' : '#10b981',
                                                        fontWeight: '600'
                                                    }}>
                                                        ({diff > 0 ? '+' : ''}{diff.toFixed(2)})
                                                    </div>
                                                </td>
                                            );
                                        })}
                                    </tr>

                                    {/* Max Drawdown */}
                                    <tr>
                                        <td style={{ padding: '0.8rem 0', color: '#e4e4e7' }}>最大回撤</td>
                                        <td style={{ padding: '0.8rem 0', textAlign: 'right', color: '#fff' }}>
                                            {data.performance.maxDrawdown}%
                                        </td>
                                        {data.additionalBenchmarks.map((benchmark, idx) => {
                                            const diff = data.performance.maxDrawdown - benchmark.maxDrawdown;
                                            return (
                                                <td key={idx} style={{ padding: '0.8rem 0', textAlign: 'right' }}>
                                                    <div style={{ color: '#fff' }}>{benchmark.maxDrawdown}%</div>
                                                    <div style={{
                                                        fontSize: '0.75rem',
                                                        color: diff > 0 ? '#ef4444' : '#10b981',
                                                        fontWeight: '600'
                                                    }}>
                                                        ({diff > 0 ? '+' : ''}{diff.toFixed(1)}%)
                                                    </div>
                                                </td>
                                            );
                                        })}
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        {/* Performance Chart - Triple Line */}
                        <div style={{ paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.8rem' }}>
                                累计收益对比（近3年）
                            </div>
                            <div style={{ height: '120px', width: '100%', position: 'relative' }}>
                                <svg width="100%" height="100%" viewBox="0 0 300 120" preserveAspectRatio="none">
                                    <defs>
                                        <linearGradient id="fundGradient2" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.2" />
                                            <stop offset="100%" stopColor="var(--accent-primary)" stopOpacity="0" />
                                        </linearGradient>
                                    </defs>

                                    {/* S&P 500 Line (Orange) - Middle performance */}
                                    <path
                                        d="M0,78 L30,72 L60,68 L90,63 L120,58 L150,55 L180,52 L210,48 L240,45 L270,43 L300,40"
                                        fill="none"
                                        stroke="#f97316"
                                        strokeWidth="2"
                                        strokeDasharray="3,3"
                                    />

                                    {/* Nasdaq 100 Line (Purple) - Highest performance */}
                                    <path
                                        d="M0,70 L30,62 L60,55 L90,48 L120,42 L150,38 L180,35 L210,30 L240,27 L270,24 L300,20"
                                        fill="none"
                                        stroke="#a855f7"
                                        strokeWidth="2"
                                        strokeDasharray="3,3"
                                    />

                                    {/* Fund Line (Primary Color) - Between S&P and Nasdaq */}
                                    <path
                                        d="M0,75 L30,68 L60,62 L90,55 L120,50 L150,45 L180,42 L210,38 L240,35 L270,32 L300,30"
                                        fill="none"
                                        stroke="var(--accent-primary)"
                                        strokeWidth="2.5"
                                    />
                                    <path
                                        d="M0,75 L30,68 L60,62 L90,55 L120,50 L150,45 L180,42 L210,38 L240,35 L270,32 L300,30 V120 H0 Z"
                                        fill="url(#fundGradient2)"
                                        stroke="none"
                                    />
                                </svg>

                                {/* Legend */}
                                <div style={{ position: 'absolute', top: '5px', right: '5px', display: 'flex', gap: '0.8rem', fontSize: '0.65rem', flexWrap: 'wrap' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                        <div style={{ width: '14px', height: '2px', background: 'var(--accent-primary)' }}></div>
                                        <span style={{ color: 'var(--text-muted)' }}>基金</span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                        <div style={{ width: '14px', height: '2px', background: '#f97316', borderTop: '2px dashed #f97316' }}></div>
                                        <span style={{ color: 'var(--text-muted)' }}>S&P 500</span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                        <div style={{ width: '14px', height: '2px', background: '#a855f7', borderTop: '2px dashed #a855f7' }}></div>
                                        <span style={{ color: 'var(--text-muted)' }}>Nasdaq 100</span>
                                    </div>
                                </div>

                                {/* Y-axis labels */}
                                <div style={{ position: 'absolute', top: '5px', left: '2px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>+50%</div>
                                <div style={{ position: 'absolute', bottom: '5px', left: '2px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>0%</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* SECTION 4: Model Selection Toggles */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                        启用分析模型
                    </h3>
                    {[
                        { id: 'dagnino', name: '乔治·达格尼诺周期模型' },
                        { id: 'styleDrift', name: '基金风格漂移分析' },
                        { id: 'feeEfficiency', name: '费用效率分析' },
                        { id: 'concentration', name: '持仓集中度分析' },
                        { id: 'trackingError', name: '跟踪误差分析 (指数基金)' },
                        { id: 'flowAnalysis', name: '资金流向分析' }
                    ].map(model => (
                        <div key={model.id} style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '0.8rem 0',
                            borderBottom: '1px solid rgba(255,255,255,0.03)'
                        }}>
                            <span style={{ fontSize: '0.95rem', color: '#e4e4e7' }}>{model.name}</span>
                            <label className="switch" style={{ position: 'relative', display: 'inline-block', width: '40px', height: '24px' }}>
                                <input
                                    type="checkbox"
                                    checked={enabledModels[model.id]}
                                    style={{ opacity: 0, width: 0, height: 0 }}
                                    onChange={(e) => {
                                        setEnabledModels({
                                            ...enabledModels,
                                            [model.id]: e.target.checked
                                        });
                                    }}
                                />
                                <div
                                    className="slider"
                                    style={{
                                        position: 'absolute',
                                        cursor: 'pointer',
                                        top: 0, left: 0, right: 0, bottom: 0,
                                        backgroundColor: enabledModels[model.id] ? 'var(--accent-primary)' : '#52525b',
                                        transition: '.4s',
                                        borderRadius: '34px'
                                    }}
                                    onClick={(e) => {
                                        e.preventDefault();
                                        setEnabledModels({
                                            ...enabledModels,
                                            [model.id]: !enabledModels[model.id]
                                        });
                                    }}
                                >
                                    <div
                                        className="dot"
                                        style={{
                                            position: 'absolute',
                                            content: '""',
                                            height: '16px',
                                            width: '16px',
                                            left: '4px',
                                            bottom: '4px',
                                            backgroundColor: 'white',
                                            transition: '.4s',
                                            borderRadius: '50%',
                                            transform: enabledModels[model.id] ? 'translateX(16px)' : 'translateX(0px)'
                                        }}
                                    />
                                </div>
                            </label>
                        </div>
                    ))}
                </div>

                {/* SECTION 5: Intelligence Completion */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                        情报补全
                    </h3>
                    <ImageUploadArea />
                </div>

                {/* SECTION 6: Full Name */}
                {data.fullName && (
                    <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                        <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                            完整名称
                        </h3>
                        <div style={{ fontSize: '0.9rem', color: '#e4e4e7', lineHeight: '1.6' }}>
                            {data.fullName}
                        </div>
                    </div>
                )}
            </div>

            {/* SECTION 7: Analysis Results */}
            <div id="analysis-result" className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)' }}>
                        上次分析结果
                    </h3>
                    <div
                        style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                        onClick={() => alert("功能开发中:查看历史分析记录")}
                    >
                        <span>📑</span> 历史记录
                    </div>
                </div>

                {analysisResult ? (
                    <>
                        {/* Cycles */}
                        <div style={{ marginBottom: '1.2rem', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', textAlign: 'center' }}>
                            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem', borderRadius: 'var(--radius-sm)' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>个股周期</div>
                                <div style={{ fontWeight: 'bold' }}>{analysisResult.stockCycle || '震荡'}</div>
                            </div>
                            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem', borderRadius: 'var(--radius-sm)' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>板块周期</div>
                                <div style={{ fontWeight: 'bold' }}>{analysisResult.sectorCycle || '复苏'}</div>
                            </div>
                            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.6rem', borderRadius: 'var(--radius-sm)' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>宏观周期</div>
                                <div style={{ fontWeight: 'bold' }}>{analysisResult.macroCycle || '衰退'}</div>
                            </div>
                        </div>

                        {/* Scoring Summary & Signal Meter */}
                        <div style={{ marginBottom: '1.2rem', background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                <div style={{ textAlign: 'center', flex: 1, borderRight: '1px solid rgba(255,255,255,0.1)' }}>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>综合得分</div>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff' }}>{analysisResult.total_score || '--'}</div>
                                </div>
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>加权得分</div>
                                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{analysisResult.weighted_score || '--'}</div>
                                </div>
                            </div>

                            {/* Signal Meter -3 to +3 */}
                            <div style={{ marginBottom: '0.5rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                                    <span>看空 (-3)</span>
                                    <span>中性 (0)</span>
                                    <span>看多 (+3)</span>
                                </div>
                                {/* Bar Container */}
                                <div style={{ height: '12px', background: 'rgba(255,255,255,0.1)', borderRadius: '6px', position: 'relative', overflow: 'hidden' }}>
                                    {/* Gradient Background */}
                                    <div style={{
                                        position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                                        background: 'linear-gradient(to right, #10b981 0%, #10b981 30%, #eab308 45%, #eab308 55%, #ef4444 70%, #ef4444 100%)',
                                        opacity: 0.3
                                    }}></div>

                                    {/* Indicator Needle */}
                                    <div style={{
                                        position: 'absolute',
                                        top: 0, bottom: 0, width: '4px',
                                        background: '#fff',
                                        boxShadow: '0 0 4px rgba(0,0,0,0.5)',
                                        left: (() => {
                                            const val = analysisResult.signal_value || 0;
                                            const percent = ((val + 3) / 6) * 100;
                                            return `${Math.max(0, Math.min(100, percent))}%`;
                                        })(),
                                        transform: 'translateX(-50%)',
                                        transition: 'left 0.5s ease-out'
                                    }}></div>
                                </div>
                                <div style={{ textAlign: 'center', marginTop: '6px', fontSize: '0.9rem', fontWeight: 'bold', color: '#fff' }}>
                                    信号强度: <span style={{ color: (analysisResult.signal_value || 0) > 0 ? '#ef4444' : (analysisResult.signal_value || 0) < 0 ? '#10b981' : '#eab308' }}>
                                        {(analysisResult.signal_value || 0) > 0 ? '+' : ''}{analysisResult.signal_value}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Conclusion */}
                        <div style={{ marginBottom: '1.2rem' }}>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 'bold' }}>综合结论</div>
                            <div style={{ lineHeight: '1.6', fontSize: '0.95rem', color: '#e4e4e7', background: 'rgba(255,255,255,0.03)', padding: '0.8rem', borderRadius: 'var(--radius-sm)' }}>
                                {analysisResult.summary}
                            </div>
                        </div>

                        {/* Model Details List */}
                        {analysisResult.model_details && Array.isArray(analysisResult.model_details) ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'bold' }}>各模型评价细则:</div>
                                {analysisResult.model_details.map((model, idx) => {
                                    // Determine color based on signal
                                    let signalColor = 'var(--text-secondary)';
                                    if (model.signal.includes('看多') || model.signal.includes('Bullish')) signalColor = '#ef4444';
                                    if (model.signal.includes('看空') || model.signal.includes('Bearish')) signalColor = '#10b981';
                                    if (model.signal.includes('中性') || model.signal.includes('Neutral')) signalColor = '#eab308';

                                    return (
                                        <div key={idx} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.8rem', borderRadius: 'var(--radius-sm)', borderLeft: `3px solid ${signalColor}` }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                                                <span style={{ fontSize: '0.95rem', fontWeight: '600', color: '#fff' }}>{model.name}</span>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <span style={{
                                                        fontSize: '0.8rem',
                                                        padding: '2px 8px',
                                                        borderRadius: '12px',
                                                        background: `${signalColor}20`,
                                                        color: signalColor,
                                                        border: `1px solid ${signalColor}40`
                                                    }}>
                                                        {model.signal}
                                                    </span>
                                                    <span style={{ fontSize: '0.9rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                                                        {model.score}分
                                                    </span>
                                                </div>
                                            </div>
                                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: model.details ? '0.8rem' : '0' }}>
                                                {model.description}
                                            </div>

                                            {/* Technical Indicator Details (if available) */}
                                            {model.details && (
                                                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '0.8rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
                                                    {/* Time Period Tabs (for Technical Analysis) */}
                                                    {model.timeframe && (
                                                        <div style={{ marginBottom: '0.8rem', paddingBottom: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>周期选择</div>
                                                            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                                                                {['15分钟', '30分钟', '1小时', '4小时', '日线', '周线', '月线'].map(period => (
                                                                    <div
                                                                        key={period}
                                                                        style={{
                                                                            padding: '0.3rem 0.6rem',
                                                                            borderRadius: '4px',
                                                                            fontSize: '0.75rem',
                                                                            cursor: 'pointer',
                                                                            background: period === model.timeframe ? 'var(--accent-primary)' : 'rgba(255,255,255,0.05)',
                                                                            color: period === model.timeframe ? '#fff' : 'var(--text-secondary)',
                                                                            border: `1px solid ${period === model.timeframe ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)'}`,
                                                                            transition: 'all 0.2s'
                                                                        }}
                                                                        onClick={() => alert(`切换到${period}周期（功能开发中）`)}
                                                                    >
                                                                        {period}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {model.details.macd && (
                                                        <div style={{ marginBottom: '0.6rem', paddingBottom: '0.6rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                                            <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold', marginBottom: '0.3rem' }}>MACD 指标</div>
                                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                                                                <div><span style={{ color: 'var(--text-muted)' }}>DIF:</span> <span style={{ color: '#fff' }}>{model.details.macd.dif}</span></div>
                                                                <div><span style={{ color: '#fff' }}>DEA:</span> <span style={{ color: '#fff' }}>{model.details.macd.dea}</span></div>
                                                                <div><span style={{ color: '#fff' }}>柱:</span> <span style={{ color: '#fff' }}>{model.details.macd.bar}</span></div>
                                                            </div>
                                                            <div style={{ color: '#e4e4e7', fontSize: '0.75rem' }}>→ {model.details.macd.conclusion}</div>
                                                        </div>
                                                    )}
                                                    {model.details.kdj && (
                                                        <div style={{ marginBottom: '0.6rem', paddingBottom: '0.6rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                                            <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold', marginBottom: '0.3rem' }}>KDJ 指标</div>
                                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                                                                <div><span style={{ color: 'var(--text-muted)' }}>K:</span> <span style={{ color: '#fff' }}>{model.details.kdj.k}</span></div>
                                                                <div><span style={{ color: 'var(--text-muted)' }}>D:</span> <span style={{ color: '#fff' }}>{model.details.kdj.d}</span></div>
                                                                <div><span style={{ color: 'var(--text-muted)' }}>J:</span> <span style={{ color: '#fff' }}>{model.details.kdj.j}</span></div>
                                                            </div>
                                                            <div style={{ color: '#e4e4e7', fontSize: '0.75rem' }}>→ {model.details.kdj.conclusion}</div>
                                                        </div>
                                                    )}
                                                    {model.details.rsi && (
                                                        <div>
                                                            <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold', marginBottom: '0.3rem' }}>RSI 指标</div>
                                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.4rem' }}>
                                                                <div><span style={{ color: 'var(--text-muted)' }}>RSI6:</span> <span style={{ color: '#fff' }}>{model.details.rsi.rsi6}</span></div>
                                                                <div><span style={{ color: 'var(--text-muted)' }}>RSI12:</span> <span style={{ color: '#fff' }}>{model.details.rsi.rsi12}</span></div>
                                                                <div><span style={{ color: 'var(--text-muted)' }}>RSI24:</span> <span style={{ color: '#fff' }}>{model.details.rsi.rsi24}</span></div>
                                                            </div>
                                                            <div style={{ color: '#e4e4e7', fontSize: '0.75rem' }}>→ {model.details.rsi.conclusion}</div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            /* Fallback for legacy text data */
                            <div style={{ fontSize: '0.85rem', background: 'rgba(0,0,0,0.2)', padding: '0.8rem', borderRadius: 'var(--radius-sm)' }}>
                                <div style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 'bold' }}>各模型分析:</div>
                                <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)' }}>
                                    {analysisResult.details}
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        暂无详细分析记录,请点击底部按钮开始分析。
                    </div>
                )}
            </div>

            {/* Fixed Bottom Button: AI Analysis */}
            <div style={{
                position: 'fixed',
                bottom: 'max(1rem, env(safe-area-inset-bottom))',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '100%',
                maxWidth: '440px',
                padding: '0 1rem',
                zIndex: 100
            }}>
                <button
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    style={{
                        width: '100%',
                        padding: '1rem',
                        background: analyzing ? 'var(--text-muted)' : 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 'var(--radius-lg)',
                        fontSize: '1.1rem',
                        fontWeight: 'bold',
                        cursor: analyzing ? 'not-allowed' : 'pointer',
                        boxShadow: '0 8px 20px rgba(0,0,0,0.3)',
                        transition: 'all 0.3s ease',
                        backdropFilter: 'blur(10px)'
                    }}
                >
                    {analyzing ? 'AI 思考中...' : '✨ 开始 AI 分析'}
                </button>
            </div>
        </div>
    );
};

export default FundDetailView;
