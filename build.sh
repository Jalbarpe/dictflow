#!/bin/bash
# Build DictFlow.app and create DMG
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}=== Building DictFlow ===${NC}"

# Activate venv
source venv/bin/activate

# Clean previous builds
rm -rf build dist

# Build .app
echo "Building DictFlow.app..."
python3 setup.py py2app 2>&1 | grep -E "(Done|Error|error)"

if [ ! -d "dist/DictFlow.app" ]; then
    echo "Build failed!"
    exit 1
fi

APP_SIZE=$(du -sh dist/DictFlow.app | cut -f1)
echo -e "${GREEN}DictFlow.app built ($APP_SIZE)${NC}"

# Create DMG
echo "Creating DictFlow.dmg..."
rm -f dist/DictFlow.dmg
hdiutil create -volname "DictFlow" \
    -srcfolder dist/DictFlow.app \
    -ov \
    -format UDZO \
    dist/DictFlow.dmg 2>/dev/null

DMG_SIZE=$(du -sh dist/DictFlow.dmg | cut -f1)
echo -e "${GREEN}DictFlow.dmg created ($DMG_SIZE)${NC}"

echo ""
echo "Output:"
echo "  dist/DictFlow.app  — App bundle"
echo "  dist/DictFlow.dmg  — Distributable DMG"
echo ""
echo "To install: open dist/DictFlow.dmg and drag to Applications"
