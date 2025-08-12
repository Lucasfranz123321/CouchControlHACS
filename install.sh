#!/bin/bash

# Couch Control HACS Integration Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Couch Control Entity Filter - Installation Script${NC}"
echo "=================================================="

# Check if Home Assistant config path is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./install.sh /path/to/homeassistant/config${NC}"
    echo -e "${YELLOW}Example: ./install.sh /config${NC}"
    echo -e "${YELLOW}Example: ./install.sh ~/.homeassistant${NC}"
    exit 1
fi

HA_CONFIG_PATH="$1"

# Verify Home Assistant config directory exists
if [ ! -d "$HA_CONFIG_PATH" ]; then
    echo -e "${RED}Error: Home Assistant config directory not found: $HA_CONFIG_PATH${NC}"
    exit 1
fi

# Check for configuration.yaml to confirm it's a HA config directory
if [ ! -f "$HA_CONFIG_PATH/configuration.yaml" ]; then
    echo -e "${YELLOW}Warning: configuration.yaml not found. Is this the correct Home Assistant config directory?${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create custom_components directory if it doesn't exist
CUSTOM_COMPONENTS_PATH="$HA_CONFIG_PATH/custom_components"
if [ ! -d "$CUSTOM_COMPONENTS_PATH" ]; then
    echo -e "${BLUE}Creating custom_components directory...${NC}"
    mkdir -p "$CUSTOM_COMPONENTS_PATH"
fi

# Copy the integration
DEST_PATH="$CUSTOM_COMPONENTS_PATH/couch_control"
echo -e "${BLUE}Installing Couch Control integration to $DEST_PATH...${NC}"

if [ -d "$DEST_PATH" ]; then
    echo -e "${YELLOW}Existing installation found. Creating backup...${NC}"
    mv "$DEST_PATH" "$DEST_PATH.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Copy files
cp -r "custom_components/couch_control" "$DEST_PATH"

echo -e "${GREEN}✓ Integration files copied successfully${NC}"

# Set permissions
chmod -R 644 "$DEST_PATH"
find "$DEST_PATH" -name "*.py" -exec chmod 644 {} \;

echo -e "${GREEN}✓ Permissions set${NC}"

# Validate Python files
echo -e "${BLUE}Validating Python files...${NC}"
python3 -m py_compile "$DEST_PATH"/*.py

echo -e "${GREEN}✓ Python files validated${NC}"

echo
echo -e "${GREEN}Installation completed successfully!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Restart Home Assistant"
echo "2. Go to Settings → Devices & Services"
echo "3. Click 'Add Integration'"
echo "4. Search for 'Couch Control Entity Filter'"
echo "5. Follow the configuration steps"
echo
echo -e "${BLUE}For troubleshooting, check:${NC}"
echo "- Home Assistant logs"
echo "- $DEST_PATH directory exists and has correct files"
echo
echo -e "${GREEN}Installation complete!${NC}"