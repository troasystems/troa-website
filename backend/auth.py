from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
import os
from typing import Optional
from datetime import datetime, timedelta
import secrets
from models import User, UserCreate
from motor.motor_asyncio import AsyncIOMotorClient

# Initialize OAuth
config = Config()
oauth = OAuth(config)

# Admin emails
ADMIN_EMAILS = ['troa.mgr@gmail.com', 'troa.systems@gmail.com']

# Register Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
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
    token = request.cookies.get('session_token')
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
    """Require admin authentication"""
    user = await require_auth(request)
    if user['email'] not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@auth_router.get('/google/login')
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@auth_router.get('/google/callback')
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        # Get database
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
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
        
        # Create session
        session_token = create_session(user_data)
        
        # Redirect to frontend with session token
        frontend_url = os.getenv('REACT_APP_BACKEND_URL', '').replace('/api', '')
        response = RedirectResponse(url=f'{frontend_url}/?auth_success=true')
        response.set_cookie(
            key='session_token',
            value=session_token,
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            samesite='lax'
        )
        
        client.close()
        return response
        
    except Exception as e:
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
