# TROA - The Retreat Owners Association

A full-stack web application for managing a residential community association. Built with React, FastAPI, and MongoDB.

> 📚 **Technical Documentation**: For a deep dive into the system architecture, booking logic, and data models, please see the [Architecture Overview](ARCHITECTURE_OVERVIEW.md).

![TROA Screenshot](https://customer-assets.emergentagent.com/job_troaresidents/artifacts/ig305kse_821366b6-decf-46dc-8c80-2dade0f65395.jpeg)

## Features

- 🏠 **Public Website** - Home, About, Committee, Amenities, Gallery, Contact pages
- 🔐 **Dual Authentication** - Google OAuth + Email/Password with email verification
- 👥 **Role-Based Access Control** - Admin, Manager, Accountant, Clubhouse Staff, and User roles
- 📅 **Amenity Booking System** - Book community amenities with calendar view
- 🎉 **Events Management** - Create events, register with online/offline payments
- 💳 **Razorpay Integration** - Online payment processing
- 🤖 **AI Chatbot** - Answer visitor queries about the community
- 📝 **Feedback System** - Collect and manage user feedback
- 📊 **Admin Portal** - Manage users, events, bookings, and approvals
- 📧 **Email Notifications** - SendGrid integration for transactional emails
- ✉️ **Email Verification** - 2-week grace period for new email registrations
- 📸 **Instagram Gallery** - Integrated Instagram feed display
- 🏘️ **Membership Applications** - New resident application workflow

## Tech Stack

- **Frontend**: React 18, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python 3.9+)
- **Database**: MongoDB
- **Authentication**: Google OAuth 2.0 + Email/Password
- **Payments**: Razorpay
- **Email Service**: SendGrid
- **AI/LLM**: OpenAI (via Emergent Integrations)

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- [Node.js](https://nodejs.org/) v18 or higher
- [Python](https://www.python.org/) v3.9 or higher
- [MongoDB](https://www.mongodb.com/try/download/community) v6.0 or higher
- [Yarn](https://yarnpkg.com/) package manager

### Step 1: Clone the Repository

```bash
git clone https://github.com/troasystems/troa-website.git
cd troa-website
```

### Step 2: Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes emergentintegrations from private registry)
pip install --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ -r requirements.txt

# Create .env file (see Environment Variables section below)
cp .env.example .env
# Edit .env with your credentials

# Start MongoDB (if not already running)
mongod --dbpath ./data/db &

# Run the backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies (use yarn, NOT npm)
yarn install

# Create .env file
cp .env.example .env
# Edit .env with your settings

# Run the development server
yarn start
```

### Step 4: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs (Swagger)**: http://localhost:8001/docs
- **API Docs (ReDoc)**: http://localhost:8001/redoc

---

## 🐳 Docker Setup (Alternative)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) v20.10 or higher
- [Docker Compose](https://docs.docker.com/compose/install/) v2.0 or higher

### Quick Start

```bash
# 1. Clone and navigate
git clone https://github.com/troasystems/troa-website.git
cd troa-website

# 2. Configure environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit both .env files with your credentials

# 3. Build and start
docker-compose up -d --build

# 4. View logs (optional)
docker-compose logs -f
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# Rebuild after code changes
docker-compose up -d --build

# Reset everything (removes all data!)
docker-compose down -v
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

```env
# Database Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=troa_residence

# CORS Configuration
CORS_ORIGINS=*

# Application URL (for email links)
REACT_APP_BACKEND_URL=http://localhost:3000

# ===========================================
# GOOGLE OAUTH (Required for Google login)
# ===========================================
# Get from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Session Secret (Change in production!)
SECRET_KEY=your-super-secret-key-change-this

# ===========================================
# INSTAGRAM INTEGRATION (Optional)
# ===========================================
# Get from: https://developers.facebook.com/apps/
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret

# ===========================================
# RAZORPAY PAYMENTS (Required for payments)
# ===========================================
# Get from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# ===========================================
# BASIC AUTH (Optional - for staging)
# ===========================================
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=your-secure-password

# ===========================================
# AI CHATBOT (Optional)
# ===========================================
# Emergent LLM Key for AI features
EMERGENT_LLM_KEY=your_emergent_llm_key

# ===========================================
# SENDGRID EMAIL (Required for email features)
# ===========================================
# Get from: https://app.sendgrid.com/settings/api_keys
SENDGRID_API_KEY=your_sendgrid_api_key
SENDER_EMAIL=noreply@yourdomain.com
```

### Frontend (`frontend/.env`)

```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# WebSocket Configuration (for development)
WDS_SOCKET_PORT=443

# Feature Flags
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false

# Basic Auth (if enabled on backend)
REACT_APP_BASIC_AUTH_USERNAME=admin
REACT_APP_BASIC_AUTH_PASSWORD=your-secure-password

# Google Client ID (for frontend Google Sign-In button)
REACT_APP_GOOGLE_CLIENT_ID=your_google_client_id
```

---

## 🔑 Third-Party Service Setup

### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client IDs**
5. Set Application type to **Web application**
6. Add Authorized JavaScript origins:
   - `http://localhost:3000` (development)
   - `https://yourdomain.com` (production)
7. Add Authorized redirect URIs:
   - `http://localhost:8001/api/auth/google/callback` (development)
   - `https://yourdomain.com/api/auth/google/callback` (production)
8. Copy Client ID and Client Secret to your `.env` files

### 2. SendGrid Setup (Email Service)

1. Go to [SendGrid Dashboard](https://app.sendgrid.com/)
2. Navigate to **Settings** > **API Keys**
3. Create a new API Key with "Full Access" or "Mail Send" permissions
4. Verify your Sender Identity (Single Sender Verification or Domain Authentication)
5. Copy the generated API Key to `SENDGRID_API_KEY` in `backend/.env`
6. Set `SENDER_EMAIL` to your verified sender address

### 3. Razorpay Setup (Payments)

1. Go to [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Navigate to **Settings** > **API Keys**
3. Generate API keys (use Test keys for development)
4. Copy Key ID and Key Secret to `backend/.env`

### 4. Instagram Integration (Optional)

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create an app with Instagram Basic Display
3. Configure OAuth redirect URIs
4. Copy App ID and App Secret to `backend/.env`

---

## 📁 Project Structure

```
troa-website/
├── backend/
│   ├── server.py          # Main FastAPI application & routes
│   ├── auth.py            # Authentication (Google OAuth + Email/Password)
│   ├── email_service.py   # SendGrid email service
│   ├── events.py          # Events management API
│   ├── chatbot.py         # AI chatbot logic
│   ├── models.py          # Pydantic models
│   ├── payment.py         # Razorpay integration
│   ├── instagram.py       # Instagram API integration
│   ├── upload.py          # File upload handling
│   ├── gridfs_upload.py   # GridFS file storage
│   ├── basic_auth.py      # Basic auth middleware
│   ├── tests/             # Backend tests
│   ├── uploads/           # Uploaded files storage
│   ├── Dockerfile         # Backend Docker image
│   └── requirements.txt   # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   │   ├── ui/        # Shadcn UI components
│   │   │   └── EmailVerificationBanner.jsx
│   │   ├── pages/         # Page components
│   │   │   ├── Login.jsx
│   │   │   ├── VerifyEmail.jsx
│   │   │   ├── Events.jsx
│   │   │   ├── Amenities.jsx
│   │   │   └── ...
│   │   ├── context/       # React context
│   │   │   └── AuthContext.jsx
│   │   ├── hooks/         # Custom hooks
│   │   └── App.js         # Main application router
│   ├── public/            # Static assets
│   ├── Dockerfile         # Frontend Docker image
│   └── package.json       # Node dependencies
│
├── docker-compose.yml     # Docker orchestration
├── start.sh              # Manual startup script
└── README.md
```

---

## 👤 User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Admin** | Full access - manage users, events, bookings, settings, approve applications |
| **Manager** | Manage events and bookings, view reports, approve registrations |
| **Accountant** | Manage maintenance invoices, view financial reports |
| **Clubhouse Staff** | Verify bookings and attendance, managing facility operations |
| **User** | Book amenities, register for events, submit feedback, view own bookings |

### Setting Up Admin User

The super admin email is hardcoded as `troa.systems@gmail.com`. To add additional admins:

```bash
# Connect to MongoDB
mongosh

# Select database
use troa_residence

# Promote user to admin
db.users.updateOne(
  { email: "user@example.com" },
  { $set: { role: "admin", is_admin: true } }
)

# Promote user to manager
db.users.updateOne(
  { email: "manager@example.com" },
  { $set: { role: "manager" } }
)
```

---

## 📧 Email Features

### Email Verification Flow

1. User registers with email/password
2. Verification email sent with unique token (valid for 2 weeks)
3. User can access the app during grace period (banner shown)
4. After 2 weeks without verification, login is blocked
5. User can request new verification email from login page

**Note**: Google OAuth users are automatically verified.

### Email Notifications

The system sends emails for:
- **Welcome Email** - On new user registration
- **Email Verification** - Registration verification link
- **Booking Confirmations** - Amenity booking created/modified/cancelled
- **Event Registrations** - Event registration pending/confirmed/withdrawn
- **Membership Applications** - New applications (to admin)
- **Feedback Submissions** - New feedback (to admin)

---

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

#### MongoDB Connection Error
```bash
# Check if MongoDB is running
systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Or run manually
mongod --dbpath ./data/db
```

#### emergentintegrations Package Not Found
```bash
# Use the extra index URL
pip install --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ -r requirements.txt
```

#### Google OAuth Not Working
- Verify redirect URIs match exactly in Google Console
- Check GOOGLE_CLIENT_ID is set in both backend and frontend `.env`
- Clear browser cookies and try again

#### AWS SES Emails Not Sending
- Check if SES is in sandbox mode (only sends to verified emails)
- Verify IAM credentials have correct permissions
- Check AWS_SES_REGION matches your SES region
- Request production access for sending to any email

#### Email Verification Banner Showing for Google Users
- This is fixed - Google users are automatically verified
- If issue persists, clear browser cache and re-login

### Viewing Logs

```bash
# Backend logs (if using uvicorn directly)
# Logs appear in terminal

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Check MongoDB
docker-compose logs mongodb
```

---

## 🧪 Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_user_whitelist.py -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
yarn test

# Run with coverage
yarn test --coverage
```

---

## 🚀 Deployment

### Production Checklist

1. **Environment Variables**
   - Change `SECRET_KEY` to a strong random value
   - Update `REACT_APP_BACKEND_URL` to production domain
   - Use production API keys (not test keys)

2. **AWS SES**
   - Move out of sandbox mode
   - Verify production domain

3. **Google OAuth**
   - Add production domain to authorized origins/redirects

4. **Security**
   - Enable HTTPS
   - Configure proper CORS origins
   - Set secure session cookies

5. **Database**
   - Use MongoDB Atlas or production MongoDB instance
   - Enable authentication
   - Set up backups

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
