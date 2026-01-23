import React, { useState, useEffect } from 'react';

// Simplified Card for Market Indices (Matches Watchlist Layout but no Score/Risk)
const IndexCard = ({ name, symbol, market, price, pct, change, changeColor, timestamp, volume }) => {

    // Format Display Symbol (remove suffixes like .OQ)
    const displaySymbol = (symbol || '').replace(/\.OQ$|\.N$|\.QQ$/i, '');

    return (
        <div style={{
            background: 'rgba(255,255,255,0.05)',
            padding: '1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '0.8rem',
            border: '1px solid rgba(255,255,255,0.1)'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {/* Left: Name & Symbol */}
                <div style={{ flex: '0 0 100px', minWidth: '0' }}>
                    <div style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.3rem', color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {displaySymbol}
                    </div>
                </div>

                {/* Right Group: Pct+Change | Price+Time */}
                <div style={{ flex: '1 1 auto', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '20px', minWidth: 0, paddingLeft: '1.5rem' }}>

                    {/* Col 1: Pct Change + Change Value (Vertical) */}
                    <div style={{
                        flexShrink: 0,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-end',
                        gap: '4px'
                    }}>
                        {/* Pct Change */}
                        <div style={{
                            color: changeColor,
                            fontSize: '1.1rem',
                            fontWeight: 'bold'
                        }}>
                            {pct}
                        </div>

                        {/* Change Value */}
                        <div style={{
                            color: changeColor,
                            fontSize: '0.85rem',
                            fontWeight: '500'
                        }}>
                            {change}
                        </div>
                    </div>

                    {/* Col 2: Price + Time (Vertical) */}
                    <div style={{
                        flexShrink: 0,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-end',
                        gap: '6px'
                    }}>
                        {/* Price */}
                        <div style={{
                            fontSize: '1.3rem',
                            fontWeight: 'bold',
                            color: changeColor,
                            lineHeight: '1',
                            textAlign: 'right',
                            whiteSpace: 'nowrap'
                        }}>
                            {price}
                        </div>

                        {/* Time info below price */}
                        <div style={{
                            fontSize: '0.65rem',
                            color: 'var(--text-muted)',
                            whiteSpace: 'nowrap'
                        }}>
                            {(() => {
                                const isUS = symbol && (market === 'US' || symbol.startsWith('^'));
                                const isHK = symbol && (market === 'HK');
                                const isCN = symbol && (market === 'CN');
                                let marketName = '';
                                if (isUS) marketName = '美东时间 ';
                                else if (isHK) marketName = '香港时间 ';
                                else if (isCN) marketName = '北京时间 ';

                                return marketName + timestamp;
                            })()}
                        </div>
                    </div>

                </div>

            </div>
        </div>
    );
};

const MarketView = () => {
    // Indices definition (Structure driven by Frontend for display order)
    const [marketData, setMarketData] = useState({});
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        try {
            const res = await fetch('/api/market-indices');
            const data = await res.json();
            // Convert array to map for easy lookup
            const dataMap = {};
            if (Array.isArray(data)) {
                data.forEach(item => {
                    dataMap[item.symbol] = item;
                });
            }
            setMarketData(dataMap);
        } catch (e) {
            console.error("Failed to fetch indices", e);
        }
    };

    useEffect(() => {
        fetchData();
        // const interval = setInterval(fetchData, 3000); // Optional auto-refresh
        // return () => clearInterval(interval);
    }, []);

    const handleRefresh = async () => {
        setRefreshing(true);
        try {
            // 1. Force Sync Backend
            await fetch('/api/sync-indices', { method: 'POST' });
            // 2. Re-fetch Data
            await fetchData();
        } catch (e) {
            console.error("Refresh failed", e);
        } finally {
            setRefreshing(false);
        }
    };

    const handleTriggerUpdate = async () => {
        setRefreshing(true);
        try {
            const res = await fetch('/api/trigger-update', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                alert('✅ ' + data.message);
                // Wait 5 seconds then refresh display
                setTimeout(async () => {
                    await fetchData();
                    setRefreshing(false);
                }, 5000);
            } else {
                alert('❌ ' + data.message);
                setRefreshing(false);
            }
        } catch (e) {
            console.error("Trigger update failed", e);
            alert('❌ 触发失败');
            setRefreshing(false);
        }
    };

    // Helper to get data safely
    const getData = (symbol) => {
        const item = marketData[symbol];
        // item structure from API: { symbol, name, price, change, pct_change, market, timestamp }

        if (!item) return { price: '--', pct: '--', change: '--', timestamp: '--', changeColor: '#888' };

        // Robust formatting: handle both string and number
        let displayPrice = item.price;
        if (typeof item.price === 'number') {
            displayPrice = item.price.toFixed(2);
        }

        // Change Color
        const rawPct = item.pct_change || 0;
        let changeColor = '#fff';
        if (rawPct > 0.001) changeColor = '#ef4444'; // Red for up
        else if (rawPct < -0.001) changeColor = '#10b981'; // Green for down

        // Formats
        const displayPct = rawPct !== undefined ? `${rawPct > 0 ? '+' : ''}${rawPct.toFixed(2)}%` : '--';
        const displayChange = item.change !== undefined ? `${item.change > 0 ? '+' : ''}${item.change.toFixed(2)}` : '--';

        // Time Format Logic: 
        // Always show MM-DD HH:mm
        // If US, add " 美东时间"
        let displayTime = '--';
        const isUS = item.symbol && (item.market === 'US' || item.symbol.startsWith('^') || item.symbol.endsWith('.OQ') || item.symbol.endsWith('.N') || item.symbol.endsWith('.K'));
        const isHK = item.symbol && (item.market === 'HK' || item.symbol.endsWith('.HK') || /^\d{5}$/.test(item.symbol));
        const isCN = item.symbol && (item.market === 'CN' || item.symbol.endsWith('.sh') || item.symbol.endsWith('.sz'));
        // Timestamp Logic
        // Principle: Respect raw data. Only fill in Close Time if data is Date-Only (00:00:00).
        displayTime = item.timestamp || '--';
        if (typeof displayTime === 'string') {
            let s = displayTime;
            // Check if it looks like midnight (Date only)
            const isMidnight = s.endsWith(' 00:00:00') || s.endsWith(' 00:00');

            if (isMidnight) {
                if (isUS) s = s.replace(/ 00:00(:00)?$/, ' 16:00');
                else if (isHK) s = s.replace(/ 00:00(:00)?$/, ' 16:00');
                else if (isCN) s = s.replace(/ 00:00(:00)?$/, ' 15:00');
            } else {
                // Live time or specific fetch time. Keep as is.
                // Just ensure seconds are trimmed if desired, but user said "don't convert forcedly".
                // Maybe trim seconds for cleaner look? "18:31:35" -> "18:31"
                // Let's keep it simple: Raw is fine, or simple truncate.
                // If formatting is needed:
                // if (s.match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)) s = s.substring(5, 16); // MM-DD HH:mm
            }

            // Format for display (MM-DD HH:mm) if it's a full date string
            // But be careful not to break "美东时间..." prefix if added elsewhere.
            // Currently backend returns "YYYY-MM-DD HH:MM:SS".
            // Let's just strip YYYY for cleaner list view?
            if (s.match(/^\d{4}-\d{2}-\d{2}/)) {
                s = s.substring(5, 16); // 2025-12-15 16:00:00 -> 12-15 16:00
            } else if (s.match(/^\d{4}\/\d{2}\/\d{2}/)) {
                s = s.substring(5, 16).replace(/\//g, '-'); // 2025/12/15 -> 12-15
            }

            displayTime = s;
        }

        // Volume
        let displayVolume = null;
        if (item.volume && item.volume > 0) {
            const v = item.volume;
            if (v >= 1e9) displayVolume = (v / 1e9).toFixed(2) + 'B';
            else if (v >= 1e6) displayVolume = (v / 1e6).toFixed(2) + 'M';
            else if (v >= 1e3) displayVolume = (v / 1e3).toFixed(2) + 'K';
            else displayVolume = v.toString();
        }

        return {
            price: displayPrice || '--',
            pct: displayPct,
            change: displayChange,
            timestamp: displayTime,
            changeColor: changeColor,
            volume: displayVolume
        };
    };

    return (
        <div style={{ padding: '1rem', paddingBottom: '6rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', marginTop: '1rem' }}>
                <h1 style={{ margin: 0, fontSize: '1.8rem' }}>全球市场</h1>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        style={{
                            background: 'rgba(255,255,255,0.1)',
                            border: 'none',
                            color: '#fff',
                            padding: '6px 10px',
                            borderRadius: '8px',
                            fontSize: '0.8rem',
                            cursor: 'not-allowed',
                            opacity: 0.5
                        }}
                        disabled
                    >
                        排序
                    </button>
                    <button
                        onClick={handleRefresh}
                        style={{
                            background: 'rgba(255,255,255,0.1)',
                            border: 'none',
                            borderRadius: '50%',
                            width: '40px',
                            height: '40px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            transform: refreshing ? 'rotate(360deg)' : 'none',
                            transition: 'transform 1s ease'
                        }}
                    >
                        <span style={{ fontSize: '1.3rem' }}>🔄</span>
                    </button>
                    <button
                        onClick={handleTriggerUpdate}
                        disabled={refreshing}
                        style={{
                            background: refreshing ? 'rgba(255,255,255,0.05)' : 'rgba(34,197,94,0.2)',
                            border: '1px solid rgba(34,197,94,0.3)',
                            borderRadius: '8px',
                            color: '#fff',
                            padding: '8px 12px',
                            fontSize: '0.75rem',
                            cursor: refreshing ? 'not-allowed' : 'pointer',
                            fontWeight: 'bold',
                            opacity: refreshing ? 0.5 : 1,
                            transition: 'all 0.2s'
                        }}
                        title="触发独立增量更新脚本（3市场全量，只获取5天数据）"
                    >
                        📥 增量更新
                    </button>
                    <button
                        style={{
                            background: 'rgba(255,255,255,0.1)',
                            border: 'none',
                            borderRadius: '50%',
                            width: '40px',
                            height: '40px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'not-allowed',
                            opacity: 0.5
                        }}
                        disabled
                    >
                        <span style={{ fontSize: '1.3rem' }}>🔍</span>
                    </button>
                </div>
            </div>

            {/* US Market */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1rem', color: '#888', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>🇺🇸</span> 美股市场
                </h3>
                <IndexCard name="道琼斯工业平均指数" symbol="^DJI" market="US" {...getData('^DJI')} />
                <IndexCard name="纳斯达克100指数" symbol="^NDX" market="US" {...getData('^NDX')} />
                <IndexCard name="标普500指数" symbol="^SPX" market="US" {...getData('^SPX')} />
            </div>

            {/* HK Market */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1rem', color: '#888', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>🇭🇰</span> 港股市场
                </h3>
                <IndexCard name="恒生指数" symbol="HSI" market="HK" {...getData('HSI')} />
                <IndexCard name="恒生科技指数" symbol="HSTECH" market="HK" {...getData('HSTECH')} />
            </div>

            {/* CN Market */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1rem', color: '#888', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>🇨🇳</span> A股市场
                </h3>
                <IndexCard name="上证综合指数" symbol="000001.SS" market="CN" {...getData('000001.SS')} />
            </div>
        </div>
    );
};

export default MarketView;
