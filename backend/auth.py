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
    """Handle Google OAuth callback - Manual implementation with popup support"""
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
        
        needs_villa_number = False
        
        if not existing_user:
            # Create new user with default 'user' role (admin can promote later)
            user_obj = User(
                email=user_info['email'],
                name=user_info.get('name', ''),
                picture=user_info.get('picture', ''),
                provider='google',
                role=user_role,
                is_admin=user_role == 'admin',
                villa_number='',  # Empty - will need to be filled
                email_verified=True  # Google users are pre-verified
            )
            await db.users.insert_one(user_obj.dict())
            logger.info(f"New user created: {user_info['email']} with role: {user_role}")
            needs_villa_number = True  # New user needs to provide villa number
        else:
            # Update existing user - preserve role and villa_number from database
            update_data = {
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'last_login': datetime.utcnow(),
                'email_verified': True  # Google users are always verified
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
            
            # Check if existing user needs villa number (empty or not set)
            if not existing_user.get('villa_number'):
                needs_villa_number = True
        
        # Add villa number requirement flag to user data
        user_data['needs_villa_number'] = needs_villa_number
        user_data['villa_number'] = existing_user.get('villa_number', '') if existing_user else ''
        
        # Create session
        session_token = await create_session(user_data)
        logger.info(f"Session created for user: {user_info['email']}, needs_villa: {needs_villa_number}")
        
        mongo_client.close()
        
        # Return HTML that will send message to parent window (for popup)
        # This works for both popup and redirect flows
        frontend_url = origin
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    text-align: center;
                    color: white;
                }}
                .spinner {{
                    border: 4px solid rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    border-top: 4px solid white;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                <h2>Authentication Successful!</h2>
                <p>Redirecting you back...</p>
            </div>
            <script>
                // Try to send message to parent window (for popup)
                if (window.opener) {{
                    console.log('Sending message to parent window');
                    window.opener.postMessage({{
                        type: 'oauth_success',
                        token: '{session_token}'
                    }}, '{frontend_url}');
                    // Close popup after sending message
                    setTimeout(() => {{
                        window.close();
                    }}, 1000);
                }} else {{
                    // If not in popup, redirect normally
                    console.log('Not in popup, redirecting normally');
                    window.location.href = '{frontend_url}/?auth_success=true&token={session_token}';
                }}
            </script>
        </body>
        </html>
        """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@auth_router.get('/user')
async def get_user(request: Request):
    """Get current user info - fetches fresh data from database"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Fetch fresh user data from database to get latest picture, etc.
    try:
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        db_user = await db.users.find_one({'email': user['email']}, {'_id': 0, 'password_hash': 0})
        mongo_client.close()
        
        if db_user:
            # Format verification_expires_at
            verification_expires_at = db_user.get('verification_expires_at')
            if verification_expires_at and isinstance(verification_expires_at, datetime):
                verification_expires_at = verification_expires_at.isoformat()
            
            # Return fresh data from database with session role info
            return {
                'email': db_user.get('email'),
                'name': db_user.get('name'),
                'picture': db_user.get('picture', ''),
                'role': user.get('role', 'user'),  # Keep role from session for consistency
                'is_admin': user.get('role') == 'admin',
                'villa_number': db_user.get('villa_number'),
                'email_verified': db_user.get('email_verified', False),
                'verification_expires_at': verification_expires_at,
                'provider': db_user.get('provider', 'email')
            }
        
        return user
    except Exception as e:
        logger.error(f"Error fetching fresh user data: {str(e)}")
        # Fallback to session data if database fetch fails
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


# Email/Password Authentication Routes
from pydantic import BaseModel, EmailStr
import bcrypt
from email_service import email_service

# Verification token expiry in days
VERIFICATION_EXPIRY_DAYS = 14

class EmailPasswordRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    villa_number: str  # Required field
    picture: Optional[str] = None  # Optional profile picture

class EmailPasswordLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyEmailRequest(BaseModel):
    token: str
    email: Optional[str] = None

@auth_router.post('/register')
async def register_with_email(credentials: EmailPasswordRegister, request: Request):
    """Register a new user with email and password"""
    try:
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Check if user already exists
        existing_user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
        if existing_user:
            mongo_client.close()
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(credentials.password.encode('utf-8'), bcrypt.gensalt())
        
        # Determine user role - super admin gets admin role, others get user role
        user_role = 'admin' if credentials.email == SUPER_ADMIN_EMAIL else 'user'
        
        # Generate verification token and expiry
        verification_token = secrets.token_urlsafe(32)
        verification_expires_at = datetime.utcnow() + timedelta(days=VERIFICATION_EXPIRY_DAYS)
        
        # Create new user
        user_obj = User(
            email=credentials.email,
            name=credentials.name,
            picture=credentials.picture or '',
            provider='email',
            role=user_role,
            is_admin=user_role == 'admin',
            villa_number=credentials.villa_number,
            email_verified=False,
            verification_token=verification_token,
            verification_expires_at=verification_expires_at
        )
        
        user_dict = user_obj.dict()
        user_dict['password_hash'] = password_hash.decode('utf-8')  # Store as string
        
        await db.users.insert_one(user_dict)
        logger.info(f"New user registered: {credentials.email} with role: {user_role}, villa: {credentials.villa_number}")
        
        # Send verification email
        # Determine the frontend URL for the verification link
        origin = None
        referer = request.headers.get('referer')
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                origin = f"{parsed.scheme}://{parsed.netloc}"
        
        if not origin:
            origin = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
        
        verification_link = f"{origin}/verify-email?token={verification_token}&email={credentials.email}"
        
        # Send verification email
        try:
            email_result = await email_service.send_verification_email(
                recipient_email=credentials.email,
                verification_link=verification_link,
                user_name=credentials.name,
                expiry_days=VERIFICATION_EXPIRY_DAYS
            )
            logger.info(f"Verification email sent to {credentials.email}: {email_result}")
        except Exception as email_error:
            logger.error(f"Failed to send verification email: {email_error}")
        
        # Send welcome email
        try:
            await email_service.send_welcome_email(
                recipient_email=credentials.email,
                user_name=credentials.name
            )
            logger.info(f"Welcome email sent to {credentials.email}")
        except Exception as email_error:
            logger.error(f"Failed to send welcome email: {email_error}")
        
        # Create session
        user_data = {
            'email': credentials.email,
            'name': credentials.name,
            'picture': credentials.picture or '',
            'role': user_role,
            'is_admin': user_role == 'admin',
            'villa_number': credentials.villa_number,
            'email_verified': False,
            'verification_expires_at': verification_expires_at.isoformat()
        }
        
        session_token = await create_session(user_data)
        
        mongo_client.close()
        
        return {
            'message': 'Registration successful. Please check your email to verify your account.',
            'token': session_token,
            'user': user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@auth_router.post('/login')
async def login_with_email(credentials: EmailPasswordLogin, request: Request):
    """Login with email and password"""
    try:
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Find user
        user = await db.users.find_one({'email': credentials.email}, {'_id': 0})
        if not user:
            mongo_client.close()
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user registered with email/password
        if user.get('provider') != 'email':
            mongo_client.close()
            raise HTTPException(status_code=400, detail="This email is registered with Google. Please use Google login.")
        
        # Verify password
        password_hash = user.get('password_hash', '')
        if not password_hash or not bcrypt.checkpw(credentials.password.encode('utf-8'), password_hash.encode('utf-8')):
            mongo_client.close()
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check email verification status
        email_verified = user.get('email_verified', False)
        verification_expires_at = user.get('verification_expires_at')
        
        # If not verified and grace period has expired, block login
        if not email_verified and verification_expires_at:
            expiry_date = verification_expires_at if isinstance(verification_expires_at, datetime) else datetime.fromisoformat(str(verification_expires_at).replace('Z', '+00:00'))
            if datetime.utcnow() > expiry_date:
                mongo_client.close()
                raise HTTPException(
                    status_code=403, 
                    detail="Your email is not verified and the grace period has expired. Please verify your email to continue using TROA.",
                    headers={"X-Email-Unverified": "true", "X-Grace-Period-Expired": "true"}
                )
        
        # Update last login
        await db.users.update_one(
            {'email': credentials.email},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Determine user role - super admin always gets admin, others use database role
        user_role = 'admin' if user['email'] == SUPER_ADMIN_EMAIL else user.get('role', 'user')
        
        # If user is super admin but database doesn't have admin role, update it
        if user['email'] == SUPER_ADMIN_EMAIL and user.get('role') != 'admin':
            await db.users.update_one(
                {'email': credentials.email},
                {'$set': {'role': 'admin', 'is_admin': True}}
            )
        
        # Create session with verification info
        user_data = {
            'email': user['email'],
            'name': user['name'],
            'picture': user.get('picture', ''),
            'role': user_role,
            'is_admin': user_role == 'admin',
            'villa_number': user.get('villa_number'),
            'email_verified': email_verified,
            'verification_expires_at': verification_expires_at.isoformat() if verification_expires_at else None,
            'provider': user.get('provider', 'email')
        }
        
        session_token = await create_session(user_data)
        logger.info(f"User logged in: {credentials.email}")
        
        mongo_client.close()
        
        return {
            'message': 'Login successful',
            'token': session_token,
            'user': user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# Change Password Endpoint
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@auth_router.post('/change-password')
async def change_password(passwords: PasswordChange, request: Request):
    """Change user password"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Find user in database
        db_user = await db.users.find_one({'email': user['email']}, {'_id': 0})
        if not db_user:
            mongo_client.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user registered with email/password
        if db_user.get('provider') != 'email':
            mongo_client.close()
            raise HTTPException(status_code=400, detail="Password change only available for email/password accounts")
        
        # Verify current password
        password_hash = db_user.get('password_hash', '')
        if not password_hash or not bcrypt.checkpw(passwords.current_password.encode('utf-8'), password_hash.encode('utf-8')):
            mongo_client.close()
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Validate new password
        if len(passwords.new_password) < 6:
            mongo_client.close()
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(passwords.new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password
        await db.users.update_one(
            {'email': user['email']},
            {'$set': {'password_hash': new_password_hash.decode('utf-8')}}
        )
        
        logger.info(f"Password changed for user: {user['email']}")
        mongo_client.close()
        
        return {'message': 'Password changed successfully'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")


# Update Profile Picture Endpoint
class ProfilePictureUpdate(BaseModel):
    picture: str  # Base64 encoded image or URL

@auth_router.post('/update-picture')
async def update_profile_picture(picture_data: ProfilePictureUpdate, request: Request):
    """Update user profile picture"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Update picture
        await db.users.update_one(
            {'email': user['email']},
            {'$set': {'picture': picture_data.picture}}
        )
        
        logger.info(f"Profile picture updated for user: {user['email']}")
        mongo_client.close()
        
        return {
            'message': 'Profile picture updated successfully',
            'picture': picture_data.picture
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile picture update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profile picture update failed: {str(e)}")


# Villa Number Update Endpoint (for Google OAuth first-time login)
class VillaNumberUpdate(BaseModel):
    villa_number: str

@auth_router.post('/update-villa-number')
async def update_villa_number(villa_data: VillaNumberUpdate, request: Request):
    """Update villa number for authenticated user"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Validate villa number (must be numeric)
        if not villa_data.villa_number or not villa_data.villa_number.isdigit():
            raise HTTPException(status_code=400, detail="Villa number must be numeric")
        
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Update villa number
        await db.users.update_one(
            {'email': user['email']},
            {'$set': {'villa_number': villa_data.villa_number}}
        )
        
        logger.info(f"Villa number updated for user: {user['email']} to {villa_data.villa_number}")
        mongo_client.close()
        
        return {
            'status': 'success',
            'message': 'Villa number updated successfully',
            'villa_number': villa_data.villa_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Villa number update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Villa number update failed: {str(e)}")


# Email Verification Endpoints
@auth_router.post('/verify-email')
async def verify_email(verify_request: VerifyEmailRequest):
    """Verify email address using the token from verification link"""
    try:
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Find user by verification token
        query = {'verification_token': verify_request.token}
        if verify_request.email:
            query['email'] = verify_request.email
        
        user = await db.users.find_one(query, {'_id': 0})
        
        if not user:
            # Token not found - but if email is provided, check if user is already verified
            # This handles the case where duplicate requests come in (e.g., React StrictMode)
            if verify_request.email:
                existing_user = await db.users.find_one({'email': verify_request.email}, {'_id': 0})
                if existing_user and existing_user.get('email_verified', False):
                    mongo_client.close()
                    return {
                        'status': 'success',
                        'message': 'Email is already verified',
                        'email': existing_user['email']
                    }
            mongo_client.close()
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        # Check if already verified
        if user.get('email_verified', False):
            mongo_client.close()
            return {
                'status': 'success',
                'message': 'Email is already verified',
                'email': user['email']
            }
        
        # Update user as verified
        await db.users.update_one(
            {'email': user['email']},
            {
                '$set': {
                    'email_verified': True,
                    'verification_token': None,  # Clear the token after use
                    'verified_at': datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Email verified for user: {user['email']}")
        mongo_client.close()
        
        return {
            'status': 'success',
            'message': 'Email verified successfully',
            'email': user['email']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email verification failed: {str(e)}")


@auth_router.post('/resend-verification')
async def resend_verification(request: Request):
    """Resend verification email to the logged in user"""
    try:
        # Get current user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Find user in database
        db_user = await db.users.find_one({'email': user['email']}, {'_id': 0})
        if not db_user:
            mongo_client.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if already verified
        if db_user.get('email_verified', False):
            mongo_client.close()
            return {
                'status': 'already_verified',
                'message': 'Your email is already verified'
            }
        
        # Check if user is a Google OAuth user (they don't need verification)
        if db_user.get('provider') == 'google':
            mongo_client.close()
            return {
                'status': 'not_required',
                'message': 'Email verification is not required for Google accounts'
            }
        
        # Generate new verification token
        new_token = secrets.token_urlsafe(32)
        new_expiry = datetime.utcnow() + timedelta(days=VERIFICATION_EXPIRY_DAYS)
        
        # Update user with new token
        await db.users.update_one(
            {'email': user['email']},
            {
                '$set': {
                    'verification_token': new_token,
                    'verification_expires_at': new_expiry
                }
            }
        )
        
        # Determine the frontend URL for the verification link
        origin = None
        referer = request.headers.get('referer')
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                origin = f"{parsed.scheme}://{parsed.netloc}"
        
        if not origin:
            origin = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
        
        verification_link = f"{origin}/verify-email?token={new_token}&email={user['email']}"
        
        # Send verification email
        email_result = await email_service.send_verification_email(
            recipient_email=user['email'],
            verification_link=verification_link,
            user_name=db_user.get('name'),
            expiry_days=VERIFICATION_EXPIRY_DAYS
        )
        
        mongo_client.close()
        
        if email_result.get('status') == 'sent':
            logger.info(f"Verification email resent to: {user['email']}")
            return {
                'status': 'sent',
                'message': 'Verification email sent successfully',
                'email': user['email']
            }
        else:
            return {
                'status': 'error',
                'message': email_result.get('message', 'Failed to send verification email')
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resend verification email: {str(e)}")


@auth_router.post('/resend-verification-by-email')
async def resend_verification_by_email(request: Request, email_data: dict):
    """Resend verification email to a user who cannot login (grace period expired)"""
    try:
        email = email_data.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Get database
        mongo_url = os.environ['MONGO_URL']
        mongo_client = AsyncIOMotorClient(mongo_url)
        db = mongo_client[os.environ['DB_NAME']]
        
        # Find user in database
        db_user = await db.users.find_one({'email': email}, {'_id': 0})
        if not db_user:
            mongo_client.close()
            # Don't reveal if user exists or not for security
            return {
                'status': 'sent',
                'message': 'If an account with this email exists, a verification email will be sent'
            }
        
        # Check if already verified
        if db_user.get('email_verified', False):
            mongo_client.close()
            return {
                'status': 'already_verified',
                'message': 'Your email is already verified. Please try logging in.'
            }
        
        # Check if user is a Google OAuth user
        if db_user.get('provider') == 'google':
            mongo_client.close()
            return {
                'status': 'not_required',
                'message': 'This account uses Google login. Email verification is not required.'
            }
        
        # Generate new verification token
        new_token = secrets.token_urlsafe(32)
        new_expiry = datetime.utcnow() + timedelta(days=VERIFICATION_EXPIRY_DAYS)
        
        # Update user with new token
        await db.users.update_one(
            {'email': email},
            {
                '$set': {
                    'verification_token': new_token,
                    'verification_expires_at': new_expiry
                }
            }
        )
        
        # Determine the frontend URL for the verification link
        origin = None
        referer = request.headers.get('referer')
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                origin = f"{parsed.scheme}://{parsed.netloc}"
        
        if not origin:
            origin = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
        
        verification_link = f"{origin}/verify-email?token={new_token}&email={email}"
        
        # Send verification email
        await email_service.send_verification_email(
            recipient_email=email,
            verification_link=verification_link,
            user_name=db_user.get('name'),
            expiry_days=VERIFICATION_EXPIRY_DAYS
        )
        
        mongo_client.close()
        
        logger.info(f"Verification email resent to: {email}")
        return {
            'status': 'sent',
            'message': 'Verification email sent. Please check your inbox and verify your email to login.'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification by email failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resend verification email: {str(e)}")

