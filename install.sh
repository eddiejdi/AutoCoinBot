#!/bin/bash

##############################################
#   KUCOIN PRO - INSTALLATION SCRIPT        #
##############################################

set -e  # Exit on error

echo "========================================"
echo "  🚀 KuCoin PRO - Installation Wizard  "
echo "========================================"
echo ""

PROJECT_DIR="$HOME/Downloads/kucoin_app"
VENV_DIR="$PROJECT_DIR/venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check Python version
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found! Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

print_success "Project directory found"

# Navigate to project
cd "$PROJECT_DIR"

# Clean up old virtual environment
if [ -d "$VENV_DIR" ]; then
    print_warning "Removing old virtual environment..."
    rm -rf "$VENV_DIR"
fi

# Create virtual environment
print_info "Creating virtual environment..."
python3 -m venv "$VENV_DIR"
print_success "Virtual environment created"

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_success "pip upgraded"

# Install dependencies
print_info "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_warning "requirements.txt not found, installing core packages..."
    pip install requests urllib3 python-dotenv pandas numpy plotly streamlit
    print_success "Core packages installed"
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    
    if [ -f ".env.example" ]; then
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_success ".env created from template"
    else
        print_info "Creating basic .env file..."
        cat > .env << 'EOF'
# KuCoin API Credentials
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
API_PASSPHRASE=your_passphrase_here
API_KEY_VERSION=2
KUCOIN_BASE=https://api.kucoin.com
EOF
        print_success ".env created"
    fi
    
    print_warning "⚠️  IMPORTANT: Edit .env with your KuCoin API credentials!"
    echo ""
    echo "Run: nano .env"
    echo ""
else
    print_success ".env file exists"
fi

# Create .gitignore if not exists
if [ ! -f ".gitignore" ]; then
    print_info "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Environment
.env
venv/
*.pyc
__pycache__/

# Database
*.db
*.db-journal

# Logs
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
EOF
    print_success ".gitignore created"
fi

# Initialize database
print_info "Initializing database..."
python3 << 'EOF'
try:
    from kucoin_app.database import db
    print("Database initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")
EOF

# Run tests
print_info "Running basic tests..."
python3 << 'EOF'
try:
    # Test imports
    from kucoin_app import api, bot_core, database, risk_manager
    print("✅ All modules imported successfully")
    
    # Test database
    from kucoin_app.database import db
    active_bots = db.get_active_bots()
    print(f"✅ Database working (active bots: {len(active_bots)})")
    
except Exception as e:
    print(f"⚠️  Warning: {e}")
EOF

echo ""
echo "========================================"
print_success "Installation completed!"
echo "========================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Configure API credentials:"
echo "   nano .env"
echo ""
echo "2. Activate virtual environment:"
echo "   source $VENV_DIR/bin/activate"
echo ""
echo "3. Run the web interface:"
echo "   streamlit run kucoin_app/ui.py"
echo ""
echo "4. Or run CLI bot:"
echo "   python -m kucoin_app.bot_worker --help"
echo ""
echo "📖 Read the documentation:"
echo "   cat README.md"
echo ""
print_warning "⚠️  SECURITY REMINDER:"
echo "   - NEVER commit .env to git"
echo "   - Start with dry-run mode (--dry)"
echo "   - Test with small amounts first"
echo ""
echo "🎉 Happy trading!"
echo ""
