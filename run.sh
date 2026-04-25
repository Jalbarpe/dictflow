#!/bin/bash
# DictFlow — Local voice dictation
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}=== DictFlow ===${NC}"
echo "Local voice dictation (Whisper MLX)"
echo ""

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: venv not found. Run: python3 -m venv $VENV_DIR"
    exit 1
fi

# Ensure Homebrew tools (ffmpeg) are in PATH
export PATH="/opt/homebrew/bin:$PATH"

# Use venv Python directly
PYTHON="$VENV_DIR/bin/python3"

echo -e "${GREEN}Starting DictFlow...${NC}"
echo "  Hold Globe key (fn) to dictate"
echo "  Release to transcribe and insert text"
echo ""

"$PYTHON" "$SCRIPT_DIR/main.py"
