#!/bin/bash

# Setup script for Stock Screener

echo "=== Stock Screener Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Initialize database
echo ""
echo "Initializing database..."
python3 -m src.api.cli init

# Show stats
echo ""
echo "Showing database statistics..."
python3 -m src.api.cli stats

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Update stock list: python3 -m src.api.cli update-stocks"
echo "2. Update price data: python3 -m src.api.cli update-price BBCA --days 30"
echo "3. View stocks: python3 -m src.api.cli list-stocks"
echo ""
