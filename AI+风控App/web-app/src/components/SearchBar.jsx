import React, { useState, useEffect } from 'react';

// Mock database for valid asset codes
const ASSET_DB = {
    '600519': '贵州茅台',
    '000001': '平安银行',
    '300750': '宁德时代',
    '700': '腾讯控股',
    'BABA': '阿里巴巴',
    'AAPL': 'Apple Inc.',
    'TSLA': 'Tesla',
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum'
};

const SearchBar = ({ value, onChange }) => {
    const [focus, setFocus] = useState(false);
    const [match, setMatch] = useState('');

    const handleChange = (e) => {
        const input = e.target.value;
        if (onChange) onChange(input);

        // Simple exact match logic (case-insensitive for letters)
        const upperInput = input.toUpperCase();
        if (ASSET_DB[input]) {
            setMatch(ASSET_DB[input]);
        } else if (ASSET_DB[upperInput]) {
            setMatch(ASSET_DB[upperInput]);
        } else {
            setMatch('');
        }
    };

    // Also clear match if value is empty/controlled from outside match
    useEffect(() => {
        if (!value) setMatch('');
    }, [value]);

    return (
        <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.9rem', fontWeight: '500' }}>
                搜索栏 (核心输入)
            </label>
            <div
                className="glass-panel"
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '0.25rem 1rem',
                    borderRadius: 'var(--radius-lg)',
                    borderColor: focus ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)',
                    boxShadow: focus ? `0 0 0 1px var(--accent-primary), 0 0 15px -3px var(--accent-glow)` : '',
                    transition: 'var(--transition)',
                    position: 'relative'
                }}
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8"></circle>
                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input
                    type="text"
                    value={value}
                    onChange={handleChange}
                    placeholder="请输入代码 / 名称 (如: 600519)"
                    style={{
                        flex: 1,
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-primary)',
                        padding: '1rem 0.75rem',
                        fontSize: '1rem',
                        outline: 'none',
                        fontFamily: 'inherit'
                    }}
                    onFocus={() => setFocus(true)}
                    onBlur={() => setFocus(false)}
                />

                {/* Auto-match Badge */}
                {match && (
                    <div style={{
                        padding: '4px 12px',
                        background: 'rgba(16, 185, 129, 0.2)', // Greenish tint
                        color: '#34d399',
                        borderRadius: '20px',
                        fontSize: '0.85rem',
                        fontWeight: '600',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        animation: 'fadeIn 0.3s ease-out'
                    }}>
                        <span>✓</span> {match}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SearchBar;
