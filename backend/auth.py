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
# ADMIN_EMAIL is the "super admin" that can never lose admin access
# This is a safety measure to ensure there's always at least one admin
SUPER_ADMIN_EMAIL = 'troa.systems@gmail.com'

# Legacy support - kept for backward compatibility
ADMIN_EMAIL = SUPER_ADMIN_EMAIL
ADMIN_EMAILS = [ADMIN_EMAIL]

# Note: Manager roles are now stored in the database and managed via User Management
# The hardcoded MANAGER_EMAILS list has been removed - use the database instead

async def get_user_role_from_db(email: str) -> str:
    """Get user role from database, with super admin override"""
    # Super admin always gets admin role
    if email == SUPER_ADMIN_EMAIL:
        return 'admin'
    
    # Check database for existing user role
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        user = await db.users.find_one({'email': email}, {'_id': 0, 'role': 1})
        if user and 'role' in user:
            return user['role']
    finally:
        client.close()
    
    # Default role for new users
    return 'user'

def get_user_role(email: str) -> str:
    """Synchronous version - only checks super admin, returns 'user' for others
    For full role check, use get_user_role_from_db() async function"""
    if email == SUPER_ADMIN_EMAIL:
        return 'admin'
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

# MongoDB session store for production (replaces in-memory sessions)
async def get_sessions_collection():
    """Get the sessions collection from MongoDB"""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    return db.sessions, client

async def create_session(user_data: dict) -> str:
    """Create a session token and store in MongoDB"""
    token = secrets.token_urlsafe(32)
    sessions_col, client = await get_sessions_collection()
    
    session_doc = {
        'token': token,
        'user': user_data,
        'expires': datetime.utcnow() + timedelta(days=7),
        'created_at': datetime.utcnow()
    }
    
    await sessions_col.insert_one(session_doc)
    client.close()
    return token

async def get_session(token: str) -> Optional[dict]:
    """Get session data from MongoDB"""
    sessions_col, client = await get_sessions_collection()
    
    session = await sessions_col.find_one(
        {'token': token, 'expires': {'$gt': datetime.utcnow()}},
        {'_id': 0}
    )
    
    client.close()
    
    if session:
        return session['user']
    return None

async def delete_session(token: str):
    """Delete session from MongoDB"""
    sessions_col, client = await get_sessions_collection()
    await sessions_col.delete_one({'token': token})
    client.close()

async def get_current_user(request: Request) -> Optional[dict]:
    """Get current logged in user from session"""
    # Try to get token from cookie first
    token = request.cookies.get('session_token')
    
    # If not in cookie, try X-Session-Token header (used when basic auth is present)
    if not token:
        session_header = request.headers.get('X-Session-Token')
        if session_header and session_header.startswith('Bearer '):
            token = session_header.replace('Bearer ', '')
    
    # If still not found, try Authorization header (fallback for backward compatibility)
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
    
    if not token:
        return None
    return await get_session(token)

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
    # Detect the origin from headers - this is where the user came from
    origin = None
    scheme = request.headers.get('x-forwarded-proto', 'https')
    
    # Log all relevant headers for debugging
    logger.info(f"OAuth login - Headers: host={request.headers.get('host')}, "
                f"x-forwarded-host={request.headers.get('x-forwarded-host')}, "
                f"x-forwarded-proto={request.headers.get('x-forwarded-proto')}, "
                f"origin={request.headers.get('origin')}, "
                f"referer={request.headers.get('referer')}")
    
    # Priority 1: Referer header (most reliable - contains the actual page URL)
    referer = request.headers.get('referer')
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            origin = f"{parsed.scheme}://{parsed.netloc}"
            logger.info(f"Using referer for origin: {origin}")
    
    # Priority 2: x-forwarded-host header
    if not origin:
        forwarded_host = request.headers.get('x-forwarded-host')
        if forwarded_host:
            forwarded_host = forwarded_host.split(',')[0].strip()
            origin = f"{scheme}://{forwarded_host}"
            logger.info(f"Using x-forwarded-host for origin: {origin}")
    
    # Priority 3: Origin header
    if not origin:
        origin = request.headers.get('origin')
        if origin:
            logger.info(f"Using origin header: {origin}")
    
    # Priority 4: Fallback to host header
    if not origin:
        host = request.headers.get('host', '')
        origin = f"{scheme}://{host}"
        logger.info(f"Using host header fallback: {origin}")
    
    # Store the origin in a cookie so we can retrieve it in the callback
    # This is needed because Google's redirect won't preserve our headers
    redirect_uri = f"{origin}/api/auth/google/callback"
    logger.info(f"OAuth login initiated with redirect_uri: {redirect_uri}")
    
    # Create response that will redirect to Google
    response = await oauth.google.authorize_redirect(request, redirect_uri)
    
    # Set cookie with the origin domain for the callback to use
    response.set_cookie(
        key='oauth_origin',
        value=origin,
        httponly=True,
        max_age=600,  # 10 minutes
        samesite='lax',
        path='/'
    )
    
    return response

