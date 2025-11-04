/**
 * IDX Stock Screener - Pattern System Frontend
 *
 * Handles pattern selection, screening execution, and results display
 */

// API Base URL
const API_BASE = window.location.origin;

// State
let patterns = {
    presets: [],
    custom: [],
    counts: {}
};
let selectedPattern = null;
let currentResults = [];

// DOM Elements
const patternDropdown = document.getElementById('pattern-dropdown');
const runBtn = document.getElementById('run-btn');
const detailsBtn = document.getElementById('details-btn');
const patternDetails = document.getElementById('pattern-details');
const closeDetailsBtn = document.getElementById('close-details');
const loadingIndicator = document.getElementById('loading');
const resultsContainer = document.getElementById('results-container');
const patternCount = document.getElementById('pattern-count');
const resultsCount = document.getElementById('results-count');
const executionTime = document.getElementById('execution-time');

// Stock Analyzer Elements
const stockInput = document.getElementById('stock-input');
const analyzeBtn = document.getElementById('analyze-btn');

// Pattern Editor Elements
const addPatternBtn = document.getElementById('add-pattern-btn');
const editPatternBtn = document.getElementById('edit-pattern-btn');
const deletePatternBtn = document.getElementById('delete-pattern-btn');
const patternEditorModal = document.getElementById('pattern-editor-modal');
const closeEditorBtn = document.getElementById('close-editor');
const cancelEditorBtn = document.getElementById('cancel-editor-btn');
const savePatternBtn = document.getElementById('save-pattern-btn');
const editorTitle = document.getElementById('editor-title');

// Editor State
let editorMode = 'create'; // 'create' or 'edit'
let editingPatternId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPatterns();
    setupEventListeners();
    initializePatternEditor();
});

// Setup Event Listeners
function setupEventListeners() {
    patternDropdown.addEventListener('change', handlePatternChange);
    runBtn.addEventListener('click', runScreening);
    detailsBtn.addEventListener('click', showPatternDetails);
    closeDetailsBtn.addEventListener('click', hidePatternDetails);

    // Pattern Editor
    addPatternBtn.addEventListener('click', openEditorForCreate);
    editPatternBtn.addEventListener('click', openEditorForEdit);
    deletePatternBtn.addEventListener('click', deletePattern);
    closeEditorBtn.addEventListener('click', closePatternEditor);
    cancelEditorBtn.addEventListener('click', closePatternEditor);
    savePatternBtn.addEventListener('click', savePattern);

    // Stock Analyzer
    analyzeBtn.addEventListener('click', analyzeStock);
    stockInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            analyzeStock();
        }
    });
}

// Load Patterns from API
async function loadPatterns() {
    try {
        const response = await fetch(`${API_BASE}/api/patterns`);
        const data = await response.json();

        patterns = data;

        // Update pattern count
        patternCount.textContent = `${data.counts.preset} presets, ${data.counts.custom} custom (${data.counts.total} total)`;

        // Populate dropdown
        populatePatternDropdown();

    } catch (error) {
        console.error('Error loading patterns:', error);
        showError('Failed to load patterns. Please refresh the page.');
    }
}

// Populate Pattern Dropdown
function populatePatternDropdown() {
    patternDropdown.innerHTML = '<option value="">Select a pattern...</option>';

    // Group by category
    const categories = {};

    // Combine presets and custom
    const allPatterns = [...patterns.presets, ...patterns.custom];

    allPatterns.forEach(pattern => {
        const category = pattern.category;
        if (!categories[category]) {
            categories[category] = [];
        }
        categories[category].push(pattern);
    });

    // Add to dropdown by category
    Object.keys(categories).sort().forEach(category => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = category.toUpperCase();

        categories[category].forEach(pattern => {
            const option = document.createElement('option');
            option.value = pattern.pattern_id;
            option.textContent = `${pattern.pattern_name}${pattern.is_preset ? '' : ' (Custom)'}`;
            optgroup.appendChild(option);
        });

        patternDropdown.appendChild(optgroup);
    });
}

