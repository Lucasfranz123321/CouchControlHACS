#!/bin/bash

# Start Test Home Assistant Environment

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Starting Test Home Assistant Environment${NC}"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Navigate to test directory
cd "$(dirname "$0")"

# Stop existing container if running
echo -e "${BLUE}Stopping existing test container...${NC}"
docker-compose down 2>/dev/null || true

# Start Home Assistant
echo -e "${BLUE}Starting Home Assistant...${NC}"
docker-compose up -d

echo -e "${GREEN}✓ Home Assistant starting up${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Wait 30-60 seconds for Home Assistant to start"
echo "2. Open http://localhost:8123 in your browser"
echo "3. Complete the initial setup (create admin user)"
echo "4. Go to Settings → Devices & Services"
echo "5. Click 'Add Integration'"
echo "6. Search for 'Couch Control Entity Filter'"
echo
echo -e "${BLUE}To monitor logs:${NC}"
echo "docker logs -f ha-test"
echo
echo -e "${BLUE}To stop test environment:${NC}"
echo "./stop_test_ha.sh"