from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import os
import logging
from typing import Optional
from datetime import datetime, timedelta
import secrets
from models import User, UserCreate
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OAuth
oauth = OAuth()

# Role-based email lists
ADMIN_EMAIL = 'troa.systems@gmail.com'
MANAGER_EMAILS = [
    'troa.mgr@gmail.com',
    'troa.secretary@gmail.com',
    'troa.treasurer@gmail.com',
    'president.troa@gmail.com'
]

# Legacy support
ADMIN_EMAILS = [ADMIN_EMAIL]

def get_user_role(email: str) -> str:
    """Determine user role based on email"""
    if email == ADMIN_EMAIL:
        return 'admin'
    elif email in MANAGER_EMAILS:
        return 'manager'
    else:
        return 'user'

# Get OAuth credentials
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Register Google OAuth
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

auth_router = APIRouter(prefix="/auth")

# Session store (in production, use Redis or database)
sessions = {}

def create_session(user_data: dict) -> str:
    """Create a session token"""
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        'user': user_data,
        'expires': datetime.utcnow() + timedelta(days=7)
    }
    return token

def get_session(token: str) -> Optional[dict]:
    """Get session data"""
    session = sessions.get(token)
    if session and session['expires'] > datetime.utcnow():
        return session['user']
    return None

def delete_session(token: str):
    """Delete session"""
    if token in sessions:
        del sessions[token]

async def get_current_user(request: Request) -> Optional[dict]:
    """Get current logged in user from session"""
    # Try to get token from cookie first
    token = request.cookies.get('session_token')
    
    # If not in cookie, try Authorization header
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
    
    if not token:
        return None
    return get_session(token)

async def require_auth(request: Request):
    """Require authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

async def require_admin(request: Request):
    """Require admin authentication - only for troa.systems@gmail.com"""
    user = await require_auth(request)
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_manager_or_admin(request: Request):
    """Require manager or admin authentication"""
    user = await require_auth(request)
    if user.get('role') not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Manager or Admin access required")
    return user

@auth_router.get('/google/login')
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    # Construct the full redirect URI
    backend_url = os.getenv('REACT_APP_BACKEND_URL', str(request.base_url).rstrip('/'))
    redirect_uri = f"{backend_url}/api/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@auth_router.get('/google/callback')
async def google_callback(code: str, state: str):
    """Handle Google OAuth callback - Manual implementation"""
    try:
        logger.info(f"Google OAuth callback received with code: {code[:20]}...")
        
        # Exchange code for token manually
        import httpx
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'redirect_uri': f"{os.getenv('REACT_APP_BACKEND_URL')}/api/auth/google/callback",
                    'grant_type': 'authorization_code'
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            # Get user info
            user_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if user_response.status_code != 200:
                logger.error(f"Failed to get user info: {user_response.text}")
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_info = user_response.json()
            logger.info(f"User authenticated: {user_info.get('email')}")
        
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Check if user exists
        existing_user = await db.users.find_one({'email': user_info['email']})
        
        user_data = {
            'email': user_info['email'],
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', ''),
            'is_admin': user_info['email'] in ADMIN_EMAILS
        }
        
        if not existing_user:
            # Create new user
            user_obj = User(
                email=user_info['email'],
                name=user_info.get('name', ''),
                picture=user_info.get('picture', ''),
                provider='google',
                is_admin=user_info['email'] in ADMIN_EMAILS
            )
            await db.users.insert_one(user_obj.dict())
            logger.info(f"New user created: {user_info['email']}")
        else:
            # Update existing user
            await db.users.update_one(
                {'email': user_info['email']},
                {'$set': {
                    'name': user_info.get('name', ''),
                    'picture': user_info.get('picture', ''),
                    'last_login': datetime.utcnow()
                }}
            )
            logger.info(f"Existing user updated: {user_info['email']}")
        
        # Create session
        session_token = create_session(user_data)
        logger.info(f"Session created for user: {user_info['email']}")
        
        # Redirect to frontend with session token in URL
        frontend_url = os.getenv('REACT_APP_BACKEND_URL', '').replace('/api', '')
        response = RedirectResponse(url=f'{frontend_url}/?auth_success=true&token={session_token}')
        response.set_cookie(
            key='session_token',
            value=session_token,
            httponly=False,
            max_age=7 * 24 * 60 * 60,  # 7 days
            samesite='lax',
            path='/'
        )
        
        mongo_client.close()
        return response
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@auth_router.get('/user')
async def get_user(request: Request):
    """Get current user info"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@auth_router.post('/logout')
async def logout(request: Request):
    """Logout user"""
    token = request.cookies.get('session_token')
    if token:
        delete_session(token)
    
    response = Response(content='{"message": "Logged out successfully"}')
    response.delete_cookie('session_token')
    return response
