import React, { useState, useEffect } from 'react';
import ImageUploadArea from './ImageUploadArea';
import CollapsibleSection from './CollapsibleSection';
import StarRating from './StarRating';
import { analyzeAsset } from '../utils/mockAI';
import { getMockData, isOfflineMode } from '../utils/mockData';

const StockDetailView = ({ asset, onBack }) => {
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    const [analysisResult, setAnalysisResult] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);

    // Fetch History on Mount
    useEffect(() => {
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

        setLoadingHistory(true);
        try {
            // Try real API
            const res = await fetch(`http://localhost:8000/api/market-data/${symbol}`);
            const data = await res.json();
            if (data.status === 'success') {
                setHistory(data.data.reverse()); // Show newest first
            }
        } catch (e) {
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
            const res = await fetch(`http://localhost:8000/api/latest-analysis/${symbol}`);
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
    const mockLatestData = latestData || asset || {
        price: 1725.50,
        prev_close: 1710.20,
        volume: 32500,
        pct_change: 0.89
    };
    const mockPrevData = prevData || {
        price: mockLatestData.prev_close || 1710.20
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
                        {asset.symbol} • {asset.market}
                    </span>
                </div>
                {/* <div style={{ textAlign: 'right' }}>
                     Removed large price here, moved to section 1
                </div> */}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

                {/* SECTION 1: Basic Information (Top) */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                        基础行情
                    </h3>

                    {/* Price and Volume/Turnover Layout */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        {/* Left: Price Section */}
                        <div>
                            <div style={{ fontSize: '2.2rem', fontWeight: 'bold', color: mockLatestData && mockLatestData.pct_change >= 0 ? '#ef4444' : '#10b981', lineHeight: 1, marginBottom: '0.5rem' }}>
                                {mockLatestData ? (mockLatestData.price || mockLatestData.close || 0).toFixed(2) : '--.--'}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                                <span style={{ fontSize: '1rem', color: mockLatestData && mockLatestData.pct_change >= 0 ? '#ef4444' : '#10b981', fontWeight: '600' }}>
                                    {mockLatestData ? `${mockLatestData.pct_change > 0 ? '+' : ''}${(mockLatestData.pct_change || 0).toFixed(2)}%` : '--'}
                                </span>
                                <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                                    {mockLatestData && mockPrevData ? `${mockLatestData.pct_change > 0 ? '+' : ''}${((mockLatestData.price || mockLatestData.close || 0) - (mockPrevData.price || mockPrevData.close || 0)).toFixed(2)}` : ''}
                                </span>
                            </div>
                        </div>

                        {/* Right: Volume, Turnover & Volume Ratio (Side by Side) */}
                        <div style={{ display: 'flex', gap: '1.2rem', alignItems: 'flex-start' }}>
                            {/* Volume */}
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>成交量</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', justifyContent: 'flex-end' }}>
                                    <span style={{ fontSize: '1rem', color: '#fff', fontWeight: '500' }}>
                                        {mockLatestData ? (mockLatestData.volume / 10000).toFixed(2) : '--'}万
                                    </span>
                                    <span style={{ fontSize: '0.9rem', color: '#10b981' }}>↑</span>
                                </div>
                            </div>

                            {/* Turnover */}
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>成交额</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', justifyContent: 'flex-end' }}>
                                    <span style={{ fontSize: '1rem', color: '#fff', fontWeight: '500' }}>
                                        {mockLatestData ? (mockLatestData.close * mockLatestData.volume / 100000000).toFixed(2) : '--'}亿
                                    </span>
                                    <span style={{ fontSize: '0.9rem', color: '#ef4444' }}>↓</span>
                                </div>
                            </div>

                            {/* Volume Ratio vs 5-day Average */}
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>量比</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', justifyContent: 'flex-end' }}>
                                    <span style={{ fontSize: '1rem', color: '#10b981', fontWeight: '500' }}>
                                        1.35
                                    </span>
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>vs 5日均</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* SECTION 2: Extended Information (Middle) */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <h3 style={{ marginTop: 0, marginBottom: '0.8rem', fontSize: '1rem', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                        扩展信息 (演示数据)
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem 0.5rem', marginBottom: '1.5rem' }}>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>股息率 (TTM)</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>3.45%</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>近一年回购股份占比</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>1.20%</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>连续派息</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>6年</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>连续回购</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>3年</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>每股收益</div>
                            <div style={{ fontSize: '1rem', color: '#fff' }}>1.02</div>
                        </div>
                    </div>

                    {/* PE Ratio Trend Chart */}
                    <div style={{ paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)', marginBottom: '1.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>近一年市盈率走势</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>8.5x</div>
                        </div>

                        {/* Simple SVG Line Chart */}
                        <div style={{ height: '80px', width: '100%', position: 'relative' }}>
                            {/* Mock Data: 12 months */}
                            <svg width="100%" height="100%" viewBox="0 0 300 80" preserveAspectRatio="none">
                                {/* Gradient Defs */}
                                <defs>
                                    <linearGradient id="peGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="var(--accent-primary)" stopOpacity="0.3" />
                                        <stop offset="100%" stopColor="var(--accent-primary)" stopOpacity="0" />
                                    </linearGradient>
                                </defs>

                                {/* Path: Mocking a declining then stabilizing PE trend */}
                                {/* Points: 0,30 -> 30,25 -> 60,35 -> 90,40 -> 120,30 -> 150,20 -> 180,25 -> 210,35 -> 240,45 -> 270,50 -> 300,55 (inverted Y for SVG) */}
                                {/* Let's assume range 5x to 15x. 8.5 is roughly mid-low. */}
                                {/* Values: 12, 11.5, 11, 10.5, 9, 8.2, 8.5, 9.0, 8.8, 8.4, 8.3, 8.5 */}
                                {/* Map to Y (0-80px): Higher Val = Lower Y */}
                                <path
                                    d="M0,20 L27,25 L54,30 L81,35 L109,50 L136,60 L163,55 L190,50 L218,52 L245,56 L272,57 L300,55"
                                    fill="none"
                                    stroke="var(--accent-primary)"
                                    strokeWidth="2"
                                />
                                <path
                                    d="M0,20 L27,25 L54,30 L81,35 L109,50 L136,60 L163,55 L190,50 L218,52 L245,56 L272,57 L300,55 V80 H0 Z"
                                    fill="url(#peGradient)"
                                    stroke="none"
                                />
                            </svg>
                            {/* Labels */}
                            <div style={{ position: 'absolute', top: '20px', left: '0', fontSize: '0.7rem', color: 'var(--text-muted)' }}>Max: 12x</div>
                            <div style={{ position: 'absolute', bottom: '25px', left: '136px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>Min: 8.2x</div>
                        </div>
                    </div>

                    {/* Dividend Yield vs Stock Price Chart (3 Years) */}
                    <div style={{ paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '0.5rem' }}>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>近三年派息率与股价对比</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                <span style={{ color: '#ef4444' }}>━</span> 股价
                                <span style={{ marginLeft: '0.5rem', color: '#10b981' }}>━</span> 派息率
                            </div>
                        </div>

                        {/* Dual Axis Chart */}
                        <div style={{ height: '100px', width: '100%', position: 'relative' }}>
                            <svg width="100%" height="100%" viewBox="0 0 300 100" preserveAspectRatio="none">
                                <defs>
                                    <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#ef4444" stopOpacity="0.2" />
                                        <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
                                    </linearGradient>
                                </defs>

                                {/* Stock Price Line (Red) - Mock trend: rising then falling */}
                                {/* Simulating: 1500 -> 1650 -> 1800 -> 1900 -> 1850 -> 1750 -> 1725 */}
                                <path
                                    d="M0,60 L50,45 L100,30 L150,20 L200,25 L250,40 L300,42"
                                    fill="none"
                                    stroke="#ef4444"
                                    strokeWidth="2"
                                />
                                <path
                                    d="M0,60 L50,45 L100,30 L150,20 L200,25 L250,40 L300,42 V100 H0 Z"
                                    fill="url(#priceGradient)"
                                    stroke="none"
                                />

                                {/* Dividend Yield Line (Green) - Mock trend: stable to rising */}
                                {/* Simulating: 2.8% -> 2.9% -> 3.0% -> 3.2% -> 3.4% -> 3.5% -> 3.45% */}
                                <path
                                    d="M0,72 L50,70 L100,68 L150,64 L200,60 L250,58 L300,59"
                                    fill="none"
                                    stroke="#10b981"
                                    strokeWidth="2.5"
                                    strokeDasharray="4,2"
                                />
                            </svg>

                            {/* Y-axis Labels */}
                            <div style={{ position: 'absolute', top: '5px', left: '2px', fontSize: '0.65rem', color: '#ef4444' }}>1900</div>
                            <div style={{ position: 'absolute', bottom: '5px', left: '2px', fontSize: '0.65rem', color: '#ef4444' }}>1500</div>
                            <div style={{ position: 'absolute', top: '5px', right: '2px', fontSize: '0.65rem', color: '#10b981' }}>3.5%</div>
                            <div style={{ position: 'absolute', bottom: '5px', right: '2px', fontSize: '0.65rem', color: '#10b981' }}>2.8%</div>

                            {/* X-axis Labels */}
                            <div style={{ position: 'absolute', bottom: '-18px', left: '0', fontSize: '0.65rem', color: 'var(--text-muted)' }}>2022</div>
                            <div style={{ position: 'absolute', bottom: '-18px', left: '50%', transform: 'translateX(-50%)', fontSize: '0.65rem', color: 'var(--text-muted)' }}>2023</div>
                            <div style={{ position: 'absolute', bottom: '-18px', right: '0', fontSize: '0.65rem', color: 'var(--text-muted)' }}>2024</div>
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
