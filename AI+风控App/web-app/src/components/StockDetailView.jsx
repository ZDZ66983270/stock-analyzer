/**
 * VERA Asset Detail View (StockDetailView.jsx)
 * ==============================================================================
 * 
 * 功能说明:
 * 1. **全维度分析**: 单个资产的详情页，集成了行情、历史指标、AI 风险评估和估值报告。
 * 2. **异步状态机**:
 *    - `fetchHistory`: 抓取 OHLCV 和 估值历史序列。
 *    - `fetchLatestAnalysis`: 加载最近一次的人工智能/量化评估记录。
 *    - `handleAnalyze`: 触发新的深度评估任务并持久化至后端。
 * 3. **多维图表系统**: 
 *    - 对接 `ChartSeriesViewer`，支持 走势 (C1)、估值 (C2)、股息 (C3) 等 6 种专业图表模式。
 *    - 支持针对 PE/PB/PS 的二级子菜单切换。
 * 4. **模块化报告**:
 *    - 使用 `CollapsibleSection` 实现可折叠的价值评估、机会洞察、风险警告等专业报告段落。
 * 
 * 作者: Antigravity
 * 日期: 2026-01-23
 */

import React, { useState, useEffect } from 'react';
import ImageUploadArea from './ImageUploadArea';
import CollapsibleSection from './CollapsibleSection';
import StarRating from './StarRating';
import { analyzeAsset } from '../utils/mockAI';
import { getMockData, isOfflineMode } from '../utils/mockData';
import ChartSeriesViewer from './ChartSeriesViewer';

