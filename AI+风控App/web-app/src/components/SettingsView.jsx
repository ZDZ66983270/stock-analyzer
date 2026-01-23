import React, { useState, useEffect } from 'react';
import { getColorConvention, setColorConvention } from '../utils/colorUtils';

const SettingsView = () => {
    const [activeTab, setActiveTab] = useState('params');
    const [dividend, setDividend] = useState('2.5');
    const [colorConvention, setColorConventionState] = useState('chinese');

    // System Logs State
    const [logs, setLogs] = useState([]);
    const [logLevel, setLogLevel] = useState('');
    const [logSearch, setLogSearch] = useState('');
    const [isLoadingLogs, setIsLoadingLogs] = useState(false);

    // Load color convention from localStorage on mount
    useEffect(() => {
        const savedConvention = getColorConvention();
        setColorConventionState(savedConvention);
    }, []);

    // Load logs when logs tab is active
    useEffect(() => {
        if (activeTab === 'logs') {
            loadLogs();
        }
    }, [activeTab, logLevel, logSearch]);

    const loadLogs = async () => {
        setIsLoadingLogs(true);
        try {
            const params = new URLSearchParams({
                limit: '100',
                ...(logLevel && { level: logLevel }),
                ...(logSearch && { search: logSearch })
            });

            const res = await fetch(`/api/admin/logs?${params}`);
            const data = await res.json();
            if (data.status === 'success') {
                setLogs(data.logs);
            }
        } catch (err) {
            console.error('Failed to load logs:', err);
        } finally {
            setIsLoadingLogs(false);
        }
    };

    const handleColorConventionChange = (convention) => {
        setColorConventionState(convention);
        setColorConvention(convention);
        // Trigger a page reload to apply changes
        window.location.reload();
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

    const [isSyncing, setIsSyncing] = useState(false);

    const handleSync = async () => {
        setIsSyncing(true);
        try {
            const res = await fetch('/api/sync-market', {
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

    const getLevelColor = (level) => {
        switch (level) {
            case 'ERROR': return '#ef4444';
            case 'WARNING': return '#f59e0b';
            case 'INFO': return '#3b82f6';
            case 'DEBUG': return '#8b5cf6';
            default: return '#fff';
        }
    };

    return (
        <div style={{ paddingLeft: '0', paddingRight: '0', paddingTop: 'max(1rem, env(safe-area-inset-top))', paddingBottom: '6rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>设置</h2>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                {[
                    { id: 'params', label: '个性化参数' },
                    { id: 'macro', label: '宏观数据' },
                    { id: 'logs', label: '系统日志' }
                ].map(tab => (
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

            {/* --- Tab 1: Parameters --- */}
            {activeTab === 'params' && (
                <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
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
                                    padding: '0.8rem',
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

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                            颜色习惯
                        </label>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                                onClick={() => handleColorConventionChange('chinese')}
                                style={{
                                    flex: 1,
                                    padding: '0.8rem',
                                    border: `1px solid ${colorConvention === 'chinese' ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)'}`,
                                    borderRadius: 'var(--radius-sm)',
                                    background: colorConvention === 'chinese' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(255,255,255,0.02)',
                                    color: colorConvention === 'chinese' ? '#fff' : 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    fontSize: '0.9rem'
                                }}
                            >
                                🇨🇳 中国习惯
                                <div style={{ fontSize: '0.7rem', marginTop: '0.3rem', opacity: 0.7 }}>
                                    红涨绿跌
                                </div>
                            </button>
                            <button
                                onClick={() => handleColorConventionChange('us')}
                                style={{
                                    flex: 1,
                                    padding: '0.8rem',
                                    border: `1px solid ${colorConvention === 'us' ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)'}`,
                                    borderRadius: 'var(--radius-sm)',
                                    background: colorConvention === 'us' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.02)',
                                    color: colorConvention === 'us' ? '#fff' : 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    fontSize: '0.9rem'
                                }}
                            >
                                🇺🇸 美国习惯
                                <div style={{ fontSize: '0.7rem', marginTop: '0.3rem', opacity: 0.7 }}>
                                    绿涨红跌
                                </div>
                            </button>
                        </div>
                        <p style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            选择价格涨跌的颜色显示习惯，更改后将自动刷新页面。
                        </p>
                    </div>

                    <div style={{ marginTop: '2rem' }}>
                        <button
                            onClick={() => alert('参数已保存')}
                            style={{
                                width: '100%',
                                padding: '0.8rem',
                                background: 'var(--accent-primary)',
                                color: '#fff',
                                border: 'none',
                                borderRadius: 'var(--radius-sm)',
                                fontWeight: 'bold',
                                cursor: 'pointer'
                            }}>
                            保存更改
                        </button>
                    </div>
                </div>
            )}

            {/* --- Tab 2: Macro Data --- */}
            {activeTab === 'macro' && (
                <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
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
                                    <th style={{ padding: '0.8rem', textAlign: 'right', color: 'var(--text-secondary)' }}>10y债</th>
                                    <th style={{ padding: '0.8rem', textAlign: 'right', color: 'var(--text-secondary)' }}>汇率</th>
                                </tr>
                            </thead>
                            <tbody>
                                {macroData[country].map((row) => (
                                    <tr key={row.id} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '0.8rem', color: 'var(--text-primary)' }}>{row.month}</td>
                                        <td style={{ padding: '0.8rem', textAlign: 'right', color: '#fff', fontWeight: '500' }}>{row.bond10y}</td>
                                        <td style={{ padding: '0.8rem', textAlign: 'right', color: '#fff' }}>{row.currency}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div style={{ marginTop: '1.5rem' }}>
                        <button
                            onClick={handleSync}
                            disabled={isSyncing}
                            style={{
                                width: '100%',
                                padding: '0.8rem',
                                background: isSyncing ? 'rgba(255,255,255,0.05)' : 'rgba(59, 130, 246, 0.1)',
                                border: '1px solid rgba(59, 130, 246, 0.2)',
                                borderRadius: 'var(--radius-sm)',
                                color: isSyncing ? 'var(--text-muted)' : '#60a5fa',
                                cursor: isSyncing ? 'not-allowed' : 'pointer',
                                fontSize: '0.9rem'
                            }}
                        >
                            {isSyncing ? '正在同步...' : '🔄 手动同步行情'}
                        </button>
                    </div>
                </div>
            )}

            {/* --- Tab 3: System Logs --- */}
            {activeTab === 'logs' && (
                <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                    {/* Filters */}
                    <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <select
                            value={logLevel}
                            onChange={(e) => setLogLevel(e.target.value)}
                            style={{
                                padding: '0.6rem',
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 'var(--radius-sm)',
                                color: '#fff',
                                fontSize: '0.85rem',
                                cursor: 'pointer'
                            }}
                        >
                            <option value="">所有级别</option>
                            <option value="DEBUG">DEBUG</option>
                            <option value="INFO">INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                        </select>

                        <input
                            type="text"
                            value={logSearch}
                            onChange={(e) => setLogSearch(e.target.value)}
                            placeholder="搜索日志..."
                            style={{
                                flex: 1,
                                minWidth: '200px',
                                padding: '0.6rem',
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 'var(--radius-sm)',
                                color: '#fff',
                                fontSize: '0.85rem'
                            }}
                        />

                        <button
                            onClick={loadLogs}
                            disabled={isLoadingLogs}
                            style={{
                                padding: '0.6rem 1.2rem',
                                background: 'rgba(59, 130, 246, 0.1)',
                                border: '1px solid rgba(59, 130, 246, 0.2)',
                                borderRadius: 'var(--radius-sm)',
                                color: '#60a5fa',
                                cursor: isLoadingLogs ? 'not-allowed' : 'pointer',
                                fontSize: '0.85rem'
                            }}
                        >
                            {isLoadingLogs ? '⏳' : '🔄'}
                        </button>
                    </div>

                    {/* Logs Display */}
                    <div style={{
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '1rem',
                        maxHeight: '500px',
                        overflowY: 'auto',
                        fontFamily: 'SF Mono, Monaco, monospace'
                    }}>
                        {logs.length === 0 ? (
                            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                                {isLoadingLogs ? '加载中...' : '暂无日志'}
                            </div>
                        ) : (
                            logs.map((log, index) => (
                                <div
                                    key={index}
                                    style={{
                                        padding: '0.5rem',
                                        marginBottom: '0.5rem',
                                        borderLeft: `3px solid ${getLevelColor(log.level)}`,
                                        background: 'rgba(255,255,255,0.02)',
                                        borderRadius: '4px',
                                        fontSize: '0.75rem'
                                    }}
                                >
                                    <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.25rem' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>{log.timestamp}</span>
                                        <span
                                            style={{
                                                color: getLevelColor(log.level),
                                                fontWeight: 'bold',
                                                minWidth: '60px'
                                            }}
                                        >
                                            {log.level}
                                        </span>
                                        <span style={{ color: 'var(--text-secondary)' }}>[{log.module}]</span>
                                    </div>
                                    <div style={{ color: '#fff', marginLeft: '1rem', wordBreak: 'break-word' }}>
                                        {log.message}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        显示最近 {logs.length} 条日志
                    </div>
                </div>
            )}
        </div>
    );
};

export default SettingsView;
