#!/bin/bash
# Start all services locally
# Comprehensive local execution script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="venv"
PYTHON_CMD="python3"
PORT_API=8000
PORT_DASHBOARD=3000
PORT_LOCK_SECURITY=8001
PORT_EMISSIONS=8002
PORT_PRE_SALE=8003

# Functions
print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check Python
check_python() {
    print_header "Checking Python Installation"
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python found: $PYTHON_VERSION"
    else
        print_error "Python3 not found. Please install Python 3.8+"
        exit 1
    fi
}

# Setup Virtual Environment
setup_venv() {
    print_header "Setting Up Virtual Environment"
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating virtual environment..."
        $PYTHON_CMD -m venv $VENV_DIR
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    print_info "Activating virtual environment..."
    source $VENV_DIR/bin/activate
    print_success "Virtual environment activated"
}

# Install Dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    # Main API dependencies
    if [ -f "api/requirements.txt" ]; then
        print_info "Installing API dependencies..."
        pip install -q --upgrade pip
        pip install -q -r api/requirements.txt
        print_success "API dependencies installed"
    fi
    
    # Engine dependencies
    if [ -f "engine/requirements.txt" ]; then
        print_info "Installing Engine dependencies..."
        pip install -q -r engine/requirements.txt
        print_success "Engine dependencies installed"
    fi
    
    # Lock Security Testing
    if [ -f "lock-security-testing/backend/requirements.txt" ]; then
        print_info "Installing Lock Security dependencies..."
        pip install -q -r lock-security-testing/backend/requirements.txt
        print_success "Lock Security dependencies installed"
    fi
    
    # Emissions Testing
    if [ -f "emissions-testing/backend/requirements.txt" ]; then
        print_info "Installing Emissions Testing dependencies..."
        pip install -q -r emissions-testing/backend/requirements.txt
        print_success "Emissions Testing dependencies installed"
    fi
    
    # Pre-Sale Inspection
    if [ -f "pre-sale-inspection/backend/requirements.txt" ]; then
        print_info "Installing Pre-Sale Inspection dependencies..."
        pip install -q -r pre-sale-inspection/backend/requirements.txt
        print_success "Pre-Sale Inspection dependencies installed"
    fi
    
    print_success "All dependencies installed"
}

# Set Environment Variables
setup_env() {
    print_header "Setting Up Environment Variables"
    
    export VENICE_API_KEY="tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz"
    export VENICE_BASE_URL="https://api.venice.ai/api/v1"
    export VENICE_MODEL="venice-uncensored"
    
    # Database (use SQLite for local)
    export DATABASE_URL="sqlite:///./local.db"
    export POSTGRES_URL="sqlite:///./local.db"
    
    # API Settings
    export API_RATE_LIMIT=1000
    export DEBUG=true
    export LOG_LEVEL=INFO
    
    print_success "Environment variables set"
}

# Test Venice AI Connection
test_venice_ai() {
    print_header "Testing Venice AI Connection"
    if [ -f "test_venice_ai.py" ]; then
        python3 test_venice_ai.py && print_success "Venice AI connection OK" || print_error "Venice AI connection failed"
    else
        print_info "Venice AI test script not found, skipping..."
    fi
}

# Start API Service
start_api() {
    print_header "Starting API Service"
    cd api
    
    if [ -f "simple_main.py" ]; then
        print_info "Starting API on port $PORT_API..."
        uvicorn simple_main:app --host 0.0.0.0 --port $PORT_API --reload &
        API_PID=$!
        echo $API_PID > ../.api.pid
        sleep 3
        if ps -p $API_PID > /dev/null; then
            print_success "API running on http://localhost:$PORT_API (PID: $API_PID)"
        else
            print_error "API failed to start"
        fi
    else
        print_info "Starting main API..."
        uvicorn main:app --host 0.0.0.0 --port $PORT_API --reload &
        API_PID=$!
        echo $API_PID > ../.api.pid
        sleep 3
        if ps -p $API_PID > /dev/null; then
            print_success "API running on http://localhost:$PORT_API (PID: $API_PID)"
        else
            print_error "API failed to start"
        fi
    fi
    
    cd ..
}

# Start Lock Security Testing
start_lock_security() {
    print_header "Starting Lock Security Testing Service"
    cd lock-security-testing/backend
    
    if [ -f "main.py" ]; then
        print_info "Starting Lock Security on port $PORT_LOCK_SECURITY..."
        uvicorn main:app --host 0.0.0.0 --port $PORT_LOCK_SECURITY --reload &
        LOCK_PID=$!
        echo $LOCK_PID > ../../.lock_security.pid
        sleep 2
        if ps -p $LOCK_PID > /dev/null; then
            print_success "Lock Security running on http://localhost:$PORT_LOCK_SECURITY (PID: $LOCK_PID)"
        else
            print_error "Lock Security failed to start"
        fi
    fi
    
    cd ../..
}

