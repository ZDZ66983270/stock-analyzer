import React, { useState } from 'react';

const ConfigModal = ({ isOpen, onClose }) => {
    const [activeTab, setActiveTab] = useState('params');
    const [dividend, setDividend] = useState('2.5');

    // Watchlist State
    const [watchlist, setWatchlist] = useState([]);

    React.useEffect(() => {
        if (isOpen && activeTab === 'watchlist') {
            fetchWatchlist();
        }
    }, [isOpen, activeTab]);

    const fetchWatchlist = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/watchlist');
            const data = await res.json();
            if (Array.isArray(data)) {
                setWatchlist(data);
            }
        } catch (e) {
            console.error("Failed to fetch watchlist", e);
        }
    };

    const handleDeleteWatchlist = async (symbol) => {
        if (!confirm(`确定要移除 ${symbol} 吗?`)) return;
        try {
            const res = await fetch(`http://localhost:8000/api/watchlist/${symbol}`, { method: 'DELETE' });
            if (res.ok) {
                setWatchlist(prev => prev.filter(item => item.symbol !== symbol));
            } else {
                alert('删除失败');
            }
        } catch (e) {
            alert('请求失败');
        }
    };

    // Macro Data State
    const [country, setCountry] = useState('CN'); // 'CN' or 'US'
    const [macroData, setMacroData] = useState({
        CN: [
            { id: 1, month: '2024-04', bond10y: '2.30%', currency: '7.24 (USD/CNY)', m2: '8.3%', cpi: '0.1%' },
            { id: 2, month: '2024-03', bond10y: '2.32%', currency: '7.22 (USD/CNY)', m2: '8.7%', cpi: '0.7%' },
        ],
        US: [
            { id: 1, month: '2024-04', bond10y: '4.45%', currency: '105.2 (DXY)', m2: 'N/A', cpi: '3.5%' },
            { id: 2, month: '2024-03', bond10y: '4.20%', currency: '104.5 (DXY)', m2: 'N/A', cpi: '3.2%' },
        ]
    });

    // Sync Logic
    const [isSyncing, setIsSyncing] = useState(false);

    const handleSync = async () => {
        setIsSyncing(true);
        try {
            const res = await fetch('http://localhost:8000/api/sync-market', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ markets: ['CN', 'HK', 'US'] })
            });
            const data = await res.json();
            if (data.status === 'completed') {
                alert(`同步完成! \n详情: ${JSON.stringify(data.details, null, 2)}`);
            } else {
                alert('同步失败: ' + JSON.stringify(data));
            }
        } catch (err) {
            alert('同步请求失败: ' + err.message);
        } finally {
            setIsSyncing(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            animation: 'fadeIn 0.2s ease-out'
        }} onClick={onClose}>
            <div className="glass-panel" style={{
                width: '90%',
                maxWidth: '600px',
                padding: '1.5rem',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                background: '#18181b',
                maxHeight: '85vh',
                display: 'flex',
                flexDirection: 'column'
            }} onClick={e => e.stopPropagation()}>

                {/* Header with Tabs */}
                <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                        <h3 style={{ fontSize: '1.2rem', fontWeight: '600', margin: 0 }}>系统设置</h3>
                        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.5rem', lineHeight: 1 }}>&times;</button>
                    </div>

                    <div style={{ display: 'flex', gap: '2rem' }}>
                        {[{ id: 'params', label: '个性化参数' }, { id: 'macro', label: '宏观数据' }, { id: 'watchlist', label: '关注列表' }].map(tab => (
                            <div
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                style={{
                                    paddingBottom: '0.8rem',
                                    cursor: 'pointer',
                                    color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-secondary)',
                                    borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
                                    fontWeight: activeTab === tab.id ? '600' : 'normal',
                                    fontSize: '0.95rem',
                                    transition: 'var(--transition)'
                                }}
                            >
                                {tab.label}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Content Area */}
                <div style={{ flex: 1, overflowY: 'auto' }}>

                    {/* --- Tab 1: Parameters --- */}
                    {activeTab === 'params' && (
                        <div>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                                    股息率偏好 (%)
                                </label>
                                <input
                                    type="number"
                                    value={dividend}
                                    onChange={(e) => setDividend(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '0.75rem',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: 'var(--radius-sm)',
                                        color: '#fff',
                                        fontSize: '1rem'
                                    }}
                                />
                                <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                    设置高股息筛选的基准阈值。
                                </p>
                            </div>

                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                                    风险厌恶系数
                                </label>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    {['低', '中', '高'].map(level => (
                                        <button key={level} style={{
                                            flex: 1,
                                            padding: '0.5rem',
                                            border: '1px solid rgba(255,255,255,0.1)',
                                            borderRadius: 'var(--radius-sm)',
                                            background: 'rgba(255,255,255,0.02)',
                                            color: 'var(--text-secondary)',
                                            cursor: 'pointer',
                                            fontSize: '0.9rem'
                                        }}>
                                            {level}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* --- Tab 2: Macro Data --- */}
                    {activeTab === 'macro' && (
                        <div>
                            {/* Country Switch */}
                            <div style={{
                                display: 'flex',
                                background: 'rgba(255,255,255,0.05)',
                                padding: '4px',
                                borderRadius: 'var(--radius-md)',
                                marginBottom: '1.5rem',
                                width: 'fit-content'
                            }}>
                                {[{ id: 'CN', label: '🇨🇳 中国 (CN)' }, { id: 'US', label: '🇺🇸 美国 (US)' }].map(c => (
                                    <button
                                        key={c.id}
                                        onClick={() => setCountry(c.id)}
                                        style={{
                                            background: country === c.id ? 'rgba(255,255,255,0.1)' : 'transparent',
                                            color: country === c.id ? '#fff' : 'var(--text-secondary)',
                                            border: 'none',
                                            borderRadius: 'var(--radius-sm)',
                                            padding: '0.4rem 1rem',
                                            fontSize: '0.85rem',
                                            cursor: 'pointer',
                                            fontWeight: country === c.id ? '500' : 'normal',
                                            transition: 'var(--transition)'
                                        }}
                                    >
                                        {c.label}
                                    </button>
                                ))}
                            </div>

                            {/* Data Table */}
                            <div style={{ overflowX: 'auto', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 'var(--radius-sm)' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                    <thead style={{ background: 'rgba(255,255,255,0.03)' }}>
                                        <tr>
                                            <th style={{ padding: '0.8rem', textAlign: 'left', color: 'var(--text-secondary)' }}>月份</th>
                                            <th style={{ padding: '0.8rem', textAlign: 'right', color: 'var(--text-secondary)' }}>10年期国债</th>
                                            <th style={{ padding: '0.8rem', textAlign: 'right', color: 'var(--text-secondary)' }}>汇率/指数</th>
                                            <th style={{ padding: '0.8rem', textAlign: 'right', color: 'var(--text-secondary)' }}>{country === 'CN' ? 'M2增速' : 'M2'}</th>
                                            <th style={{ padding: '0.8rem', textAlign: 'right', color: 'var(--text-secondary)' }}>CPI</th>
                                            <th style={{ padding: '0.8rem', textAlign: 'center', color: 'var(--text-secondary)' }}>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {macroData[country].map((row) => (
                                            <tr key={row.id} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                                <td style={{ padding: '0.8rem', color: 'var(--text-primary)' }}>{row.month}</td>
                                                <td style={{ padding: '0.8rem', textAlign: 'right', color: '#fff', fontWeight: '500' }}>{row.bond10y}</td>
                                                <td style={{ padding: '0.8rem', textAlign: 'right', color: '#fff' }}>{row.currency}</td>
                                                <td style={{ padding: '0.8rem', textAlign: 'right', color: '#fff' }}>{row.m2}</td>
                                                <td style={{ padding: '0.8rem', textAlign: 'right', color: '#fff' }}>{row.cpi}</td>
                                                <td style={{ padding: '0.8rem', textAlign: 'center' }}>
                                                    <span style={{ color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.8rem' }}>编辑</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                                <button style={{
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px dashed rgba(255,255,255,0.2)',
                                    color: 'var(--text-secondary)',
                                    padding: '0.6rem 2rem',
                                    borderRadius: 'var(--radius-md)',
                                    cursor: 'pointer',
                                }}>
                                    添加新数据
                                </button>
                            </div>
                        </div>
                    )}


                    {/* --- Tab 3: Watchlist --- */}
                    {activeTab === 'watchlist' && (
                        <div>
                            <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>
                                    当前关注的标的列表。此处列表将包含自动添加和手动添加的标的。
                                </p>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '1rem' }}>
                                {watchlist.length === 0 ? (
                                    <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                                        暂无关注标的
                                    </div>
                                ) : (
                                    watchlist.map((item) => (
                                        <div
                                            key={item.id}
                                            className="watchlist-item-card"
                                            style={{
                                                background: 'rgba(255,255,255,0.05)',
                                                borderRadius: 'var(--radius-sm)',
                                                padding: '0.8rem',
                                                display: 'flex',
                                                flexDirection: 'column',
                                                justifyContent: 'space-between',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                position: 'relative',
                                                cursor: 'default'
                                            }}
                                            onMouseEnter={(e) => {
                                                const btn = e.currentTarget.querySelector('.delete-btn');
                                                if (btn) btn.style.display = 'block';
                                            }}
                                            onMouseLeave={(e) => {
                                                const btn = e.currentTarget.querySelector('.delete-btn');
                                                if (btn) btn.style.display = 'none';
                                            }}
                                        >
                                            <div style={{ marginBottom: '0.5rem' }}>
                                                <div style={{ fontSize: '1rem', fontWeight: '600', color: '#fff', marginBottom: '2px' }}>
                                                    {item.name}
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                                    {item.symbol}
                                                </div>
                                            </div>

                                            <div style={{ marginBottom: '0.5rem' }}>
                                                <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>
                                                    {item.price ? item.price.toFixed(2) : '-.--'}
                                                </span>
                                            </div>

                                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                                {item.market || 'Unknown'}
                                            </div>

                                            <button
                                                className="delete-btn"
                                                onClick={() => handleDeleteWatchlist(item.symbol)}
                                                style={{
                                                    display: 'none',
                                                    position: 'absolute',
                                                    top: '4px',
                                                    right: '4px',
                                                    background: 'rgba(0,0,0,0.6)',
                                                    border: 'none',
                                                    color: '#ef4444',
                                                    cursor: 'pointer',
                                                    fontSize: '0.9rem',
                                                    width: '24px',
                                                    height: '24px',
                                                    borderRadius: '4px',
                                                    display: 'none', // controlled by hover
                                                    alignItems: 'center',
                                                    justifyContent: 'center'
                                                }}
                                                title="删除"
                                            >
                                                ×
                                            </button>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>

                    {/* Manual Sync Button */}
                    <button
                        onClick={handleSync}
                        disabled={isSyncing}
                        style={{
                            padding: '0.6rem 1rem',
                            background: isSyncing ? 'rgba(255,255,255,0.05)' : 'rgba(59, 130, 246, 0.1)',
                            border: '1px solid rgba(59, 130, 246, 0.2)',
                            borderRadius: 'var(--radius-sm)',
                            color: isSyncing ? 'var(--text-muted)' : '#60a5fa',
                            cursor: isSyncing ? 'not-allowed' : 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        {isSyncing ? '正在同步...' : '🔄 手动同步行情'}
                    </button>

                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <button
                            onClick={onClose}
                            style={{
                                padding: '0.6rem 1.2rem',
                                background: 'transparent',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 'var(--radius-sm)',
                                color: 'var(--text-secondary)',
                                cursor: 'pointer'
                            }}
                        >
                            关闭
                        </button>
                        <button
                            onClick={() => { alert('设置已保存'); onClose(); }}
                            style={{
                                padding: '0.6rem 1.2rem',
                                background: 'var(--accent-primary)',
                                border: 'none',
                                borderRadius: 'var(--radius-sm)',
                                color: '#fff',
                                cursor: 'pointer',
                                fontWeight: '500'
                            }}
                        >
                            保存更改
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ConfigModal;