// Handle Pattern Change
async function handlePatternChange(e) {
    const patternId = e.target.value;

    if (!patternId) {
        runBtn.disabled = true;
        detailsBtn.disabled = true;
        editPatternBtn.disabled = true;
        deletePatternBtn.disabled = true;
        selectedPattern = null;
        hidePatternDetails();
        return;
    }

    // Enable buttons
    runBtn.disabled = false;
    detailsBtn.disabled = false;

    // Load pattern details
    try {
        const response = await fetch(`${API_BASE}/api/patterns/${patternId}`);
        selectedPattern = await response.json();

        // Enable Edit/Delete only for custom patterns (not presets)
        const isCustom = !selectedPattern.is_preset;
        editPatternBtn.disabled = !isCustom;
        deletePatternBtn.disabled = !isCustom;
    } catch (error) {
        console.error('Error loading pattern details:', error);
        showError('Failed to load pattern details.');
    }
}

// Show Pattern Details
function showPatternDetails() {
    if (!selectedPattern) return;

    // Set title and description
    document.getElementById('details-name').textContent = selectedPattern.pattern_name;
    document.getElementById('details-description').textContent = selectedPattern.description || 'No description available.';

    // Technical criteria
    const technicalDiv = document.getElementById('details-technical');
    const techCriteria = selectedPattern.technical_criteria || {};

    if (Object.keys(techCriteria).length === 0) {
        technicalDiv.innerHTML = '<p style="color: #999;">No technical criteria</p>';
    } else {
        let techHtml = '<ul>';

        if (techCriteria.signals && techCriteria.signals.length > 0) {
            techHtml += '<li><strong>Required Signals:</strong><br>';
            techHtml += techCriteria.signals.map(s => `• ${formatSignalName(s)}`).join('<br>');
            techHtml += '</li>';
        }

        if (techCriteria.min_signal_strength) {
            techHtml += `<li><strong>Minimum Strength:</strong> ${techCriteria.min_signal_strength}</li>`;
        }

        techHtml += '</ul>';
        technicalDiv.innerHTML = techHtml;
    }

    // Fundamental criteria
    const fundamentalDiv = document.getElementById('details-fundamental');
    const fundCriteria = selectedPattern.fundamental_criteria || {};

    if (Object.keys(fundCriteria).length === 0) {
        fundamentalDiv.innerHTML = '<p style="color: #999;">No fundamental criteria</p>';
    } else {
        let fundHtml = '<ul>';

        for (const [key, value] of Object.entries(fundCriteria)) {
            const label = formatMetricName(key);

            if (typeof value === 'object' && value !== null) {
                const min = value.min !== undefined ? value.min : '-';
                const max = value.max !== undefined && value.max !== 999 && value.max !== null ? value.max : 'No limit';
                fundHtml += `<li><strong>${label}:</strong> ${min} to ${max}</li>`;
            } else {
                fundHtml += `<li><strong>${label}:</strong> ${value}</li>`;
            }
        }

        fundHtml += '</ul>';
        fundamentalDiv.innerHTML = fundHtml;
    }

    // Show panel
    patternDetails.style.display = 'block';
}

// Hide Pattern Details
function hidePatternDetails() {
    patternDetails.style.display = 'none';
}

