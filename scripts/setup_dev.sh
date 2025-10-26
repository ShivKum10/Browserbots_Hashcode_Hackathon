#!/bin/bash

# FLYO Development Environment Setup Script
# Run this to set up your environment in 5 minutes

set -e  # Exit on error

echo "🚀 FLYO Development Environment Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.9+ required. You have: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Install Playwright browsers
echo "Installing Playwright browsers (this may take a few minutes)..."
playwright install chromium
echo "✓ Playwright browsers installed"
echo ""

# Create necessary directories
echo "Creating project directories..."
mkdir -p logs
mkdir -p assets/screenshots
mkdir -p demos
echo "✓ Directories created"
echo ""

# Check for API key
echo "Checking for API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set"
    echo ""
    echo "Set your API key:"
    echo "  export OPENAI_API_KEY='sk-your-key-here'"
    echo ""
    echo "Or create a .env file:"
    echo "  echo 'OPENAI_API_KEY=sk-your-key-here' > .env"
else
    echo "✓ OPENAI_API_KEY is set"
fi
echo ""

# Run a quick test
echo "Running quick test..."
python -c "from flyo import FlyoAgent; print('✓ FLYO imports working')"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set your OpenAI API key (if not done):"
echo "     export OPENAI_API_KEY='sk-...'"
echo ""
echo "  2. Run your first automation:"
echo "     python -m flyo \"Go to Google and search for test\""
echo ""
echo "  3. Or run the demo:"
echo "     ./demo.sh"
echo ""
echo "Happy automating! 🤖"
