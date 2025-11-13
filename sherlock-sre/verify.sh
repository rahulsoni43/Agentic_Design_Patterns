#!/bin/bash
# Quick verification script for Sherlock SRE

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Sherlock SRE - Quick Verification                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./scripts/setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Copy .env.example and configure it"
    exit 1
fi

echo "✅ Environment setup OK"
echo ""

# Run verification tests
echo "🔍 Running verification tests..."
echo ""
python tests/test_verification.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                ✅ VERIFICATION PASSED! ✅                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Sherlock is ready to use!"
    echo ""
    echo "Try these commands:"
    echo "  python -m src.cli health"
    echo "  python -m src.cli investigate 'why is my pod crashlooping?'"
    echo ""
    exit 0
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                ❌ VERIFICATION FAILED ❌                    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Please fix the issues above and try again."
    echo ""
    exit 1
fi