// Run Screening
async function runScreening() {
    if (!selectedPattern) return;

    // Show loading
    loadingIndicator.style.display = 'block';
    resultsContainer.innerHTML = '';
    resultsCount.textContent = 'Screening...';
    executionTime.textContent = '';

    try {
        const response = await fetch(`${API_BASE}/api/patterns/${selectedPattern.pattern_id}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                limit: 50,
                use_cache: true
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentResults = data.results;
            displayResults(data);
        } else {
            throw new Error(data.error || 'Failed to run screening');
        }

    } catch (error) {
        console.error('Error running screening:', error);
        showError(`Failed to run screening: ${error.message}`);
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

// Display Results
function displayResults(data) {
    resultsCount.textContent = `${data.total_found} stocks found`;
    executionTime.textContent = `(${data.execution_time}s)`;

    if (data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="placeholder">
                <p>No stocks found matching this pattern.</p>
                <p style="color: #999; margin-top: 10px;">Try a different pattern or adjust the criteria.</p>
            </div>
        `;
        return;
    }

    // Get pattern's fundamental criteria to filter display
    const patternCriteria = selectedPattern?.fundamental_criteria || {};

    // Create table
    let html = `
        <table class="results-table">
            <thead>
                <tr>
                    <th>Stock</th>
                    <th>Match Score</th>
                    <th>Signals</th>
                    <th>Fundamentals</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.results.forEach(result => {
        const scoreClass = getScoreClass(result.match_score);
        const signalsHtml = formatSignals(result.signals);
        const fundamentalsHtml = formatFundamentals(result.fundamentals, patternCriteria);

        html += `
            <tr>
                <td><span class="stock-symbol">${result.stock_id}</span></td>
                <td><span class="score-badge ${scoreClass}">${result.match_score}/100</span></td>
                <td class="signals-list">${signalsHtml}</td>
                <td>${fundamentalsHtml}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    resultsContainer.innerHTML = html;
}

// Get Score Class
function getScoreClass(score) {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
}

// Format Signals
function formatSignals(signals) {
    if (!signals || signals.length === 0) {
        return '<span style="color: #999;">-</span>';
    }

    return signals.slice(0, 3).map(signal => {
        const name = signal.name || 'Unknown';
        return `<span class="signal-item">${formatSignalName(name)}</span>`;
    }).join(' ');
}

// Format Fundamentals - only show metrics in pattern criteria
function formatFundamentals(fundamentals, patternCriteria = {}) {
    if (!fundamentals || Object.keys(fundamentals).length === 0) {
        return '<span style="color: #999;">-</span>';
    }

    // Metric display configuration (label and formatter)
    const metricConfig = {
        'pe_ratio': { label: 'P/E', format: (v) => v.toFixed(1) },
        'pb_ratio': { label: 'P/B', format: (v) => v.toFixed(1) },
        'ps_ratio': { label: 'P/S', format: (v) => v.toFixed(1) },
        'peg_ratio': { label: 'PEG', format: (v) => v.toFixed(2) },
        'ev_ebitda': { label: 'EV/EBITDA', format: (v) => v.toFixed(1) },
        'roe_percent': { label: 'ROE', format: (v) => v.toFixed(1) + '%' },
        'roa_percent': { label: 'ROA', format: (v) => v.toFixed(1) + '%' },
        'roic': { label: 'ROIC', format: (v) => v.toFixed(1) + '%' },
        'npm_percent': { label: 'NPM', format: (v) => v.toFixed(1) + '%' },
        'revenue_growth_yoy': { label: 'Rev Growth', format: (v) => v.toFixed(1) + '%' },
        'eps_growth_yoy': { label: 'EPS Growth', format: (v) => v.toFixed(1) + '%' },
        'current_ratio': { label: 'Current Ratio', format: (v) => v.toFixed(2) },
        'quick_ratio': { label: 'Quick Ratio', format: (v) => v.toFixed(2) },
        'debt_to_assets': { label: 'Debt/Assets', format: (v) => v.toFixed(2) },
        'debt_to_equity': { label: 'D/E', format: (v) => v.toFixed(2) },
        'cash_ratio': { label: 'Cash Ratio', format: (v) => v.toFixed(2) },
        'piotroski_score': { label: 'F-Score', format: (v) => Math.round(v) },
        'altman_z_score': { label: 'Z-Score', format: (v) => v.toFixed(2) },
        'market_cap': { label: 'Market Cap', format: (v) => formatLargeNumber(v) },
        'cf_operating': { label: 'Op Cash Flow', format: (v) => formatLargeNumber(v) },
        'cf_investing': { label: 'Inv Cash Flow', format: (v) => formatLargeNumber(v) },
        'cf_financing': { label: 'Fin Cash Flow', format: (v) => formatLargeNumber(v) }
    };

    const items = [];

    // Get list of metrics that are in the pattern criteria
    const criteriaKeys = Object.keys(patternCriteria);

    // If no criteria specified, show all (fallback for backwards compatibility)
    const metricsToShow = criteriaKeys.length > 0 ? criteriaKeys : Object.keys(fundamentals);

    // Only display metrics that are in the pattern criteria
    for (const key of metricsToShow) {
        // Skip non-metric keys like 'stock_id', 'score'
        if (key === 'stock_id' || key === 'score') continue;

        const value = fundamentals[key];
        if (value !== null && value !== undefined) {
            const config = metricConfig[key];
            if (config) {
                try {
                    const formattedValue = config.format(value);
                    items.push(`${config.label}: ${formattedValue}`);
                } catch (e) {
                    // Skip if formatting fails
                    console.warn(`Failed to format ${key}:`, e);
                }
            }
        }
    }

    if (items.length === 0) {
        return '<span style="color: #999;">-</span>';
    }

    return '<div class="fundamentals-grid">' + items.map(item => {
        const [label, value] = item.split(': ');
        return `<div class="fund-item"><span class="fund-label">${label}</span><span class="fund-value">${value}</span></div>`;
    }).join('') + '</div>';
}

// Format Signal Name
function formatSignalName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

// Format Metric Name
function formatMetricName(name) {
    const nameMap = {
        'pe_ratio': 'P/E Ratio',
        'pb_ratio': 'P/B Ratio',
        'ps_ratio': 'P/S Ratio',
        'roe_percent': 'ROE %',
        'roa_percent': 'ROA %',
        'debt_to_assets': 'Debt/Assets',
        'debt_to_equity': 'Debt/Equity',
        'current_ratio': 'Current Ratio',
        'market_cap': 'Market Cap',
        'peg_ratio': 'PEG Ratio',
        'piotroski_score': 'Piotroski Score',
        'altman_z_score': 'Altman Z-Score',
        'revenue_growth_yoy': 'Revenue Growth (YoY)',
        'eps_growth_yoy': 'EPS Growth (YoY)',
        'roic': 'ROIC',
        'ev_ebitda': 'EV/EBITDA',
        'cf_operating': 'Operating Cash Flow'
    };

    return nameMap[name] || formatSignalName(name);
}

// Show Error
function showError(message) {
    resultsContainer.innerHTML = `
        <div class="error-message">
            <strong>Error:</strong> ${message}
        </div>
    `;
}

// =============================================================================
// STOCK ANALYZER FUNCTIONS
// =============================================================================

// Analyze Stock
async function analyzeStock() {
    const stockId = stockInput.value.trim().toUpperCase();

    if (!stockId) {
        showError('Please enter a stock code');
        return;
    }

    // Show loading
    loadingIndicator.style.display = 'block';
    resultsContainer.innerHTML = '';
    resultsCount.textContent = `Analyzing ${stockId}...`;
    executionTime.textContent = '';

    try {
        const response = await fetch(`${API_BASE}/api/stocks/${stockId}/analysis`);
        const data = await response.json();

        if (response.ok) {
            displayStockAnalysis(data);
        } else {
            throw new Error(data.error || 'Failed to analyze stock');
        }

    } catch (error) {
        console.error('Error analyzing stock:', error);
        showError(`Failed to analyze ${stockId}: ${error.message}`);
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

// Display Stock Analysis
function displayStockAnalysis(data) {
    resultsCount.textContent = `Analysis: ${data.stock_id}`;
    executionTime.textContent = '';

    let html = `
        <div class="analysis-grid">
            <!-- Signals Card -->
            <div class="analysis-card">
                <h3>🔔 Technical Signals</h3>

                <div class="signal-summary">
                    <div class="summary-item">
                        <span class="summary-count" style="color: #28a745;">${data.signal_summary.bullish}</span>
                        <span class="summary-label">Bullish</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-count" style="color: #dc3545;">${data.signal_summary.bearish}</span>
                        <span class="summary-label">Bearish</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-count" style="color: #ffc107;">${data.signal_summary.neutral}</span>
                        <span class="summary-label">Neutral</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-count" style="color: #667eea;">${data.signal_summary.total}</span>
                        <span class="summary-label">Total</span>
                    </div>
                </div>

                <div class="signal-list-detailed">
                    ${data.signals.length === 0 ? '<p style="color: #999;">No active signals found</p>' : ''}
                    ${data.signals.map(signal => `
                        <div class="signal-detail-item ${signal.direction}">
                            <div class="signal-detail-header">
                                <span class="signal-detail-name">${formatSignalName(signal.name)}</span>
                                <span class="signal-detail-strength">
                                    ${signal.value !== null && signal.value !== undefined ? `Value: ${signal.value}` : `Strength: ${Math.round(signal.strength || 0)}`}
                                </span>
                            </div>
                            <div class="signal-detail-meta">
                                ${signal.description || `Type: ${signal.type.toUpperCase()} | Direction: ${signal.direction.toUpperCase()}${signal.date ? ' | Date: ' + signal.date : ''}`}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Fundamentals Card -->
            <div class="analysis-card">
                <h3>📊 Fundamental Metrics</h3>

                ${Object.keys(data.fundamentals).length === 0 ?
                    '<p style="color: #999;">No fundamental data found</p>' :
                    `<div class="metrics-grid">
                        ${formatFundamentalMetrics(data.fundamentals)}
                    </div>`
                }
            </div>
        </div>
    `;

    resultsContainer.innerHTML = html;
}

// Format Fundamental Metrics for Display
function formatFundamentalMetrics(fundamentals) {
    const metrics = [
        { key: 'close_price', label: 'Price', formatter: (v) => `Rp ${formatNumber(v)}` },
        { key: 'pe_ratio', label: 'P/E Ratio', formatter: (v) => v.toFixed(2) },
        { key: 'pb_ratio', label: 'P/B Ratio', formatter: (v) => v.toFixed(2) },
        { key: 'roe_percent', label: 'ROE %', formatter: (v) => v.toFixed(2) + '%' },
        { key: 'roa_percent', label: 'ROA %', formatter: (v) => v.toFixed(2) + '%' },
        { key: 'debt_to_equity', label: 'D/E Ratio', formatter: (v) => v.toFixed(2) },
        { key: 'current_ratio', label: 'Current Ratio', formatter: (v) => v.toFixed(2) },
        { key: 'revenue_growth_yoy', label: 'Revenue Growth', formatter: (v) => v.toFixed(2) + '%' },
        { key: 'eps_growth_yoy', label: 'EPS Growth', formatter: (v) => v.toFixed(2) + '%' },
        { key: 'peg_ratio', label: 'PEG Ratio', formatter: (v) => v.toFixed(2) },
        { key: 'roic', label: 'ROIC %', formatter: (v) => v.toFixed(2) + '%' },
        { key: 'piotroski_score', label: 'Piotroski F-Score', formatter: (v) => Math.round(v) + '/9' },
        { key: 'altman_z_score', label: 'Altman Z-Score', formatter: (v) => v.toFixed(2) },
        { key: 'market_cap', label: 'Market Cap', formatter: (v) => 'Rp ' + formatLargeNumber(v) },
        { key: 'revenue', label: 'Revenue', formatter: (v) => 'Rp ' + formatLargeNumber(v) },
        { key: 'net_income', label: 'Net Income', formatter: (v) => 'Rp ' + formatLargeNumber(v) },
        { key: 'quarter', label: 'Data Period', formatter: (v) => v }
    ];

    return metrics
        .filter(m => fundamentals[m.key] !== null && fundamentals[m.key] !== undefined)
        .map(m => `
            <div class="metric-item">
                <span class="metric-label">${m.label}</span>
                <span class="metric-value">${m.formatter(fundamentals[m.key])}</span>
            </div>
        `)
        .join('');
}

// Format Number with Thousands Separator
function formatNumber(num) {
    return num.toLocaleString('id-ID');
}

// Format Large Numbers (Billions, Trillions)
function formatLargeNumber(num) {
    if (num >= 1_000_000_000_000) {
        return (num / 1_000_000_000_000).toFixed(2) + 'T';
    } else if (num >= 1_000_000_000) {
        return (num / 1_000_000_000).toFixed(2) + 'B';
    } else if (num >= 1_000_000) {
        return (num / 1_000_000).toFixed(2) + 'M';
    } else {
        return formatNumber(num);
    }
}

// =============================================================================
// PATTERN EDITOR FUNCTIONS
// =============================================================================

// Available Technical Signals
const AVAILABLE_SIGNALS = {
    'Trend': [
        { id: 'golden_cross', name: 'Golden Cross' },
        { id: 'death_cross', name: 'Death Cross' },
        { id: 'fast_cross', name: 'Fast Cross (SMA20/50)' },
        { id: 'bullish_trend', name: 'Bullish Trend' },
        { id: 'bearish_trend', name: 'Bearish Trend' },
        { id: 'bullish_breakout', name: 'Bullish Breakout' }
    ],
    'Momentum': [
        { id: 'rsi_oversold', name: 'RSI Oversold' },
        { id: 'rsi_overbought', name: 'RSI Overbought' },
        { id: 'rsi_bullish', name: 'RSI Bullish' },
        { id: 'rsi_bearish', name: 'RSI Bearish' },
        { id: 'macd_positive', name: 'MACD Positive' },
        { id: 'macd_negative', name: 'MACD Negative' },
        { id: 'stochastic_oversold', name: 'Stochastic Oversold' },
        { id: 'stochastic_overbought', name: 'Stochastic Overbought' },
        { id: 'cci_extreme', name: 'CCI Extreme' },
        { id: 'williams_extreme', name: 'Williams %R Extreme' }
    ],
    'Volatility': [
        { id: 'bollinger_squeeze', name: 'Bollinger Squeeze' },
        { id: 'bollinger_breakout', name: 'Bollinger Breakout' }
    ],
    'Volume': [
        { id: 'volume_surge', name: 'Volume Surge' }
    ]
};

// Available Fundamental Metrics
const AVAILABLE_METRICS = [
    { id: 'pe_ratio', name: 'P/E Ratio', defaultMin: 0, defaultMax: 15 },
    { id: 'pb_ratio', name: 'P/B Ratio', defaultMin: 0, defaultMax: 1.5 },
    { id: 'ps_ratio', name: 'P/S Ratio', defaultMin: 0, defaultMax: 2.0 },
    { id: 'peg_ratio', name: 'PEG Ratio', defaultMin: 0, defaultMax: 1.0 },
    { id: 'ev_ebitda', name: 'EV/EBITDA', defaultMin: 0, defaultMax: 15 },
    { id: 'roe_percent', name: 'ROE %', defaultMin: 15, defaultMax: 999 },
    { id: 'roa_percent', name: 'ROA %', defaultMin: 10, defaultMax: 999 },
    { id: 'roic', name: 'ROIC %', defaultMin: 12, defaultMax: 999 },
    { id: 'npm_percent', name: 'Net Profit Margin %', defaultMin: 10, defaultMax: 999 },
    { id: 'revenue_growth_yoy', name: 'Revenue Growth (YoY) %', defaultMin: 20, defaultMax: 999 },
    { id: 'eps_growth_yoy', name: 'EPS Growth (YoY) %', defaultMin: 15, defaultMax: 999 },
    { id: 'current_ratio', name: 'Current Ratio', defaultMin: 2.0, defaultMax: 999 },
    { id: 'quick_ratio', name: 'Quick Ratio', defaultMin: 1.0, defaultMax: 999 },
    { id: 'debt_to_assets', name: 'Debt/Assets', defaultMin: 0, defaultMax: 0.4 },
    { id: 'debt_to_equity', name: 'Debt/Equity', defaultMin: 0, defaultMax: 1.0 },
    { id: 'cash_ratio', name: 'Cash Ratio', defaultMin: 0.5, defaultMax: 999 },
    { id: 'piotroski_score', name: 'Piotroski F-Score', defaultMin: 7, defaultMax: 9 },
    { id: 'altman_z_score', name: 'Altman Z-Score', defaultMin: 3.0, defaultMax: 999 },
    { id: 'market_cap', name: 'Market Cap', defaultMin: 1000000000, defaultMax: 999999999999 }
];

// Initialize Pattern Editor
function initializePatternEditor() {
    // Populate signals grid
    const signalsGrid = document.getElementById('signals-grid');
    signalsGrid.innerHTML = '';

    for (const [category, signals] of Object.entries(AVAILABLE_SIGNALS)) {
        signals.forEach(signal => {
            const div = document.createElement('div');
            div.className = 'signal-checkbox-group';
            div.innerHTML = `
                <label>
                    <input type="checkbox" data-signal="${signal.id}">
                    ${signal.name}
                </label>
                <span class="signal-type-label">${category}</span>
            `;

            // Add change handler to update visual state
            const checkbox = div.querySelector('input');
            checkbox.addEventListener('change', () => {
                div.classList.toggle('selected', checkbox.checked);
            });

            signalsGrid.appendChild(div);
        });
    }

    // Populate metrics container
    const metricsContainer = document.getElementById('metrics-container');
    metricsContainer.innerHTML = '';

    AVAILABLE_METRICS.forEach(metric => {
        const div = document.createElement('div');
        div.className = 'metric-control';
        div.innerHTML = `
            <div class="metric-header">
                <input type="checkbox" id="metric-${metric.id}" data-metric="${metric.id}">
                <label for="metric-${metric.id}">${metric.name}</label>
            </div>
            <div class="metric-inputs">
                <div class="metric-input-group">
                    <label>Minimum</label>
                    <input type="number" id="metric-${metric.id}-min" step="any" disabled>
                </div>
                <div class="metric-input-group">
                    <label>Maximum</label>
                    <input type="number" id="metric-${metric.id}-max" step="any" disabled>
                </div>
            </div>
        `;

        // Add change handler to enable/disable inputs
        const checkbox = div.querySelector('input[type="checkbox"]');
        const minInput = div.querySelector(`#metric-${metric.id}-min`);
        const maxInput = div.querySelector(`#metric-${metric.id}-max`);

        checkbox.addEventListener('change', () => {
            const isEnabled = checkbox.checked;
            div.classList.toggle('enabled', isEnabled);
            minInput.disabled = !isEnabled;
            maxInput.disabled = !isEnabled;

            if (isEnabled) {
                // Set default values when enabled
                minInput.value = metric.defaultMin;
                maxInput.value = metric.defaultMax;
            }
        });

        metricsContainer.appendChild(div);
    });
}

// Open Editor for Creating New Pattern
function openEditorForCreate() {
    editorMode = 'create';
    editingPatternId = null;
    editorTitle.textContent = 'Create Custom Pattern';

    // Reset form
    document.getElementById('pattern-name').value = '';
    document.getElementById('pattern-category').value = 'custom';
    document.getElementById('pattern-description').value = '';
    document.getElementById('min-signal-strength').value = '70';

    // Reset all checkboxes
    document.querySelectorAll('.signal-checkbox-group input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
        cb.closest('.signal-checkbox-group').classList.remove('selected');
    });

    document.querySelectorAll('.metric-control input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
        cb.dispatchEvent(new Event('change')); // Trigger to disable inputs
    });

    // Show modal
    patternEditorModal.style.display = 'flex';
}

