#!/bin/bash
# Quick start script for your AI Agent learning journey

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     AI Agent Learning Path - Quick Start                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if in correct directory
if [ ! -f "YOUR_LEARNING_PATH.md" ]; then
    echo "❌ Please run this from the Agentic_Design_Patterns directory"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

echo "Setting up your learning environment..."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "learning_venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv learning_venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source learning_venv/bin/activate

# Install required packages
echo "📦 Installing Jupyter and dependencies..."
pip install -q jupyter notebook ipykernel anthropic langchain

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   Setup Complete! ✅                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📚 Your Learning Path: YOUR_LEARNING_PATH.md"
echo ""
echo "🚀 What to do next:"
echo ""
echo "Option 1: Start with the Learning Guide"
echo "   cat YOUR_LEARNING_PATH.md | less"
echo ""
echo "Option 2: Launch Jupyter Notebooks"
echo "   jupyter notebook notebooks/"
echo ""
echo "Option 3: Check your progress"
echo "   cat progress.md"
echo ""
echo "Current Week: Week 1 - Foundation (Prompt Chaining, Routing, Parallelization)"
echo ""
echo "First exercise: Open 'notebooks/Chapter 1_ Prompt Chaining (Code Example)'"
echo ""
echo "Happy learning! 🎓"
echo ""
