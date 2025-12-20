#!/usr/bin/env python3
"""
Create a test session token for the admin user for API testing
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets

load_dotenv('/app/backend/.env')

async def create_test_session():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Get admin user
    admin_user = await db.users.find_one({'email': 'troa.systems@gmail.com'}, {'_id': 0})
    
    if not admin_user:
        print("Admin user not found!")
        return None
    
    # Create session token
    token = secrets.token_urlsafe(32)
    
    session_doc = {
        'token': token,
        'user': {
            'email': admin_user['email'],
            'name': admin_user['name'],
            'picture': admin_user['picture'],
            'role': admin_user['role'],
            'is_admin': admin_user['is_admin']
        },
        'expires': datetime.utcnow() + timedelta(days=1),
        'created_at': datetime.utcnow()
    }
    
    await db.sessions.insert_one(session_doc)
    client.close()
    
    print(f"Session token created: {token}")
    return token

if __name__ == "__main__":
    token = asyncio.run(create_test_session())