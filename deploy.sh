#!/bin/bash

# Claude Integration Deployment Script

set -e

echo "🚀 Claude Integration Deployment"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Install Docker to use this deployment script.${NC}"
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${BLUE}Step 1: Checking configuration...${NC}"

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please update .env with your Home Assistant token${NC}"
    exit 1
fi

# Validate .env
if grep -q "your_home_assistant_token_here" .env; then
    echo -e "${YELLOW}⚠️  Please update HA_TOKEN in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Configuration valid${NC}"

echo -e "${BLUE}Step 2: Building containers...${NC}"

# Build containers
docker-compose build

echo -e "${GREEN}✓ Containers built${NC}"

echo -e "${BLUE}Step 3: Starting services...${NC}"

# Start services
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

echo -e "${GREEN}✓ Services started${NC}"

echo -e "${BLUE}Step 4: Verifying deployment...${NC}"

# Check API health
if curl -s http://localhost:5000/health > /dev/null; then
    echo -e "${GREEN}✓ Claude API is running${NC}"
else
    echo -e "${YELLOW}⚠️  Claude API not responding yet. Give it a moment...${NC}"
fi

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📊 Services:"
echo "  - Claude API: http://localhost:5000"
echo "  - Home Assistant: http://localhost:8123"
echo ""
echo "📝 Next steps:"
echo "  1. Configure Claude integration in Home Assistant"
echo "  2. Set API Endpoint to: http://claude-api:5000"
echo "  3. Select your preferred Claude model"
echo ""
echo "📖 Documentation:"
echo "  - API: http://localhost:5000/health"
echo "  - Logs: docker-compose logs -f"
echo ""
