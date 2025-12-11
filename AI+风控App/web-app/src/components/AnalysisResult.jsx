import React, { useState } from 'react';

const ResultItem = ({ label, value, highlight = false, isEditing = false, onChange }) => (
    <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.75rem 0',
        borderBottom: '1px solid rgba(255,255,255,0.05)'
    }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{label}</span>
        {isEditing && onChange ? (
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                style={{
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '4px',
                    color: '#fff',
                    padding: '2px 6px',
                    textAlign: 'right',
                    width: '60%'
                }}
            />
        ) : (
            <span style={{
                color: highlight ? 'var(--accent-primary)' : 'var(--text-primary)',
                fontWeight: highlight ? '700' : '500',
                fontSize: highlight ? '1.1rem' : '1rem'
            }}>
                {value}
            </span>
        )}
    </div>
);

const operations = ['建仓', '加仓', '持有', '减仓', '平仓'];
const AnalysisResult = ({ data: initialData, onReset }) => {
    const [selectedOp, setSelectedOp] = useState(null);
    const [localData, setLocalData] = useState(initialData);
    const [isEditing, setIsEditing] = useState(false);

    // Configuration State for Operation
    const [selectedModels, setSelectedModels] = useState(['technical', 'flow']); // Default selected
    const [analysisOptions, setAnalysisOptions] = useState({
        sectorCycle: true,
        macroCycle: false
    });

    const availableModels = [
        { id: 'dagnino', label: 'Dagnino 周期模型' },
        { id: 'technical', label: '多周期技术趋势' },
        { id: 'flow', label: '主力资金流向' },
        { id: 'fundamental', label: '基本面价值' }
    ];

    const toggleModel = (id) => {
        if (selectedModels.includes(id)) {
            setSelectedModels(selectedModels.filter(m => m !== id));
        } else {
            setSelectedModels([...selectedModels, id]);
        }
    };

    // Update localData when initialData changes (e.g. re-analysis)
    React.useEffect(() => {
        setLocalData(initialData);
    }, [initialData]);

    const handleEditChange = (field, value) => {
        setLocalData(prev => ({ ...prev, [field]: value }));
    };

    if (!localData) return null;

    // Use localData for display
    const data = localData;

    // Override with Real Data if available
    if (data.realHistory && data.realHistory.length > 0) {
        const latest = data.realHistory[data.realHistory.length - 1];
        data.price = latest.close.toFixed(2);
        data.volume = (latest.volume / 10000).toFixed(1) + '万';
        // data.name = data.symbol; // Or keep mock name if real name fetch failed
    }

    // Dynamically derive periods from the returned technical data
    // If no technicals, validPeriods will be empty.
    const validPeriods = data.technicals ? Object.keys(data.technicals) : [];

    return (
        <div className="glass-panel" style={{
            padding: '1.5rem',
            borderRadius: 'var(--radius-lg)',
            marginTop: '2rem',
            animation: 'fadeIn 0.5s ease-out'
        }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1.5rem'
            }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: '600' }}>✨ AI 分析结果</h3>
                <span style={{ fontSize: '0.8rem', marginRight: '0.5rem', color: isEditing ? 'var(--accent-primary)' : 'var(--text-secondary)', cursor: 'pointer' }} onClick={() => setIsEditing(!isEditing)}>
                    {isEditing ? '完成' : '编辑'}
                </span>
                <span style={{
                    fontSize: '0.75rem',
                    background: 'rgba(59, 130, 246, 0.15)',
                    color: '#60a5fa',
                    padding: '2px 8px',
                    borderRadius: '4px'
                }}>
                    已识别
                </span>
            </div>

            {/* Top Section: Basic Info & Core Data */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '2rem', marginBottom: '2rem' }}>
                {/* Basic Info */}
                <div>
                    <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>基本信息</h4>
                    <ResultItem label="资产名称" value={data.name} highlight isEditing={isEditing} onChange={(v) => handleEditChange('name', v)} />
                    {data.symbol && data.symbol !== data.name && (
                        <ResultItem label="资产代码" value={data.symbol} isEditing={isEditing} onChange={(v) => handleEditChange('symbol', v)} />
                    )}
                    <ResultItem label="当前价格" value={data.price} highlight isEditing={isEditing} onChange={(v) => handleEditChange('price', v)} />
                    <ResultItem
                        label="资产类别"
                        value={
                            Array.isArray(data.category)
                                ? (
                                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                        {data.category.map((tag, i) => (
                                            <span key={i} style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                )
                                : data.category
                        }
                        isEditing={isEditing}
                        onChange={(v) => handleEditChange('category', v.split(/[,，]/).map(s => s.trim()).filter(Boolean))}
                    />
                    <ResultItem label="交易市场" value={data.market} isEditing={isEditing} onChange={(v) => handleEditChange('market', v)} />
                    <ResultItem label="计价货币" value={data.currency} isEditing={isEditing} onChange={(v) => handleEditChange('currency', v)} />
                    <ResultItem label="52周最高" value={data.high52w} isEditing={isEditing} onChange={(v) => handleEditChange('high52w', v)} />
                </div>

                {/* Core Stats */}
                <div>
                    <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px' }}>核心数据</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>成交量</div>
                            <div style={{ fontWeight: '600', marginTop: '4px' }}>{data.volume}</div>
                        </div>
                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>换手率</div>
                            <div style={{ fontWeight: '600', marginTop: '4px' }}>{data.turnover}</div>
                        </div>
                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>市盈率</div>
                            <div style={{ fontWeight: '600', marginTop: '4px' }}>{data.pe}</div>
                        </div>
                        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>股息率</div>
                            <div style={{ fontWeight: '600', marginTop: '4px' }}>{data.dividend}</div>
                        </div>
                        {/* Chips Integated Here */}
                        {data.chips && (
                            <div style={{ gridColumn: 'span 2', background: 'rgba(59, 130, 246, 0.1)', padding: '1rem', borderRadius: 'var(--radius-sm)', textAlign: 'center', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                                <div style={{ fontSize: '0.8rem', color: '#60a5fa', marginBottom: '4px' }}>筹码分布 (日线)</div>
                                <div style={{ fontWeight: '600', color: '#fff' }}>{data.chips}</div>
                            </div>
                        )}
                    </div>
                </div>
            </div>



            {/* Capital Flow */}
            <div style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', margin: 0 }}>资金流向</h4>
                    <span style={{ color: data.flow?.total?.includes('+') ? '#ef4444' : '#10b981', fontSize: '1rem', fontWeight: '500' }}>
                        整体净流: {data.flow?.total}
                    </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
                    {[
                        { label: '特大单', value: data.flow?.super },
                        { label: '大单', value: data.flow?.large },
                        { label: '中单', value: data.flow?.medium },
                        { label: '小单', value: data.flow?.small },
                    ].map((item) => (
                        <div key={item.label} style={{
                            background: 'rgba(255,255,255,0.03)',
                            padding: '0.75rem 0.5rem',
                            borderRadius: 'var(--radius-sm)',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>{item.label}</div>
                            <div style={{
                                fontSize: '0.9rem',
                                fontWeight: '600',
                                color: item.value?.includes('+') ? '#ef4444' : (item.value?.includes('-') ? '#10b981' : 'var(--text-primary)')
                            }}>
                                {item.value}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Multi-Day Flow */}
                {data.flow?.multiDay && (
                    <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', padding: '0.8rem', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-sm)' }}>
                        {Object.entries(data.flow.multiDay).map(([label, value]) => (
                            <div key={label} style={{ textAlign: 'center' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginRight: '6px' }}>{label}</span>
                                <span style={{
                                    fontWeight: '600',
                                    fontSize: '0.9rem',
                                    color: value?.includes('+') ? '#ef4444' : (value?.includes('-') ? '#10b981' : 'var(--text-primary)')
                                }}>{value}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>




            {/* Real History Data */}
            {data.realHistory && (
                <div style={{ marginBottom: '2rem' }}>
                    <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        近期行情 (Real Market Data)
                    </h4>
                    <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 'var(--radius-sm)' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'right' }}>
                            <thead style={{ position: 'sticky', top: 0, background: '#1c1c1e', zIndex: 1 }}>
                                <tr>
                                    <th style={{ padding: '8px', textAlign: 'left', color: 'var(--text-secondary)' }}>日期</th>
                                    <th style={{ padding: '8px', color: 'var(--text-secondary)' }}>开盘</th>
                                    <th style={{ padding: '8px', color: 'var(--text-secondary)' }}>收盘</th>
                                    <th style={{ padding: '8px', color: 'var(--text-secondary)' }}>最高</th>
                                    <th style={{ padding: '8px', color: 'var(--text-secondary)' }}>最低</th>
                                    <th style={{ padding: '8px', color: 'var(--text-secondary)' }}>成交量</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[...data.realHistory].reverse().map((row, idx) => (
                                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                        <td style={{ padding: '8px', textAlign: 'left', color: 'var(--text-primary)' }}>{row.date.split(' ')[0]}</td>
                                        <td style={{ padding: '8px' }}>{row.open}</td>
                                        <td style={{ padding: '8px', fontWeight: 'bold' }}>{row.close}</td>
                                        <td style={{ padding: '8px' }}>{row.high}</td>
                                        <td style={{ padding: '8px' }}>{row.low}</td>
                                        <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>{row.volume}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}


            {/* Multi-Period Technicals */}
            <div style={{ marginBottom: '2.5rem' }}>
                <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                    技术形态分析 (已识别 {validPeriods.length} 个周期)
                </h4>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '1rem'
                }}>
                    {validPeriods.map(p => (
                        <div key={p} style={{
                            background: 'rgba(255,255,255,0.03)',
                            borderRadius: 'var(--radius-md)',
                            padding: '1rem',
                            border: '1px solid rgba(255,255,255,0.05)'
                        }}>
                            <div style={{
                                color: '#fff', // Changed to White per user request
                                fontWeight: '600',
                                marginBottom: '1rem',
                                paddingBottom: '0.5rem',
                                borderBottom: '1px solid rgba(255,255,255,0.05)',
                                fontSize: '0.95rem'
                            }}>
                                {p}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                                {
                                    [
                                        { label: 'K线', value: data.technicals?.[p]?.kline },
                                        { label: 'MACD', value: data.technicals?.[p]?.macd },
                                        { label: 'KDJ', value: data.technicals?.[p]?.kdj },
                                        {
                                            label: 'RSI',
                                            value: (
                                                <span style={{ fontSize: '0.8rem' }}>
                                                    <span style={{ color: 'var(--text-muted)', marginRight: '2px' }}>1:</span>{data.technicals?.[p]?.rsi1 || '-'}
                                                    <span style={{ margin: '0 4px', color: 'rgba(255,255,255,0.1)' }}>|</span>
                                                    <span style={{ color: 'var(--text-muted)', marginRight: '2px' }}>2:</span>{data.technicals?.[p]?.rsi2 || '-'}
                                                    <span style={{ margin: '0 4px', color: 'rgba(255,255,255,0.1)' }}>|</span>
                                                    <span style={{ color: 'var(--text-muted)', marginRight: '2px' }}>3:</span>{data.technicals?.[p]?.rsi3 || '-'}
                                                </span>
                                            )
                                        }
                                    ].map((item, idx) => (
                                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                                            <span style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
                                            <span style={{ color: 'var(--text-primary)', fontWeight: '500', textAlign: 'right', maxWidth: '75%' }}>{item.value || '---'}</span>
                                        </div>
                                    ))
                                }
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Sector Analysis */}
            {data.sector && (
                <div style={{ marginBottom: '2.5rem' }}>
                    <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        板块走势关联 (Sector Analysis)
                    </h4>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '1rem'
                    }}>
                        <div style={{
                            background: 'rgba(255,255,255,0.03)',
                            borderRadius: 'var(--radius-md)',
                            padding: '1.2rem',
                            border: '1px solid rgba(255,255,255,0.05)'
                        }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>所属板块</div>
                            <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                                {data.sector.name}
                                <span style={{
                                    fontSize: '0.8rem',
                                    marginLeft: '0.8rem',
                                    color: data.sector.trendColor || 'var(--text-muted)',
                                    background: 'rgba(255,255,255,0.05)',
                                    padding: '2px 8px',
                                    borderRadius: '4px'
                                }}>
                                    {data.sector.trend}
                                </span>
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                {data.sector.comparison}
                            </div>
                        </div>

                        <div style={{
                            background: 'rgba(255,255,255,0.03)',
                            borderRadius: 'var(--radius-md)',
                            padding: '1.2rem',
                            border: '1px solid rgba(255,255,255,0.05)',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>相对强弱</span>
                                <span style={{
                                    fontWeight: '600',
                                    color: data.sector.signal === '强势' || data.sector.signal === '领涨' ? '#ef4444' : (data.sector.signal === '弱势' ? '#10b981' : 'var(--text-primary)')
                                }}>
                                    {data.sector.signal}
                                </span>
                            </div>
                            <div style={{ fontSize: '0.95rem', fontWeight: 'bold' }}>
                                {data.sector.relativeStrength}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Macro Environment Scan (Moved to Bottom) */}
            {data.macro && (
                <div style={{ marginBottom: '2rem' }}>
                    <h4 style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                        宏观环境扫描 (Macro Environment)
                    </h4>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '0.75rem'
                    }}>
                        {Object.entries(data.macro).map(([key, item]) => (
                            <div key={key} style={{
                                background: 'rgba(255,255,255,0.03)',
                                borderRadius: 'var(--radius-md)',
                                padding: '1rem',
                                border: '1px solid rgba(255,255,255,0.05)',
                                position: 'relative',
                                overflow: 'hidden'
                            }}>
                                {/* Impact Indicator Line - China Style: Positive=Red, Negative=Green */}
                                <div style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    bottom: 0,
                                    width: '3px',
                                    background: item.impact === 'Positive' ? '#ef4444' : (item.impact === 'Negative' ? '#10b981' : 'var(--text-muted)')
                                }} />

                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
                                    {item.label}
                                </div>
                                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                                    {item.value}
                                </div>
                                <div style={{
                                    fontSize: '0.7rem',
                                    color: item.impact === 'Positive' ? '#ef4444' : (item.impact === 'Negative' ? '#10b981' : 'var(--text-muted)'),
                                    background: item.impact === 'Positive' ? 'rgba(239, 68, 68, 0.1)' : (item.impact === 'Negative' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.05)'),
                                    display: 'inline-block',
                                    padding: '2px 6px',
                                    borderRadius: '4px'
                                }}>
                                    {item.impact === 'Positive' ? '利多' : (item.impact === 'Negative' ? '利空' : '中性')}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div style={{ marginBottom: '2rem' }}>
                {/* Analysis Configuration - Always Visible */}
                <div style={{
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid rgba(255,255,255,0.05)'
                }}>
                    {/* 1. Model Selection - Standardized Toggles */}
                    <div style={{ marginBottom: '1rem' }}>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>启用分析模型 (多选):</div>
                        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                            {availableModels.map(model => (
                                <div key={model.id}
                                    onClick={() => toggleModel(model.id)}
                                    style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                                >
                                    <div style={{
                                        width: '32px', height: '18px',
                                        background: selectedModels.includes(model.id) ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)',
                                        borderRadius: '10px',
                                        position: 'relative',
                                        transition: 'var(--transition)',
                                        marginRight: '8px'
                                    }}>
                                        <div style={{
                                            width: '14px', height: '14px',
                                            background: '#fff',
                                            borderRadius: '50%',
                                            position: 'absolute',
                                            top: '2px',
                                            left: selectedModels.includes(model.id) ? '16px' : '2px',
                                            transition: 'var(--transition)'
                                        }} />
                                    </div>
                                    <span style={{ fontSize: '0.85rem', color: selectedModels.includes(model.id) ? '#fff' : 'var(--text-muted)' }}>
                                        {model.label}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 2. Cycle Analysis Options */}
                    <div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>深度周期验证:</div>
                        <div style={{ display: 'flex', gap: '1.5rem' }}>
                            <div
                                onClick={() => setAnalysisOptions(prev => ({ ...prev, sectorCycle: !prev.sectorCycle }))}
                                style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                            >
                                <div style={{
                                    width: '32px', height: '18px',
                                    background: analysisOptions.sectorCycle ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)',
                                    borderRadius: '10px',
                                    position: 'relative',
                                    transition: 'var(--transition)',
                                    marginRight: '8px'
                                }}>
                                    <div style={{
                                        width: '14px', height: '14px',
                                        background: '#fff',
                                        borderRadius: '50%',
                                        position: 'absolute',
                                        top: '2px',
                                        left: analysisOptions.sectorCycle ? '16px' : '2px',
                                        transition: 'var(--transition)'
                                    }} />
                                </div>
                                <span style={{ fontSize: '0.85rem', color: analysisOptions.sectorCycle ? '#fff' : 'var(--text-muted)' }}>板块周期分析</span>
                            </div>

                            <div
                                onClick={() => setAnalysisOptions(prev => ({ ...prev, macroCycle: !prev.macroCycle }))}
                                style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                            >
                                <div style={{
                                    width: '32px', height: '18px',
                                    background: analysisOptions.macroCycle ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)',
                                    borderRadius: '10px',
                                    position: 'relative',
                                    transition: 'var(--transition)',
                                    marginRight: '8px'
                                }}>
                                    <div style={{
                                        width: '14px', height: '14px',
                                        background: '#fff',
                                        borderRadius: '50%',
                                        position: 'absolute',
                                        top: '2px',
                                        left: analysisOptions.macroCycle ? '16px' : '2px',
                                        transition: 'var(--transition)'
                                    }} />
                                </div>
                                <span style={{ fontSize: '0.85rem', color: analysisOptions.macroCycle ? '#fff' : 'var(--text-muted)' }}>宏观经济周期分析</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div style={{ marginBottom: '2rem' }}>
                <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem', fontWeight: '500' }}>
                    请确认您的操作意图：
                </label>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {operations.map(op => (
                        <button
                            key={op}
                            onClick={() => setSelectedOp(op)}
                            style={{
                                flex: '1 0 30%',
                                padding: '0.75rem',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid',
                                borderColor: selectedOp === op ? 'var(--accent-primary)' : 'rgba(255,255,255,0.1)',
                                background: selectedOp === op ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                                color: selectedOp === op ? '#fff' : 'var(--text-secondary)',
                                cursor: 'pointer',
                                transition: 'var(--transition)',
                                fontSize: '0.9rem',
                                fontWeight: selectedOp === op ? '600' : '400'
                            }}
                        >
                            {op}
                        </button>
                    ))}
                </div>
            </div>

            {/* Actions */}
            <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                    onClick={onReset}
                    style={{
                        flex: 1,
                        padding: '0.85rem',
                        background: 'transparent',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        fontSize: '0.9rem',
                        transition: 'var(--transition)'
                    }}
                >
                    重新识别
                </button>

                <button
                    disabled={!selectedOp}
                    style={{
                        flex: 2,
                        padding: '0.85rem',
                        background: selectedOp ? 'var(--accent-primary)' : 'rgba(255,255,255,0.05)',
                        border: 'none',
                        borderRadius: 'var(--radius-md)',
                        color: selectedOp ? '#fff' : 'rgba(255,255,255,0.2)',
                        cursor: selectedOp ? 'pointer' : 'not-allowed',
                        fontSize: '0.9rem',
                        fontWeight: '600',
                        boxShadow: selectedOp ? '0 4px 12px var(--accent-glow)' : 'none',
                        transition: 'var(--transition)'
                    }}
                >
                    确认并继续
                </button>
            </div>
        </div>
    );
};

export default AnalysisResult;
