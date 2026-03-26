#!/bin/bash
# =============================================================================
# Start the AI Learning Assistant locally (backend + frontend)
# Usage: ./start-local.sh
# =============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}Starting AI Learning Assistant locally...${NC}"

# ─── BACKEND ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[1/3] Installing backend dependencies...${NC}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Created virtual environment${NC}"
fi

source venv/bin/activate

pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# ─── FRONTEND ENV ─────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/3] Setting up frontend...${NC}"

if [ ! -f "frontend/.env.local" ]; then
    echo "REACT_APP_API_URL=http://localhost:8000" > frontend/.env.local
    echo "REACT_APP_ENV=development" >> frontend/.env.local
    echo -e "${GREEN}✓ Created frontend/.env.local with API URL${NC}"
else
    echo -e "${GREEN}✓ frontend/.env.local already exists${NC}"
fi

cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi
cd ..

# ─── START BOTH SERVERS ───────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/3] Starting servers...${NC}"
echo ""
echo -e "${GREEN}Backend  → http://localhost:8000${NC}"
echo -e "${GREEN}Frontend → http://localhost:3000${NC}"
echo -e "${GREEN}API Docs → http://localhost:8000/docs${NC}"
echo ""
echo -e "${CYAN}Press Ctrl+C to stop both servers${NC}"
echo ""

# Start backend in background
uvicorn app:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
cd frontend && REACT_APP_API_URL=http://localhost:8000 npm start &
FRONTEND_PID=$!

# Trap to kill both on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT

wait
