#!/bin/bash

echo "🏠 TROA - The Retreat Owners Association"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

command -v node >/dev/null 2>&1 || { echo -e "${RED}Node.js is required but not installed. Please install from https://nodejs.org/${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python 3 is required but not installed.${NC}"; exit 1; }
command -v mongod >/dev/null 2>&1 || { echo -e "${RED}MongoDB is required but not installed. Please install from https://www.mongodb.com/try/download/community${NC}"; exit 1; }
command -v yarn >/dev/null 2>&1 || { echo -e "${RED}Yarn is required. Install with: npm install -g yarn${NC}"; exit 1; }

echo -e "${GREEN}✓ All prerequisites found${NC}"
echo ""

# Start MongoDB if not running
echo -e "${YELLOW}Starting MongoDB...${NC}"
if ! pgrep -x "mongod" > /dev/null; then
    mkdir -p ./data/db
    mongod --dbpath ./data/db --fork --logpath ./data/mongod.log
    sleep 2
fi
echo -e "${GREEN}✓ MongoDB running${NC}"
echo ""

# Setup Backend
echo -e "${YELLOW}Setting up Backend...${NC}"
cd backend

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt --quiet

# Create .env file if not exists
if [ ! -f ".env" ]; then
    cat << 'ENVFILE' > .env
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=troa_db

# Google OAuth (Get from https://console.cloud.google.com/)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Razorpay (Get from https://dashboard.razorpay.com/)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Session Secret (generate a random string)
SESSION_SECRET=your-super-secret-key-change-this

# OpenAI for Chatbot (optional)
# EMERGENT_LLM_KEY=your_openai_key
ENVFILE
    echo -e "${YELLOW}⚠ Created backend/.env - Please update with your API keys${NC}"
fi

# Start backend in background
echo -e "${YELLOW}Starting Backend on port 8001...${NC}"
uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
cd ..

sleep 3
echo -e "${GREEN}✓ Backend running (PID: $BACKEND_PID)${NC}"
echo ""

# Setup Frontend
echo -e "${YELLOW}Setting up Frontend...${NC}"
cd frontend

# Install dependencies
yarn install --silent

# Create .env file if not exists
if [ ! -f ".env" ]; then
    cat << 'ENVFILE' > .env
REACT_APP_BACKEND_URL=http://localhost:8001
ENVFILE
fi

# Start frontend
echo -e "${YELLOW}Starting Frontend on port 3000...${NC}"
yarn start &
FRONTEND_PID=$!
cd ..

sleep 5
echo -e "${GREEN}✓ Frontend running (PID: $FRONTEND_PID)${NC}"
echo ""

echo "========================================="
echo -e "${GREEN}🎉 TROA is now running!${NC}"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8001"
echo "  API Docs: http://localhost:8001/docs"
echo ""
echo -e "${YELLOW}Note: Update backend/.env with your Google OAuth and Razorpay keys${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo "========================================="

# Wait for user to stop
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo 'Stopped all services.'; exit 0" SIGINT SIGTERM
wait
