import React, { useState, useEffect, useRef } from 'react';

const SearchBar = ({ value, onChange, onSelect, placeholder }) => {
    const [focus, setFocus] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [loading, setLoading] = useState(false);

    const timeoutRef = useRef(null);

    const fetchSuggestions = async (q) => {
        if (!q.trim()) {
            setSuggestions([]);
            return;
        }
        setLoading(true);
        console.log(`[SearchBar] Fetching suggestions for: ${q}`);
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=5`);
            const data = await res.json();
            if (data.status === 'success') {
                setSuggestions(data.data);
            }
        } catch (e) {
            console.error("[SearchBar] Search failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const input = e.target.value;
        if (onChange) onChange(input);
        setShowSuggestions(true);

        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => {
            fetchSuggestions(input);
        }, 300);
    };

    const handleSelectSuggestion = (item) => {
        console.log(`[SearchBar] Selected:`, item);
        if (onChange) onChange(item.symbol);
        if (onSelect) onSelect(item);
        setShowSuggestions(false);
        setSuggestions([]);
    };

    const handleBlur = () => {
        setTimeout(() => {
            setFocus(false);
            setShowSuggestions(false);
        }, 200);
    };

    const handleClear = () => {
        if (onChange) onChange('');
        setSuggestions([]);
        setShowSuggestions(false);
    };

    return (
        <div style={{ marginBottom: '1rem', position: 'relative', zIndex: 1000 }}>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.9rem', fontWeight: '500' }}>
                搜索标的 {loading && <span style={{ fontSize: '0.8rem', color: 'var(--accent-primary)' }}>(搜索中...)</span>}
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
                    position: 'relative',
                    background: 'rgba(0,0,0,0.3)'
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
                    placeholder={placeholder || "代码(600519) / 名称(茅台)"}
                    style={{
                        flex: 1,
                        background: 'transparent',
                        border: 'none',
                        color: '#fff',
                        padding: '1rem 0.75rem',
                        fontSize: '1rem',
                        outline: 'none',
                        fontFamily: 'inherit'
                    }}
                    onFocus={() => { setFocus(true); setShowSuggestions(true); }}
                    onBlur={handleBlur}
                />
                {value && (
                    <button
                        onClick={handleClear}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--text-tertiary)',
                            cursor: 'pointer',
                            padding: '0.25rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            transition: 'color 0.2s',
                            zIndex: 10
                        }}
                        onMouseEnter={(e) => e.target.style.color = 'var(--text-primary)'}
                        onMouseLeave={(e) => e.target.style.color = 'var(--text-tertiary)'}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                )}
            </div>

            {/* Suggestions Dropdown */}
            {showSuggestions && suggestions.length > 0 && (
                <ul style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    marginTop: '0.5rem',
                    background: '#27272a',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: 'var(--radius-md)',
                    zIndex: 9999,
                    boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                    overflow: 'hidden',
                    maxHeight: '300px',
                    overflowY: 'auto',
                    listStyle: 'none',
                    padding: 0,
                    margin: 0
                }}>
                    {suggestions.map((item, index) => (
                        <li
                            key={index}
                            onClick={() => handleSelectSuggestion(item)}
                            style={{
                                padding: '0.75rem 1rem',
                                borderBottom: index < suggestions.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                cursor: 'pointer',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                color: '#fff',
                                transition: 'background 0.2s'
                            }}
                            className="search-item"
                            onMouseEnter={(e) => e.currentTarget.style.background = '#3f3f46'}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontWeight: '500' }}>{item.name}</span>
                                <span style={{
                                    fontSize: '0.8rem',
                                    color: '#fff',
                                    background: 'var(--accent-primary)',
                                    padding: '2px 4px',
                                    borderRadius: '4px',
                                    opacity: 0.8
                                }}>
                                    {item.market}
                                </span>
                            </div>
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                {(item.symbol || '').replace(/\.OQ$|\.N$|\.QQ$/i, '')}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default SearchBar;
