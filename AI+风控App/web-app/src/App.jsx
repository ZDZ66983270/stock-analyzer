import React, { useState } from 'react';
import AppLayout from './components/AppLayout';
import HomeView from './components/HomeView';
import StockDetailView from './components/StockDetailView';
import FundDetailView from './components/FundDetailView';
import ConfigModal from './components/ConfigModal';
import SettingsView from './components/SettingsView';

const App = () => {
    // View State
    const [currentView, setCurrentView] = useState('home'); // 'home' | 'detail'
    const [activeTab, setActiveTab] = useState('watchlist'); // 'watchlist' | 'settings'

    // Data State
    const [selectedAsset, setSelectedAsset] = useState(null);

    const handleSelectAsset = (asset) => {
        setSelectedAsset(asset);
        setCurrentView('detail');
    };

    const handleBack = () => {
        setCurrentView('home');
        setSelectedAsset(null);
    };

    // Render Content based on View & Tab
    const renderContent = () => {
        if (currentView === 'detail') {
            // Route to different detail views based on asset type
            if (selectedAsset?.type === 'fund') {
                return <FundDetailView asset={selectedAsset} onBack={handleBack} />;
            }
            // Default to stock detail view
            return <StockDetailView asset={selectedAsset} onBack={handleBack} />;
        }

        // Home View (Tabbed)
        switch (activeTab) {
            case 'settings':
                return <SettingsView />;
            case 'watchlist':
            default:
                return <HomeView onSelectAsset={handleSelectAsset} />;
        }
    };

    return (
        <div style={{
            maxWidth: '1200px',
            margin: '0 auto',
            minHeight: '100vh',
            paddingBottom: currentView === 'home' ? '60px' : '0' // Space for bottom tab
        }}>
            {/* Top Bar Removed per user request */}

            {/* Main Content Area */}
            <div style={{ minHeight: '90vh' }}>
                {renderContent()}
            </div>

            {/* Bottom Tab Bar (Only visible in Home View) */}
            {currentView === 'home' && (
                <div style={{
                    position: 'fixed',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: '60px',
                    background: '#18181b', // var(--card-bg)
                    borderTop: '1px solid rgba(255,255,255,0.1)',
                    display: 'flex',
                    justifyContent: 'space-around',
                    alignItems: 'center',
                    zIndex: 1000,
                    // Constrain width for desktop
                    maxWidth: '1200px', // Match app max-width if centered, but usually fixed works relative to viewport. 
                    // To handle max-width centering correctly for fixed element:
                    // We can wrap content or just let it span full width which is standard for mobile apps.
                    // But if app is constrained to 480px on desktop (via index.css), we should respect that.
                    // index.css handles mobile constraint. global .root or .app container usually.
                    // If #root has max-width, Fixed position breaks out of it unless strict.
                    // Let's assume standard mobile behavior (full width fixed).
                }}>
                    <div
                        onClick={() => setActiveTab('watchlist')}
                        style={{
                            flex: 1,
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            alignItems: 'center',
                            cursor: 'pointer',
                            color: activeTab === 'watchlist' ? 'var(--accent-primary)' : 'var(--text-secondary)'
                        }}
                    >
                        <span style={{ fontSize: '1.2rem', marginBottom: '2px' }}>📊</span>
                        <span style={{ fontSize: '0.75rem' }}>自选</span>
                    </div>

                    <div
                        onClick={() => setActiveTab('settings')}
                        style={{
                            flex: 1,
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            alignItems: 'center',
                            cursor: 'pointer',
                            color: activeTab === 'settings' ? 'var(--accent-primary)' : 'var(--text-secondary)'
                        }}
                    >
                        <span style={{ fontSize: '1.2rem', marginBottom: '2px' }}>⚙️</span>
                        <span style={{ fontSize: '0.75rem' }}>设置</span>
                    </div>
                </div>
            )}

            {/* Global Modals (Optional, ConfigModal logic moved to SettingsView, but others might exist) */}
        </div>
    );
};

export default App;
