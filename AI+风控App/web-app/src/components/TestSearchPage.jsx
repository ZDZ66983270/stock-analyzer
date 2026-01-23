import React, { useState } from 'react';
import SearchBar from './SearchBar';

const TestSearchPage = () => {
    const [lastSelected, setLastSelected] = useState(null);
    const [currentValue, setCurrentValue] = useState('');

    return (
        <div style={{
            minHeight: '100vh',
            background: '#18181b', // dark bg
            color: '#fff',
            padding: '2rem',
            fontFamily: 'system-ui, sans-serif'
        }}>
            <h1 style={{ borderBottom: '1px solid #333', paddingBottom: '1rem', marginBottom: '2rem' }}>
                🧪 搜索组件测试实验室
            </h1>

            <div style={{ maxWidth: '600px', margin: '0 auto' }}>
                {/* Search Component Container */}
                <div style={{
                    background: '#27272a',
                    padding: '2rem',
                    borderRadius: '12px',
                    border: '1px solid #3f3f46'
                }}>
                    <SearchBar
                        value={currentValue}
                        onChange={setCurrentValue}
                        onSelect={(item) => {
                            console.log("TestPage Selected:", item);
                            setLastSelected(item);
                            setCurrentValue(item.symbol);
                        }}
                    />
                </div>

                {/* Result Display */}
                <div style={{ marginTop: '2rem' }}>
                    <h3>调试信息 / Debug Info:</h3>
                    <div style={{
                        background: '#000',
                        padding: '1rem',
                        borderRadius: '8px',
                        fontFamily: 'monospace',
                        color: '#4ade80'
                    }}>
                        <div>Current Input: "{currentValue}"</div>
                        <div style={{ marginTop: '0.5rem' }}>
                            Last Selected:
                            <pre>{JSON.stringify(lastSelected, null, 2)}</pre>
                        </div>
                    </div>
                </div>

                <div style={{ marginTop: '2rem', color: '#71717a', fontSize: '0.9rem' }}>
                    * 如果在这里能够正常使用，说明组件逻辑正常，问题可能出在主页面的布局覆盖上。
                </div>
            </div>
        </div>
    );
};

export default TestSearchPage;
