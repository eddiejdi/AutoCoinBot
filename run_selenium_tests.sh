#!/bin/bash
# AutoCoinBot - Test Runner Wrapper
# Facilita execução dos testes Selenium de qualquer lugar

set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEST_DIR="$SCRIPT_DIR/tests/selenium"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🧪 AutoCoinBot Test Runner${NC}"
echo ""

# Check if test directory exists
if [ ! -d "$TEST_DIR" ]; then
    echo "❌ Test directory not found: $TEST_DIR"
    exit 1
fi

# Parse arguments
COMMAND=${1:-all}

case "$COMMAND" in
    all|full|complete)
        echo -e "${YELLOW}Running complete test suite...${NC}"
        cd "$TEST_DIR"
        ./run_tests.sh
        ;;
        
    local|dev)
        echo -e "${YELLOW}Running local tests...${NC}"
        export APP_ENV=dev
        export LOCAL_URL=${LOCAL_URL:-http://localhost:8501}
        cd "$TEST_DIR"
        ./run_tests.sh
        ;;
        
    hom|homolog|homologation)
        echo -e "${YELLOW}Running homologation tests...${NC}"
        export APP_ENV=hom
        export LOCAL_URL=${HOM_URL:-https://autocoinbot.fly.dev}
        cd "$TEST_DIR"
        ./run_tests.sh
        ;;
        
    prod|production)
        echo -e "${YELLOW}Running production tests...${NC}"
        export APP_ENV=prod
        export LOCAL_URL=${PROD_URL:-https://autocoinbot.fly.dev}
        cd "$TEST_DIR"
        ./run_tests.sh
        ;;
        
    show|visible|browser)
        echo -e "${YELLOW}Running with visible browser...${NC}"
        export HEADLESS=0
        cd "$TEST_DIR"
        ./run_tests.sh
        ;;
        
    help|--help|-h)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  all, full, complete  - Run complete test suite (default)"
        echo "  local, dev           - Run local tests (http://localhost:8501)"
        echo "  hom, homolog         - Run homologation tests"
        echo "  prod, production     - Run production tests"
        echo "  show, visible        - Run with visible browser (not headless)"
        echo "  help                 - Show this help"
        echo ""
        echo "Environment variables:"
        echo "  LOCAL_URL            - Override local URL"
        echo "  HOM_URL              - Override homologation URL"
        echo "  HEADLESS             - Run headless (1) or with browser (0)"
        echo "  TAKE_SCREENSHOTS     - Save screenshots (1/0)"
        echo ""
        echo "Examples:"
        echo "  $0                        # Run all tests (local)"
        echo "  $0 hom                    # Test homologation"
        echo "  $0 show                   # Run with visible browser"
        echo "  LOCAL_URL=:8506 $0        # Custom port"
        ;;
        
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
