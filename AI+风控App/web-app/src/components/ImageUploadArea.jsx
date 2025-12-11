import React, { useState, useRef } from 'react';

const ImageUploadArea = () => {
    const [images, setImages] = useState([]);
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            const newImages = files.map(file => ({
                url: URL.createObjectURL(file), // Create local preview URL
                file
            }));
            setImages(prev => [...prev, ...newImages]);
        }
    };

    const removeImage = (index) => {
        setImages(prev => prev.filter((_, i) => i !== index));
    };

    const triggerUpload = () => {
        fileInputRef.current.click();
    };

    return (
        <div style={{ marginBottom: '2rem' }}>
            <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.9rem', fontWeight: '500' }}>
                上传行情截图 (支持多图)
            </label>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))',
                gap: '0.75rem'
            }}>
                {/* Existing Images */}
                {images.map((img, index) => (
                    <div key={index} style={{
                        position: 'relative',
                        aspectRatio: '1',
                        borderRadius: 'var(--radius-sm)',
                        overflow: 'hidden',
                        border: '1px solid rgba(255,255,255,0.1)'
                    }}>
                        <img
                            src={img.url}
                            alt="preview"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                        <button
                            onClick={() => removeImage(index)}
                            style={{
                                position: 'absolute',
                                top: '2px',
                                right: '2px',
                                background: 'rgba(0,0,0,0.6)',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '50%',
                                width: '18px',
                                height: '18px',
                                fontSize: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer'
                            }}
                        >
                            ×
                        </button>
                    </div>
                ))}

                {/* Add Button */}
                <div
                    onClick={triggerUpload}
                    className="glass-panel"
                    style={{
                        aspectRatio: '1',
                        borderRadius: 'var(--radius-sm)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        transition: 'var(--transition)',
                        borderStyle: 'dashed',
                        borderColor: 'rgba(255,255,255,0.2)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
                    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)'}
                >
                    <span style={{ fontSize: '1.5rem', color: 'var(--text-secondary)' }}>+</span>
                </div>
            </div>

            <input
                type="file"
                multiple
                accept="image/*"
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileChange}
            />
        </div>
    );
};

export default ImageUploadArea;
