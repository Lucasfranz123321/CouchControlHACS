#!/bin/bash

# Couch Control HACS Integration - Fix and Reinstall Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Couch Control Entity Filter - Fix and Reinstall${NC}"
echo "================================================="

# Check if Home Assistant config path is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./fix_and_reinstall.sh /path/to/homeassistant/config${NC}"
    echo -e "${YELLOW}Example: ./fix_and_reinstall.sh /config${NC}"
    echo -e "${YELLOW}Example: ./fix_and_reinstall.sh ~/.homeassistant${NC}"
    exit 1
fi

HA_CONFIG_PATH="$1"
CUSTOM_COMPONENTS_PATH="$HA_CONFIG_PATH/custom_components"
DEST_PATH="$CUSTOM_COMPONENTS_PATH/couch_control"

echo -e "${BLUE}Step 1: Removing old integration...${NC}"

# Remove existing integration if it exists
if [ -d "$DEST_PATH" ]; then
    echo -e "${YELLOW}Backing up old integration...${NC}"
    mv "$DEST_PATH" "$DEST_PATH.backup.$(date +%Y%m%d_%H%M%S)"
fi

echo -e "${GREEN}✓ Old integration removed${NC}"

echo -e "${BLUE}Step 2: Installing fixed integration...${NC}"

# Create custom_components directory if it doesn't exist
mkdir -p "$CUSTOM_COMPONENTS_PATH"

# Copy the fixed integration
cp -r "custom_components/couch_control" "$DEST_PATH"
chmod -R 644 "$DEST_PATH"
find "$DEST_PATH" -name "*.py" -exec chmod 644 {} \;

echo -e "${GREEN}✓ Fixed integration installed${NC}"

echo -e "${BLUE}Step 3: Validation...${NC}"

# Validate Python files
python3 -m py_compile "$DEST_PATH"/*.py
echo -e "${GREEN}✓ Python files validated${NC}"

echo
echo -e "${GREEN}Installation completed successfully!${NC}"
echo
echo -e "${YELLOW}IMPORTANT: Next steps to fix the disappearing integration:${NC}"
echo
echo "1. ${BLUE}Restart Home Assistant${NC} (this is CRITICAL)"
echo "   - Settings → System → Restart"
echo
echo "2. ${BLUE}Remove any old/broken integrations:${NC}"
echo "   - Settings → Devices & Services"
echo "   - If you see any broken/red Couch Control entries, delete them"
echo "   - Look for entries with error icons or 'Unknown' status"
echo
echo "3. ${BLUE}Add the integration fresh:${NC}"
echo "   - Click 'Add Integration'"
echo "   - Search for 'Couch Control Entity Filter'"
echo "   - Select entities you want to expose to the app"
echo
echo "4. ${BLUE}Verify it's working:${NC}"
echo "   - Check that you can access 'Configure' on the integration"
echo "   - Modify entity selection to test it stays stable"
echo
echo -e "${BLUE}Troubleshooting:${NC}"
echo "- Check Home Assistant logs: Settings → System → Logs"
echo "- Look for 'couch_control' entries in the logs"
echo "- If still disappearing, check for Python errors in logs"
echo
echo -e "${GREEN}The integration should now be stable and not disappear!${NC}"