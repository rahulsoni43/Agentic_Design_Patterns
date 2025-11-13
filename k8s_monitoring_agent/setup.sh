#!/bin/bash
# Quick setup script for K8s Monitoring Agent

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Kubernetes AI Monitoring Agent - Setup Script           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "⚠️  kubectl not found. Install from: https://kubernetes.io/docs/tasks/tools/"
    echo "   You can still run locally tests, but cluster monitoring won't work."
else
    echo "✅ kubectl found: $(kubectl version --client --short 2>/dev/null || echo 'installed')"
fi

# Check kubectl access
if kubectl get pods &> /dev/null; then
    echo "✅ kubectl can access cluster"
else
    echo "⚠️  kubectl cannot access cluster (this is OK for setup)"
fi

echo ""

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Setup environment
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo ""
    echo "   1. Get Anthropic API key: https://console.anthropic.com/"
    echo "   2. Get Slack webhook: https://api.slack.com/messaging/webhooks"
    echo "   3. Edit .env and paste your keys"
    echo ""
    read -p "Press Enter when you've added your API keys to .env..."
else
    echo "✅ .env file already exists"
fi

echo ""

# Test setup
echo "🧪 Testing setup..."
echo ""

# Check if API key is set
if grep -q "sk-ant-api03-your-key-here" .env; then
    echo "⚠️  API key not configured in .env - tests will fail"
    echo "   Please edit .env and add your Anthropic API key"
    exit 0
fi

# Source .env
export $(cat .env | xargs)

echo "Running integration tests..."
echo ""
python src/monitor.py --test

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ✅ SETUP COMPLETE! ✅                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Run once to see results:"
echo "   python src/monitor.py --once"
echo ""
echo "2. Start continuous monitoring:"
echo "   python src/monitor.py --interval 60"
echo ""
echo "3. Deploy to Kubernetes:"
echo "   kubectl apply -f deploy/kubernetes.yaml"
echo ""
echo "📚 See README.md for full documentation"
echo ""
