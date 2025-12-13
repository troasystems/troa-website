# TROA - The Retreat Owners Association

A full-stack web application for managing a residential community association. Built with React, FastAPI, and MongoDB.

![TROA Screenshot](https://customer-assets.emergentagent.com/job_troaresidents/artifacts/ig305kse_821366b6-decf-46dc-8c80-2dade0f65395.jpeg)

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

---

## 🐳 Docker Setup (Recommended)

The easiest way to run TROA is using Docker. This will set up the entire stack (Frontend, Backend, MongoDB) with a single command.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0 or higher)

### Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/your-username/troa.git
cd troa

# 2. Configure environment variables
# Option A: If backend/.env exists, edit it with your API keys
# Option B: If not, create it from the example:
cp backend/.env.example backend/.env
# Then edit backend/.env with your API keys (see Configuration section below)

# 3. Start the application
docker-compose up -d --build

# 4. View logs (optional)
docker-compose logs -f
```

**That's it!** The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart all services
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# Rebuild images (after code changes)
docker-compose up -d --build

# Remove all containers and volumes (clean slate)
docker-compose down -v

# Check service status
docker-compose ps
```

### Configuration

Before starting, ensure `backend/.env` exists with your credentials. If it doesn't exist, create it from the example:

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env` with your credentials:

```env
# Google OAuth (Required)
# Get from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Razorpay (Required for payments)
# Get from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Session Secret (Change this!)
SESSION_SECRET=generate-a-random-secret-key-here

# OpenAI for Chatbot (Optional)
EMERGENT_LLM_KEY=your_openai_api_key
```

### Production Deployment with Docker

For production, create a `docker-compose.prod.yml`:

```bash
# Build and deploy for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 💻 Manual Setup (Without Docker)

If you prefer to run without Docker:

### Prerequisites

- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/) (v3.9 or higher)
- [MongoDB](https://www.mongodb.com/try/download/community) (v6.0 or higher)
- [Yarn](https://yarnpkg.com/) package manager

### Option 1: Using the Start Script

```bash
# Clone the repository
git clone https://github.com/your-username/troa.git
cd troa

# Make the script executable and run
chmod +x start.sh
./start.sh
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat << EOF > .env
MONGO_URL=mongodb://localhost:27017
DB_NAME=troa_db
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
SESSION_SECRET=your-super-secret-key
EOF

# Start MongoDB (if not running)
mongod --dbpath ./data/db &

# Run the server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Create .env file
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Run the development server
yarn start
```

---

## 🔧 Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client IDs**
5. Set Application type to **Web application**
6. Add Authorized redirect URIs:
   - Development: `http://localhost:8001/api/auth/google/callback`
   - Docker: `http://localhost:8001/api/auth/google/callback`
   - Production: `https://yourdomain.com/api/auth/google/callback`
7. Copy the Client ID and Client Secret to your `.env` file

---

## 📁 Project Structure

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
│   ├── Dockerfile         # Backend Docker image
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
│   ├── Dockerfile         # Frontend Docker image
│   ├── nginx.conf         # Nginx config for production
│   └── package.json       # Node dependencies
│
├── docker-compose.yml     # Docker orchestration
├── start.sh              # Manual startup script
└── README.md
```

---

## 👤 Admin Setup

After first login with Google OAuth, make yourself an admin:

### Using Docker:

```bash
# Connect to MongoDB container
docker exec -it troa-mongodb mongosh

# In mongosh:
use troa_db
db.users.updateOne(
  { email: "your-email@gmail.com" },
  { $set: { role: "admin" } }
)
exit
```

### Without Docker:

```bash
mongosh
use troa_db
db.users.updateOne(
  { email: "your-email@gmail.com" },
  { $set: { role: "admin" } }
)
```

---

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

---

## 🔍 Troubleshooting

### Docker Issues

```bash
# Check if containers are running
docker-compose ps

# Check container logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb

# Restart a specific service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build

# Reset everything (removes data!)
docker-compose down -v
docker-compose up -d --build
```

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

### MongoDB Connection Error

```bash
# Check if MongoDB is running
docker-compose ps mongodb

# Or for manual setup:
mongod --dbpath ./data/db
```

### Google OAuth Not Working

- Ensure redirect URIs match exactly in Google Console
- For Docker: Use `http://localhost:8001/api/auth/google/callback`
- Check that GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct
- Clear browser cookies and try again

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Support

For support, email troa.systems@gmail.com or open an issue on GitHub.
