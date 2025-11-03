"""
Command-line interface for stock screener
"""

import click
import sys
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.storage import DataStorage
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Stock Screener CLI - Indonesian Stock Exchange Technical Analysis"""
    pass


@cli.command()
@click.option('--db-path', default=None, help='Database file path')
def init(db_path):
    """Initialize the database"""
    from scripts.init_db import init_database

    if db_path is None:
        config = get_config()
        db_path = config.get('database.path', 'database/stockCode.sqlite')

    click.echo(f"Initializing database at: {db_path}")
    init_database(db_path)
    click.echo(click.style("Database initialized successfully!", fg='green'))


@cli.command()
@click.option('--db-path', default=None, help='Database file path')
def stats(db_path):
    """Show database statistics"""
    storage = DataStorage(db_path)
    stats = storage.get_stats()

    click.echo("\n" + click.style("=== Database Statistics ===", fg='cyan', bold=True))
    click.echo(f"Active Stocks:      {stats.get('active_stocks', 0)}")
    click.echo(f"Price Records:      {stats.get('price_records', 0)}")
    click.echo(f"Indicator Records:  {stats.get('indicator_records', 0)}")
    click.echo(f"Active Signals:     {stats.get('active_signals', 0)}")
    click.echo(f"Latest Price Date:  {stats.get('latest_price_date', 'N/A')}")
    click.echo("")


@cli.command()
@click.option('--db-path', default=None, help='Database file path')
def update_stocks(db_path):
    """Fetch and update stock list"""
    storage = DataStorage(db_path)

    click.echo("Fetching stock list from IDX...")

    with click.progressbar(length=1, label='Updating stocks') as bar:
        count = storage.update_stock_list()
        bar.update(1)

    click.echo(click.style(f"Successfully updated {count} stocks!", fg='green'))


@cli.command()
@click.argument('stock_id')
@click.option('--days', default=365, help='Number of days of history to fetch')
@click.option('--db-path', default=None, help='Database file path')
def update_price(stock_id, days, db_path):
    """Update price data for a specific stock"""
    storage = DataStorage(db_path)

    click.echo(f"Updating price data for {stock_id}...")

    start_date = datetime.now() - timedelta(days=days)

    try:
        count = storage.update_price_data(stock_id, start_date=start_date)
        click.echo(click.style(f"Successfully stored {count} price records!", fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        raise click.Abort()


@cli.command()
@click.option('--limit', default=None, type=int, help='Limit number of stocks to update')
@click.option('--delay', default=1.0, type=float, help='Delay between requests (seconds)')
@click.option('--db-path', default=None, help='Database file path')
def update_all(limit, delay, db_path):
    """Update price data for all stocks"""
    storage = DataStorage(db_path)

    click.echo("Updating price data for all stocks...")

    if limit:
        click.echo(f"Limited to {limit} stocks")

    try:
        stats = storage.update_all_price_data(limit=limit, delay=delay)

        click.echo("\n" + click.style("=== Update Summary ===", fg='cyan', bold=True))
        click.echo(f"Total Stocks:    {stats['total_stocks']}")
        click.echo(f"Successful:      {stats['successful']}")
        click.echo(f"Failed:          {stats['failed']}")
        click.echo(f"Total Records:   {stats['total_records']}")
        click.echo("")

        if stats['successful'] > 0:
            click.echo(click.style("Update completed!", fg='green'))
        else:
            click.echo(click.style("No stocks updated", fg='yellow'))

    except KeyboardInterrupt:
        click.echo(click.style("\nUpdate interrupted by user", fg='yellow'))
        raise click.Abort()


@cli.command()
@click.option('--limit', default=20, type=int, help='Number of stocks to show')
@click.option('--db-path', default=None, help='Database file path')
def list_stocks(limit, db_path):
    """List all stocks in database"""
    storage = DataStorage(db_path)
    stocks = storage.get_all_stocks()

    if not stocks:
        click.echo(click.style("No stocks found in database", fg='yellow'))
        click.echo("Run 'update-stocks' command first to fetch stock list")
        return

    if limit:
        stocks = stocks[:limit]

    # Prepare table data
    headers = ['Stock ID', 'Name', 'Sector', 'Last Updated']
    rows = [
        [
            s['stock_id'],
            s['stock_name'] or 'N/A',
            s['sector'] or 'N/A',
            s['last_updated'] or 'Never'
        ]
        for s in stocks
    ]

    click.echo(f"\n{click.style('Stock List', fg='cyan', bold=True)} (showing {len(stocks)} stocks)\n")
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo("")


@cli.command()
@click.argument('stock_id')
@click.option('--limit', default=10, type=int, help='Number of records to show')
@click.option('--db-path', default=None, help='Database file path')
def show_price(stock_id, limit, db_path):
    """Show price data for a stock"""
    storage = DataStorage(db_path)

    price_data = storage.get_price_data(stock_id, limit=limit)

    if not price_data:
        click.echo(click.style(f"No price data found for {stock_id}", fg='yellow'))
        click.echo(f"Run 'update-price {stock_id}' to fetch data")
        return

    # Prepare table data
    headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    rows = [
        [
            p['date'],
            f"{p['open']:.2f}",
            f"{p['high']:.2f}",
            f"{p['low']:.2f}",
            f"{p['close']:.2f}",
            f"{p['volume']:,}"
        ]
        for p in price_data
    ]

    click.echo(f"\n{click.style(f'Price Data for {stock_id}', fg='cyan', bold=True)} (latest {len(price_data)} records)\n")
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo("")


@cli.command()
@click.argument('stock_id')
@click.option('--db-path', default=None, help='Database file path')
def quality(stock_id, db_path):
    """Show data quality report for a stock"""
    storage = DataStorage(db_path)

    click.echo(f"Generating quality report for {stock_id}...")

    report = storage.generate_quality_report(stock_id)

    click.echo("\n" + click.style(f"=== Quality Report for {stock_id} ===", fg='cyan', bold=True))
    click.echo(f"Total Records:    {report['total_records']}")
    click.echo(f"Valid Records:    {report['valid_records']}")
    click.echo(f"Invalid Records:  {report['invalid_records']}")
    click.echo(f"Outliers:         {report['outliers']}")
    click.echo(f"Date Gaps:        {report['gaps']}")

    score = report['quality_score']
    if score >= 90:
        color = 'green'
    elif score >= 70:
        color = 'yellow'
    else:
        color = 'red'

    click.echo(f"Quality Score:    {click.style(f'{score}%', fg=color, bold=True)}")
    click.echo("")


@cli.command()
@click.argument('stock_id')
@click.option('--db-path', default=None, help='Database file path')
def info(stock_id, db_path):
    """Show stock information"""
    storage = DataStorage(db_path)

    stock = storage.get_stock_info(stock_id)

    if not stock:
        click.echo(click.style(f"Stock {stock_id} not found", fg='red'))
        return

    click.echo("\n" + click.style(f"=== Stock Information ===", fg='cyan', bold=True))
    click.echo(f"Stock ID:      {stock['stock_id']}")
    click.echo(f"Stock Code:    {stock['stock_code']}")
    click.echo(f"Stock Name:    {stock['stock_name'] or 'N/A'}")
    click.echo(f"Sector:        {stock['sector'] or 'N/A'}")
    click.echo(f"Subsector:     {stock['subsector'] or 'N/A'}")
    click.echo(f"Last Updated:  {stock['last_updated'] or 'Never'}")
    click.echo(f"Active:        {stock['is_active']}")
    click.echo("")


@cli.command()
@click.argument('stock_id')
@click.option('--db-path', default=None, help='Database file path')
def calculate_indicators(stock_id, db_path):
    """Calculate technical indicators for a stock"""
    from src.indicators.calculator import IndicatorCalculator

    calc = IndicatorCalculator(db_path)

    click.echo(f"Calculating indicators for {stock_id}...")

    try:
        df = calc.calculate_indicators_for_stock(stock_id)

        if not df.empty:
            # Count indicator columns
            indicator_cols = [c for c in df.columns if c not in ['id', 'stock_id', 'open', 'high', 'low', 'close', 'volume']]

            click.echo(click.style(f"✓ Successfully calculated {len(indicator_cols)} indicators!", fg='green'))
            click.echo(f"  Data points: {len(df)}")
            click.echo(f"  Total indicator values: {len(df) * len(indicator_cols):,}")
        else:
            click.echo(click.style("No data to calculate indicators", fg='yellow'))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        raise click.Abort()


@cli.command()
@click.option('--limit', default=None, type=int, help='Limit number of stocks')
@click.option('--skip-existing', is_flag=True, default=True, help='Skip stocks with existing indicators')
@click.option('--db-path', default=None, help='Database file path')
def calculate_all_indicators(limit, skip_existing, db_path):
    """Calculate technical indicators for all stocks"""
    from src.indicators.calculator import IndicatorCalculator

    calc = IndicatorCalculator(db_path)

    click.echo("Calculating indicators for all stocks...")

    if limit:
        click.echo(f"Limited to {limit} stocks")

    try:
        stats = calc.calculate_indicators_for_all_stocks(limit=limit, skip_existing=skip_existing)

        click.echo("\n" + click.style("=== Indicator Calculation Summary ===", fg='cyan', bold=True))
        click.echo(f"Total Stocks:        {stats['total_stocks']}")
        click.echo(f"Successful:          {stats['successful']}")
        click.echo(f"Failed:              {stats['failed']}")
        click.echo(f"Skipped:             {stats['skipped']}")
        click.echo(f"Total Indicators:    {stats['total_indicators']:,}")
        click.echo("")

        if stats['successful'] > 0:
            click.echo(click.style("Indicator calculation completed!", fg='green'))
        else:
            click.echo(click.style("No indicators calculated", fg='yellow'))

    except KeyboardInterrupt:
        click.echo(click.style("\nCalculation interrupted by user", fg='yellow'))
        raise click.Abort()


@cli.command()
@click.argument('stock_id')
@click.option('--db-path', default=None, help='Database file path')
def show_indicators(stock_id, db_path):
    """Show latest indicator values for a stock"""
    from src.indicators.calculator import IndicatorCalculator

    calc = IndicatorCalculator(db_path)

    indicators = calc.get_latest_indicators(stock_id)

    if not indicators:
        click.echo(click.style(f"No indicators found for {stock_id}", fg='yellow'))
        click.echo(f"Run 'calculate-indicators {stock_id}' first")
        return

    click.echo(f"\n{click.style(f'Latest Indicators for {stock_id}', fg='cyan', bold=True)}\n")

    # Group by category
    trend = {k: v for k, v in indicators.items() if k.startswith(('sma', 'ema', 'macd', 'adx'))}
    momentum = {k: v for k, v in indicators.items() if k.startswith(('rsi', 'stoch', 'williams', 'cci', 'roc'))}
    volatility = {k: v for k, v in indicators.items() if k.startswith(('bb_', 'atr', 'percent_b', 'hist'))}
    volume_inds = {k: v for k, v in indicators.items() if k.startswith(('obv', 'volume', 'vwap', 'cmf', 'ad_', 'mfi', 'vpt'))}

    if trend:
        click.echo(click.style("Trend Indicators:", fg='green', bold=True))
        for name, value in sorted(trend.items()):
            click.echo(f"  {name:20s} {value:,.4f}")
        click.echo("")

    if momentum:
        click.echo(click.style("Momentum Indicators:", fg='blue', bold=True))
        for name, value in sorted(momentum.items()):
            click.echo(f"  {name:20s} {value:,.4f}")
        click.echo("")

    if volatility:
        click.echo(click.style("Volatility Indicators:", fg='yellow', bold=True))
        for name, value in sorted(volatility.items()):
            click.echo(f"  {name:20s} {value:,.4f}")
        click.echo("")

    if volume_inds:
        click.echo(click.style("Volume Indicators:", fg='magenta', bold=True))
        for name, value in sorted(volume_inds.items()):
            click.echo(f"  {name:20s} {value:,.4f}")
        click.echo("")


@cli.command()
@click.argument('stock_id')
@click.option('--db-path', default=None, help='Database file path')
def detect_signals(stock_id, db_path):
    """Detect trading signals for a stock"""
    from src.signals.engine import SignalEngine

    engine = SignalEngine(db_path)

    click.echo(f"Detecting signals for {stock_id}...")

    try:
        signals = engine.detect_signals_for_stock(stock_id)

        if signals:
            click.echo(click.style(f"\n✓ Detected {len(signals)} signals!", fg='green'))
            click.echo("")

            for signal in signals:
                # Color code by direction
                if signal.direction.value == 'bullish':
                    color = 'green'
                    arrow = '↑'
                elif signal.direction.value == 'bearish':
                    color = 'red'
                    arrow = '↓'
                else:
                    color = 'yellow'
                    arrow = '→'

                click.echo(click.style(f"{arrow} {signal.signal_name}", fg=color, bold=True))
                click.echo(f"   Type: {signal.signal_type.value}")
                click.echo(f"   Strength: {signal.strength:.1f}/100")
                click.echo(f"   Date: {signal.date}")
                if signal.price:
                    click.echo(f"   Price: {signal.price:,.2f}")
                click.echo("")
        else:
            click.echo(click.style("No signals detected", fg='yellow'))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        raise click.Abort()


@cli.command()
@click.option('--limit', default=None, type=int, help='Limit number of stocks')
@click.option('--skip-existing', is_flag=True, default=True, help='Skip stocks with recent signals')
@click.option('--db-path', default=None, help='Database file path')
def detect_all_signals(limit, skip_existing, db_path):
    """Detect trading signals for all stocks"""
    from src.signals.engine import SignalEngine

    engine = SignalEngine(db_path)

    click.echo("Detecting signals for all stocks...")

    if limit:
        click.echo(f"Limited to {limit} stocks")

    try:
        stats = engine.detect_signals_for_all_stocks(limit=limit, skip_existing=skip_existing)

        click.echo("\n" + click.style("=== Signal Detection Summary ===", fg='cyan', bold=True))
        click.echo(f"Total Stocks:        {stats['total_stocks']}")
        click.echo(f"Successful:          {stats['successful']}")
        click.echo(f"Failed:              {stats['failed']}")
        click.echo(f"Skipped:             {stats['skipped']}")
        click.echo(f"Total Signals:       {stats['total_signals']}")
        click.echo("")

        if stats['total_signals'] > 0:
            click.echo(click.style("Signal detection completed!", fg='green'))
        else:
            click.echo(click.style("No new signals detected", fg='yellow'))

    except KeyboardInterrupt:
        click.echo(click.style("\nSignal detection interrupted by user", fg='yellow'))
        raise click.Abort()


@cli.command()
@click.option('--signal-type', default=None, help='Filter by signal type (trend/momentum/volatility/volume)')
@click.option('--min-strength', default=50.0, type=float, help='Minimum signal strength')
@click.option('--limit', default=50, type=int, help='Number of signals to show')
@click.option('--db-path', default=None, help='Database file path')
def show_signals(signal_type, min_strength, limit, db_path):
    """Show detected signals across all stocks"""
    from src.signals.engine import SignalEngine

    engine = SignalEngine(db_path)

    signals = engine.get_signals_by_type(signal_type, min_strength, limit)

    if not signals:
        click.echo(click.style("No signals found", fg='yellow'))
        return

    click.echo(f"\n{click.style('Active Trading Signals', fg='cyan', bold=True)} (showing {len(signals)})\n")

    # Prepare table data
    headers = ['Stock', 'Signal', 'Type', 'Direction', 'Strength', 'Date']
    rows = []

    for sig in signals:
        # metadata is already a dict (parsed by db.get_signals)
        metadata = sig['metadata'] if sig['metadata'] else {}
        direction = metadata.get('direction', 'neutral')

        rows.append([
            sig['stock_id'],
            sig['signal_name'],
            sig['signal_type'],
            direction,
            f"{sig['strength']:.1f}",
            sig['detected_date']
        ])

    from tabulate import tabulate
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo("")


@cli.command()
@click.option('--limit', default=20, type=int, help='Number of opportunities to show')
@click.option('--db-path', default=None, help='Database file path')
def top_opportunities(limit, db_path):
    """Show top stock opportunities based on signal strength"""
    from src.signals.engine import SignalEngine

    engine = SignalEngine(db_path)

    opportunities = engine.get_top_opportunities(limit)

    if not opportunities:
        click.echo(click.style("No opportunities found", fg='yellow'))
        return

    click.echo(f"\n{click.style('Top Trading Opportunities', fg='green', bold=True)} (by signal strength)\n")

    for i, opp in enumerate(opportunities, 1):
        import json
        metadata = json.loads(opp['metadata']) if opp['metadata'] else {}
        direction = metadata.get('direction', 'neutral')

        if direction == 'bullish':
            color = 'green'
            arrow = '↑'
        elif direction == 'bearish':
            color = 'red'
            arrow = '↓'
        else:
            color = 'yellow'
            arrow = '→'

        click.echo(f"{i}. {click.style(opp['stock_id'], fg='cyan', bold=True)} - {opp['stock_name'] or 'N/A'}")
        click.echo(f"   {click.style(arrow + ' ' + opp['signal_name'], fg=color)}")
        strength_text = f"{opp['strength']:.1f}/100"
        click.echo(f"   Strength: {click.style(strength_text, fg=color, bold=True)} | Type: {opp['signal_type']} | Date: {opp['detected_date']}")
        click.echo("")


@cli.command()
@click.option('--delay', default=1.0, type=float, help='Delay between stock updates (seconds)')
@click.option('--limit', default=None, type=int, help='Limit number of stocks (for testing)')
@click.option('--skip-price-update', is_flag=True, help='Skip price update, only recalculate indicators and signals')
@click.option('--db-path', default=None, help='Database file path')
def refresh_intraday(delay, limit, skip_price_update, db_path):
    """
    Refresh intraday data: fetch latest prices, recalculate indicators, and detect signals.

    This command is designed to be called periodically (e.g., every 15 minutes during trading hours)
    to keep the screening data current.

    Example:
        python3 -m src.api.cli refresh-intraday --delay 1.0
    """
    import time
    from datetime import datetime

    start_time = datetime.now()

    click.echo("\n" + click.style("=== Intraday Data Refresh ===", fg='cyan', bold=True))
    click.echo(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Initialize components
    storage = DataStorage(db_path)

    from src.indicators.calculator import IndicatorCalculator
    from src.signals.engine import SignalEngine

    indicator_calc = IndicatorCalculator(db_path)
    signal_engine = SignalEngine(db_path)

    # Get all active stocks
    stocks = storage.db.get_all_stocks(active_only=True)

    if limit:
        stocks = stocks[:limit]
        click.echo(f"Limited to {limit} stocks\n")

    total_stocks = len(stocks)

    # Summary statistics
    summary = {
        'total_stocks': total_stocks,
        'prices_updated': 0,
        'prices_failed': 0,
        'indicators_updated': 0,
        'indicators_failed': 0,
        'signals_detected': 0,
        'signals_failed': 0,
        'total_new_signals': 0
    }

    # Step 1: Update prices (if not skipped)
    if not skip_price_update:
        click.echo(click.style("Step 1/3: Updating prices...", fg='yellow', bold=True))

        for i, stock in enumerate(stocks):
            stock_id = stock['stock_id']

            try:
                # Fetch latest data (incremental update from last date in DB)
                records = storage.update_price_data(stock_id)

                if records > 0:
                    summary['prices_updated'] += 1
                    click.echo(f"  [{i+1}/{total_stocks}] ✓ {stock_id} ({records} records)")
                else:
                    # No new records is still success (already up to date)
                    summary['prices_updated'] += 1
                    if (i + 1) % 100 == 0:
                        click.echo(f"  [{i+1}/{total_stocks}] Already up to date")

                # Rate limiting
                if delay > 0 and i < total_stocks - 1:
                    time.sleep(delay)

            except Exception as e:
                summary['prices_failed'] += 1
                click.echo(f"  [{i+1}/{total_stocks}] ✗ {stock_id}: {str(e)[:50]}")

        click.echo(f"\nPrice update: {summary['prices_updated']} succeeded, {summary['prices_failed']} failed\n")
    else:
        click.echo(click.style("Step 1/3: Skipping price update", fg='yellow', bold=True) + "\n")

    # Step 2: Recalculate indicators
    click.echo(click.style("Step 2/3: Recalculating indicators...", fg='yellow', bold=True))

    for i, stock in enumerate(stocks):
        stock_id = stock['stock_id']

        try:
            # Recalculate all indicators
            df = indicator_calc.calculate_indicators_for_stock(stock_id)

            if df is not None:
                summary['indicators_updated'] += 1
                if (i + 1) % 50 == 0 or i == 0:
                    click.echo(f"  [{i+1}/{total_stocks}] Processed...")
            else:
                summary['indicators_failed'] += 1

        except Exception as e:
            summary['indicators_failed'] += 1
            logger.error(f"Failed to calculate indicators for {stock_id}: {e}")

    click.echo(f"Indicator calculation: {summary['indicators_updated']} succeeded, {summary['indicators_failed']} failed\n")

    # Step 3: Detect signals
    click.echo(click.style("Step 3/3: Detecting signals...", fg='yellow', bold=True))

    # Deactivate old signals first
    from src.utils.config import get_config
    config = get_config()
    expiry_days = config.get('signals.signal_expiry_days', 5)
    deactivated = storage.db.deactivate_old_signals(expiry_days)
    click.echo(f"Deactivated {deactivated} old signals\n")

    for i, stock in enumerate(stocks):
        stock_id = stock['stock_id']

        try:
            # Detect signals (this will replace old signals for the stock)
            signals = signal_engine.detect_signals_for_stock(stock_id, store=True)

            if signals:
                summary['signals_detected'] += 1
                summary['total_new_signals'] += len(signals)
                if (i + 1) % 50 == 0 or i == 0:
                    click.echo(f"  [{i+1}/{total_stocks}] Processed... ({len(signals)} signals)")
            else:
                summary['signals_detected'] += 1

        except Exception as e:
            summary['signals_failed'] += 1
            logger.error(f"Failed to detect signals for {stock_id}: {e}")

    click.echo(f"Signal detection: {summary['signals_detected']} succeeded, {summary['signals_failed']} failed\n")

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    click.echo("\n" + click.style("=== Refresh Complete ===", fg='green', bold=True))
    click.echo(f"Duration: {duration.total_seconds():.1f} seconds")
    click.echo(f"\nPrices:     {summary['prices_updated']} updated, {summary['prices_failed']} failed")
    click.echo(f"Indicators: {summary['indicators_updated']} updated, {summary['indicators_failed']} failed")
    click.echo(f"Signals:    {summary['total_new_signals']} new signals detected")

    # Show current stats
    click.echo("\n" + click.style("=== Database Statistics ===", fg='cyan', bold=True))
    stats = storage.get_stats()
    click.echo(f"Active Stocks:      {stats['active_stocks']}")
    click.echo(f"Price Records:      {stats['price_records']}")
    click.echo(f"Indicator Records:  {stats['indicator_records']}")
    click.echo(f"Active Signals:     {stats['active_signals']}")
    click.echo(f"Latest Price Date:  {stats['latest_price_date']}")
    click.echo("")


# =============================================================================
# FUNDAMENTAL DATA COMMANDS
# =============================================================================

@cli.command()
@click.argument('stock_id')
@click.option('--quarters', default=8, type=int, help='Number of quarters to fetch')
@click.option('--db-path', default=None, help='Database file path')
def update_fundamentals(stock_id, quarters, db_path):
    """Fetch and store fundamental data for a stock"""
    from src.fundamentals.storage import FundamentalDataStorage

    storage = FundamentalDataStorage(db_path)

    click.echo(f"\nFetching fundamental data for {click.style(stock_id, fg='cyan', bold=True)}")
    click.echo(f"Quarters: {quarters}\n")

    stored = storage.fetch_and_store_multiple(stock_id, quarters)

    if stored > 0:
        click.echo(f"\n{click.style('✓', fg='green')} Stored {stored}/{quarters} quarters successfully")

        # Show latest data
        latest = storage.get_latest_quarter(stock_id)
        if latest:
            click.echo(f"\nLatest Quarter: Q{latest['quarter']} {latest['year']}")
            click.echo(f"Report Date: {latest['report_date']}")
            click.echo(f"Revenue: {latest['revenue']:,.0f}" if latest['revenue'] else "Revenue: N/A")
            click.echo(f"Net Income: {latest['net_income']:,.0f}" if latest['net_income'] else "Net Income: N/A")
            click.echo(f"EPS: {latest['eps']:.2f}" if latest['eps'] else "EPS: N/A")
            click.echo(f"ROE: {latest['roe_percent']:.2f}%" if latest['roe_percent'] else "ROE: N/A")
    else:
        click.echo(f"\n{click.style('✗', fg='red')} Failed to fetch fundamental data")


@cli.command()
@click.option('--quarters', default=8, type=int, help='Number of quarters per stock')
@click.option('--delay', default=1.0, type=float, help='Delay between stocks')
@click.option('--limit', default=None, type=int, help='Limit number of stocks')
@click.option('--db-path', default=None, help='Database file path')
def update_all_fundamentals(quarters, delay, limit, db_path):
    """Update fundamental data for all stocks"""
    from src.fundamentals.storage import FundamentalDataStorage

    storage = FundamentalDataStorage(db_path)

    click.echo("\n" + click.style("=== Update All Fundamentals ===", fg='cyan', bold=True))

    if limit:
        click.echo(f"Limited to {limit} stocks")

    click.echo(f"Quarters per stock: {quarters}")
    click.echo(f"Delay: {delay}s\n")

    stats = storage.update_all_stocks(
        num_quarters=quarters,
        delay=delay,
        limit=limit
    )

    click.echo("\n" + click.style("=== Update Complete ===", fg='green', bold=True))
    click.echo(f"Total Stocks:     {stats['total_stocks']}")
    click.echo(f"Successful:       {stats['successful']}")
    click.echo(f"Failed:           {stats['failed']}")
    click.echo(f"Quarters Stored:  {stats['total_quarters_stored']}")
    click.echo("")


@cli.command()
@click.argument('stock_id')
@click.option('--quarters', default=4, type=int, help='Number of quarters to show')
@click.option('--db-path', default=None, help='Database file path')
def show_fundamentals(stock_id, quarters, db_path):
    """Show fundamental data for a stock"""
    from src.fundamentals.storage import FundamentalDataStorage

    storage = FundamentalDataStorage(db_path)

    click.echo(f"\n{click.style('=== Fundamental Data: ' + stock_id + ' ===', fg='cyan', bold=True)}\n")

    # Get latest quarters
    data_list = storage.get_quarters(stock_id, quarters)

    if not data_list:
        click.echo(click.style("No fundamental data found", fg='yellow'))
        click.echo(f"\nTry: python3 -m src.api.cli update-fundamentals {stock_id}")
        return

    # Show quarterly data
    for i, data in enumerate(data_list):
        if i > 0:
            click.echo("")

        quarter_label = f"Q{data['quarter']} {data['year']}"
        click.echo(click.style(quarter_label, fg='cyan', bold=True))
        click.echo(f"Report Date: {data['report_date']}")

        # Income Statement
        click.echo("\n" + click.style("Income Statement:", fg='yellow'))
        if data['revenue']:
            click.echo(f"  Revenue:          {data['revenue']:>15,.0f}")
        if data['gross_profit']:
            click.echo(f"  Gross Profit:     {data['gross_profit']:>15,.0f}")
        if data['operating_profit']:
            click.echo(f"  Operating Profit: {data['operating_profit']:>15,.0f}")
        if data['net_income']:
            click.echo(f"  Net Income:       {data['net_income']:>15,.0f}")

        # Ratios
        click.echo("\n" + click.style("Key Ratios:", fg='yellow'))
        if data['eps']:
            click.echo(f"  EPS:              {data['eps']:>15,.2f}")
        if data['roe_percent']:
            click.echo(f"  ROE:              {data['roe_percent']:>14,.2f}%")
        if data['roa_percent']:
            click.echo(f"  ROA:              {data['roa_percent']:>14,.2f}%")
        if data['npm_percent']:
            click.echo(f"  Net Margin:       {data['npm_percent']:>14,.2f}%")

        # Valuation
        click.echo("\n" + click.style("Valuation:", fg='yellow'))
        if data['pe_ratio']:
            click.echo(f"  P/E Ratio:        {data['pe_ratio']:>15,.2f}")
        if data['pb_ratio']:
            click.echo(f"  P/B Ratio:        {data['pb_ratio']:>15,.2f}")

        # Balance Sheet
        click.echo("\n" + click.style("Balance Sheet:", fg='yellow'))
        if data['total_assets']:
            click.echo(f"  Total Assets:     {data['total_assets']:>15,.0f}")
        if data['total_liabilities']:
            click.echo(f"  Total Liabilities:{data['total_liabilities']:>15,.0f}")
        if data['total_equity']:
            click.echo(f"  Total Equity:     {data['total_equity']:>15,.0f}")
        if data['debt_equity_ratio']:
            click.echo(f"  D/E Ratio:        {data['debt_equity_ratio']:>15,.2f}")

    click.echo("")


@cli.command()
@click.option('--db-path', default=None, help='Database file path')
def fundamental_stats(db_path):
    """Show fundamental data statistics"""
    from src.fundamentals.storage import FundamentalDataStorage

    storage = FundamentalDataStorage(db_path)
    stats = storage.get_stats()

    click.echo("\n" + click.style("=== Fundamental Data Statistics ===", fg='cyan', bold=True))
    click.echo(f"Total Records:         {stats['total_records']}")
    click.echo(f"Stocks with Data:      {stats['stocks_with_data']}")
    click.echo(f"Avg Quarters/Stock:    {stats['avg_quarters_per_stock']}")
    click.echo(f"Latest Report Date:    {stats['latest_report_date']}")
    click.echo("")


# =============================================================================
# FUNDAMENTAL METRICS COMMANDS
# =============================================================================

@cli.command()
@click.argument('stock_id')
@click.option('--db-path', default=None, help='Database file path')
def calculate_metrics(stock_id, db_path):
    """Calculate fundamental metrics for a stock (growth, ratios, quality, TTM)"""
    from src.fundamentals.storage import FundamentalDataStorage
    from src.fundamentals.growth import GrowthCalculator
    from src.fundamentals.ratios import RatioCalculator
    from src.fundamentals.quality import QualityScorer
    from src.fundamentals.ttm import TTMCalculator

    storage = FundamentalDataStorage(db_path)

    click.echo(f"\n{click.style('Calculating metrics for ' + stock_id, fg='cyan', bold=True)}\n")

    # Get quarterly data (need at least 8 quarters for comprehensive analysis)
    quarters = storage.get_quarters(stock_id, num_quarters=8)

    if not quarters:
        click.echo(click.style("No fundamental data found", fg='red'))
        click.echo(f"\nRun: python3 -m src.api.cli update-fundamentals {stock_id}")
        return

    click.echo(f"Found {len(quarters)} quarters of data")

    # Initialize calculators
    growth_calc = GrowthCalculator()
    ratio_calc = RatioCalculator()
    quality_scorer = QualityScorer()
    ttm_calc = TTMCalculator(db_path)

    # Calculate growth metrics
    click.echo("\n" + click.style("📈 Growth Metrics:", fg='green'))
    growth_metrics = growth_calc.calculate_all_growth_metrics(quarters)
    if growth_metrics:
        for metric, value in sorted(growth_metrics.items()):
            if value is not None:
                click.echo(f"  {metric:30s} {value:>10,.2f}{'%' if 'growth' in metric or 'cagr' in metric or 'trend' in metric else ''}")
    else:
        click.echo("  Insufficient data for growth metrics")

    # Calculate ratios (use latest quarter)
    latest = quarters[0]
    click.echo("\n" + click.style("📊 Financial Ratios:", fg='blue'))

    liquidity = ratio_calc.calculate_liquidity_ratios(latest)
    if liquidity:
        click.echo("  Liquidity:")
        for metric, value in sorted(liquidity.items()):
            click.echo(f"    {metric:28s} {value:>10,.2f}")

    leverage = ratio_calc.calculate_leverage_ratios(latest)
    if leverage:
        click.echo("  Leverage:")
        for metric, value in sorted(leverage.items()):
            click.echo(f"    {metric:28s} {value:>10,.2f}")

    efficiency = ratio_calc.calculate_efficiency_ratios(latest)
    if efficiency:
        click.echo("  Efficiency:")
        for metric, value in sorted(efficiency.items()):
            click.echo(f"    {metric:28s} {value:>10,.2f}")

    valuation = ratio_calc.calculate_valuation_ratios(latest)
    if valuation:
        click.echo("  Valuation:")
        for metric, value in sorted(valuation.items()):
            if value > 1e9:  # Format large numbers (market cap, EV)
                click.echo(f"    {metric:28s} {value:>10,.0f}")
            else:
                click.echo(f"    {metric:28s} {value:>10,.2f}")

    # Calculate quality scores (need current and previous year)
    click.echo("\n" + click.style("⭐ Quality Scores:", fg='yellow'))

    previous = quarters[4] if len(quarters) >= 5 else None

    # Piotroski F-Score
    if previous:
        f_score, f_components = quality_scorer.piotroski_f_score(latest, previous)

        # Color code based on score
        if f_score >= 8:
            score_color = 'green'
            score_label = 'Strong'
        elif f_score >= 5:
            score_color = 'yellow'
            score_label = 'Average'
        else:
            score_color = 'red'
            score_label = 'Weak'

        click.echo(f"  Piotroski F-Score:     {click.style(f'{f_score}/9', fg=score_color, bold=True)} ({score_label})")
        click.echo("    Components:")
        for component, score in f_components.items():
            symbol = '✓' if score == 1 else '✗'
            color = 'green' if score == 1 else 'red'
            click.echo(f"      {click.style(symbol, fg=color)} {component}")

    # Altman Z-Score
    z_score = quality_scorer.altman_z_score(latest)
    if z_score:
        z_interpretation = quality_scorer.interpret_z_score(z_score)

        if z_score > 3.0:
            z_color = 'green'
        elif z_score >= 1.8:
            z_color = 'yellow'
        else:
            z_color = 'red'

        click.echo(f"  Altman Z-Score:        {click.style(f'{z_score:.2f}', fg=z_color, bold=True)} ({z_interpretation})")

    # Cash quality
    cash_quality = quality_scorer.cash_quality_score(
        latest.get('cf_operating'),
        latest.get('net_income')
    )
    if cash_quality:
        cq_color = 'green' if cash_quality > 1.0 else 'yellow' if cash_quality > 0.8 else 'red'
        click.echo(f"  Cash Quality Ratio:    {click.style(f'{cash_quality:.2f}', fg=cq_color)}")

    # TTM metrics
    if len(quarters) >= 4:
        click.echo("\n" + click.style("📅 TTM (Trailing 12 Months):", fg='magenta'))
        ttm_metrics = ttm_calc.calculate_all_ttm_metrics(quarters)

        if ttm_metrics:
            # Group TTM metrics
            ttm_income = {k: v for k, v in ttm_metrics.items() if k.startswith('ttm_') and k not in ['ttm_gross_margin', 'ttm_operating_margin', 'ttm_net_margin', 'ttm_roe', 'ttm_roa', 'ttm_roic', 'ttm_cf_operating', 'ttm_cf_investing', 'ttm_cf_financing']}
            ttm_margins = {k: v for k, v in ttm_metrics.items() if 'margin' in k}
            ttm_returns = {k: v for k, v in ttm_metrics.items() if k in ['ttm_roe', 'ttm_roa', 'ttm_roic']}
            ttm_cf = {k: v for k, v in ttm_metrics.items() if k.startswith('ttm_cf_')}

            if ttm_income:
                click.echo("  Income Statement:")
                for metric, value in sorted(ttm_income.items()):
                    if value is not None:
                        click.echo(f"    {metric:28s} {value:>15,.0f}")

            if ttm_margins:
                click.echo("  Margins:")
                for metric, value in sorted(ttm_margins.items()):
                    if value is not None:
                        click.echo(f"    {metric:28s} {value:>14,.2f}%")

            if ttm_returns:
                click.echo("  Returns:")
                for metric, value in sorted(ttm_returns.items()):
                    if value is not None:
                        click.echo(f"    {metric:28s} {value:>14,.2f}%")

            if ttm_cf:
                click.echo("  Cash Flow:")
                for metric, value in sorted(ttm_cf.items()):
                    if value is not None:
                        click.echo(f"    {metric:28s} {value:>15,.0f}")

            # Store TTM metrics
            ttm_calc.store_ttm_metrics(stock_id, latest['report_date'], ttm_metrics)
            click.echo(f"\n  {click.style('✓', fg='green')} TTM metrics stored in database")
    else:
        click.echo("\n" + click.style("Need at least 4 quarters for TTM calculation", fg='yellow'))

    click.echo(f"\n{click.style('✓ Metrics calculation complete', fg='green')}\n")


@cli.command()
@click.option('--limit', default=None, type=int, help='Limit number of stocks')
@click.option('--db-path', default=None, help='Database file path')
def calculate_all_metrics(limit, db_path):
    """Calculate fundamental metrics for all stocks with fundamental data"""
    from src.fundamentals.storage import FundamentalDataStorage
    from src.fundamentals.growth import GrowthCalculator
    from src.fundamentals.ratios import RatioCalculator
    from src.fundamentals.quality import QualityScorer
    from src.fundamentals.ttm import TTMCalculator

    storage = FundamentalDataStorage(db_path)

    click.echo("\n" + click.style("=== Calculate Metrics for All Stocks ===", fg='cyan', bold=True))

    # Get all stocks with fundamental data
    query = """
        SELECT DISTINCT stock_id
        FROM fundamental_data
        ORDER BY stock_id
    """
    stocks_result = storage.db.execute_query(query)
    stocks = [row['stock_id'] for row in stocks_result]

    if limit:
        stocks = stocks[:limit]
        click.echo(f"Limited to {limit} stocks")

    total_stocks = len(stocks)
    click.echo(f"Processing {total_stocks} stocks\n")

    # Initialize calculators
    growth_calc = GrowthCalculator()
    ratio_calc = RatioCalculator()
    quality_scorer = QualityScorer()
    ttm_calc = TTMCalculator(db_path)

    # Statistics
    stats = {
        'total_stocks': total_stocks,
        'successful': 0,
        'failed': 0,
        'insufficient_data': 0,
        'ttm_calculated': 0
    }

    for i, stock_id in enumerate(stocks):
        try:
            click.echo(f"[{i+1}/{total_stocks}] {stock_id}...", nl=False)

            # Get quarters
            quarters = storage.get_quarters(stock_id, num_quarters=8)

            if not quarters or len(quarters) < 2:
                click.echo(click.style(" insufficient data", fg='yellow'))
                stats['insufficient_data'] += 1
                continue

            # Calculate growth metrics
            growth_metrics = growth_calc.calculate_all_growth_metrics(quarters)

            # Calculate TTM if enough data
            if len(quarters) >= 4:
                ttm_metrics = ttm_calc.calculate_all_ttm_metrics(quarters)
                if ttm_metrics:
                    latest = quarters[0]
                    ttm_calc.store_ttm_metrics(stock_id, latest['report_date'], ttm_metrics)
                    stats['ttm_calculated'] += 1

            click.echo(click.style(" ✓", fg='green'))
            stats['successful'] += 1

        except Exception as e:
            click.echo(click.style(f" ✗ {str(e)}", fg='red'))
            stats['failed'] += 1

    # Summary
    click.echo("\n" + click.style("=== Calculation Complete ===", fg='cyan', bold=True))
    click.echo(f"Total Stocks:        {stats['total_stocks']}")
    click.echo(f"Successful:          {stats['successful']}")
    click.echo(f"Failed:              {stats['failed']}")
    click.echo(f"Insufficient Data:   {stats['insufficient_data']}")
    click.echo(f"TTM Calculated:      {stats['ttm_calculated']}")
    click.echo("")

    if stats['successful'] > 0:
        click.echo(click.style("✓ Metrics calculation completed!", fg='green'))
    else:
        click.echo(click.style("No metrics calculated", fg='yellow'))


@cli.command()
@click.argument('stock_id')
@click.option('--db-path', default=None, help='Database file path')
def show_metrics(stock_id, db_path):
    """Show calculated fundamental metrics for a stock"""
    from src.fundamentals.ttm import TTMCalculator

    ttm_calc = TTMCalculator(db_path)

    click.echo(f"\n{click.style('=== Calculated Metrics: ' + stock_id + ' ===', fg='cyan', bold=True)}\n")

    # Get TTM metrics
    ttm_metrics = ttm_calc.get_ttm_metrics(stock_id)

    if not ttm_metrics:
        click.echo(click.style("No calculated metrics found", fg='yellow'))
        click.echo(f"\nRun: python3 -m src.api.cli calculate-metrics {stock_id}")
        return

    click.echo(f"As of: {ttm_metrics['as_of_date']}")

    # Income Statement
    click.echo("\n" + click.style("TTM Income Statement:", fg='green'))
    if ttm_metrics.get('ttm_revenue'):
        click.echo(f"  Revenue:          {ttm_metrics['ttm_revenue']:>15,.0f}")
    if ttm_metrics.get('ttm_gross_profit'):
        click.echo(f"  Gross Profit:     {ttm_metrics['ttm_gross_profit']:>15,.0f}")
    if ttm_metrics.get('ttm_operating_profit'):
        click.echo(f"  Operating Profit: {ttm_metrics['ttm_operating_profit']:>15,.0f}")
    if ttm_metrics.get('ttm_net_income'):
        click.echo(f"  Net Income:       {ttm_metrics['ttm_net_income']:>15,.0f}")
    if ttm_metrics.get('ttm_eps'):
        click.echo(f"  EPS:              {ttm_metrics['ttm_eps']:>15,.2f}")

    # Margins
    click.echo("\n" + click.style("TTM Margins:", fg='blue'))
    if ttm_metrics.get('ttm_gross_margin'):
        click.echo(f"  Gross Margin:     {ttm_metrics['ttm_gross_margin']:>14,.2f}%")
    if ttm_metrics.get('ttm_operating_margin'):
        click.echo(f"  Operating Margin: {ttm_metrics['ttm_operating_margin']:>14,.2f}%")
    if ttm_metrics.get('ttm_net_margin'):
        click.echo(f"  Net Margin:       {ttm_metrics['ttm_net_margin']:>14,.2f}%")

    # Returns
    click.echo("\n" + click.style("TTM Returns:", fg='yellow'))
    if ttm_metrics.get('ttm_roe'):
        click.echo(f"  ROE:              {ttm_metrics['ttm_roe']:>14,.2f}%")
    if ttm_metrics.get('ttm_roa'):
        click.echo(f"  ROA:              {ttm_metrics['ttm_roa']:>14,.2f}%")
    if ttm_metrics.get('ttm_roic'):
        click.echo(f"  ROIC:             {ttm_metrics['ttm_roic']:>14,.2f}%")

    # Cash Flow
    click.echo("\n" + click.style("TTM Cash Flow:", fg='magenta'))
    if ttm_metrics.get('ttm_cf_operating'):
        click.echo(f"  Operating CF:     {ttm_metrics['ttm_cf_operating']:>15,.0f}")
    if ttm_metrics.get('ttm_cf_investing'):
        click.echo(f"  Investing CF:     {ttm_metrics['ttm_cf_investing']:>15,.0f}")
    if ttm_metrics.get('ttm_cf_financing'):
        click.echo(f"  Financing CF:     {ttm_metrics['ttm_cf_financing']:>15,.0f}")

    click.echo("")


# =============================================================================
# FUNDAMENTAL SCREENING COMMANDS
# =============================================================================

@cli.command()
@click.option('--screen-type',
              type=click.Choice(['value', 'growth', 'quality', 'health', 'composite']),
              required=True,
              help='Type of screen to run')
@click.option('--criterion',
              type=click.Choice([
                  'low-pe', 'low-pb', 'low-ps',  # Value
                  'revenue-growth', 'eps-growth', 'accelerating',  # Growth
                  'high-piotroski', 'high-roe', 'high-margins',  # Quality
                  'strong-liquidity', 'low-debt', 'safe-zscore', 'positive-cf',  # Health
                  'garp', 'magic-formula', 'financial-strength'  # Composite
              ]),
              required=True,
              help='Specific screening criterion')
@click.option('--limit', default=50, type=int, help='Maximum results to show')
@click.option('--db-path', default=None, help='Database file path')
def screen_fundamental(screen_type, criterion, limit, db_path):
    """
    Screen stocks based on fundamental criteria

    Examples:
        python3 -m src.api.cli screen-fundamental --screen-type value --criterion low-pe
        python3 -m src.api.cli screen-fundamental --screen-type growth --criterion revenue-growth
        python3 -m src.api.cli screen-fundamental --screen-type composite --criterion garp
    """
    from src.fundamentals.screener import FundamentalScreener

    screener = FundamentalScreener(db_path)

    click.echo(f"\n{click.style('=== Fundamental Screening ===', fg='cyan', bold=True)}")
    click.echo(f"Screen Type: {screen_type.title()}")
    click.echo(f"Criterion: {criterion.replace('-', ' ').title()}\n")

    # Run appropriate screen
    results = []

    if criterion == 'low-pe':
        results = screener.screen_low_pe(max_pe=15.0)
    elif criterion == 'low-pb':
        results = screener.screen_low_pb(max_pb=1.5)
    elif criterion == 'low-ps':
        results = screener.screen_low_ps(max_ps=2.0)
    elif criterion == 'revenue-growth':
        results = screener.screen_revenue_growth(min_growth_yoy=20.0)
    elif criterion == 'eps-growth':
        results = screener.screen_eps_growth(min_growth_yoy=15.0)
    elif criterion == 'accelerating':
        results = screener.screen_accelerating_growth()
    elif criterion == 'high-piotroski':
        results = screener.screen_high_piotroski(min_score=7)
    elif criterion == 'high-roe':
        results = screener.screen_high_roe(min_roe=15.0)
    elif criterion == 'high-margins':
        results = screener.screen_high_margins(min_npm=15.0)
    elif criterion == 'strong-liquidity':
        results = screener.screen_strong_liquidity(min_current_ratio=2.0)
    elif criterion == 'low-debt':
        results = screener.screen_low_debt(max_debt_to_assets=0.4)
    elif criterion == 'safe-zscore':
        results = screener.screen_safe_zscore(min_zscore=3.0)
    elif criterion == 'positive-cf':
        results = screener.screen_positive_cash_flow()
    elif criterion == 'garp':
        results = screener.screen_garp(max_peg=1.0, min_growth=10.0, min_roe=12.0)
    elif criterion == 'magic-formula':
        results = screener.screen_magic_formula(min_roic=12.0, max_ev_ebitda=15.0)
    elif criterion == 'financial-strength':
        results = screener.screen_financial_strength()

    if not results:
        click.echo(click.style("No stocks matched the criteria", fg='yellow'))
        return

    # Limit results
    if limit:
        results = results[:limit]

    click.echo(f"{click.style(f'Found {len(results)} stocks', fg='green', bold=True)}\n")

    # Display results
    from tabulate import tabulate

    if criterion == 'low-pe':
        headers = ['Stock', 'P/E', 'EPS', 'Price', 'ROE %', 'Net Income']
        rows = [[r['stock_id'], f"{r['pe_ratio']:.2f}", f"{r['eps']:.2f}",
                 f"{r['close_price']:.0f}", f"{r.get('roe_percent', 0):.2f}",
                 f"{r['net_income']:,.0f}"] for r in results]

    elif criterion == 'low-pb':
        headers = ['Stock', 'P/B', 'Book Value', 'Price', 'ROE %', 'ROA %']
        rows = [[r['stock_id'], f"{r['pb_ratio']:.2f}", f"{r['book_value']:.2f}",
                 f"{r['close_price']:.0f}", f"{r.get('roe_percent', 0):.2f}",
                 f"{r.get('roa_percent', 0):.2f}"] for r in results]

    elif criterion == 'low-ps':
        headers = ['Stock', 'P/S', 'Revenue', 'NPM %', 'ROE %']
        rows = [[r['stock_id'], f"{r['ps_ratio']:.2f}", f"{r['revenue']:,.0f}",
                 f"{r.get('npm_percent', 0):.2f}", f"{r.get('roe_percent', 0):.2f}"] for r in results]

    elif criterion in ['revenue-growth', 'eps-growth']:
        if criterion == 'revenue-growth':
            headers = ['Stock', 'Rev Growth YoY', 'Rev Growth QoQ', 'Revenue', 'NPM %']
            rows = [[r['stock_id'], f"{r['revenue_growth_yoy']:.2f}%",
                     f"{r.get('revenue_growth_qoq', 0):.2f}%", f"{r['revenue']:,.0f}",
                     f"{r.get('npm_percent', 0):.2f}"] for r in results]
        else:
            headers = ['Stock', 'EPS Growth YoY', 'EPS Growth QoQ', 'EPS', 'P/E']
            rows = [[r['stock_id'], f"{r['eps_growth_yoy']:.2f}%",
                     f"{r.get('eps_growth_qoq', 0):.2f}%", f"{r['eps']:.2f}",
                     f"{r.get('pe_ratio', 0):.2f}"] for r in results]

    elif criterion == 'accelerating':
        headers = ['Stock', 'Rev Growth YoY', 'Rev Growth QoQ', 'Revenue', 'NPM %']
        rows = [[r['stock_id'], f"{r.get('revenue_growth_yoy', 0):.2f}%",
                 f"{r.get('revenue_growth_qoq', 0):.2f}%", f"{r['revenue']:,.0f}",
                 f"{r.get('npm_percent', 0):.2f}"] for r in results]

    elif criterion == 'high-piotroski':
        headers = ['Stock', 'F-Score', 'ROE %', 'ROA %', 'NPM %', 'P/E']
        rows = [[r['stock_id'], r['piotroski_score'], f"{r.get('roe_percent', 0):.2f}",
                 f"{r.get('roa_percent', 0):.2f}", f"{r.get('npm_percent', 0):.2f}",
                 f"{r.get('pe_ratio', 0):.2f}"] for r in results]

    elif criterion == 'high-roe':
        headers = ['Stock', 'ROE %', 'ROA %', 'NPM %', 'P/E', 'Net Income']
        rows = [[r['stock_id'], f"{r['roe_percent']:.2f}", f"{r.get('roa_percent', 0):.2f}",
                 f"{r.get('npm_percent', 0):.2f}", f"{r.get('pe_ratio', 0):.2f}",
                 f"{r['net_income']:,.0f}"] for r in results]

    elif criterion == 'high-margins':
        headers = ['Stock', 'NPM %', 'OPM %', 'GM %', 'ROE %', 'Revenue']
        rows = [[r['stock_id'], f"{r['npm_percent']:.2f}",
                 f"{r.get('opm_percent', 0):.2f}", f"{r.get('gross_margin_percent', 0):.2f}",
                 f"{r.get('roe_percent', 0):.2f}", f"{r['revenue']:,.0f}"] for r in results]

    elif criterion == 'strong-liquidity':
        headers = ['Stock', 'Current Ratio', 'Current Assets', 'Current Liab', 'ROE %']
        rows = [[r['stock_id'], f"{r['current_ratio']:.2f}", f"{r['current_assets']:,.0f}",
                 f"{r['current_liabilities']:,.0f}", f"{r.get('roe_percent', 0):.2f}"] for r in results]

    elif criterion == 'low-debt':
        headers = ['Stock', 'D/A Ratio', 'Total Assets', 'Total Liab', 'ROE %']
        rows = [[r['stock_id'], f"{r['debt_to_assets']:.2f}", f"{r['total_assets']:,.0f}",
                 f"{r['total_liabilities']:,.0f}", f"{r.get('roe_percent', 0):.2f}"] for r in results]

    elif criterion == 'safe-zscore':
        headers = ['Stock', 'Z-Score', 'Total Assets', 'Total Equity', 'Revenue']
        rows = [[r['stock_id'], f"{r['altman_z_score']:.2f}", f"{r['total_assets']:,.0f}",
                 f"{r['total_equity']:,.0f}", f"{r['revenue']:,.0f}"] for r in results]

    elif criterion == 'positive-cf':
        headers = ['Stock', 'OCF', 'Cash Quality', 'Net Income', 'Revenue']
        rows = [[r['stock_id'], f"{r['cf_operating']:,.0f}",
                 f"{r.get('cash_quality', 0):.2f}", f"{r['net_income']:,.0f}",
                 f"{r['revenue']:,.0f}"] for r in results]

    elif criterion == 'garp':
        headers = ['Stock', 'PEG', 'P/E', 'EPS Growth', 'ROE %', 'EPS']
        rows = [[r['stock_id'], f"{r['peg_ratio']:.2f}", f"{r['pe_ratio']:.2f}",
                 f"{r['eps_growth_yoy']:.2f}%", f"{r['roe_percent']:.2f}",
                 f"{r['eps']:.2f}"] for r in results]

    elif criterion == 'magic-formula':
        headers = ['Stock', 'ROIC %', 'EV/EBITDA', 'Revenue (TTM)', 'Market Cap']
        rows = [[r['stock_id'], f"{r['roic']:.2f}", f"{r['ev_ebitda']:.2f}",
                 f"{r['ttm_revenue']:,.0f}", f"{r['market_cap']:,.0f}"] for r in results]

    elif criterion == 'financial-strength':
        headers = ['Stock', 'F-Score', 'Current Ratio', 'D/A', 'OCF', 'ROE %']
        rows = [[r['stock_id'], r['piotroski_score'], f"{r['current_ratio']:.2f}",
                 f"{r['debt_to_assets']:.2f}", f"{r['cf_operating']:,.0f}",
                 f"{r.get('roe_percent', 0):.2f}"] for r in results]

    else:
        # Generic display
        headers = ['Stock'] + list(results[0].keys())[1:]
        rows = [[r['stock_id']] + list(r.values())[1:] for r in results]

    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo("")


@cli.command()
@click.option('--db-path', default=None, help='Database file path')
def list_screens(db_path):
    """List all available fundamental screening criteria"""

    click.echo(f"\n{click.style('=== Available Fundamental Screens ===', fg='cyan', bold=True)}\n")

    screens = {
        'Value Screens': [
            ('low-pe', 'Low P/E Ratio', 'P/E <= 15, positive earnings'),
            ('low-pb', 'Low P/B Ratio', 'P/B <= 1.5, positive equity'),
            ('low-ps', 'Low Price/Sales', 'P/S <= 2.0'),
        ],
        'Growth Screens': [
            ('revenue-growth', 'High Revenue Growth', 'YoY growth >= 20%'),
            ('eps-growth', 'High EPS Growth', 'YoY growth >= 15%'),
            ('accelerating', 'Accelerating Growth', 'Growth rate increasing'),
        ],
        'Quality Screens': [
            ('high-piotroski', 'High Piotroski Score', 'F-Score >= 7 (out of 9)'),
            ('high-roe', 'High ROE', 'ROE >= 15%'),
            ('high-margins', 'High Profit Margins', 'Net margin >= 15%'),
        ],
        'Health Screens': [
            ('strong-liquidity', 'Strong Liquidity', 'Current ratio >= 2.0'),
            ('low-debt', 'Low Debt', 'Debt/Assets <= 0.4'),
            ('safe-zscore', 'Safe Z-Score', 'Altman Z-Score >= 3.0'),
            ('positive-cf', 'Positive Cash Flow', 'Operating CF > 0'),
        ],
        'Composite Screens': [
            ('garp', 'GARP Strategy', 'Growth at Reasonable Price (PEG<1, Growth>10%, ROE>12%)'),
            ('magic-formula', 'Magic Formula', 'Quality + Value (ROIC>12%, EV/EBITDA<15)'),
            ('financial-strength', 'Financial Strength', 'F-Score>=7, Current>=2, D/A<=0.5, OCF>0'),
        ]
    }

    for category, criteria in screens.items():
        click.echo(click.style(category, fg='green', bold=True))
        for criterion, name, description in criteria:
            click.echo(f"  {click.style(criterion, fg='cyan'):25s} - {name:25s} ({description})")
        click.echo("")

    click.echo(click.style("Usage:", fg='yellow', bold=True))
    click.echo("  python3 -m src.api.cli screen-fundamental --screen-type <type> --criterion <criterion>")
    click.echo("\nExamples:")
    click.echo("  python3 -m src.api.cli screen-fundamental --screen-type value --criterion low-pe")
    click.echo("  python3 -m src.api.cli screen-fundamental --screen-type composite --criterion garp --limit 20")
    click.echo("")


# ============================================================================
# PATTERN SCREENING COMMANDS
# ============================================================================

@cli.command()
@click.option('--db-path', default=None, help='Database file path')
def list_patterns(db_path):
    """List all available screening patterns"""
    from src.patterns.storage import PatternStorage

    if db_path is None:
        config = get_config()
        db_path = config.get('database.path', 'database/stockCode.sqlite')

    storage = PatternStorage(db_path)

    click.echo(f"\n{click.style('=== Available Screening Patterns ===', fg='cyan', bold=True)}\n")

    # Get pattern counts
    counts = storage.get_pattern_count()
    click.echo(f"Preset Patterns: {counts['preset']}")
    click.echo(f"Custom Patterns: {counts['custom']}")
    click.echo(f"Total: {counts['total']}\n")

    # Get all patterns grouped by category
    patterns = storage.get_all_patterns()

    # Group by category
    by_category = {}
    for pattern in patterns:
        category = pattern['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(pattern)

    # Display by category
    for category in sorted(by_category.keys()):
        click.echo(click.style(f"{category.upper()} PATTERNS:", fg='green', bold=True))

        for pattern in by_category[category]:
            pattern_type = click.style('[PRESET]', fg='blue') if pattern['is_preset'] else click.style('[CUSTOM]', fg='yellow')
            click.echo(f"  {pattern_type} {pattern['pattern_id']}")
            click.echo(f"         {pattern['pattern_name']}")
            if pattern['description']:
                click.echo(f"         {click.style(pattern['description'], fg='white', dim=True)}")
            click.echo("")

    click.echo(click.style("\nUsage:", fg='yellow', bold=True))
    click.echo("  python3 -m src.api.cli run-pattern <pattern_id>")
    click.echo("  python3 -m src.api.cli show-pattern <pattern_id>")
    click.echo("\nExamples:")
    click.echo("  python3 -m src.api.cli run-pattern cheap_quality_reversal")
    click.echo("  python3 -m src.api.cli run-pattern garp --limit 20")
    click.echo("")


@cli.command()
@click.argument('pattern_id')
@click.option('--db-path', default=None, help='Database file path')
def show_pattern(pattern_id, db_path):
    """Show details of a specific pattern"""
    from src.patterns.storage import PatternStorage

    if db_path is None:
        config = get_config()
        db_path = config.get('database.path', 'database/stockCode.sqlite')

    storage = PatternStorage(db_path)
    pattern = storage.get_pattern(pattern_id)

    if not pattern:
        click.echo(click.style(f"Pattern not found: {pattern_id}", fg='red'))
        return

    click.echo(f"\n{click.style('=== Pattern Details ===', fg='cyan', bold=True)}\n")

    click.echo(f"ID:          {pattern['pattern_id']}")
    click.echo(f"Name:        {pattern['pattern_name']}")
    click.echo(f"Category:    {pattern['category']}")
    click.echo(f"Type:        {'Preset' if pattern['is_preset'] else 'Custom'}")
    click.echo(f"Description: {pattern.get('description', 'N/A')}")
    click.echo("")

    # Technical criteria
    tech_criteria = pattern.get('technical_criteria', {})
    if tech_criteria:
        click.echo(click.style("Technical Criteria:", fg='green', bold=True))
        if tech_criteria.get('signals'):
            click.echo(f"  Required Signals: {', '.join(tech_criteria['signals'])}")
        if tech_criteria.get('min_signal_strength'):
            click.echo(f"  Min Strength: {tech_criteria['min_signal_strength']}")
        click.echo("")

    # Fundamental criteria
    fund_criteria = pattern.get('fundamental_criteria', {})
    if fund_criteria:
        click.echo(click.style("Fundamental Criteria:", fg='green', bold=True))
        for metric, range_spec in fund_criteria.items():
            if isinstance(range_spec, dict):
                min_val = range_spec.get('min', '-')
                max_val = range_spec.get('max', '-')
                if max_val == 999 or max_val is None:
                    max_val = 'No limit'
                click.echo(f"  {metric:20s}: {min_val} to {max_val}")
            else:
                click.echo(f"  {metric:20s}: {range_spec}")
        click.echo("")

    click.echo(f"Sort by:     {pattern.get('sort_by', 'match_score')}")
    click.echo(f"Created:     {pattern.get('created_at', 'N/A')}")
    click.echo(f"Updated:     {pattern.get('updated_at', 'N/A')}")
    click.echo("")


@cli.command()
@click.argument('pattern_id')
@click.option('--limit', default=50, help='Maximum number of results')
@click.option('--no-cache', is_flag=True, help='Force fresh screening (ignore cache)')
@click.option('--db-path', default=None, help='Database file path')
def run_pattern(pattern_id, limit, no_cache, db_path):
    """Run a screening pattern and show matching stocks"""
    from src.patterns.engine import PatternEngine

    if db_path is None:
        config = get_config()
        db_path = config.get('database.path', 'database/stockCode.sqlite')

    engine = PatternEngine(db_path)

    # Get pattern details
    pattern = engine.get_pattern_details(pattern_id)
    if not pattern:
        click.echo(click.style(f"Pattern not found: {pattern_id}", fg='red'))
        return

    click.echo(f"\n{click.style('=== Running Pattern: ' + pattern['pattern_name'] + ' ===', fg='cyan', bold=True)}\n")

    if pattern.get('description'):
        click.echo(f"{pattern['description']}\n")

    # Run pattern
    try:
        with click.progressbar(length=1, label='Screening stocks') as bar:
            results = engine.run_pattern(
                pattern_id,
                use_cache=not no_cache,
                limit=limit
            )
            bar.update(1)

        if not results:
            click.echo(click.style("\nNo stocks found matching this pattern.", fg='yellow'))
            return

        click.echo(f"\n{click.style(f'Found {len(results)} matching stocks:', fg='green', bold=True)}\n")

        # Prepare table data
        headers = ['Stock', 'Match Score', 'Signals', 'Fundamentals']
        rows = []

        for result in results:
            stock_id = result['stock_id']
            match_score = result.get('match_score', 0)

            # Format signals
            signals = result.get('matched_signals', [])
            if isinstance(signals, list) and signals:
                if isinstance(signals[0], dict):
                    signal_str = ', '.join([s.get('signal_name', '') for s in signals[:3]])
                else:
                    signal_str = ', '.join(signals[:3])
                if len(signals) > 3:
                    signal_str += f" (+{len(signals)-3} more)"
            else:
                signal_str = '-'

            # Format fundamentals
            fundamentals = result.get('matched_fundamentals', {})
            fund_parts = []
            if 'pe_ratio' in fundamentals and fundamentals['pe_ratio']:
                fund_parts.append(f"P/E:{fundamentals['pe_ratio']:.1f}")
            if 'roe_percent' in fundamentals and fundamentals['roe_percent']:
                fund_parts.append(f"ROE:{fundamentals['roe_percent']:.1f}%")
            if 'revenue_growth_yoy' in fundamentals and fundamentals['revenue_growth_yoy']:
                fund_parts.append(f"Growth:{fundamentals['revenue_growth_yoy']:.1f}%")

            fund_str = ', '.join(fund_parts) if fund_parts else '-'

            # Color code match score
            if match_score >= 80:
                score_str = click.style(f"{match_score}/100", fg='green', bold=True)
            elif match_score >= 60:
                score_str = click.style(f"{match_score}/100", fg='yellow')
            else:
                score_str = click.style(f"{match_score}/100", fg='white')

            rows.append([
                stock_id,
                score_str,
                signal_str[:40],
                fund_str[:50]
            ])

        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        click.echo("")

        # Show summary statistics
        avg_score = sum(r.get('match_score', 0) for r in results) / len(results)
        click.echo(f"Average Match Score: {click.style(f'{avg_score:.1f}/100', fg='cyan')}")
        click.echo("")

    except Exception as e:
        click.echo(click.style(f"Error running pattern: {str(e)}", fg='red'))
        import traceback
        traceback.print_exc()
        raise click.Abort()
    finally:
        engine.close()


if __name__ == '__main__':
    # Import for timedelta
    from datetime import timedelta
    cli()
