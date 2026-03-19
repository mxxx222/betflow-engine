#!/bin/bash
# Stop all local services

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${YELLOW}Stopping all local services...${NC}\n"

# Stop API
if [ -f ".api.pid" ]; then
    PID=$(cat .api.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✅ Stopped API (PID: $PID)${NC}"
    fi
    rm .api.pid
fi

# Stop Lock Security
if [ -f ".lock_security.pid" ]; then
    PID=$(cat .lock_security.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✅ Stopped Lock Security (PID: $PID)${NC}"
    fi
    rm .lock_security.pid
fi

# Stop Emissions
if [ -f ".emissions.pid" ]; then
    PID=$(cat .emissions.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✅ Stopped Emissions Testing (PID: $PID)${NC}"
    fi
    rm .emissions.pid
fi

# Stop Pre-Sale
if [ -f ".pre_sale.pid" ]; then
    PID=$(cat .pre_sale.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo -e "${GREEN}✅ Stopped Pre-Sale Inspection (PID: $PID)${NC}"
    fi
    rm .pre_sale.pid
fi

# Kill any remaining uvicorn processes
pkill -f "uvicorn" 2>/dev/null && echo -e "${GREEN}✅ Stopped remaining uvicorn processes${NC}" || true

echo -e "\n${GREEN}✅ All services stopped${NC}\n"

