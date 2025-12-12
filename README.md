# TROA - The Retreat Owners Association

A full-stack web application for managing a residential community association. Built with React, FastAPI, and MongoDB.

![TROA Screenshot](https://customer-assets.emergentagent.com/job_tron-inspired/artifacts/s7kqkc41_Gemini_Generated_Image_b3s3itb3s3itb3s3.png)

## Features

- 🏠 **Public Website** - Home, About, Committee, Amenities, Gallery, Contact pages
- 🔐 **Google OAuth Authentication** - Secure login with Google
- 👥 **Role-Based Access Control** - Admin, Manager, and User roles
- 📅 **Amenity Booking System** - Book community amenities with calendar view
- 🎉 **Events Management** - Create events, register with online/offline payments
- 💳 **Razorpay Integration** - Online payment processing
- 🤖 **AI Chatbot** - Answer visitor queries about the community
- 📝 **Feedback System** - Collect and manage user feedback
- 📊 **Admin Portal** - Manage users, events, bookings, and approvals

## Tech Stack

- **Frontend**: React 18, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: Google OAuth 2.0
- **Payments**: Razorpay

## Prerequisites

Before running the application, ensure you have installed:

- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/) (v3.9 or higher)
- [MongoDB](https://www.mongodb.com/try/download/community) (v6.0 or higher)
- [Yarn](https://yarnpkg.com/) package manager

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/troa.git
cd troa
```

### 2. Run the Setup Script

Create a file called `start.sh` in the root directory and run it:

```bash
chmod +x start.sh
./start.sh
```

**Or run this single command to create and execute the setup:**

```bash
cat << 'EOF' > start.sh
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
EOF
chmod +x start.sh && ./start.sh
```

## Manual Setup

If you prefer to set up manually:

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables section)

# Run the server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Create .env file
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Run the development server
yarn start
```

## Environment Variables

### Backend (`backend/.env`)

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=troa_db

# Google OAuth (Required for login)
# Get from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Razorpay (Required for payments)
# Get from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Session
SESSION_SECRET=generate-a-random-secret-key

# OpenAI for Chatbot (Optional)
EMERGENT_LLM_KEY=your_openai_api_key
```

### Frontend (`frontend/.env`)

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client IDs**
5. Set Application type to **Web application**
6. Add Authorized redirect URIs:
   - `http://localhost:8001/api/auth/google/callback` (development)
   - `https://yourdomain.com/api/auth/google/callback` (production)
7. Copy the Client ID and Client Secret to your `.env` file

## Project Structure

```
troa/
├── backend/
│   ├── server.py          # Main FastAPI application
│   ├── auth.py            # Authentication & OAuth
│   ├── events.py          # Events management API
│   ├── chatbot.py         # AI chatbot logic
│   ├── models.py          # Pydantic models
│   ├── upload.py          # File upload handling
│   ├── payment.py         # Razorpay integration
│   └── requirements.txt   # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── context/       # React context (Auth)
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utility functions
│   ├── public/            # Static assets
│   └── package.json       # Node dependencies
│
└── README.md
```

## Default Admin Setup

After first login with Google OAuth, make yourself an admin:

```bash
# Connect to MongoDB
mongosh

# Switch to database
use troa_db

# Update your user role to admin
db.users.updateOne(
  { email: "your-email@gmail.com" },
  { $set: { role: "admin" } }
)
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Stopping the Application

If you used the start script:
- Press `Ctrl+C` to stop all services

To stop MongoDB:
```bash
mongod --shutdown --dbpath ./data/db
```

## Troubleshooting

### MongoDB Connection Error
```bash
# Make sure MongoDB is running
mongod --dbpath ./data/db
```

### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

### Google OAuth Not Working
- Ensure redirect URIs match exactly in Google Console
- Check that GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct
- Clear browser cookies and try again

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email troa.systems@gmail.com or open an issue on GitHub.
