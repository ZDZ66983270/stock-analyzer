import React from 'react';

const AppLayout = ({ children }) => {
    return (
        <div className="min-h-screen container" style={{ paddingTop: '2rem', paddingBottom: '4rem' }}>
            {children}
        </div>
    );
};

export default AppLayout;
