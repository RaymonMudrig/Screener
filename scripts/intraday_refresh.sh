#!/bin/bash
#
# Intraday Refresh Wrapper Script
#
# This script can be called by external programs (Java, Node.js, etc.)
# to trigger an intraday data refresh.
#
# Usage:
#   ./scripts/intraday_refresh.sh [OPTIONS]
#
# Options:
#   --delay SECONDS     Delay between stock updates (default: 1.0)
#   --limit NUMBER      Limit to NUMBER stocks (for testing)
#   --skip-price        Skip price update, only recalculate indicators/signals
#   --help              Show this help message
#
# Examples:
#   ./scripts/intraday_refresh.sh
#   ./scripts/intraday_refresh.sh --delay 0.5
#   ./scripts/intraday_refresh.sh --limit 10 --delay 0.5
#

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Default values
DELAY="1.0"
LIMIT=""
SKIP_PRICE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --delay)
            DELAY="$2"
            shift 2
            ;;
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        --skip-price)
            SKIP_PRICE="--skip-price-update"
            shift
            ;;
        --help)
            head -n 20 "$0" | grep '^#' | sed 's/^# //g' | sed 's/^#//g'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Log file
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/intraday_$(date +%Y%m%d).log"

# Log start
echo "========================================" | tee -a "$LOG_FILE"
echo "Intraday Refresh Started" | tee -a "$LOG_FILE"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "Delay: ${DELAY}s" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run refresh command
python3 -m src.api.cli refresh-intraday --delay "$DELAY" $LIMIT $SKIP_PRICE 2>&1 | tee -a "$LOG_FILE"

# Log end
EXIT_CODE=${PIPESTATUS[0]}
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Intraday Refresh Completed" | tee -a "$LOG_FILE"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Return exit code
exit $EXIT_CODE
