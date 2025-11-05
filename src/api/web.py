"""
Flask Web API for Pattern Screening System

Provides REST endpoints for the web GUI to interact with the pattern system.

Endpoints:
- GET  /api/patterns              - List all patterns
- GET  /api/patterns/:id          - Get pattern details
- POST /api/patterns/:id/run      - Run pattern screening
- POST /api/patterns              - Create new pattern
- PUT  /api/patterns/:id          - Update pattern
- DELETE /api/patterns/:id        - Delete pattern

Author: Claude Code
Date: 2025-11-03
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import traceback
import sys
import math
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.patterns.engine import PatternEngine
from src.patterns.storage import PatternStorage
from src.data.storage import DataStorage
from src.indicators.calculator import IndicatorCalculator
from src.signals.engine import SignalEngine
from src.fundamentals.ratios import RatioCalculator

app = Flask(__name__, static_folder='../../web', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Database path
DB_PATH = 'database/stockCode.sqlite'

# Initialize pattern system
engine = PatternEngine(DB_PATH)
storage = PatternStorage(DB_PATH)

# Initialize data refresh components
data_storage = DataStorage(DB_PATH)
indicator_calc = IndicatorCalculator(DB_PATH)
signal_engine = SignalEngine(DB_PATH)

# Setup logging for scheduler
scheduler_logger = logging.getLogger('apscheduler')
scheduler_logger.setLevel(logging.INFO)

# Global variable to track last refresh
last_refresh_status = {
    'timestamp': None,
    'status': 'not_started',
    'stats': None
}


def sanitize_json_value(value):
    """
    Sanitize a value for JSON serialization
    Converts Infinity, -Infinity, and NaN to None
    """
    if isinstance(value, float):
        if math.isinf(value) or math.isnan(value):
            return None
    elif isinstance(value, dict):
        return {k: sanitize_json_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_json_value(item) for item in value]
    return value


def is_market_hours():
    """
    Check if current time is within market hours
    Monday-Friday, 09:00-16:00
    """
    now = datetime.now()

    # Check if it's a weekday (0=Monday, 4=Friday)
    if now.weekday() > 4:  # Saturday=5, Sunday=6
        return False

    # Check if within trading hours (09:00-16:00)
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= now <= market_close


def refresh_intraday_data():
    """
    Background job to refresh intraday data:
    1. Update prices for all stocks
    2. Recalculate indicators
    3. Detect new signals

    Runs every 5 minutes during market hours (Mon-Fri, 09:00-16:00)
    """
    global last_refresh_status

    # Check if we're in market hours
    if not is_market_hours():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Skipping refresh - outside market hours")
        return

    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"[{start_time.strftime('%H:%M:%S')}] Starting intraday data refresh...")
    print(f"{'='*60}")

    last_refresh_status['status'] = 'running'
    last_refresh_status['timestamp'] = start_time.isoformat()

    stats = {
        'prices_updated': 0,
        'prices_failed': 0,
        'indicators_updated': 0,
        'indicators_failed': 0,
        'signals_updated': 0,
        'signals_failed': 0,
        'total_new_signals': 0
    }

    try:
        # Get all active stocks
        stocks = data_storage.db.get_all_stocks(active_only=True)
        total_stocks = len(stocks)

        print(f"Processing {total_stocks} active stocks...")

        # Step 1: Update prices
        print(f"\n[1/3] Updating prices...")
        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            try:
                records = data_storage.update_price_data(stock_id)
                stats['prices_updated'] += 1
                if records > 0:
                    print(f"  [{i+1}/{total_stocks}] ✓ {stock_id} ({records} new records)")
            except Exception as e:
                stats['prices_failed'] += 1
                print(f"  [{i+1}/{total_stocks}] ✗ {stock_id}: {str(e)[:50]}")

        print(f"Prices: {stats['prices_updated']} succeeded, {stats['prices_failed']} failed")

        # Step 2: Recalculate indicators
        print(f"\n[2/3] Recalculating indicators...")
        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            try:
                count = indicator_calc.calculate_all_indicators(stock_id)
                stats['indicators_updated'] += 1
                if i % 100 == 0:
                    print(f"  [{i+1}/{total_stocks}] Processed...")
            except Exception as e:
                stats['indicators_failed'] += 1
                if i % 100 == 0:
                    print(f"  [{i+1}/{total_stocks}] Some failures")

        print(f"Indicators: {stats['indicators_updated']} succeeded, {stats['indicators_failed']} failed")

        # Step 3: Detect signals
        print(f"\n[3/3] Detecting signals...")
        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']
            try:
                new_signals = signal_engine.detect_all_signals(stock_id)
                stats['signals_updated'] += 1
                stats['total_new_signals'] += len(new_signals)
                if i % 100 == 0:
                    print(f"  [{i+1}/{total_stocks}] Processed...")
            except Exception as e:
                stats['signals_failed'] += 1

        print(f"Signals: {stats['signals_updated']} succeeded, {stats['signals_failed']} failed")
        print(f"Total new signals detected: {stats['total_new_signals']}")

        # Update status
        last_refresh_status['status'] = 'success'
        last_refresh_status['stats'] = stats

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"Refresh completed in {elapsed:.1f} seconds")
        print(f"{'='*60}\n")

    except Exception as e:
        last_refresh_status['status'] = 'error'
        last_refresh_status['stats'] = stats
        print(f"\n[ERROR] Refresh failed: {str(e)}")
        traceback.print_exc()


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/patterns', methods=['GET'])
def get_patterns():
    """
    List all available patterns

    Returns:
        {
            "presets": [...],
            "custom": [...],
            "counts": {"preset": N, "custom": M, "total": X}
        }
    """
    try:
        all_patterns = storage.get_all_patterns()

        presets = [p for p in all_patterns if p['is_preset']]
        custom = [p for p in all_patterns if not p['is_preset']]
        counts = storage.get_pattern_count()

        # Simplify patterns for list view
        def simplify_pattern(p):
            return {
                'pattern_id': p['pattern_id'],
                'pattern_name': p['pattern_name'],
                'category': p['category'],
                'description': p['description'],
                'is_preset': p['is_preset']
            }

        return jsonify({
            'presets': [simplify_pattern(p) for p in presets],
            'custom': [simplify_pattern(p) for p in custom],
            'counts': counts
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patterns/<pattern_id>', methods=['GET'])
def get_pattern(pattern_id):
    """
    Get detailed information about a specific pattern

    Args:
        pattern_id: Pattern identifier

    Returns:
        Pattern object with all details
    """
    try:
        pattern = storage.get_pattern(pattern_id)

        if not pattern:
            return jsonify({'error': f'Pattern not found: {pattern_id}'}), 404

        return jsonify(pattern)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patterns/<pattern_id>/run', methods=['POST'])
def run_pattern(pattern_id):
    """
    Run a pattern screening

    Args:
        pattern_id: Pattern identifier

    Request body (optional):
        {
            "limit": 50,
            "use_cache": true
        }

    Returns:
        {
            "pattern": {...},
            "results": [...],
            "total_found": N,
            "execution_time": X.XX
        }
    """
    try:
        import time
        start_time = time.time()

        # Get request parameters
        data = request.get_json() or {}
        limit = data.get('limit', 50)
        use_cache = data.get('use_cache', True)

        # Get pattern details
        pattern = storage.get_pattern(pattern_id)
        if not pattern:
            return jsonify({'error': f'Pattern not found: {pattern_id}'}), 404

        # Run screening
        results = engine.run_pattern(
            pattern_id,
            use_cache=use_cache,
            limit=limit
        )

        execution_time = time.time() - start_time

        # Format results for frontend
        formatted_results = []
        for result in results:
            formatted_result = {
                'stock_id': result['stock_id'],
                'match_score': result.get('match_score', 0),
                'signals': [],
                'fundamentals': {}
            }

            # Format signals
            signals = result.get('matched_signals', [])
            if isinstance(signals, list) and signals:
                if isinstance(signals[0], dict):
                    formatted_result['signals'] = [
                        {
                            'name': s.get('signal_name', ''),
                            'strength': s.get('strength', 0)
                        }
                        for s in signals[:5]  # Top 5 signals
                    ]
                else:
                    formatted_result['signals'] = [{'name': s, 'strength': 0} for s in signals[:5]]

            # Format fundamentals - return all matched fundamentals
            fundamentals = result.get('matched_fundamentals', {})
            if fundamentals:
                # Return all fundamentals that have non-null values
                formatted_result['fundamentals'] = {
                    key: value for key, value in fundamentals.items()
                    if value is not None
                }

            formatted_results.append(formatted_result)

        return jsonify({
            'pattern': {
                'pattern_id': pattern['pattern_id'],
                'pattern_name': pattern['pattern_name'],
                'description': pattern['description'],
                'category': pattern['category']
            },
            'results': formatted_results,
            'total_found': len(results),
            'execution_time': round(execution_time, 2)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        engine.close()


@app.route('/api/patterns', methods=['POST'])
def create_pattern():
    """
    Create a new custom pattern

    Request body:
        {
            "pattern_id": "my_pattern",
            "pattern_name": "My Strategy",
            "category": "custom",
            "description": "...",
            "technical_criteria": {...},
            "fundamental_criteria": {...}
        }

    Returns:
        Created pattern object
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required = ['pattern_id', 'pattern_name', 'category']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Create pattern
        success = storage.create_pattern(data)

        if success:
            pattern = storage.get_pattern(data['pattern_id'])
            return jsonify(pattern), 201
        else:
            return jsonify({'error': 'Failed to create pattern'}), 500

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/patterns/<pattern_id>', methods=['PUT'])
def update_pattern(pattern_id):
    """
    Update an existing pattern

    Args:
        pattern_id: Pattern identifier

    Request body:
        {
            "pattern_name": "Updated Name",
            "technical_criteria": {...},
            "fundamental_criteria": {...}
        }

    Returns:
        Updated pattern object
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update pattern
        success = storage.update_pattern(pattern_id, data)

        if success:
            pattern = storage.get_pattern(pattern_id)
            return jsonify(pattern)
        else:
            return jsonify({'error': f'Pattern not found: {pattern_id}'}), 404

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/patterns/<pattern_id>', methods=['DELETE'])
def delete_pattern(pattern_id):
    """
    Delete a custom pattern

    Args:
        pattern_id: Pattern identifier

    Returns:
        {"success": true}
    """
    try:
        success = storage.delete_pattern(pattern_id)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': f'Pattern not found: {pattern_id}'}), 404

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def calculate_realtime_signals(indicators: dict, fundamentals: dict) -> list:
    """
    Calculate real-time signal states from current indicator values

    This provides consistent signals for all stocks based on their current
    indicator values, rather than relying only on stored event-based signals.

    Args:
        indicators: Dictionary of indicator names and values
        fundamentals: Dictionary of fundamental data (for price comparisons)

    Returns:
        List of signal objects with name, direction, strength, value
    """
    signals = []

    # 1. RSI Signal (always calculated if RSI exists)
    if 'rsi' in indicators and indicators['rsi'] is not None:
        rsi = indicators['rsi']
        if rsi > 70:
            signals.append({
                'type': 'momentum',
                'name': 'RSI Overbought',
                'direction': 'bearish',
                'strength': min(50 + (rsi - 70) * 2, 100),
                'value': round(rsi, 2),
                'description': f'RSI at {rsi:.1f} (>70 threshold)'
            })
        elif rsi < 30:
            signals.append({
                'type': 'momentum',
                'name': 'RSI Oversold',
                'direction': 'bullish',
                'strength': min(50 + (30 - rsi) * 2, 100),
                'value': round(rsi, 2),
                'description': f'RSI at {rsi:.1f} (<30 threshold)'
            })
        else:
            signals.append({
                'type': 'momentum',
                'name': 'RSI Neutral',
                'direction': 'neutral',
                'strength': 50,
                'value': round(rsi, 2),
                'description': f'RSI at {rsi:.1f} (neutral zone)'
            })

    # 2. MACD Signal
    if 'macd_histogram' in indicators and indicators['macd_histogram'] is not None:
        hist = indicators['macd_histogram']
        if hist > 0:
            signals.append({
                'type': 'trend',
                'name': 'MACD Bullish',
                'direction': 'bullish',
                'strength': min(50 + abs(hist) * 0.5, 80),
                'value': round(hist, 2),
                'description': f'MACD histogram positive ({hist:.2f})'
            })
        else:
            signals.append({
                'type': 'trend',
                'name': 'MACD Bearish',
                'direction': 'bearish',
                'strength': min(50 + abs(hist) * 0.5, 80),
                'value': round(hist, 2),
                'description': f'MACD histogram negative ({hist:.2f})'
            })

    # 3. Stochastic Signal
    if 'stoch_k' in indicators and indicators['stoch_k'] is not None:
        stoch = indicators['stoch_k']
        if stoch > 80:
            signals.append({
                'type': 'momentum',
                'name': 'Stochastic Overbought',
                'direction': 'bearish',
                'strength': min(50 + (stoch - 80) * 2.5, 100),
                'value': round(stoch, 2),
                'description': f'Stochastic at {stoch:.1f} (>80 threshold)'
            })
        elif stoch < 20:
            signals.append({
                'type': 'momentum',
                'name': 'Stochastic Oversold',
                'direction': 'bullish',
                'strength': min(50 + (20 - stoch) * 2.5, 100),
                'value': round(stoch, 2),
                'description': f'Stochastic at {stoch:.1f} (<20 threshold)'
            })
        else:
            signals.append({
                'type': 'momentum',
                'name': 'Stochastic Neutral',
                'direction': 'neutral',
                'strength': 50,
                'value': round(stoch, 2),
                'description': f'Stochastic at {stoch:.1f} (neutral zone)'
            })

    # 4. Williams %R Signal
    if 'williams_r' in indicators and indicators['williams_r'] is not None:
        wr = indicators['williams_r']
        if wr > -20:
            signals.append({
                'type': 'momentum',
                'name': 'Williams %R Overbought',
                'direction': 'bearish',
                'strength': min(50 + abs(wr + 10) * 2, 100),
                'value': round(wr, 2),
                'description': f'Williams %R at {wr:.1f} (>-20 threshold)'
            })
        elif wr < -80:
            signals.append({
                'type': 'momentum',
                'name': 'Williams %R Oversold',
                'direction': 'bullish',
                'strength': min(50 + abs(wr + 90) * 2, 100),
                'value': round(wr, 2),
                'description': f'Williams %R at {wr:.1f} (<-80 threshold)'
            })
        else:
            signals.append({
                'type': 'momentum',
                'name': 'Williams %R Neutral',
                'direction': 'neutral',
                'strength': 50,
                'value': round(wr, 2),
                'description': f'Williams %R at {wr:.1f} (neutral zone)'
            })

    # 5. MFI Signal
    if 'mfi' in indicators and indicators['mfi'] is not None:
        mfi = indicators['mfi']
        if mfi > 80:
            signals.append({
                'type': 'volume',
                'name': 'MFI Overbought',
                'direction': 'bearish',
                'strength': min(50 + (mfi - 80) * 2.5, 100),
                'value': round(mfi, 2),
                'description': f'Money Flow Index at {mfi:.1f} (>80 threshold)'
            })
        elif mfi < 20:
            signals.append({
                'type': 'volume',
                'name': 'MFI Oversold',
                'direction': 'bullish',
                'strength': min(50 + (20 - mfi) * 2.5, 100),
                'value': round(mfi, 2),
                'description': f'Money Flow Index at {mfi:.1f} (<20 threshold)'
            })
        else:
            signals.append({
                'type': 'volume',
                'name': 'MFI Neutral',
                'direction': 'neutral',
                'strength': 50,
                'value': round(mfi, 2),
                'description': f'Money Flow Index at {mfi:.1f} (neutral zone)'
            })

    # 6. CCI Signal
    if 'cci' in indicators and indicators['cci'] is not None:
        cci = indicators['cci']
        if cci > 100:
            signals.append({
                'type': 'momentum',
                'name': 'CCI Overbought',
                'direction': 'bearish',
                'strength': min(50 + (cci - 100) * 0.2, 80),
                'value': round(cci, 2),
                'description': f'CCI at {cci:.1f} (>100 threshold)'
            })
        elif cci < -100:
            signals.append({
                'type': 'momentum',
                'name': 'CCI Oversold',
                'direction': 'bullish',
                'strength': min(50 + abs(cci + 100) * 0.2, 80),
                'value': round(cci, 2),
                'description': f'CCI at {cci:.1f} (<-100 threshold)'
            })
        else:
            signals.append({
                'type': 'momentum',
                'name': 'CCI Neutral',
                'direction': 'neutral',
                'strength': 50,
                'value': round(cci, 2),
                'description': f'CCI at {cci:.1f} (neutral zone)'
            })

    # 7. ADX Trend Strength
    if 'adx' in indicators and indicators['adx'] is not None:
        adx = indicators['adx']
        if adx > 25:
            signals.append({
                'type': 'trend',
                'name': 'Strong Trend',
                'direction': 'neutral',
                'strength': min(50 + (adx - 25) * 1.5, 100),
                'value': round(adx, 2),
                'description': f'ADX at {adx:.1f} indicates strong trend'
            })
        else:
            signals.append({
                'type': 'trend',
                'name': 'Weak Trend',
                'direction': 'neutral',
                'strength': 40,
                'value': round(adx, 2),
                'description': f'ADX at {adx:.1f} indicates weak/no trend'
            })

    # 8. Bollinger Bands Position
    if all(k in indicators for k in ['percent_b']) and indicators['percent_b'] is not None:
        pb = indicators['percent_b']
        if pb > 1.0:
            signals.append({
                'type': 'volatility',
                'name': 'Above Bollinger Upper',
                'direction': 'bearish',
                'strength': min(50 + (pb - 1.0) * 100, 90),
                'value': round(pb, 2),
                'description': f'Price above upper band (%B = {pb:.2f})'
            })
        elif pb < 0.0:
            signals.append({
                'type': 'volatility',
                'name': 'Below Bollinger Lower',
                'direction': 'bullish',
                'strength': min(50 + abs(pb) * 100, 90),
                'value': round(pb, 2),
                'description': f'Price below lower band (%B = {pb:.2f})'
            })
        else:
            signals.append({
                'type': 'volatility',
                'name': 'Within Bollinger Bands',
                'direction': 'neutral',
                'strength': 50,
                'value': round(pb, 2),
                'description': f'Price within bands (%B = {pb:.2f})'
            })

    # 9. Moving Average Trend (Price vs SMA 50)
    if 'sma_50' in indicators and indicators['sma_50'] is not None:
        price = fundamentals.get('close_price')
        sma50 = indicators['sma_50']
        if price and sma50:
            diff_pct = ((price - sma50) / sma50) * 100
            if diff_pct > 2:
                signals.append({
                    'type': 'trend',
                    'name': 'Above SMA50',
                    'direction': 'bullish',
                    'strength': min(50 + diff_pct * 2, 85),
                    'value': round(diff_pct, 2),
                    'description': f'Price {diff_pct:.1f}% above SMA50'
                })
            elif diff_pct < -2:
                signals.append({
                    'type': 'trend',
                    'name': 'Below SMA50',
                    'direction': 'bearish',
                    'strength': min(50 + abs(diff_pct) * 2, 85),
                    'value': round(diff_pct, 2),
                    'description': f'Price {abs(diff_pct):.1f}% below SMA50'
                })
            else:
                signals.append({
                    'type': 'trend',
                    'name': 'Near SMA50',
                    'direction': 'neutral',
                    'strength': 50,
                    'value': round(diff_pct, 2),
                    'description': f'Price near SMA50 ({diff_pct:+.1f}%)'
                })

    return signals


@app.route('/api/stocks/<stock_id>/analysis', methods=['GET'])
def analyze_stock(stock_id):
    """
    Get complete analysis for a specific stock

    Args:
        stock_id: Stock symbol/code

    Returns:
        {
            "stock_id": "BBCA",
            "signals": [...],
            "fundamentals": {...},
            "indicators": {...}
        }
    """
    try:
        conn = storage._get_connection()
        cursor = conn.cursor()

        # Get all active signals for this stock
        cursor.execute("""
            SELECT signal_type, signal_name, strength, detected_date, metadata
            FROM signals
            WHERE stock_id = ?
            AND is_active = 1
            ORDER BY detected_date DESC
        """, (stock_id.upper(),))

        signals_rows = cursor.fetchall()
        signals = []

        for row in signals_rows:
            signal = {
                'type': row['signal_type'],
                'name': row['signal_name'],
                'strength': row['strength'],
                'date': row['detected_date'],
                'direction': 'bullish' if 'bullish' in row['signal_name'].lower() or
                             'golden' in row['signal_name'].lower() or
                             'buy' in row['signal_name'].lower()
                             else 'bearish' if 'bearish' in row['signal_name'].lower() or
                             'death' in row['signal_name'].lower() or
                             'sell' in row['signal_name'].lower()
                             else 'neutral'
            }
            signals.append(signal)

        # Get fundamental data
        cursor.execute("""
            SELECT *
            FROM fundamental_data
            WHERE stock_id = ?
            ORDER BY year DESC, quarter DESC
            LIMIT 1
        """, (stock_id.upper(),))

        fund_row = cursor.fetchone()
        fundamentals = {}

        if fund_row:
            fund_dict = dict(fund_row)

            # Get latest market price from price_data table
            cursor.execute("""
                SELECT close, date
                FROM price_data
                WHERE stock_id = ?
                ORDER BY date DESC
                LIMIT 1
            """, (stock_id.upper(),))

            latest_price_row = cursor.fetchone()
            latest_price = latest_price_row['close'] if latest_price_row else fund_dict.get('close_price')
            latest_price_date = latest_price_row['date'] if latest_price_row else None

            # Calculate real-time P/E and P/B ratios using latest price
            eps = fund_dict.get('eps')
            book_value = fund_dict.get('book_value')

            pe_ratio_realtime = RatioCalculator.pe_ratio_realtime(latest_price, eps) if eps else None
            pb_ratio_realtime = RatioCalculator.pb_ratio_realtime(latest_price, book_value) if book_value else None

            fundamentals = {
                # Latest Price (real-time)
                'close_price': latest_price,
                'price_date': latest_price_date,

                # Real-time Valuation Ratios (calculated with latest price)
                'pe_ratio': pe_ratio_realtime,
                'pb_ratio': pb_ratio_realtime,

                # Quarterly snapshot values (for reference)
                'pe_ratio_quarterly': fund_dict.get('pe_ratio'),
                'pb_ratio_quarterly': fund_dict.get('pb_ratio'),
                'close_price_quarterly': fund_dict.get('close_price'),

                # Profitability metrics
                'roe_percent': fund_dict.get('roe_percent'),
                'roa_percent': fund_dict.get('roa_percent'),

                # Financial health
                'debt_to_equity': fund_dict.get('debt_to_equity'),
                'current_ratio': fund_dict.get('current_ratio'),

                # Income statement
                'revenue': fund_dict.get('revenue'),
                'net_income': fund_dict.get('net_income'),

                # Balance sheet
                'total_assets': fund_dict.get('total_assets'),
                'total_equity': fund_dict.get('total_equity'),

                # Per-share values
                'eps': eps,
                'book_value': book_value,

                # Market cap (calculated with latest price)
                'market_cap': latest_price * fund_dict.get('shares_outstanding', 0) if latest_price and fund_dict.get('shares_outstanding') else None,

                # Report period
                'quarter': f"Q{fund_dict.get('quarter')}/{fund_dict.get('year')}"
            }

        # Get calculated metrics
        cursor.execute("""
            SELECT metric_name, value
            FROM fundamental_metrics
            WHERE stock_id = ?
            ORDER BY calculated_at DESC
        """, (stock_id.upper(),))

        metrics_rows = cursor.fetchall()
        calculated_metrics = {}

        for row in metrics_rows:
            metric_name = row['metric_name']
            if metric_name not in calculated_metrics:  # Keep most recent
                calculated_metrics[metric_name] = row['value']

        # Add important calculated metrics to fundamentals
        if 'peg_ratio' in calculated_metrics:
            fundamentals['peg_ratio'] = calculated_metrics['peg_ratio']
        if 'revenue_growth_yoy' in calculated_metrics:
            fundamentals['revenue_growth_yoy'] = calculated_metrics['revenue_growth_yoy']
        if 'eps_growth_yoy' in calculated_metrics:
            fundamentals['eps_growth_yoy'] = calculated_metrics['eps_growth_yoy']
        if 'roic' in calculated_metrics:
            fundamentals['roic'] = calculated_metrics['roic']
        if 'piotroski_score' in calculated_metrics:
            fundamentals['piotroski_score'] = calculated_metrics['piotroski_score']
        if 'altman_z_score' in calculated_metrics:
            fundamentals['altman_z_score'] = calculated_metrics['altman_z_score']

        # Get latest indicators
        cursor.execute("""
            SELECT indicator_name, value, date
            FROM indicators
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT 50
        """, (stock_id.upper(),))

        indicator_rows = cursor.fetchall()
        indicators = {}

        for row in indicator_rows:
            indicator_name = row['indicator_name']
            if indicator_name not in indicators:  # Keep most recent
                indicators[indicator_name] = row['value']

        conn.close()

        # Check if stock exists
        if not fundamentals and not indicators:
            return jsonify({'error': f'Stock not found: {stock_id}'}), 404

        # Calculate real-time signals from indicators
        realtime_signals = calculate_realtime_signals(indicators, fundamentals)

        # Add stored event-based signals to the list for additional context
        for stored_signal in signals:
            # Only add if it's not already covered by realtime signals
            signal_names = [s['name'] for s in realtime_signals]
            if stored_signal['name'] not in signal_names:
                realtime_signals.append({
                    'type': stored_signal['type'],
                    'name': stored_signal['name'],
                    'direction': stored_signal['direction'],
                    'strength': stored_signal['strength'],
                    'value': None,
                    'description': f"Detected on {stored_signal['date']}",
                    'date': stored_signal['date']
                })

        # Sanitize indicators to remove Infinity and NaN values
        sanitized_indicators = sanitize_json_value(indicators)
        sanitized_fundamentals = sanitize_json_value(fundamentals)

        return jsonify({
            'stock_id': stock_id.upper(),
            'signals': realtime_signals,
            'fundamentals': sanitized_fundamentals,
            'indicators': sanitized_indicators,
            'signal_summary': {
                'total': len(realtime_signals),
                'bullish': len([s for s in realtime_signals if s['direction'] == 'bullish']),
                'bearish': len([s for s in realtime_signals if s['direction'] == 'bearish']),
                'neutral': len([s for s in realtime_signals if s['direction'] == 'neutral'])
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks/<stock_id>/ohlc', methods=['GET'])
def get_stock_ohlc(stock_id):
    """
    Get OHLC data for a stock

    Args:
        stock_id: Stock symbol/code
        days: Number of days to fetch (default: 90, max: 365)

    Returns:
        {
            "stock_id": "BBCA",
            "data": [
                {
                    "date": "2024-01-01",
                    "open": 100.0,
                    "high": 105.0,
                    "low": 98.0,
                    "close": 102.0,
                    "volume": 1000000
                },
                ...
            ]
        }
    """
    try:
        days = min(int(request.args.get('days', 90)), 365)

        conn = storage._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date, open, high, low, close, volume
            FROM price_data
            WHERE stock_id = ?
            ORDER BY date DESC
            LIMIT ?
        """, (stock_id.upper(), days))

        rows = cursor.fetchall()

        if not rows:
            return jsonify({'error': 'No price data found for this stock'}), 404

        # Reverse to get chronological order
        data = []
        for row in reversed(rows):
            data.append({
                'date': row['date'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            })

        return jsonify({
            'stock_id': stock_id.upper(),
            'data': data
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Pattern Screening API',
        'version': '1.0.0'
    })


@app.route('/api/refresh-status', methods=['GET'])
def refresh_status():
    """Get status of automatic data refresh"""
    global last_refresh_status
    return jsonify({
        'last_refresh': last_refresh_status,
        'market_hours_active': is_market_hours(),
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'schedule': 'Every 5 minutes during Mon-Fri 09:00-16:00'
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Pattern Screening Web API")
    print("=" * 60)
    print("")
    print("Starting server at http://localhost:5001")
    print("")
    print("API Endpoints:")
    print("  GET    /api/patterns              - List all patterns")
    print("  GET    /api/patterns/:id          - Get pattern details")
    print("  POST   /api/patterns/:id/run      - Run screening")
    print("  POST   /api/patterns              - Create pattern")
    print("  PUT    /api/patterns/:id          - Update pattern")
    print("  DELETE /api/patterns/:id          - Delete pattern")
    print("  GET    /api/refresh-status        - Check auto-refresh status")
    print("")
    print("Web Interface:")
    print("  http://localhost:5001/")
    print("")
    print("=" * 60)
    print("")
    print("Automatic Data Refresh:")
    print("  Schedule: Every 5 minutes")
    print("  Active: Monday-Friday, 09:00-16:00")
    print("  Status: Check /api/refresh-status")
    print("")
    print("=" * 60)

    # Initialize background scheduler
    scheduler = BackgroundScheduler()

    # Schedule refresh every 5 minutes
    # The function itself checks if we're in market hours
    scheduler.add_job(
        func=refresh_intraday_data,
        trigger='interval',
        minutes=5,
        id='intraday_refresh',
        name='Intraday Data Refresh',
        replace_existing=True
    )

    # Start the scheduler
    scheduler.start()
    print("")
    print("✓ Background scheduler started")
    print("  Next refresh: Check /api/refresh-status")
    print("")

    try:
        app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        # Shutdown the scheduler gracefully
        scheduler.shutdown()
        print("\n✓ Scheduler shutdown complete")