// Open Editor for Editing Existing Pattern
async function openEditorForEdit() {
    if (!selectedPattern || selectedPattern.is_preset) {
        alert('Cannot edit preset patterns. Only custom patterns can be edited.');
        return;
    }

    editorMode = 'edit';
    editingPatternId = selectedPattern.pattern_id;
    editorTitle.textContent = 'Edit Custom Pattern';

    // Fill form with existing data
    document.getElementById('pattern-name').value = selectedPattern.pattern_name;
    document.getElementById('pattern-category').value = selectedPattern.category;
    document.getElementById('pattern-description').value = selectedPattern.description || '';

    // Technical criteria
    const techCriteria = selectedPattern.technical_criteria || {};
    const signals = techCriteria.signals || [];
    const minStrength = techCriteria.min_signal_strength || 70;

    document.getElementById('min-signal-strength').value = minStrength;

    // Reset and set signals
    document.querySelectorAll('.signal-checkbox-group input[type="checkbox"]').forEach(cb => {
        const signalId = cb.getAttribute('data-signal');
        const isChecked = signals.includes(signalId);
        cb.checked = isChecked;
        cb.closest('.signal-checkbox-group').classList.toggle('selected', isChecked);
    });

    // Fundamental criteria
    const fundCriteria = selectedPattern.fundamental_criteria || {};

    // Reset all metrics
    document.querySelectorAll('.metric-control input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
        cb.dispatchEvent(new Event('change'));
    });

    // Set metrics that are defined
    for (const [metricId, values] of Object.entries(fundCriteria)) {
        const checkbox = document.getElementById(`metric-${metricId}`);
        if (checkbox) {
            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change'));

            if (values && typeof values === 'object') {
                const minInput = document.getElementById(`metric-${metricId}-min`);
                const maxInput = document.getElementById(`metric-${metricId}-max`);
                if (minInput && values.min !== undefined) minInput.value = values.min;
                if (maxInput && values.max !== undefined) maxInput.value = values.max;
            }
        }
    }

    // Show modal
    patternEditorModal.style.display = 'flex';
}

