import React, { useState, useEffect } from 'react';
import ImageUploadArea from './ImageUploadArea';
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

                        {/* Right: Volume & Turnover Stacked */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', alignItems: 'flex-end' }}>
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

                {/* SECTION 3: Analysis Results (Bottom) */}
                <div className="glass-panel" style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: '#1c1c20' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
                        <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)' }}>
                            上次分析结果
                        </h3>
                        <div
                            style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                            onClick={() => alert("功能开发中：查看历史分析记录")}
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
                                                // Map -3 to +3 range to 0% to 100%
                                                // -3 => 0%, 0 => 50%, +3 => 100%
                                                // Formula: ((val + 3) / 6) * 100
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
                                        if (model.signal.includes('中性') || model.signal.includes('Neutral')) signalColor = '#eab308'; // Yellow

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
                            暂无详细分析记录，请点击底部按钮开始分析。
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
        </div>
    );
};

export default StockDetailView;
