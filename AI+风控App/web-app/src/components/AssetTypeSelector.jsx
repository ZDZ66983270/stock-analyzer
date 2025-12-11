import React, { useState } from 'react';

const types = ['股票', '股指', '国债', '基金', '贵金属', 'BTC', '衍生品'];

const AssetTypeSelector = () => {
    const [selected, setSelected] = useState(types[0]);

    return (
        <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.9rem', fontWeight: '500' }}>
                标的类型选择
            </label>
            <div className="glass-panel" style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '0.5rem',
                padding: '0.75rem',
                borderRadius: 'var(--radius-md)'
            }}>
                {types.map((type) => (
                    <button
                        key={type}
                        onClick={() => setSelected(type)}
                        style={{
                            flex: '1 0 auto',
                            padding: '0.5rem 1rem',
                            borderRadius: 'var(--radius-sm)',
                            border: 'none',
                            fontSize: '0.85rem',
                            cursor: 'pointer',
                            transition: 'var(--transition)',
                            backgroundColor: selected === type ? 'var(--accent-primary)' : 'transparent',
                            color: selected === type ? '#fff' : 'var(--text-secondary)',
                            fontWeight: selected === type ? '600' : '400'
                        }}
                    >
                        {type}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default AssetTypeSelector;
