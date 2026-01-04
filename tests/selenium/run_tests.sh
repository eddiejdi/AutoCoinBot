#!/bin/bash
# Run all Selenium tests for AutoCoinBot

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."

echo -e "${GREEN}🧪 AutoCoinBot Selenium Test Suite${NC}"
echo "=================================="

# Activate venv if exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Set environment
export APP_ENV=${APP_ENV:-dev}
export LOCAL_URL=${LOCAL_URL:-http://localhost:8501}
export HEADLESS=${HEADLESS:-1}
export TAKE_SCREENSHOTS=${TAKE_SCREENSHOTS:-1}
export SAVE_DOM=${SAVE_DOM:-1}

echo -e "Environment: ${YELLOW}$APP_ENV${NC}"
echo -e "URL: ${YELLOW}$LOCAL_URL${NC}"
echo ""

# Run complete test suite
echo -e "${GREEN}Running complete test suite...${NC}"
python3 "$SCRIPT_DIR/test_all_pages.py"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo ""
    echo -e "${RED}❌ Some tests failed!${NC}"
fi

# Show artifacts location
echo ""
echo -e "${YELLOW}📸 Screenshots: $SCRIPT_DIR/screenshots${NC}"
echo -e "${YELLOW}📄 Reports: $SCRIPT_DIR/reports${NC}"

exit $EXIT_CODE