// Close Pattern Editor
function closePatternEditor() {
    patternEditorModal.style.display = 'none';
}

// Save Pattern
async function savePattern() {
    // Collect form data
    const patternName = document.getElementById('pattern-name').value.trim();
    const category = document.getElementById('pattern-category').value;
    const description = document.getElementById('pattern-description').value.trim();
    const minSignalStrength = parseInt(document.getElementById('min-signal-strength').value);

    // Validate
    if (!patternName) {
        alert('Please enter a pattern name');
        return;
    }

    // Collect selected signals
    const selectedSignals = [];
    document.querySelectorAll('.signal-checkbox-group input[type="checkbox"]:checked').forEach(cb => {
        selectedSignals.push(cb.getAttribute('data-signal'));
    });

    // Collect enabled metrics
    const fundamentalCriteria = {};
    document.querySelectorAll('.metric-control input[type="checkbox"]:checked').forEach(cb => {
        const metricId = cb.getAttribute('data-metric');
        const minInput = document.getElementById(`metric-${metricId}-min`);
        const maxInput = document.getElementById(`metric-${metricId}-max`);

        fundamentalCriteria[metricId] = {
            min: parseFloat(minInput.value) || 0,
            max: parseFloat(maxInput.value) || 999
        };
    });

    // Build pattern object
    const pattern = {
        pattern_name: patternName,
        category: category,
        description: description,
        technical_criteria: selectedSignals.length > 0 ? {
            signals: selectedSignals,
            min_signal_strength: minSignalStrength
        } : {},
        fundamental_criteria: fundamentalCriteria
    };

    // Add pattern_id for create mode
    if (editorMode === 'create') {
        // Generate pattern_id from pattern name
        pattern.pattern_id = patternName.toLowerCase()
            .replace(/[^a-z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '');
    }

    try {
        let response;
        if (editorMode === 'create') {
            // Create new pattern
            response = await fetch(`${API_BASE}/api/patterns`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pattern)
            });
        } else {
            // Update existing pattern
            response = await fetch(`${API_BASE}/api/patterns/${editingPatternId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pattern)
            });
        }

        if (response.ok) {
            closePatternEditor();
            await loadPatterns();
            alert(`Pattern ${editorMode === 'create' ? 'created' : 'updated'} successfully!`);

            // Select the newly created/edited pattern
            if (editorMode === 'create') {
                patternDropdown.value = pattern.pattern_id;
            } else {
                patternDropdown.value = editingPatternId;
            }
            patternDropdown.dispatchEvent(new Event('change'));
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save pattern');
        }
    } catch (error) {
        console.error('Error saving pattern:', error);
        alert(`Failed to save pattern: ${error.message}`);
    }
}

// Delete Pattern
async function deletePattern() {
    if (!selectedPattern || selectedPattern.is_preset) {
        alert('Cannot delete preset patterns. Only custom patterns can be deleted.');
        return;
    }

    const confirmDelete = confirm(`Are you sure you want to delete "${selectedPattern.pattern_name}"? This action cannot be undone.`);
    if (!confirmDelete) return;

    try {
        const response = await fetch(`${API_BASE}/api/patterns/${selectedPattern.pattern_id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('Pattern deleted successfully!');
            selectedPattern = null;
            await loadPatterns();
            patternDropdown.value = '';
            patternDropdown.dispatchEvent(new Event('change'));
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete pattern');
        }
    } catch (error) {
        console.error('Error deleting pattern:', error);
        alert(`Failed to delete pattern: ${error.message}`);
    }
}
