#!/bin/bash

# Claude Integration Setup Script

set -e

echo "🚀 Claude AI Integration Setup"
echo "==============================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r backend/requirements.txt

# Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your Home Assistant token"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your Home Assistant token"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python backend/api.py"
echo ""
echo "Or use Docker:"
echo "1. docker-compose up -d"
echo ""
