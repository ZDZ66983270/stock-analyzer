/**
 * VERA Dashboard View (HomeView.jsx)
 * ==============================================================================
 * 
 * 功能说明:
 * 1. **核心看板**: 集中展示用户关注的所有资产实时行情、风险建议和涨跌幅。
 * 2. **交互引擎**:
 *    - **Swipe-to-Delete**: 实现了自定义的手势侧滑删除逻辑。
 *    - **Pull-to-Refresh**: 基于 Touch 事件的阻尼感下拉刷新。
 *    - **Double-Tap Magic**: 刷新按钮支持单次普通同步和双击“强制全量刷新”模式。
 * 3. **实时数据流**:
 *    - **WebSocket**: 订阅后台 `/ws/market-data`，实现毫秒级的实时跳价更新。
 *    - **Smart Polling**: 针对新添加、数据尚未就绪的资产，自动开启 2s 间隔的高频轮询直到数据补全。
 * 4. **排序与搜索**:
 *    - 内嵌 `SearchBar` 搜索组件。
 *    - 支持按市场 (CN/HK/US) 或资产名称进行加权排序。
 * 
 * 作者: Antigravity
 * 日期: 2026-01-23
 */

import React, { useState, useEffect, useRef } from 'react';
import SearchBar from './SearchBar';


const SwipeableItem = ({ children, onDelete, onClick }) => {
    const [startX, setStartX] = useState(null);
    const [currentX, setCurrentX] = useState(0);
    const threshold = -80;

    // Unix timestamp to distinguish click vs swipe
    const startTime = useRef(0);

    const handleStart = (clientX) => {
        setStartX(clientX);
        startTime.current = Date.now();
    };

    const handleMove = (clientX) => {
        if (startX === null) return;
        const diff = clientX - startX;
        // Only allow swipe left (diff < 0)
        // Add some resistance or limit
        if (diff < 0) {
            setCurrentX(Math.max(diff, -120));
        }
    };

    const handleEnd = () => {
        if (startX === null) return;

        const timeDiff = Date.now() - startTime.current;
        const isClick = Math.abs(currentX) < 5 && timeDiff < 200;

        if (isClick && onClick) {
            onClick(); // Trigger click if it was just a tap
        } else if (currentX < threshold) {
            setCurrentX(-100); // Snap open
        } else {
            setCurrentX(0); // Snap close
        }
        setStartX(null);
    };

    return (
        <div style={{ position: 'relative', overflow: 'hidden' }}>
            {/* Delete Button (Behind) */}
            <div
                style={{
                    position: 'absolute',
                    top: 0, bottom: 0, right: 0,
                    width: '100px',
                    background: '#ef4444',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    borderRadius: 'var(--radius-md)',
                    zIndex: 0
                }}
                onClick={(e) => {
                    e.stopPropagation();
                    onDelete();
                }}
            >
                <span style={{ color: 'white', fontWeight: 'bold' }}>删除</span>
            </div>

            {/* Content (Foreground) */}
            <div
                onTouchStart={(e) => handleStart(e.touches[0].clientX)}
                onTouchMove={(e) => handleMove(e.touches[0].clientX)}
                onTouchEnd={handleEnd}
                onMouseDown={(e) => handleStart(e.clientX)}
                onMouseMove={(e) => { if (e.buttons === 1) handleMove(e.clientX); }}
                onMouseUp={handleEnd}
                onMouseLeave={handleEnd}
                style={{
                    position: 'relative',
                    zIndex: 1,
                    transform: `translateX(${currentX}px)`,
                    transition: startX !== null ? 'none' : 'transform 0.2s ease-out', // No transition while dragging
                    background: '#1c1c20',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid rgba(255,255,255,0.05)'
                }}
            >
                {children}
            </div>
        </div>
    );
};

