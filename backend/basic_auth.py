from fastapi import Request, HTTPException, status
from fastapi.responses import Response
import base64
import secrets
import os

# Basic auth credentials from environment variables
BASIC_AUTH_USERNAME = os.getenv('BASIC_AUTH_USERNAME', 'dogfooding')
BASIC_AUTH_PASSWORD = os.getenv('BASIC_AUTH_PASSWORD', 'skywalker')

def verify_basic_auth(auth_header: str) -> bool:
    """Verify basic authentication credentials"""
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    
    try:
        # Decode the base64 encoded credentials
        encoded_credentials = auth_header.replace('Basic ', '')
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
        
        # Use secrets.compare_digest to prevent timing attacks
        username_match = secrets.compare_digest(username, BASIC_AUTH_USERNAME)
        password_match = secrets.compare_digest(password, BASIC_AUTH_PASSWORD)
        
        return username_match and password_match
    except Exception:
        return False

async def basic_auth_middleware(request: Request, call_next):
    """Middleware to enforce basic authentication on all routes"""
    # Skip auth check for health check endpoints if any
    if request.url.path == "/health":
        return await call_next(request)
    
    # Skip auth check for image GET requests (allow public image viewing)
    if request.url.path.startswith("/api/upload/image/") and request.method == "GET":
        return await call_next(request)
    
    # Skip auth check for Google OAuth endpoints (login and callback)
    if request.url.path in ["/api/auth/google/login", "/api/auth/google/callback"]:
        return await call_next(request)
    
    # Get authorization header
    auth_header = request.headers.get('Authorization')
    
    # Verify credentials
    if not verify_basic_auth(auth_header):
        return Response(
            content="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={
                'WWW-Authenticate': 'Basic realm="TROA Portal"'
            }
        )
    
    # If authenticated, proceed with request
    response = await call_next(request)
    return response
