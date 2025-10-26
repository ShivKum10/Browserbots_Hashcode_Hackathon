#!/bin/bash

# FLYO Demo Script
# Quick demonstration of FLYO's capabilities

echo "🤖 FLYO - Natural Language Browser Automation Demo"
echo "=================================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Check if API key is set
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  OPENAI_API_KEY not set"
    echo "Run: export OPENAI_API_KEY='sk-...'"
    exit 1
fi

echo "✓ Environment ready"
echo ""

# Demo 1: Simple Google Search
echo "Demo 1: Simple Google Search"
echo "----------------------------"
python -m flyo "Go to Google and search for browser automation" --no-approval
echo ""

# Demo 2: Flight Search (with approval)
echo "Demo 2: Flight Search (Interactive Approval)"
echo "--------------------------------------------"
python -m flyo "Search for flights from Mumbai to Delhi" --config configs/google_flights.json
echo ""

echo "Demo complete! 🎉"
