#!/bin/bash
# Quick setup script for Sherlock SRE

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Sherlock SRE - Setup Script                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION found"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "⚠️  kubectl not found. Install from: https://kubernetes.io/docs/tasks/tools/"
    echo "   You can still run setup, but cluster monitoring won't work."
else
    echo "✅ kubectl found: $(kubectl version --client --short 2>/dev/null || echo 'installed')"
fi

echo ""

# Create virtual environment
echo "📦 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# Setup environment file
echo ""
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo ""
    echo "   1. Get Anthropic API key: https://console.anthropic.com/"
    echo "   2. (Optional) Get Slack tokens: https://api.slack.com/apps"
    echo "   3. Edit .env and paste your keys"
    echo ""
else
    echo "✅ .env file already exists"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ✅ SETUP COMPLETE! ✅                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your Anthropic API key:"
echo "   nano .env"
echo ""
echo "2. Test with CLI:"
echo "   source venv/bin/activate"
echo "   python -m src.cli health"
echo ""
echo "3. Try an investigation:"
echo "   python -m src.cli investigate \"why is my pod crashlooping?\""
echo ""
echo "4. (Optional) Start Slack bot:"
echo "   python -m src.main"
echo ""
echo "📚 See docs/SETUP.md for full documentation"
echo ""
