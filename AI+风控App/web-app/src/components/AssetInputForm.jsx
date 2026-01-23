import React, { useState } from 'react';
import SearchBar from './SearchBar';
import ImageUploadArea from './ImageUploadArea';
import AnalysisResult from './AnalysisResult';
import { analyzeAsset } from '../utils/mockAI';

const AssetInputForm = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [searchValue, setSearchValue] = useState('');

    const handleSubmit = async () => {
        setLoading(true);

        try {
            // New Robust Logic: Call Sync Fetch Endpoint
            // This endpoint adds to watchlist, fetches real data, saves to DB, and returns it.
            const res = await fetch('/api/fetch-stock', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: searchValue })
            });
            const resData = await res.json();

            let realData = [];
            let realName = null;
            let realSymbol = searchValue;

            if (resData.status === 'success') {
                realData = resData.data;
                if (resData.meta) {
                    realName = resData.meta.name;
                    realSymbol = resData.meta.symbol;
                }
            } else {
                console.warn("Fetch stock failed:", resData.message);
                // Try to add to watchlist anyway if fetch failed (fallback)
                // Actually the endpoint tries both. If it failed, maybe symbol invalid.
            }

            // Get Mock AI Analysis (Text)
            const mockData = await analyzeAsset(realSymbol);

            // Override with Real Info
            if (realName) {
                mockData.name = realName;
                mockData.symbol = realSymbol;
            } else if (mockData.name.includes('建设银行')) {
                // Formatting fallback
                mockData.name = realSymbol;
            }

            if (realData && realData.length > 0) {
                mockData.realHistory = realData;
            }

            setResult(mockData);

        } catch (e) {
            console.error("Error in submission flow", e);
            const data = await analyzeAsset(searchValue);
            setResult(data);
        }

        setLoading(false);
    };

    const handleReset = () => {
        setResult(null);
        setSearchValue('');
    };

    if (result) {
        return <AnalysisResult data={result} onReset={handleReset} />;
    }

    return (
        <div style={{ marginTop: '2rem' }}>
            <SearchBar value={searchValue} onChange={setSearchValue} />
            <ImageUploadArea />

            {/* Submit Area */}
            <div style={{ textAlign: 'center', marginTop: '3rem' }}>
                <button
                    onClick={handleSubmit}
                    disabled={loading}
                    style={{
                        background: loading ? 'var(--text-muted)' : 'var(--accent-primary)',
                        color: '#fff',
                        border: 'none',
                        padding: '1rem 3rem',
                        borderRadius: 'var(--radius-lg)',
                        fontSize: '1rem',
                        fontWeight: '600',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        boxShadow: loading ? 'none' : '0 4px 15px var(--accent-glow)',
                        transition: 'var(--transition)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}
                >
                    {loading ? (
                        <>
                            <span className="spinner"></span>
                            AI 识别中...
                        </>
                    ) : '提交'}
                </button>

                {!loading && (
                    <p style={{ marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        * 系统将自动识别您输入的代码或上传的截图
                    </p>
                )}
            </div>
        </div >
    );
};

export default AssetInputForm;