@auth_router.get('/google/callback')
async def google_callback(code: str, state: str, request: Request):
    """Handle Google OAuth callback - Manual implementation"""
    try:
        logger.info(f"Google OAuth callback received with code: {code[:20]}...")
        
        # Get the origin from the cookie we set during login
        origin = request.cookies.get('oauth_origin')
        
        if origin:
            logger.info(f"Using origin from oauth_origin cookie: {origin}")
        else:
            # Fallback: try to determine from headers (less reliable)
            scheme = request.headers.get('x-forwarded-proto', 'https')
            
            # Log headers for debugging
            logger.info(f"OAuth callback - No oauth_origin cookie found. Headers: host={request.headers.get('host')}, "
                        f"x-forwarded-host={request.headers.get('x-forwarded-host')}, "
                        f"referer={request.headers.get('referer')}")
            
            # Try x-forwarded-host first
            forwarded_host = request.headers.get('x-forwarded-host')
            if forwarded_host:
                forwarded_host = forwarded_host.split(',')[0].strip()
                origin = f"{scheme}://{forwarded_host}"
            
            # Fallback to host header
            if not origin:
                host = request.headers.get('host', '')
                origin = f"{scheme}://{host}"
                
            logger.info(f"Using fallback origin: {origin}")
        
        redirect_uri = f"{origin}/api/auth/google/callback"
        logger.info(f"OAuth callback using redirect_uri: {redirect_uri}")
        
        # Exchange code for token manually
        import httpx
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': GOOGLE_CLIENT_ID,
                    'client_secret': GOOGLE_CLIENT_SECRET,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed with status {token_response.status_code}")
                logger.error(f"Token exchange response: {token_response.text}")
                logger.error(f"Used redirect_uri: {redirect_uri}")
                raise HTTPException(status_code=400, detail=f"Failed to exchange code for token: {token_response.text}")
            
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
        existing_user = await db.users.find_one({'email': user_info['email']}, {'_id': 0})
        
        # Determine user role - super admin always gets admin, others check database
        if user_info['email'] == SUPER_ADMIN_EMAIL:
            user_role = 'admin'
        elif existing_user and 'role' in existing_user:
            # Use existing role from database (set by admin via User Management)
            user_role = existing_user['role']
        else:
            # Default role for new users
            user_role = 'user'
        
        user_data = {
            'email': user_info['email'],
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', ''),
            'role': user_role,
            'is_admin': user_role == 'admin'  # Legacy support
        }
        
        if not existing_user:
            # Create new user with default 'user' role (admin can promote later)
            user_obj = User(
                email=user_info['email'],
                name=user_info.get('name', ''),
                picture=user_info.get('picture', ''),
                provider='google',
                role=user_role,
                is_admin=user_role == 'admin'
            )
            await db.users.insert_one(user_obj.dict())
            logger.info(f"New user created: {user_info['email']} with role: {user_role}")
        else:
            # Update existing user - preserve role from database
            update_data = {
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'last_login': datetime.utcnow()
            }
            
            # Only update role for super admin to ensure they always have admin access
            if user_info['email'] == SUPER_ADMIN_EMAIL and existing_user.get('role') != 'admin':
                update_data['role'] = 'admin'
                update_data['is_admin'] = True
            
            await db.users.update_one(
                {'email': user_info['email']},
                {'$set': update_data}
            )
            logger.info(f"Existing user updated: {user_info['email']} with role: {user_role}")
        
        # Create session
        session_token = await create_session(user_data)
        logger.info(f"Session created for user: {user_info['email']}")
        
        # Redirect to frontend with session token in URL
        # Use the same origin that initiated the request
        frontend_url = origin
        logger.info(f"Redirecting to frontend: {frontend_url} with token: {session_token[:20]}...")
        response = RedirectResponse(url=f'{frontend_url}/?auth_success=true&token={session_token}')
        
        # Set cookie with proper settings for production
        # Note: samesite='none' requires secure=True for HTTPS
        is_secure = frontend_url.startswith('https')
        response.set_cookie(
            key='session_token',
            value=session_token,
            httponly=False,
            secure=is_secure,
            max_age=7 * 24 * 60 * 60,  # 7 days
            samesite='none' if is_secure else 'lax',
            path='/'
        )
        
        # Clear the oauth_origin cookie
        response.delete_cookie('oauth_origin')
        
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
        await delete_session(token)
    
    response = Response(content='{"message": "Logged out successfully"}')
    response.delete_cookie('session_token')
    return response
