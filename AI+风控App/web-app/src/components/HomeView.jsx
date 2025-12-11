import React, { useState, useEffect } from 'react';
import SearchBar from './SearchBar';
import SwipeableItem from './SwipeableItem';

const HomeView = ({ onSelectAsset }) => {
    const [searchValue, setSearchValue] = useState('');
    const [loading, setLoading] = useState(false);
    const [watchlist, setWatchlist] = useState([
        // Built-in demo stocks
        {
            id: 'demo-600519',
            type: 'stock',
            symbol: '600519',
            market: 'SH',
            name: '贵州茅台',
            price: 1725.50,
            pct_change: 0.89,
            last_score: 82,
            analysis_summary: '当前处于典型的磨底阶段，宏观流动性边际改善，估值处于历史低位',
            recommendation: '建议：分批建仓，重点关注北向资金回流'
        },
        {
            id: 'demo-09988',
            type: 'stock',
            symbol: '09988',
            market: 'HK',
            name: '阿里巴巴-SW',
            price: 82.50,
            pct_change: -1.25,
            last_score: 68,
            analysis_summary: '技术面显示超跌反弹信号，但基本面仍需观察电商业务恢复情况',
            recommendation: '建议：观望为主，等待明确的业绩改善信号'
        },
        {
            id: 'demo-TSLA',
            type: 'stock',
            symbol: 'TSLA',
            market: 'US',
            name: 'Tesla Inc',
            price: 248.50,
            pct_change: 2.15,
            last_score: 75,
            analysis_summary: 'AI和自动驾驶业务进展顺利，但估值仍处于高位，需关注交付量数据',
            recommendation: '建议：长期看好，短期注意回调风险'
        },
        {
            id: 'demo-BGF-GSA',
            type: 'fund',
            symbol: 'BGF-GSA',
            market: 'US',
            name: '贝莱德全球基金',
            currency: 'USD',
            price: 9.28,
            pct_change: 0.32,
            last_score: 78,
            analysis_summary: '高股息策略表现稳健，年度化回报率13.89%，适合追求稳定收益的投资者',
            recommendation: '建议：适合长期持有，关注每月派息情况'
        }
    ]);
    const [isSearchOpen, setIsSearchOpen] = useState(false);

    useEffect(() => {
        // Disable API fetch to use built-in mock data
        // fetchWatchlist();
    }, []);

    const fetchWatchlist = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/watchlist');
            const data = await res.json();
            if (Array.isArray(data)) {
                setWatchlist(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleSearchSubmit = async () => {
        if (!searchValue.trim()) return;
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8000/api/fetch-stock', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: searchValue })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setSearchValue('');
                await fetchWatchlist();
            } else {
                alert(data.message || '添加失败');
            }
        } catch (e) {
            alert('请求失败');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (symbol) => {
        if (!confirm(`确定要移除 ${symbol} 吗?`)) return;
        try {
            const res = await fetch(`http://localhost:8000/api/watchlist/${symbol}`, { method: 'DELETE' });
            if (res.ok) {
                setWatchlist(prev => prev.filter(item => item.symbol !== symbol));
            }
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div style={{ paddingLeft: '0', paddingRight: '0', paddingTop: 'max(1rem, env(safe-area-inset-top))', paddingBottom: '3rem' }}>
            {/* Header / Search Area */}
            <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 'bold' }}>自选</h2>
                <button
                    onClick={() => setIsSearchOpen(!isSearchOpen)}
                    style={{ background: 'none', border: 'none', color: '#fff', fontSize: '1.5rem', cursor: 'pointer', padding: '0.5rem' }}
                >
                    {isSearchOpen ? '✕' : '🔍'}
                </button>
            </div>

            {/* Collapsible Search Bar */}
            {isSearchOpen && (
                <div style={{ marginBottom: '1.5rem', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: 'var(--radius-md)', animation: 'fadeIn 0.2s ease-out' }}>
                    <SearchBar
                        value={searchValue}
                        onChange={setSearchValue}
                        placeholder="输入名称或代码 (如 600536)..."
                    />
                    <button
                        onClick={handleSearchSubmit}
                        disabled={loading || !searchValue}
                        style={{
                            marginTop: '0.8rem',
                            width: '100%',
                            padding: '0.8rem',
                            background: loading ? 'var(--text-muted)' : 'var(--accent-primary)',
                            color: '#fff',
                            border: 'none',
                            borderRadius: 'var(--radius-sm)',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            fontSize: '0.95rem',
                            fontWeight: '600'
                        }}
                    >
                        {loading ? '添加 / 更新...' : '加入关注列表'}
                    </button>
                </div>
            )}

            {/* Watchlist Section */}
            <div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.8rem', fontWeight: '600' }}>
                    我的关注 ({watchlist.length})
                </div>

                {watchlist.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                        暂无关注标的，点击右上角搜索添加
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                        {watchlist.map((item) => {
                            const isPositive = (item.pct_change || 0) >= 0;
                            const changeColor = isPositive ? '#ef4444' : '#10b981';
                            // Extract score from analysis_summary if available
                            const score = item.last_score || '--';

                            return (
                                <SwipeableItem
                                    key={item.symbol}
                                    onDelete={() => handleDelete(item.symbol)}
                                    onClick={() => onSelectAsset(item)}
                                >
                                    <div
                                        style={{
                                            background: 'rgba(255,255,255,0.05)',
                                            padding: '1rem',
                                            borderRadius: 'var(--radius-md)',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s',
                                            border: '1px solid rgba(255,255,255,0.1)'
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            {/* Left: Name and Code */}
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '0.3rem', color: '#fff' }}>
                                                    {item.name || item.symbol}
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                                    {item.symbol}
                                                </div>
                                            </div>

                                            {/* Middle: Price */}
                                            <div style={{ textAlign: 'center', marginRight: '1rem' }}>
                                                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: changeColor }}>
                                                    {item.price ? item.price.toFixed(2) : '--'}
                                                </div>
                                                <div style={{ fontSize: '0.75rem', color: changeColor, fontWeight: '600' }}>
                                                    {item.pct_change !== null && item.pct_change !== undefined
                                                        ? `${isPositive ? '+' : ''}${item.pct_change.toFixed(2)}%`
                                                        : '--'}
                                                </div>
                                            </div>

                                            {/* Right: Score */}
                                            <div style={{ textAlign: 'right' }}>
                                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                                                    上次得分
                                                </div>
                                                <div style={{
                                                    fontSize: '1.3rem',
                                                    fontWeight: 'bold',
                                                    color: score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'
                                                }}>
                                                    {score}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </SwipeableItem>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default HomeView;
