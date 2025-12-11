import React, { useState } from 'react';

const SwipeableItem = ({ children, onDelete, onClick }) => {
    const [startX, setStartX] = useState(0);
    const [currentX, setCurrentX] = useState(0);
    const [isSwiping, setIsSwiping] = useState(false);
    const maxSwipe = 80;

    const handleStart = (clientX) => {
        setStartX(clientX);
        setIsSwiping(false);
    };

    const handleMove = (clientX) => {
        const diff = startX - clientX;

        if (diff > 5) setIsSwiping(true);

        if (diff >= 0 && diff <= maxSwipe + 20) {
            setCurrentX(-diff);
        }
    };

    const handleEnd = () => {
        if (Math.abs(currentX) > maxSwipe / 2) {
            setCurrentX(-maxSwipe);
        } else {
            setCurrentX(0);
        }
        setTimeout(() => setIsSwiping(false), 100);
    };

    const handleClick = (e) => {
        console.log('SwipeableItem clicked, isSwiping:', isSwiping, 'currentX:', currentX);
        if (!isSwiping && currentX === 0) {
            console.log('Calling onClick');
            onClick?.(e);
        } else {
            console.log('Click blocked - isSwiping or swiped');
        }
    };

    return (
        <div style={{ position: 'relative', overflow: 'hidden', borderRadius: 'var(--radius-md)' }}>
            {/* Delete Button - Behind everything */}
            <div
                onClick={(e) => {
                    e.stopPropagation();
                    onDelete?.();
                }}
                style={{
                    position: 'absolute',
                    right: 0,
                    top: 0,
                    bottom: 0,
                    width: maxSwipe + 'px',
                    background: '#ef4444',
                    color: '#fff',
                    border: 'none',
                    fontSize: '0.9rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}
            >
                删除
            </div>

            {/* Content - Slides over delete button */}
            <div
                onTouchStart={(e) => handleStart(e.targetTouches[0].clientX)}
                onTouchMove={(e) => handleMove(e.targetTouches[0].clientX)}
                onTouchEnd={handleEnd}
                onMouseDown={(e) => handleStart(e.clientX)}
                onMouseMove={(e) => e.buttons === 1 && handleMove(e.clientX)}
                onMouseUp={handleEnd}
                onMouseLeave={handleEnd}
                onClick={handleClick}
                style={{
                    transform: `translateX(${currentX}px)`,
                    transition: isSwiping ? 'none' : 'transform 0.3s ease-out',
                    position: 'relative',
                    background: '#18181b',  // Solid background to hide delete button
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer'
                }}
            >
                {children}
            </div>
        </div>
    );
};

export default SwipeableItem;
