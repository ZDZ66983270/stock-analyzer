// Color utility functions based on user preference
// Supports both Chinese and US market conventions

/**
 * Get color for price change based on user preference
 * @param {number} value - The change value (positive or negative)
 * @param {string} convention - 'chinese' or 'us'
 * @returns {string} - Color hex code
 */
export const getChangeColor = (value, convention = 'chinese') => {
    const isPositive = value >= 0;

    if (convention === 'chinese') {
        // Chinese convention: red = up/good, green = down/bad
        return isPositive ? '#ef4444' : '#10b981';
    } else {
        // US convention: green = up/good, red = down/bad
        return isPositive ? '#10b981' : '#ef4444';
    }
};

/**
 * Get color for performance comparison (fund vs benchmark)
 * @param {number} fundValue - Fund's metric value
 * @param {number} benchmarkValue - Benchmark's metric value
 * @param {string} metricType - 'return' | 'volatility' | 'sharpe' | 'drawdown'
 * @param {string} convention - 'chinese' or 'us'
 * @returns {string} - Color hex code
 */
export const getPerformanceColor = (fundValue, benchmarkValue, metricType, convention = 'chinese') => {
    let isBetter = false;

    switch (metricType) {
        case 'return':
        case 'sharpe':
            // Higher is better
            isBetter = fundValue > benchmarkValue;
            break;
        case 'volatility':
            // Lower is better
            isBetter = fundValue < benchmarkValue;
            break;
        case 'drawdown':
            // Less negative (closer to 0) is better
            isBetter = fundValue > benchmarkValue;
            break;
        default:
            isBetter = fundValue > benchmarkValue;
    }

    if (convention === 'chinese') {
        // Chinese convention: red = better, green = worse
        return isBetter ? '#ef4444' : '#10b981';
    } else {
        // US convention: green = better, red = worse
        return isBetter ? '#10b981' : '#ef4444';
    }
};

/**
 * Get color convention from localStorage
 * @returns {string} - 'chinese' or 'us'
 */
export const getColorConvention = () => {
    return localStorage.getItem('colorConvention') || 'chinese';
};

/**
 * Set color convention to localStorage
 * @param {string} convention - 'chinese' or 'us'
 */
export const setColorConvention = (convention) => {
    localStorage.setItem('colorConvention', convention);
};
