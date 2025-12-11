import { useState } from 'react';

/**
 * 可折叠Section组件
 * 用于评估报告的分层展示
 */
function CollapsibleSection({
    title,
    children,
    defaultExpanded = true,
    icon = ''
}) {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    return (
        <div style={{
            marginBottom: '1rem',
            background: 'rgba(255,255,255,0.02)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid rgba(255,255,255,0.05)',
            overflow: 'hidden'
        }}>
            <div
                onClick={() => setIsExpanded(!isExpanded)}
                style={{
                    padding: '0.8rem 1rem',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: isExpanded ? 'rgba(255,255,255,0.03)' : 'transparent',
                    borderBottom: isExpanded ? '1px solid rgba(255,255,255,0.05)' : 'none',
                    transition: 'all 0.2s ease'
                }}
            >
                <h4 style={{
                    margin: 0,
                    fontSize: '0.95rem',
                    fontWeight: '600',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                }}>
                    {icon && <span>{icon}</span>}
                    {title}
                </h4>
                <span style={{
                    fontSize: '0.8rem',
                    color: 'var(--text-muted)',
                    transition: 'transform 0.2s ease',
                    transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)'
                }}>
                    ▼
                </span>
            </div>
            {isExpanded && (
                <div style={{
                    padding: '1rem',
                    animation: 'slideDown 0.2s ease-out'
                }}>
                    {children}
                </div>
            )}
        </div>
    );
}

export default CollapsibleSection;
