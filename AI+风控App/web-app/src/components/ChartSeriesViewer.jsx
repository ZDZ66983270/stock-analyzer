import React, { useMemo } from 'react';
import {
    ResponsiveContainer,
    ComposedChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    Area
} from 'recharts';

/**
 * ChartSeriesViewer
 * 
 * Renders different financial chart series based on requirements:
 * C1: Stock Price (Line/Area)
 * C2: Price + Valuation (PE/PB/PS)
 * C3: Price + Dividend Yield
 * C4: Price + EPS
 * C5: Price + Macro (VIX/Rates) - Placeholder
 * C6: Price + Volume
 * 
 * @param {Object[]} data - Array of data objects (must have date, close, high, low, open, volume, etc.)
 * @param {string} seriesType - 'C1' | 'C2' | 'C3' | 'C4' | 'C5' | 'C6'
 * @param {string} subType - e.g., 'PE' | 'PB' for C2
 */
const ChartSeriesViewer = ({ data, seriesType = 'C1', subType = 'PE' }) => {

    if (!data || data.length === 0) {
        return <div style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>暂无数据</div>;
    }

    // Format Date Logic
    const formattedData = useMemo(() => {
        return data.map(item => ({
            ...item,
            // Ensure date is string
            dateStr: typeof item.timestamp === 'string' ? item.timestamp.substring(0, 10) : item.timestamp
        }));
    }, [data]);

    // Common Props
    const commonXAxis = <XAxis dataKey="dateStr" tick={{ fontSize: 10, fill: '#888' }} minTickGap={30} />;
    const commonGrid = <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />;
    const commonTooltip = (
        <Tooltip
            contentStyle={{ backgroundColor: '#1c1c20', border: '1px solid #333' }}
            itemStyle={{ color: '#ccc' }}
            labelStyle={{ color: '#fff' }}
        />
    );
    const commonLegend = <Legend wrapperStyle={{ paddingTop: '10px' }} />;

    // Render Logic
    const renderChart = () => {
        switch (seriesType) {
            case 'C1': // Price Only
                return (
                    <ComposedChart data={formattedData}>
                        {commonGrid}
                        {commonXAxis}
                        <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#888' }} orientation="right" />
                        {commonTooltip}
                        <Area type="monotone" dataKey="close" name="股价" stroke="#3b82f6" fillOpacity={0.1} fill="#3b82f6" strokeWidth={2} />
                    </ComposedChart>
                );

            case 'C2': // Price + Valuation
                const valKey = subType.toLowerCase(); // pe, pb, ps
                const valName = subType;
                return (
                    <ComposedChart data={formattedData}>
                        {commonGrid}
                        {commonXAxis}
                        <YAxis yAxisId="price" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#888' }} orientation="right" />
                        <YAxis yAxisId="val" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#f59e0b' }} orientation="left" />
                        {commonTooltip}
                        {commonLegend}
                        <Line yAxisId="price" type="monotone" dataKey="close" name="股价" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        <Line yAxisId="val" type="monotone" dataKey={valKey} name={valName} stroke="#f59e0b" strokeWidth={2} dot={false} connectNulls />
                    </ComposedChart>
                );

            case 'C3': // Price + Dividend
                return (
                    <ComposedChart data={formattedData}>
                        {commonGrid}
                        {commonXAxis}
                        <YAxis yAxisId="price" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#888' }} orientation="right" />
                        <YAxis yAxisId="div" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#10b981' }} orientation="left" unit="%" />
                        {commonTooltip}
                        {commonLegend}
                        <Line yAxisId="price" type="monotone" dataKey="close" name="股价" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        <Line yAxisId="div" type="monotone" dataKey="dividend_yield" name="股息率" stroke="#10b981" strokeWidth={2} dot={false} connectNulls />
                    </ComposedChart>
                );

            case 'C4': // Price + EPS
                return (
                    <ComposedChart data={formattedData}>
                        {commonGrid}
                        {commonXAxis}
                        <YAxis yAxisId="price" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#888' }} orientation="right" />
                        <YAxis yAxisId="eps" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#8b5cf6' }} orientation="left" />
                        {commonTooltip}
                        {commonLegend}
                        <Line yAxisId="price" type="monotone" dataKey="close" name="股价" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        <Line yAxisId="eps" type="stepAfter" dataKey="eps" name="EPS(每股收益)" stroke="#8b5cf6" strokeWidth={2} dot={false} connectNulls />
                    </ComposedChart>
                );

            case 'C5': // Price + Macro (Mock)
                return (
                    <ComposedChart data={formattedData}>
                        {commonGrid}
                        {commonXAxis}
                        <YAxis yAxisId="price" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#888' }} orientation="right" />
                        <YAxis yAxisId="macro" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#ef4444' }} orientation="left" />
                        {commonTooltip}
                        {commonLegend}
                        <Line yAxisId="price" type="monotone" dataKey="close" name="股价" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        {/* Placeholder for Macro Data if not in props, showing generic line */}
                        <Line yAxisId="macro" type="monotone" dataKey="macro_val" name="宏观指标" stroke="#ef4444" strokeWidth={2} dot={false} />
                    </ComposedChart>
                );

            case 'C6': // Price + Volume
                return (
                    <ComposedChart data={formattedData}>
                        {commonGrid}
                        {commonXAxis}
                        <YAxis yAxisId="price" domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#888' }} orientation="right" />
                        <YAxis yAxisId="vol" domain={['auto', 'auto']} tick={{ fontSize: 0 }} axisLine={false} orientation="left" width={0} />
                        {commonTooltip}
                        {commonLegend}
                        <Bar yAxisId="vol" dataKey="volume" name="成交量" fill="#3f3f46" opacity={0.5} barSize={20} />
                        <Line yAxisId="price" type="monotone" dataKey="close" name="股价" stroke="#3b82f6" strokeWidth={2} dot={false} />
                    </ComposedChart>
                );

            default:
                return null;
        }
    };

    return (
        <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
                {renderChart()}
            </ResponsiveContainer>
        </div>
    );
};

export default ChartSeriesViewer;