# Start Emissions Testing
start_emissions() {
    print_header "Starting Emissions Testing Service"
    cd emissions-testing/backend
    
    if [ -f "main.py" ]; then
        print_info "Starting Emissions Testing on port $PORT_EMISSIONS..."
        uvicorn main:app --host 0.0.0.0 --port $PORT_EMISSIONS --reload &
        EMISSIONS_PID=$!
        echo $EMISSIONS_PID > ../../.emissions.pid
        sleep 2
        if ps -p $EMISSIONS_PID > /dev/null; then
            print_success "Emissions Testing running on http://localhost:$PORT_EMISSIONS (PID: $EMISSIONS_PID)"
        else
            print_error "Emissions Testing failed to start"
        fi
    fi
    
    cd ../..
}

# Start Pre-Sale Inspection
start_pre_sale() {
    print_header "Starting Pre-Sale Inspection Service"
    cd pre-sale-inspection/backend
    
    if [ -f "main.py" ]; then
        print_info "Starting Pre-Sale Inspection on port $PORT_PRE_SALE..."
        uvicorn main:app --host 0.0.0.0 --port $PORT_PRE_SALE --reload &
        PRE_SALE_PID=$!
        echo $PRE_SALE_PID > ../../.pre_sale.pid
        sleep 2
        if ps -p $PRE_SALE_PID > /dev/null; then
            print_success "Pre-Sale Inspection running on http://localhost:$PORT_PRE_SALE (PID: $PRE_SALE_PID)"
        else
            print_error "Pre-Sale Inspection failed to start"
        fi
    fi
    
    cd ../..
}

# Health Check
health_check() {
    print_header "Health Check"
    sleep 5
    
    # Check API
    if curl -s http://localhost:$PORT_API/health > /dev/null 2>&1; then
        print_success "API health check passed"
    else
        print_error "API health check failed"
    fi
    
    # Check Lock Security
    if curl -s http://localhost:$PORT_LOCK_SECURITY/health > /dev/null 2>&1; then
        print_success "Lock Security health check passed"
    else
        print_info "Lock Security health check skipped (may not be running)"
    fi
    
    # Check Emissions
    if curl -s http://localhost:$PORT_EMISSIONS/health > /dev/null 2>&1; then
        print_success "Emissions Testing health check passed"
    else
        print_info "Emissions Testing health check skipped (may not be running)"
    fi
    
    # Check Pre-Sale
    if curl -s http://localhost:$PORT_PRE_SALE/health > /dev/null 2>&1; then
        print_success "Pre-Sale Inspection health check passed"
    else
        print_info "Pre-Sale Inspection health check skipped (may not be running)"
    fi
}

# Show Status
show_status() {
    print_header "Service Status"
    echo ""
    echo -e "${GREEN}Services Running:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${BLUE}Main API:${NC}        http://localhost:$PORT_API"
    echo -e "${BLUE}Lock Security:${NC}   http://localhost:$PORT_LOCK_SECURITY"
    echo -e "${BLUE}Emissions:${NC}       http://localhost:$PORT_EMISSIONS"
    echo -e "${BLUE}Pre-Sale:${NC}        http://localhost:$PORT_PRE_SALE"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}To stop all services, run:${NC}"
    echo "  ./stop_local.sh"
    echo ""
    echo -e "${YELLOW}Or manually kill processes:${NC}"
    if [ -f ".api.pid" ]; then
        echo "  kill $(cat .api.pid)"
    fi
    if [ -f ".lock_security.pid" ]; then
        echo "  kill $(cat .lock_security.pid)"
    fi
    if [ -f ".emissions.pid" ]; then
        echo "  kill $(cat .emissions.pid)"
    fi
    if [ -f ".pre_sale.pid" ]; then
        echo "  kill $(cat .pre_sale.pid)"
    fi
    echo ""
}

# Cleanup function
cleanup() {
    print_header "Cleaning Up"
    if [ -f ".api.pid" ]; then
        kill $(cat .api.pid) 2>/dev/null || true
        rm .api.pid
    fi
    if [ -f ".lock_security.pid" ]; then
        kill $(cat .lock_security.pid) 2>/dev/null || true
        rm .lock_security.pid
    fi
    if [ -f ".emissions.pid" ]; then
        kill $(cat .emissions.pid) 2>/dev/null || true
        rm .emissions.pid
    fi
    if [ -f ".pre_sale.pid" ]; then
        kill $(cat .pre_sale.pid) 2>/dev/null || true
        rm .pre_sale.pid
    fi
}

# Trap signals
trap cleanup EXIT INT TERM

# Main execution
main() {
    print_header "🚀 Starting All Services Locally"
    
    check_python
    setup_venv
    install_dependencies
    setup_env
    test_venice_ai
    
    # Start services
    start_api
    start_lock_security
    start_emissions
    start_pre_sale
    
    # Wait a bit for services to start
    sleep 3
    
    # Health check
    health_check
    
    # Show status
    show_status
    
    print_header "✅ All Services Started"
    print_info "Press Ctrl+C to stop all services"
    
    # Keep script running
    wait
}

# Run main
main

