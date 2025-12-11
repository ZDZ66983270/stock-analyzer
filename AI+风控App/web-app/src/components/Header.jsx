import React from 'react';

const Header = ({ onOpenConfig }) => {
    return (
        <header style={{
            marginBottom: '2.5rem',
            textAlign: 'center',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        }}>
            <div>
                <h1 style={{
                    fontSize: '1.75rem',
                    fontWeight: '800',
                    letterSpacing: '-0.5px',
                    background: 'linear-gradient(to right, #fff, #a1a1aa)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                }}>
                    笨 AI 投资风险评价
                </h1>
                <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    智能分析 · 风险量化 · 策略优化
                </p>
            </div>

            {/* Left Actions Group */}
            <div style={{ position: 'absolute', left: 0, top: '10px', display: 'flex', gap: '0.5rem' }}>
                <button
                    onClick={onOpenConfig}
                    style={{
                        background: 'rgba(255, 255, 255, 0.05)',
                        color: 'var(--text-secondary)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        borderRadius: '20px',
                        padding: '0.4rem 0.8rem',
                        fontSize: '0.85rem',
                        fontWeight: '500',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        transition: 'var(--transition)'
                    }}
                >
                    <span style={{ fontSize: '1.1em' }}>⚙️</span> 设置
                </button>
            </div>

            <button style={{
                position: 'absolute',
                right: 0,
                top: '10px', // Adjusted for better visual alignment on mobile/desktop
                background: 'linear-gradient(135deg, var(--accent-primary), #60a5fa)',
                color: '#fff',
                border: 'none',
                borderRadius: '20px',
                padding: '0.5rem 1rem',
                fontSize: '0.85rem',
                fontWeight: '600',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(59, 130, 246, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'var(--transition)'
            }}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
                <span style={{ fontSize: '1.1em' }}>✨</span> AI 话痨
            </button>
        </header >
    );
};

export default Header;
