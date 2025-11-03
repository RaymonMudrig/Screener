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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPatterns();
    setupEventListeners();
});

// Setup Event Listeners
function setupEventListeners() {
    patternDropdown.addEventListener('change', handlePatternChange);
    runBtn.addEventListener('click', runScreening);
    detailsBtn.addEventListener('click', showPatternDetails);
    closeDetailsBtn.addEventListener('click', hidePatternDetails);

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
        const fundamentalsHtml = formatFundamentals(result.fundamentals);

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

// Format Fundamentals
function formatFundamentals(fundamentals) {
    if (!fundamentals || Object.keys(fundamentals).length === 0) {
        return '<span style="color: #999;">-</span>';
    }

    const items = [];

    if (fundamentals.pe_ratio !== null && fundamentals.pe_ratio !== undefined) {
        items.push(`P/E: ${fundamentals.pe_ratio.toFixed(1)}`);
    }

    if (fundamentals.pb_ratio !== null && fundamentals.pb_ratio !== undefined) {
        items.push(`P/B: ${fundamentals.pb_ratio.toFixed(1)}`);
    }

    if (fundamentals.roe_percent !== null && fundamentals.roe_percent !== undefined) {
        items.push(`ROE: ${fundamentals.roe_percent.toFixed(1)}%`);
    }

    if (fundamentals.revenue_growth_yoy !== null && fundamentals.revenue_growth_yoy !== undefined) {
        items.push(`Growth: ${fundamentals.revenue_growth_yoy.toFixed(1)}%`);
    }

    if (fundamentals.peg_ratio !== null && fundamentals.peg_ratio !== undefined) {
        items.push(`PEG: ${fundamentals.peg_ratio.toFixed(2)}`);
    }

    if (fundamentals.roic !== null && fundamentals.roic !== undefined) {
        items.push(`ROIC: ${fundamentals.roic.toFixed(1)}%`);
    }

    if (fundamentals.piotroski_score !== null && fundamentals.piotroski_score !== undefined) {
        items.push(`F-Score: ${fundamentals.piotroski_score}`);
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
