import React, { useState, useEffect } from 'react';
import ImageUploadArea from './ImageUploadArea';
import CollapsibleSection from './CollapsibleSection';
import StarRating from './StarRating';
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

            {/* SECTION 7: 价值评估报告 */}
            <div id="analysis-result" className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.8rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--text-secondary)', fontWeight: '600' }}>
                        💎 价值评估报告
                    </h3>
                    <div
                        style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                        onClick={() => alert("功能开发中:查看历史评估记录")}
                    >
                        <span>📑</span> 历史记录
                    </div>
                </div>

                {analysisResult ? (
                    <>
                        {/* 综合评分区 */}
                        <div style={{
                            marginBottom: '1.5rem',
                            background: 'linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(139,92,246,0.1) 100%)',
                            padding: '1.5rem',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid rgba(59,130,246,0.2)',
                            textAlign: 'center'
                        }}>
                            <div style={{ marginBottom: '1rem' }}>
                                <StarRating score={analysisResult.weighted_score || analysisResult.total_score || 0} />
                            </div>
                            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#fff', marginBottom: '0.5rem' }}>
                                {analysisResult.weighted_score || analysisResult.total_score || '--'} <span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>/ 100</span>
                            </div>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                                综合评分
                            </div>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: '1fr 1fr',
                                gap: '0.8rem',
                                marginTop: '1rem',
                                paddingTop: '1rem',
                                borderTop: '1px solid rgba(255,255,255,0.1)'
                            }}>
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>适合投资者</div>
                                    <div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '500' }}>长期价值投资者</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>建议持有周期</div>
                                    <div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '500' }}>3年以上</div>
                                </div>
                            </div>
                        </div>

                        {/* 价值分析 */}
                        <CollapsibleSection title="价值分析" icon="💎" defaultExpanded={true}>
                            <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                    估值水平: <span style={{ color: '#f59e0b', fontWeight: '600' }}>合理偏高 ⚠️</span>
                                </div>
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: '1fr 1fr',
                                    gap: '0.8rem',
                                    background: 'rgba(255,255,255,0.03)',
                                    padding: '1rem',
                                    borderRadius: 'var(--radius-sm)'
                                }}>
                                    <div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>费用率</div>
                                        <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>1.5%</div>
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>行业均值: 1.8%</div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>夏普比率</div>
                                        <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>1.2</div>
                                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>风险调整后收益</div>
                                    </div>
                                </div>
                                <div style={{
                                    marginTop: '0.8rem',
                                    padding: '0.8rem',
                                    background: 'rgba(59,130,246,0.1)',
                                    borderRadius: 'var(--radius-sm)',
                                    borderLeft: '3px solid #3b82f6'
                                }}>
                                    <div style={{ fontSize: '0.85rem', color: '#e4e4e7', lineHeight: '1.5' }}>
                                        该基金费用率低于行业平均水平,长期持有成本优势明显。风险调整后收益表现良好,适合稳健型投资者。
                                    </div>
                                </div>
                            </div>
                        </CollapsibleSection>

                        {/* 机会洞察 */}
                        <CollapsibleSection title="机会洞察" icon="⚡" defaultExpanded={true}>
                            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                发现 <span style={{ color: '#10b981', fontWeight: 'bold' }}>3</span> 个有利因素:
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '0.5rem',
                                    padding: '0.8rem',
                                    background: 'rgba(16,185,129,0.05)',
                                    borderRadius: 'var(--radius-sm)',
                                    borderLeft: '3px solid #10b981'
                                }}>
                                    <span style={{ fontSize: '1.2rem' }}>✓</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '500', marginBottom: '0.2rem' }}>
                                            分散化投资组合
                                        </div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                            持仓分散,单一股票占比不超过5%,有效降低个股风险
                                        </div>
                                    </div>
                                </div>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '0.5rem',
                                    padding: '0.8rem',
                                    background: 'rgba(16,185,129,0.05)',
                                    borderRadius: 'var(--radius-sm)',
                                    borderLeft: '3px solid #10b981'
                                }}>
                                    <span style={{ fontSize: '1.2rem' }}>✓</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '500', marginBottom: '0.2rem' }}>
                                            稳定分红记录
                                        </div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                            过去5年连续分红,年化股息率约2.5%
                                        </div>
                                    </div>
                                </div>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '0.5rem',
                                    padding: '0.8rem',
                                    background: 'rgba(16,185,129,0.05)',
                                    borderRadius: 'var(--radius-sm)',
                                    borderLeft: '3px solid #10b981'
                                }}>
                                    <span style={{ fontSize: '1.2rem' }}>✓</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '500', marginBottom: '0.2rem' }}>
                                            行业复苏趋势
                                        </div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                            所投资行业处于复苏初期,未来增长空间较大
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </CollapsibleSection>

                        {/* 需要关注的风险点 */}
                        <CollapsibleSection title="需要关注的风险点" icon="⚠️" defaultExpanded={true}>
                            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                识别到 <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>3</span> 个风险点:
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                                <div style={{
                                    padding: '1rem',
                                    background: 'rgba(245,158,11,0.05)',
                                    borderRadius: 'var(--radius-sm)',
                                    borderLeft: '3px solid #f59e0b'
                                }}>
                                    <div style={{ fontSize: '0.95rem', color: '#fff', fontWeight: '600', marginBottom: '0.5rem' }}>
                                        估值处于历史高位
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>影响程度:</span>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            padding: '2px 8px',
                                            borderRadius: '12px',
                                            background: 'rgba(245,158,11,0.2)',
                                            color: '#f59e0b'
                                        }}>中等</span>
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '0.5rem' }}>
                                        当前估值水平较历史均值偏高约15%,短期回调风险存在
                                    </div>
                                    <div style={{
                                        fontSize: '0.8rem',
                                        color: '#10b981',
                                        padding: '0.5rem',
                                        background: 'rgba(16,185,129,0.1)',
                                        borderRadius: 'var(--radius-sm)',
                                        marginTop: '0.5rem'
                                    }}>
                                        💡 建议: 分批建仓,避免一次性重仓
                                    </div>
                                </div>

                                <div style={{
                                    padding: '1rem',
                                    background: 'rgba(245,158,11,0.05)',
                                    borderRadius: 'var(--radius-sm)',
                                    borderLeft: '3px solid #f59e0b'
                                }}>
                                    <div style={{ fontSize: '0.95rem', color: '#fff', fontWeight: '600', marginBottom: '0.5rem' }}>
                                        短期波动性较大
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>影响程度:</span>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            padding: '2px 8px',
                                            borderRadius: '12px',
                                            background: 'rgba(34,197,94,0.2)',
                                            color: '#22c55e'
                                        }}>低</span>
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '0.5rem' }}>
                                        年化波动率约25%,短期价格波动可能较大
                                    </div>
                                    <div style={{
                                        fontSize: '0.8rem',
                                        color: '#10b981',
                                        padding: '0.5rem',
                                        background: 'rgba(16,185,129,0.1)',
                                        borderRadius: 'var(--radius-sm)',
                                        marginTop: '0.5rem'
                                    }}>
                                        💡 建议: 长期持有,不要被短期波动影响
                                    </div>
                                </div>

                                <div style={{
                                    padding: '1rem',
                                    background: 'rgba(245,158,11,0.05)',
                                    borderRadius: 'var(--radius-sm)',
                                    borderLeft: '3px solid #f59e0b'
                                }}>
                                    <div style={{ fontSize: '0.95rem', color: '#fff', fontWeight: '600', marginBottom: '0.5rem' }}>
                                        宏观经济放缓风险
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>影响程度:</span>
                                        <span style={{
                                            fontSize: '0.75rem',
                                            padding: '2px 8px',
                                            borderRadius: '12px',
                                            background: 'rgba(245,158,11,0.2)',
                                            color: '#f59e0b'
                                        }}>中等</span>
                                    </div>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '0.5rem' }}>
                                        全球经济增速放缓可能影响企业盈利
                                    </div>
                                    <div style={{
                                        fontSize: '0.8rem',
                                        color: '#10b981',
                                        padding: '0.5rem',
                                        background: 'rgba(16,185,129,0.1)',
                                        borderRadius: 'var(--radius-sm)',
                                        marginTop: '0.5rem'
                                    }}>
                                        💡 建议: 关注宏观经济政策变化
                                    </div>
                                </div>
                            </div>
                        </CollapsibleSection>

                        {/* 周期与趋势 */}
                        <CollapsibleSection title="周期与趋势" icon="📈" defaultExpanded={false}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.8rem', marginBottom: '1rem' }}>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.8rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>个股周期</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#fff' }}>{analysisResult.stockCycle || '震荡'}</div>
                                </div>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.8rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>板块周期</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#fff' }}>{analysisResult.sectorCycle || '复苏'}</div>
                                </div>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.8rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>宏观周期</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#fff' }}>{analysisResult.macroCycle || '衰退'}</div>
                                </div>
                            </div>
                            <div style={{
                                padding: '1rem',
                                background: 'rgba(139,92,246,0.1)',
                                borderRadius: 'var(--radius-sm)',
                                borderLeft: '3px solid #8b5cf6'
                            }}>
                                <div style={{ fontSize: '0.85rem', color: '#e4e4e7', lineHeight: '1.5' }}>
                                    当前行业处于复苏初期,技术面呈现筑底形态,资金流向显示小幅流入。建议关注行业政策变化和龙头企业动态。
                                </div>
                            </div>
                        </CollapsibleSection>

                        {/* 评估总结 */}
                        <div style={{
                            marginTop: '1.5rem',
                            padding: '1.5rem',
                            background: 'linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(59,130,246,0.1) 100%)',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid rgba(139,92,246,0.2)'
                        }}>
                            <div style={{ fontSize: '1rem', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <span>💡</span> 评估总结
                            </div>
                            <div style={{ fontSize: '0.95rem', color: '#e4e4e7', lineHeight: '1.7', marginBottom: '1rem' }}>
                                {analysisResult.summary || '该标的具有良好的长期投资价值,但当前估值偏高,建议等待更好时机。适合风险承受能力中等及以上的长期投资者。'}
                            </div>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: '1fr 1fr',
                                gap: '0.8rem',
                                paddingTop: '1rem',
                                borderTop: '1px solid rgba(255,255,255,0.1)'
                            }}>
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>建议仓位比例</div>
                                    <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>≤ 15%</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>建议持有周期</div>
                                    <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>3年以上</div>
                                </div>
                            </div>
                        </div>

                        {/* 免责声明 */}
                        <div style={{
                            marginTop: '1.5rem',
                            padding: '1rem',
                            background: 'rgba(245,158,11,0.05)',
                            borderRadius: 'var(--radius-sm)',
                            border: '1px solid rgba(245,158,11,0.2)',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                                ⚠️ 本评估仅供参考,不构成投资建议。投资决策由用户自主做出,风险自负。
                            </div>
                        </div>
                    </>
                ) : (
                    <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.3 }}>📊</div>
                        <div style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>暂无评估记录</div>
                        <div style={{ fontSize: '0.85rem' }}>请点击底部按钮开始价值评估</div>
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
