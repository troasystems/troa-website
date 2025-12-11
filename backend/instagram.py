from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

instagram_router = APIRouter(prefix="/instagram")

# Instagram credentials from environment variables
INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID')
INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET')
INSTAGRAM_REDIRECT_URI = os.getenv('INSTAGRAM_REDIRECT_URI', '')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@instagram_router.get('/auth')
async def instagram_auth(request: Request):
    """Initiate Instagram OAuth"""
    backend_url = os.getenv('REACT_APP_BACKEND_URL', str(request.base_url).rstrip('/'))
    redirect_uri = f"{backend_url}/api/instagram/callback"
    
    auth_url = (
        f"https://api.instagram.com/oauth/authorize"
        f"?client_id={INSTAGRAM_APP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=user_profile,user_media"
        f"&response_type=code"
    )
    
    return RedirectResponse(url=auth_url)

@instagram_router.get('/callback')
async def instagram_callback(code: str, request: Request):
    """Handle Instagram OAuth callback"""
    try:
        backend_url = os.getenv('REACT_APP_BACKEND_URL', str(request.base_url).rstrip('/'))
        redirect_uri = f"{backend_url}/api/instagram/callback"
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.instagram.com/oauth/access_token',
                data={
                    'client_id': INSTAGRAM_APP_ID,
                    'client_secret': INSTAGRAM_APP_SECRET,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri,
                    'code': code
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Instagram auth error: {response.text}")
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            data = response.json()
            access_token = data.get('access_token')
            user_id = data.get('user_id')
            
            # Store token in database
            await db.instagram_tokens.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'access_token': access_token,
                        'user_id': user_id,
                        'created_at': datetime.utcnow(),
                        'expires_at': datetime.utcnow() + timedelta(days=60)
                    }
                },
                upsert=True
            )
            
            # Redirect to admin or success page
            frontend_url = os.getenv('REACT_APP_BACKEND_URL', '').replace('/api', '')
            return RedirectResponse(url=f'{frontend_url}/admin?instagram_auth=success')
            
    except Exception as e:
        logger.error(f"Instagram callback error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@instagram_router.get('/posts')
async def get_instagram_posts():
    """Get Instagram posts from stored token"""
    try:
        # Get token from database
        token_doc = await db.instagram_tokens.find_one()
        
        if not token_doc:
            return {"posts": [], "authenticated": False}
        
        access_token = token_doc.get('access_token')
        
        # Fetch user's media
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://graph.instagram.com/me/media',
                params={
                    'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp',
                    'access_token': access_token,
                    'limit': 12
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Instagram API error: {response.text}")
                return {"posts": [], "authenticated": False, "error": response.text}
            
            data = response.json()
            posts = data.get('data', [])
            
            return {"posts": posts, "authenticated": True}
            
    except Exception as e:
        logger.error(f"Error fetching Instagram posts: {str(e)}")
        return {"posts": [], "authenticated": False, "error": str(e)}

@instagram_router.get('/status')
async def instagram_status():
    """Check Instagram authentication status"""
    token_doc = await db.instagram_tokens.find_one()
    
    if not token_doc:
        return {"authenticated": False}
    
    expires_at = token_doc.get('expires_at')
    is_expired = expires_at < datetime.utcnow() if expires_at else True
    
    return {
        "authenticated": not is_expired,
        "expires_at": expires_at.isoformat() if expires_at else None
    }