const StockDetailView = ({ asset, onBack }) => {
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    const [analysisResult, setAnalysisResult] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);

    // Chart State
    const [chartType, setChartType] = useState('C1'); // C1, C2, C3, C4, C5, C6
    const [chartSubType, setChartSubType] = useState('PE'); // For C2 (PE/PB/PS)

    // Fetch History on Mount
    useEffect(() => {
        // Enforce top scroll position on entry
        window.scrollTo(0, 0);

        if (asset && asset.symbol) {
            fetchHistory(asset.symbol);
            fetchLatestAnalysis(asset.symbol);
        }
    }, [asset]);

    const fetchHistory = async (symbol) => {
        // Load mock data immediately for offline support
        const mockData = getMockData(symbol);
        if (mockData) {
            setHistory([mockData]);
        }

        if (!asset) return; // Added from instruction, assuming 'asset' is available in scope
        setLoadingHistory(true);
        try {
            const res = await fetch(`/api/market-data/${asset.symbol}`);
            const data = await res.json();

            if (data.status === 'success') {
                setHistory(data.data); // API already returns newest first
            }
        } catch (e) {
            console.error('Failed to fetch history:', e);
            console.log("API unavailable, using mock data");
            // Mock data already set above
        } finally {
            setLoadingHistory(false);
        }
    };

    const fetchLatestAnalysis = async (symbol) => {
        // Load mock analysis immediately
        const mockData = getMockData(symbol);
        if (mockData && mockData.analysisResult) {
            setAnalysisResult(mockData.analysisResult);
        }

        try {
            const res = await fetch(`/api/latest-analysis/${symbol}`);
            const data = await res.json();
            if (data.status === 'success' && data.analysis) {
                setAnalysisResult(data.analysis);
            }
        } catch (e) {
            console.log("Analysis API unavailable, using mock data");
            // Mock data already set above
        }
    };

    const handleAnalyze = async () => {
        setAnalyzing(true);
        try {
            // Future: Call real backend analysis endpoint
            // Current: Use mockAI but inject real data context if needed
            const result = await analyzeAsset(asset.symbol);

            // Inject Real Context if available
            if (asset.name) result.name = asset.name;
            result.symbol = asset.symbol;
            result.price = asset.price; // Use latest price

            // SAVE to Backend
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

    // Helper to get latest data point
    const latestData = history.length > 0 ? history[0] : null;
    const prevData = history.length > 1 ? history[1] : null;

    // Mock data for UI preview when no real data
    // Use asset data directly if available, otherwise use latestData from history
    // Fallback to 0 instead of random numbers
    const mockLatestData = latestData || asset || {
        price: 0,
        prev_close: 0,
        volume: 0,
        pct_change: 0
    };

    // Determine Reference Price for Change Calculation
    // Priority: 1. History[1].close (Yesterday) -> 2. Asset.open (Intraday) -> 3. Current Price (0 Change)
    // Avoid hardcoded 1710.20 which causes -72% error when no history exists.
    const referencePrice = prevData?.close || prevData?.price || asset?.open || asset?.prev_close || mockLatestData.price || 0;

    const mockPrevData = prevData || {
        price: referencePrice
    };


    // Debug logging
    console.log('DetailView rendered, asset:', asset);
    console.log('History:', history);
    console.log('Analysis Result:', analysisResult);

    if (!asset) {
        console.error('No asset provided to DetailView!');
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#fff' }}>
                <h2>错误：未选择资产</h2>
                <p>Asset 数据为空</p>
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

    console.log('Asset is valid, rendering DetailView for:', asset.symbol);

    return (
        <div style={{ paddingLeft: '0', paddingRight: '0', paddingTop: 'max(1rem, env(safe-area-inset-top))', paddingBottom: '6rem' }}>
            {/* Header / Nav */}
            <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                <button
                    onClick={onBack}
                    style={{
                        background: 'rgba(255,255,255,0.1)',
                        border: 'none',
                        color: 'var(--text-secondary)',
                        padding: '0.5rem',
                        borderRadius: '50%', // Circular back button
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
                    <h1 style={{ margin: 0, fontSize: '1.4rem' }}>{asset.name || asset.symbol}</h1>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                        {(asset.symbol || '').replace(/\.OQ$|\.N$|\.QQ$/i, '')} • {asset.market}
                    </span>

                </div>
                {/* <div style={{ textAlign: 'right' }}>
                     Removed large price here, moved to section 1
                </div> */}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

                {/* SECTION 1: Basic Information (Top) */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>基础行情</span>
                        {mockLatestData && mockLatestData.timestamp && (
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 'normal' }}>
                                {(() => {
                                    // Format time
                                    const formatTime = (timeStr) => {
                                        if (!timeStr) return '--';

                                        // Database stores timestamps as strings in their respective market timezone
                                        // e.g., "2025-12-12 16:00:00" for US stocks is already in US Eastern time
                                        // We should display it as-is without timezone conversion

                                        let displayStr = String(timeStr);

                                        // Remove any timezone suffix that might exist
                                        displayStr = displayStr.replace('美东', '').replace('CN', '').replace('HK', '').trim();

                                        // Parse the date string components directly (avoid new Date() timezone conversion)
                                        const match = displayStr.match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/);
                                        if (match) {
                                            const [_, year, month, day, hour, minute] = match;
                                            // Add timezone label based on market
                                            let tzLabel = '';
                                            if (asset.market === 'US') tzLabel = ' 美东';
                                            else if (asset.market === 'HK') tzLabel = ' 香港';
                                            else if (asset.market === 'CN') tzLabel = ' 北京';
                                            return `${month}/${day} ${hour}:${minute}${tzLabel}`;
                                        }

                                        // Fallback: try to extract date parts
                                        const parts = displayStr.split(/[\s-:]+/);
                                        if (parts.length >= 5) {
                                            const [year, month, day, hour, minute] = parts;
                                            let tzLabel = '';
                                            if (asset.market === 'US') tzLabel = ' 美东';
                                            else if (asset.market === 'HK') tzLabel = ' 香港';
                                            else if (asset.market === 'CN') tzLabel = ' 北京';
                                            return `${month}/${day} ${hour}:${minute}${tzLabel}`;
                                        }

                                        return displayStr;
                                    };
                                    try {
                                        return formatTime(mockLatestData.timestamp);
                                    } catch (e) {
                                        return mockLatestData.timestamp;
                                    }
                                })()}
                            </span>
                        )}
                    </h3>

                    {/* Price and Volume/Turnover Layout */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        {/* Left: Price Section */}
                        {(() => {
                            // Use API-provided change and pct_change instead of recalculating
                            const price = mockLatestData ? (mockLatestData.price || mockLatestData.close || 0) : 0;
                            const change = mockLatestData ? (mockLatestData.change || 0) : 0;
                            const pct = mockLatestData ? (mockLatestData.pct_change || 0) : 0;

                            // Use threshold to handle floating point precision issues
                            const threshold = 0.01; // Consider changes < 0.01% as zero
                            const isPositive = Math.abs(pct) >= threshold && pct > 0;
                            const isNegative = Math.abs(pct) >= threshold && pct < 0;
                            const isZero = Math.abs(pct) < threshold;
                            // Zero change should be white, positive red, negative green
                            const color = isZero ? 'var(--text-primary)' : (isPositive ? '#ef4444' : '#10b981');

                            return (
                                <div>
                                    <div style={{ fontSize: '2.2rem', fontWeight: 'bold', color: color, lineHeight: 1, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        {mockLatestData ? price.toFixed(2) : '--.--'}
                                        {isPositive && <span style={{ fontSize: '1.2rem' }}>↑</span>}
                                        {isNegative && <span style={{ fontSize: '1.2rem' }}>↓</span>}
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                                        <span style={{ fontSize: '1rem', color: color, fontWeight: '600' }}>
                                            {mockLatestData ? (
                                                <>
                                                    {isPositive ? '+' : ''}{pct.toFixed(2)}%
                                                </>
                                            ) : '--'}
                                        </span>
                                        <span style={{ fontSize: '0.9rem', color: color }}>
                                            {mockLatestData ? `${isPositive ? '+' : ''}${change.toFixed(2)}` : ''}
                                        </span>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Right: Volume & Volume Ratio (Side by Side) */}
                        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
                            {/* Volume */}
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.2rem' }}>
                                    成交量(股)
                                </div>
                                <div style={{ fontSize: '1rem', fontWeight: '500' }}>
                                    {mockLatestData ? (() => {
                                        let vol = mockLatestData.volume || 0;
                                        // Display raw volume from source (User Request)

                                        if (vol > 100000000) return (vol / 100000000).toFixed(2) + '亿';
                                        if (vol > 10000) return (vol / 10000).toFixed(2) + '万';
                                        return vol.toLocaleString();
                                    })() : '--'}
                                </div>
                            </div>
                            {/* Volume Ratio vs 5-day Average */}
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>量比</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', justifyContent: 'flex-end' }}>
                                    <span style={{ fontSize: '1rem', color: '#10b981', fontWeight: '500' }}>
                                        {/* TODO: Real Vol Ratio calculation */}
                                        1.35
                                    </span>
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>vs 5日</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* SECTION 2: Extended Information (Middle) */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                        扩展信息
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem 0.5rem', marginBottom: '1.5rem' }}>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>股息率 (TTM)</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>
                                {mockLatestData && mockLatestData.dividend_yield != null ? `${Number(mockLatestData.dividend_yield).toFixed(2)}%` : '--'}
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>近一年回购股份占比</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>--%</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>连续派息</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>--年</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>连续回购</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>--年</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>每股收益 (EPS)</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>
                                {mockLatestData && mockLatestData.eps ? mockLatestData.eps : '--'}
                            </div>
                        </div>
                    </div>

                    {/* INTERACTIVE CHART SECTION */}
                    <div style={{ paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)', marginBottom: '1.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '8px' }}>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>核心指标分析</div>

                            {/* Chart Type Tabs */}
                            <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '8px' }}>
                                {[
                                    { id: 'C1', label: '走势' },
                                    { id: 'C2', label: '估值' },
                                    { id: 'C3', label: '股息' },
                                    { id: 'C4', label: '盈利' },
                                    { id: 'C6', label: '量价' }
                                ].map(tab => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setChartType(tab.id)}
                                        style={{
                                            padding: '4px 12px',
                                            fontSize: '0.8rem',
                                            border: 'none',
                                            borderRadius: '6px',
                                            background: chartType === tab.id ? 'var(--accent-primary)' : 'transparent',
                                            color: chartType === tab.id ? '#fff' : 'var(--text-secondary)',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                    >
                                        {tab.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Sub-Tabs for Valuation (C2) */}
                        {chartType === 'C2' && (
                            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', justifyContent: 'flex-end' }}>
                                {['PE', 'PB', 'PS'].map(type => (
                                    <span
                                        key={type}
                                        onClick={() => setChartSubType(type)}
                                        style={{
                                            fontSize: '0.75rem',
                                            padding: '2px 8px',
                                            cursor: 'pointer',
                                            borderRadius: '4px',
                                            background: chartSubType === type ? 'rgba(255,255,255,0.2)' : 'transparent',
                                            color: chartSubType === type ? '#fff' : 'var(--text-muted)'
                                        }}
                                    >
                                        {type}
                                    </span>
                                ))}
                            </div>
                        )}

                        {/* CHART COMPONENT */}
                        <ChartSeriesViewer
                            data={history}
                            seriesType={chartType}
                            subType={chartSubType}
                        />

                        <div style={{ marginTop: '0.5rem', fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                            数据来源: AkShare & 实时行情
                        </div>
                    </div>
                </div>

                {/* SECTION 3: 价值评估报告 */}
                <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
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
                                        <div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '500' }}>1年以上</div>
                                    </div>
                                </div>
                            </div>

                            {/* 价值分析 */}


                            {/* 价值分析 */}
                            <CollapsibleSection title="价值分析" icon="💎" defaultExpanded={true}>
                                <div style={{ marginBottom: '1rem' }}>
                                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                        估值水平: <span style={{ color: '#f59e0b', fontWeight: '600' }}>合理区间 ✓</span>
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
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>市盈率(PE)</div>
                                            <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>15.2</div>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>行业均值: 18.5</div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>市净率(PB)</div>
                                            <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>2.8</div>
                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>历史均值: 3.2</div>
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
                                            当前估值处于合理区间,PE低于行业平均水平,具有一定的安全边际。适合关注基本面的价值投资者。
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
                                                行业龙头地位稳固
                                            </div>
                                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                                市场份额领先,具有较强的定价能力和品牌优势
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
                                                财务状况健康
                                            </div>
                                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                                现金流充沛,负债率低,盈利能力稳定
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
                                                技术面出现积极信号
                                            </div>
                                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                                突破关键阻力位,成交量配合良好
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </CollapsibleSection>

                            {/* 需要关注的风险点 */}
                            <CollapsibleSection title="需要关注的风险点" icon="⚠️" defaultExpanded={true}>
                                <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                    识别到 <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>2</span> 个风险点:
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                                    <div style={{
                                        padding: '1rem',
                                        background: 'rgba(245,158,11,0.05)',
                                        borderRadius: 'var(--radius-sm)',
                                        borderLeft: '3px solid #f59e0b'
                                    }}>
                                        <div style={{ fontSize: '0.95rem', color: '#fff', fontWeight: '600', marginBottom: '0.5rem' }}>
                                            行业竞争加剧
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
                                            新进入者增加,可能对市场份额造成压力
                                        </div>
                                        <div style={{
                                            fontSize: '0.8rem',
                                            color: '#10b981',
                                            padding: '0.5rem',
                                            background: 'rgba(16,185,129,0.1)',
                                            borderRadius: 'var(--radius-sm)',
                                            marginTop: '0.5rem'
                                        }}>
                                            💡 建议: 关注公司应对策略和市场份额变化
                                        </div>
                                    </div>

                                    <div style={{
                                        padding: '1rem',
                                        background: 'rgba(245,158,11,0.05)',
                                        borderRadius: 'var(--radius-sm)',
                                        borderLeft: '3px solid #f59e0b'
                                    }}>
                                        <div style={{ fontSize: '0.95rem', color: '#fff', fontWeight: '600', marginBottom: '0.5rem' }}>
                                            短期技术面调整压力
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
                                            短期可能面临技术性回调,但不影响长期趋势
                                        </div>
                                        <div style={{
                                            fontSize: '0.8rem',
                                            color: '#10b981',
                                            padding: '0.5rem',
                                            background: 'rgba(16,185,129,0.1)',
                                            borderRadius: 'var(--radius-sm)',
                                            marginTop: '0.5rem'
                                        }}>
                                            💡 建议: 可利用回调机会分批建仓
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
                                        个股处于震荡筑底阶段,板块进入复苏初期。宏观经济虽然承压,但政策支持力度加大。建议关注板块轮动机会。
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
                                    {analysisResult.summary || '该标的基本面稳健,估值合理,具有一定的投资价值。短期可能面临技术性调整,但长期趋势向好。适合风险承受能力中等的投资者。'}
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
                                        <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>≤ 20%</div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>建议持有周期</div>
                                        <div style={{ fontSize: '1rem', color: '#fff', fontWeight: '600' }}>1年以上</div>
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

                {/* 3. Upload & Config */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    {/* Analysis Models - MOVED TO TOP */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <div style={{ marginBottom: '0.8rem', fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 'bold' }}>启用分析模型:</div>
                        {[
                            { id: 'dagnino', name: '乔治·达格尼诺周期模型' },
                            { id: 'technical', name: '技术分析模型 (MACD/KDJ)' },
                            { id: 'fundamental', name: '基本面分析模型' },
                            { id: 'sentiment', name: '舆情分析 (Sentiment)' }
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
                                        defaultChecked={true}
                                        style={{ opacity: 0, width: 0, height: 0 }}
                                        onChange={(e) => {
                                            // Future: Update state. For UI demo we just let it toggle visually via CSS if we had it,
                                            // but since we need inline styles or state:
                                            e.target.parentNode.querySelector('.slider').style.backgroundColor = e.target.checked ? 'var(--accent-primary)' : '#ccc';
                                            e.target.parentNode.querySelector('.slider').style.transform = e.target.checked ? 'translateX(0)' : 'translateX(0)'; // visual only
                                            // Actually best to use State. But for quick replacement without full refactor of component state:
                                        }}
                                    />
                                    {/* Simplest Toggle UI using State is better. Let's assume we use state in next step or use a localized component approach here if possible. 
                                        Actually, let's use a cleaner button toggle or just standard checkbox styled.
                                    */}
                                    <div
                                        className="slider"
                                        style={{
                                            position: 'absolute',
                                            cursor: 'pointer',
                                            top: 0, left: 0, right: 0, bottom: 0,
                                            backgroundColor: 'var(--accent-primary)',
                                            transition: '.4s',
                                            borderRadius: '34px'
                                        }}
                                        onClick={(e) => {
                                            const bg = e.currentTarget.style.backgroundColor;
                                            // Simple visual toggle for prototype
                                            e.currentTarget.style.backgroundColor = bg === 'var(--accent-primary)' ? '#52525b' : 'var(--accent-primary)';
                                            const dot = e.currentTarget.querySelector('.dot');
                                            dot.style.transform = bg === 'var(--accent-primary)' ? 'translateX(0px)' : 'translateX(16px)';
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
                                                transform: 'translateX(16px)' // Default checked
                                            }}
                                        />
                                    </div>
                                </label>
                            </div>
                        ))}
                    </div>

                    {/* Intelligence Completion - MOVED TO BOTTOM */}
                    <h4 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)' }}>情报补全</h4>
                    <ImageUploadArea />
                </div>
            </div>

            {/* Sticky Bottom Action Button */}
            <div style={{
                position: 'fixed',
                bottom: '1.5rem',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '100%',
                maxWidth: '440px', // slightly less than 480px container
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
        </div >
    );
};

export default StockDetailView;