const HomeView = ({ onSelectAsset }) => {
    const [watchlist, setWatchlist] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchValue, setSearchValue] = useState('');
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [toastMsg, setToastMsg] = useState(null);
    const [selectedItem, setSelectedItem] = useState(null);
    const [sortMethod, setSortMethod] = useState('default'); // 'default', 'market', 'name'
    const [activeTab, setActiveTab] = useState('watchlist'); // 'watchlist' or 'market'

    // Pull to Refresh State
    const [pullY, setPullY] = useState(0);
    const startY = useRef(0);
    const isPulling = useRef(false);
    const currentPullY = useRef(0);

    // Auto-poll if data incomplete (waiting for background update)
    useEffect(() => {
        let interval;
        const hasPending = watchlist.some(item => item.price === undefined || item.price === null);
        if (hasPending) {
            // Poll every 2s
            interval = setInterval(() => fetchWatchlist(false), 2000); // Pass false to avoid loading spinner
        }
        return () => clearInterval(interval);
    }, [watchlist]);

    const fetchWatchlist = async (showLoading = true) => {
        try {
            console.log('[DEBUG] fetchWatchlist called, showLoading:', showLoading);
            if (showLoading) setLoading(true);
            const res = await fetch('/api/watchlist');
            console.log('[DEBUG] API response status:', res.status);
            const data = await res.json();
            console.log('[DEBUG] API response data:', data);
            if (Array.isArray(data)) {
                console.log('[DEBUG] Setting watchlist with', data.length, 'items');
                setWatchlist(data);
            } else {
                console.log('[DEBUG] Data is not array, setting empty');
                setWatchlist([]);
            }
        } catch (e) {
            console.error("[ERROR] Failed to fetch watchlist:", e);
        } finally {
            if (showLoading) setLoading(false);
        }
    };

    useEffect(() => {
        fetchWatchlist();

        // Touch Listeners for Pull to Refresh (Window level for better UX)
        const handleTouchStart = (e) => {
            if (window.scrollY === 0) {
                startY.current = e.touches[0].clientY;
                isPulling.current = true;
            }
        };

        const handleTouchMove = (e) => {
            if (!isPulling.current) return;
            const y = e.touches[0].clientY;
            const diff = y - startY.current;
            if (diff > 0 && window.scrollY === 0) {
                // Resistance effect
                const newPullY = Math.pow(diff, 0.8);
                currentPullY.current = newPullY;
                setPullY(newPullY);
                if (e.cancelable) e.preventDefault(); // Prevent native scroll
            } else {
                setPullY(0);
                currentPullY.current = 0;
            }
        };

        const handleTouchEnd = async () => {
            if (currentPullY.current > 60) {
                // Trigger Refresh
                handleRefresh();
            }
            isPulling.current = false;
            // Animate back
            const interval = setInterval(() => {
                currentPullY.current *= 0.8;
                setPullY(currentPullY.current);
                if (currentPullY.current < 1) {
                    clearInterval(interval);
                    setPullY(0);
                    currentPullY.current = 0;
                }
            }, 10);
        };

        window.addEventListener('touchstart', handleTouchStart, { passive: false });
        // Use passive: false to allow preventDefault
        window.addEventListener('touchmove', handleTouchMove, { passive: false });
        window.addEventListener('touchend', handleTouchEnd);

        return () => {
            window.removeEventListener('touchstart', handleTouchStart);
            window.removeEventListener('touchmove', handleTouchMove);
            window.removeEventListener('touchend', handleTouchEnd);
        };

    }, []);

    // WebSocket connection for real-time updates
    useEffect(() => {
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 3;

        const connectWebSocket = () => {
            if (reconnectAttempts >= maxReconnectAttempts) {
                console.log('WebSocket: Max reconnect attempts reached, stopping');
                return;
            }

            try {
                ws = new WebSocket('ws://localhost:8000/ws/market-data');

                ws.onopen = () => {
                    console.log('WebSocket connected');
                    reconnectAttempts = 0;
                };

                ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);

                        if (message.type === 'market_update') {
                            setWatchlist(prevList => {
                                return prevList.map(item => {
                                    if (item.symbol === message.symbol && item.market === message.market) {
                                        return {
                                            ...item,
                                            ...message.data,
                                            price: message.data.price || message.data.close,
                                            last_updated: message.timestamp
                                        };
                                    }
                                    return item;
                                });
                            });

                            console.log(`Updated ${message.symbol} via WebSocket`);
                        }
                    } catch (e) {
                        // Silent error
                    }
                };

                ws.onerror = () => {
                    // Silent
                };

                ws.onclose = () => {
                    reconnectAttempts++;
                    if (reconnectAttempts < maxReconnectAttempts) {
                        console.log(`WebSocket disconnected, will retry (${reconnectAttempts}/${maxReconnectAttempts})...`);
                        setTimeout(connectWebSocket, 5000);
                    }
                };
            } catch (e) {
                reconnectAttempts++;
            }
        };

        connectWebSocket();

        return () => {
            if (ws) {
                ws.close();
            }
        };
    }, []);


    const lastRefreshClick = useRef(0);

    const handleRefresh = async () => {
        const now = Date.now();
        const isDoubleTap = now - lastRefreshClick.current < 2000; // 2 second window for double tap

        // ✅ 修复：如果不是双击且正在刷新，则阻止
        // 如果是双击，即使正在刷新也允许（升级为force-refresh）
        if (!isDoubleTap && isRefreshing) return;

        lastRefreshClick.current = now;

        setIsRefreshing(true);
        try {
            if (isDoubleTap) {
                // 强制全量刷新流程
                setToastMsg('⚡️ 正在强制全量刷新...');

                // 触发后台强制刷新任务
                const response = await fetch('/api/force-refresh', { method: 'POST' });
                const result = await response.json();

                console.log('[强制刷新] 后台任务已启动:', result);

                // 等待后台任务处理(根据股票数量调整等待时间)
                const stockCount = result.total || 6;
                const waitTime = Math.min(stockCount * 500, 5000); // 每只股票500ms,最多5秒

                // 倒计时显示
                const startTime = Date.now();
                const countdownInterval = setInterval(() => {
                    const elapsed = Date.now() - startTime;
                    const remaining = Math.max(0, Math.ceil((waitTime - elapsed) / 1000));
                    if (remaining > 0) {
                        setToastMsg(`⚡️ 正在刷新 ${stockCount} 只股票... ${remaining}秒`);
                    }
                }, 500);

                await new Promise(resolve => setTimeout(resolve, waitTime));
                clearInterval(countdownInterval);

                // 第一次获取更新后的数据
                setToastMsg('📊 正在获取最新数据 (1/3)...');
                await fetchWatchlist();
                await new Promise(resolve => setTimeout(resolve, 1000));

                // 第二次获取(确保获取到最新数据)
                setToastMsg('📊 正在获取最新数据 (2/3)...');
                await fetchWatchlist();
                await new Promise(resolve => setTimeout(resolve, 500));

                // 第三次获取(最终确认)
                setToastMsg('📊 正在获取最新数据 (3/3)...');
                await fetchWatchlist();

                // 显示实际状态提示
                setToastMsg('✅ 已发起数据获取,处理和显示需要一定时间...');
                setTimeout(() => setToastMsg(null), 5000);  // 延长显示时间到5秒

            } else {
                // 普通刷新 - 触发后台同步
                setToastMsg('正在请求同步...');

                try {
                    // Call sync API
                    const res = await fetch('/api/sync-market', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ markets: ['CN', 'HK', 'US'] })
                    });

                    if (res.ok) {
                        setToastMsg('✅ 数据获取已发起，处理和显示将需要一点时间');

                        // Optional: Poll a few times updates
                        setTimeout(fetchWatchlist, 1000);
                        setTimeout(fetchWatchlist, 3000);
                    } else {
                        setToastMsg('同步请求失败');
                    }
                } catch (e) {
                    console.error("Sync failed", e);
                    setToastMsg('同步请求异常');
                }

                setTimeout(() => setToastMsg(null), 4000);
            }

        } catch (error) {
            console.error('Refresh failed:', error);
            setToastMsg('刷新失败');
            setTimeout(() => setToastMsg(null), 2000);
        } finally {
            setIsRefreshing(false);
        }
    };

    const toggleSort = () => {
        if (sortMethod === 'default') setSortMethod('market');
        else if (sortMethod === 'market') setSortMethod('name');
        else setSortMethod('default');
    };

    const handleSearchSubmit = async (itemOrSymbol) => {
        console.log('[HomeView] handleSearchSubmit called with:', itemOrSymbol);

        let symbolToAdd = null;
        let nameToAdd = null;
        let marketToAdd = null;

        if (typeof itemOrSymbol === 'object') {
            symbolToAdd = itemOrSymbol.symbol;
            nameToAdd = itemOrSymbol.name;
            marketToAdd = itemOrSymbol.market; // Use market from suggestion
            console.log('[HomeView] extracted from object:', symbolToAdd, nameToAdd, marketToAdd);
        } else {
            symbolToAdd = searchValue;
            console.log('[HomeView] using searchValue:', symbolToAdd);
        }

        if (!symbolToAdd) {
            console.warn('[HomeView] No symbol to add');
            return;
        }

        setIsSearchOpen(false);
        setLoading(true);
        try {
            console.log('[HomeView] sending POST to /api/watchlist');
            const res = await fetch('/api/watchlist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbolToAdd,
                    name: nameToAdd,
                    market: marketToAdd
                })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setSearchValue('');
                await fetchWatchlist();
            } else if (data.status === 'info') {
                // Already exists
                setToastMsg('已在关注列表中');
                setTimeout(() => setToastMsg(null), 2000);
            } else {
                setToastMsg(data.message || '添加失败');
                setTimeout(() => setToastMsg(null), 2000);
            }
        } catch (e) {
            setToastMsg('请求失败');
            setTimeout(() => setToastMsg(null), 2000);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (symbol) => {
        if (!confirm(`确定要移除 ${symbol} 吗?`)) return;
        try {
            const res = await fetch(`/api/watchlist/${symbol}`, { method: 'DELETE' });
            if (res.ok) {
                setWatchlist(prev => prev.filter(item => item.symbol !== symbol));
            }
        } catch (e) {
            console.error(e);
        }
    };

    const getSortedWatchlist = () => {
        let sorted = [...watchlist];
        if (sortMethod === 'market') {
            const marketOrder = { 'CN': 1, 'HK': 2, 'US': 3, 'Other': 4 };
            sorted.sort((a, b) => (marketOrder[a.market] || 99) - (marketOrder[b.market] || 99));
        } else if (sortMethod === 'name') {
            sorted.sort((a, b) => {
                const nameA = (a.name || a.symbol).trim();
                const nameB = (b.name || b.symbol).trim();

                // Helper to check if string starts with English/ASCII
                const isEnglishA = /^[A-Za-z0-9]/.test(nameA);
                const isEnglishB = /^[A-Za-z0-9]/.test(nameB);

                if (isEnglishA && !isEnglishB) return -1; // English first
                if (!isEnglishA && isEnglishB) return 1;

                // If both same type, sort standard
                return nameA.localeCompare(nameB, 'zh-CN');
            });
        }
        return sorted;
    };

    const sortedWatchlist = getSortedWatchlist();

    return (
        <div style={{
            padding: '1rem',
            paddingTop: 'max(1rem, env(safe-area-inset-top))',
            minHeight: '100vh',
            boxSizing: 'border-box',
            position: 'relative',
            paddingBottom: '80px', // Space for bottom nav
            overflowX: 'hidden'
        }}>

            {/* Pull Refresh Indicator */}
            {pullY > 0 && (
                <div style={{
                    position: 'fixed',
                    top: 'calc(env(safe-area-inset-top) + 10px)',
                    left: 0, right: 0,
                    display: 'flex', justifyContent: 'center',
                    pointerEvents: 'none',
                    zIndex: 200
                }}>
                    <div style={{
                        background: 'rgba(0,0,0,0.6)',
                        color: 'white',
                        padding: '5px 12px',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        backdropFilter: 'blur(5px)',
                        transform: `scale(${Math.min(pullY / 60, 1)})`,
                        opacity: Math.min(pullY / 40, 1),
                        transition: 'transform 0.1s'
                    }}>
                        {currentPullY.current > 60 ? '释放刷新' : '下拉刷新'}
                    </div>
                </div>
            )}

            {/* Main Content with Pull Transform */}
            <div style={{
                transform: `translateY(${pullY * 0.4}px)`,
                transition: isPulling.current ? 'none' : 'transform 0.3s ease-out'
            }}>

                {activeTab === 'watchlist' && (
                    <>
                        {/* Header */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: 0 }}>我的关注 ({getSortedWatchlist().length}) <span style={{ fontSize: '0.8rem', color: '#666' }}>v1.1</span></h1>
                                {isRefreshing && <span style={{ fontSize: '0.8rem', color: '#888' }}>刷新中...</span>}
                            </div>

                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    onClick={toggleSort}
                                    style={{
                                        background: 'rgba(255,255,255,0.1)',
                                        border: 'none',
                                        color: '#fff',
                                        padding: '6px 10px',
                                        borderRadius: '8px',
                                        fontSize: '0.8rem',
                                        cursor: 'pointer'
                                    }}
                                >
                                    {sortMethod === 'default' ? '排序' : (sortMethod === 'market' ? '按市场' : '按名称')}
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
                                        transform: isRefreshing ? 'rotate(360deg)' : 'none',
                                        transition: 'transform 1s ease'
                                    }}
                                >
                                    <span style={{ fontSize: '1.3rem' }}>🔄</span>
                                </button>
                                <button
                                    onClick={() => setIsSearchOpen(!isSearchOpen)}
                                    style={{
                                        background: 'rgba(255,255,255,0.1)',
                                        border: 'none',
                                        borderRadius: '50%',
                                        width: '40px',
                                        height: '40px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: 'pointer'
                                    }}
                                >
                                    <span style={{ fontSize: '1.3rem' }}>🔍</span>
                                </button>
                            </div>
                        </div>

                        {/* Loading State */}
                        {loading && <div style={{ textAlign: 'center', padding: '1rem', color: '#666' }}>处理中...</div>}

                        {/* Empty State */}
                        {!loading && watchlist.length === 0 && (
                            <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                                <p>这里空空如也</p>
                                <button
                                    onClick={() => setIsSearchOpen(true)}
                                    style={{ background: 'var(--accent-primary)', border: 'none', color: '#fff', padding: '0.5rem 1rem', borderRadius: '4px', marginTop: '1rem' }}
                                >
                                    添加股票/基金
                                </button>
                            </div>
                        )}

                        {/* List */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {getSortedWatchlist().map(item => {
                                const pct = item.pct_change || 0;
                                let changeColor = '#fff';
                                if (pct > 0.001) changeColor = '#ef4444';
                                else if (pct < -0.001) changeColor = '#10b981';
                                const score = item.last_score;
                                const displayScore = score || '不适合';
                                const prevScore = item.prev_score || score;
                                const prevRiskCount = item.prev_risk_count || (item.risk_count || 2);
                                const displaySymbol = (item.symbol || '').replace(/\.OQ$|\.N$|\.QQ$/i, '');
                                const scoreTrend = score > prevScore ? 1 : score < prevScore ? -1 : 0;
                                const riskTrend = (item.risk_count || 2) > prevRiskCount ? 1 : (item.risk_count || 2) < prevRiskCount ? -1 : 0;

                                return (
                                    <SwipeableItem
                                        key={item.symbol}
                                        onDelete={() => handleDelete(item.symbol)}
                                        onClick={() => onSelectAsset(item)}
                                    >
                                        <div
                                            style={{
                                                background: 'rgba(255,255,255,0.05)',
                                                padding: '1rem 1rem 1rem 1rem', // Increased to 2.5rem to move content left
                                                boxSizing: 'border-box',
                                                borderRadius: 'var(--radius-md)',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s',
                                                border: '1px solid rgba(255,255,255,0.1)'
                                            }}
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                {/* Left: Name */}
                                                <div style={{ flex: '0 0 100px', minWidth: '0' }}>
                                                    <div style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.3rem', color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                        {item.name || item.symbol}
                                                    </div>
                                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                                        {displaySymbol}
                                                    </div>
                                                </div>

                                                {/* Middle: Score - Shifted Left */}
                                                <div style={{ flex: '0 0 80px', display: 'flex', gap: '0.6rem', alignItems: 'center', justifyContent: 'flex-start' }}>
                                                    <div style={{ textAlign: 'center', flex: '0 0 70px' }}>
                                                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>当前建议</div>
                                                        <div style={{
                                                            fontSize: (item.risk_count || 2) === 2 ? '0.75rem' : '1.4rem',
                                                            fontWeight: 'bold',
                                                            color: (item.risk_count || 2) === 2 ? '#ffffff' : '#facc15',
                                                            whiteSpace: 'nowrap'
                                                        }}>
                                                            {(item.risk_count || 2) === 2 ? '继续等待' : item.risk_count}
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Right Group: Pct | Price+Time */}
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
                                                            {typeof item.pct_change === 'number' ? `${item.pct_change > 0 ? '+' : ''}${item.pct_change.toFixed(2)}%` : '--'}
                                                        </div>

                                                        {/* Change Value */}
                                                        <div style={{
                                                            color: changeColor,
                                                            fontSize: '0.85rem',
                                                            fontWeight: '500',
                                                            lineHeight: '1.2'
                                                        }}>
                                                            {typeof item.change === 'number' ? `${item.change > 0 ? '+' : ''}${item.change.toFixed(2)}` : '--'}
                                                        </div>
                                                    </div>

                                                    {/* Col 2: Price + Time (Vertical) */}
                                                    <div style={{
                                                        flexShrink: 0,
                                                        display: 'flex',
                                                        flexDirection: 'column',
                                                        alignItems: 'flex-end',
                                                        gap: '4px'
                                                    }}>
                                                        {/* Price */}
                                                        <div style={{
                                                            fontSize: '1.3rem',
                                                            fontWeight: 'bold',
                                                            color: (item.pct_change && Math.abs(item.pct_change) > 0.001) ? changeColor : 'var(--text-primary)',
                                                            lineHeight: '1',
                                                            textAlign: 'right',
                                                            whiteSpace: 'nowrap'
                                                        }}>
                                                            {item.price ? item.price.toFixed(2) : '--'}
                                                        </div>

                                                        {/* Time info below price */}
                                                        <div style={{
                                                            fontSize: '0.65rem',
                                                            color: 'var(--text-muted)',
                                                            whiteSpace: 'nowrap',
                                                            lineHeight: '1.2'
                                                        }}>
                                                            {(() => {
                                                                const isUS = item.symbol && (item.market === 'US' || item.symbol.startsWith('^'));
                                                                const isHK = item.symbol && (item.market === 'HK');
                                                                const isCN = item.symbol && (item.market === 'CN');
                                                                let marketName = '';
                                                                if (isUS) marketName = '美东时间 ';
                                                                else if (isHK) marketName = '香港时间 ';
                                                                else if (isCN) marketName = '北京时间 ';

                                                                if (!item.timestamp) return marketName || '';
                                                                let s = String(item.timestamp);
                                                                if (s.includes('T')) s = s.replace('T', ' ');
                                                                // Show: 香港时间 12-16 14:40
                                                                let timeStr = '';
                                                                if (s.length >= 16) timeStr = s.substring(5, 16);
                                                                else if (s.length >= 10) timeStr = s.substring(5, 10);

                                                                return marketName + timeStr;
                                                            })()}
                                                        </div>
                                                    </div>

                                                </div>

                                            </div>
                                        </div>
                                    </SwipeableItem>
                                );
                            })}
                        </div>
                    </>
                )}

            </div>

            {/* Search Overlay */}
            {
                isSearchOpen && (
                    <div style={{
                        position: 'fixed',
                        top: 0, left: 0, right: 0, bottom: 0,
                        background: 'rgba(0,0,0,0.8)',
                        backdropFilter: 'blur(5px)',
                        zIndex: 1000,
                        padding: '1rem',
                        paddingTop: 'max(1rem, env(safe-area-inset-top))',
                        animation: 'fadeIn 0.2s ease-out'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
                            <button
                                onClick={() => setIsSearchOpen(false)}
                                style={{ background: 'none', border: 'none', color: '#fff', fontSize: '1rem' }}
                            >
                                关闭
                            </button>
                        </div>

                        <SearchBar
                            value={searchValue}
                            onChange={setSearchValue}
                            onSelect={handleSearchSubmit}
                        />
                    </div>
                )
            }

            {/* Toaster */}
            {
                toastMsg && (
                    <div style={{
                        position: 'fixed',
                        bottom: '80px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(50, 50, 50, 0.9)',
                        color: '#fff',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        fontSize: '0.9rem',
                        zIndex: 2000,
                        boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
                    }}>
                        {toastMsg}
                    </div>
                )
            }

            {/* Bottom Nav - High Z-Index to ensure visibility */}
            <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0,
                background: 'rgba(28, 28, 32, 0.95)', backdropFilter: 'blur(10px)',
                borderTop: '1px solid rgba(255,255,255,0.1)',
                display: 'flex', justifyContent: 'space-around', alignItems: 'center',
                height: '60px', paddingBottom: 'env(safe-area-inset-bottom)',
                zIndex: 2000 // Boost Z-Index
            }}>
                <button
                    onClick={() => setActiveTab('watchlist')}
                    style={{
                        color: activeTab === 'watchlist' ? '#3b82f6' : '#888',
                        background: 'none', border: 'none', fontSize: '0.75rem',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
                        flex: 1, height: '100%', justifyContent: 'center', cursor: 'pointer'
                    }}
                >
                    <span style={{ fontSize: '1.2rem' }}>★</span>
                    <span>自选</span>
                </button>
                <button
                    onClick={() => setActiveTab('market')}
                    style={{
                        color: activeTab === 'market' ? '#3b82f6' : '#888',
                        background: 'none', border: 'none', fontSize: '0.75rem',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
                        flex: 1, height: '100%', justifyContent: 'center', cursor: 'pointer'
                    }}
                >
                    <span style={{ fontSize: '1.2rem' }}>📊</span>
                    <span>市场</span>
                </button>
            </div>

        </div>
    );
};
export default HomeView;
