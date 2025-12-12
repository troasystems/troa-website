#!/usr/bin/env python3
"""
Full User Whitelist Feature Testing with Real Session
This test attempts to create a real admin session and test the full functionality
"""

import requests
import json
import os
import base64
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Add backend directory to path
sys.path.append('/app/backend')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troaresidents.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Basic Auth credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

class FullUserWhitelistTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.basic_auth_header = self._create_basic_auth_header()
        self.admin_session_token = None
        self.created_user_ids = []
        
    def _create_basic_auth_header(self) -> str:
        """Create Basic Auth header"""
        credentials = f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    async def create_admin_session_directly(self):
        """Create admin session by directly calling backend functions"""
        try:
            # Import auth functions
            from auth import create_session
            
            # Create admin user data
            admin_user_data = {
                'email': 'troa.systems@gmail.com',
                'name': 'TROA Admin',
                'picture': '',
                'role': 'admin',
                'is_admin': True
            }
            
            # Create session
            session_token = create_session(admin_user_data)
            self.admin_session_token = f"Bearer {session_token}"
            
            print(f"✅ Created admin session token: {session_token[:20]}...")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create admin session: {str(e)}")
            return False
    
    def test_full_user_whitelist_functionality(self):
        """Test the full user whitelist functionality with real session"""
        print("\n🧪 Testing Full User Whitelist Functionality...")
        
        # Test data
        test_users = [
            {
                "email": "test.manager@example.com",
                "name": "Test Manager",
                "role": "manager"
            },
            {
                "email": "test.user@example.com",
                "name": "Test User", 
                "role": "user"
            }
        ]
        
        success_count = 0
        
        # Test 1: Create users
        print("\n📝 Testing user creation...")
        for i, test_user in enumerate(test_users):
            try:
                response = requests.post(
                    f"{self.base_url}/users",
                    json=test_user,
                    headers={
                        'Authorization': self.basic_auth_header,
                        'X-Session-Token': self.admin_session_token,
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if ('id' in data and 
                        data['email'] == test_user['email'] and 
                        data['role'] == test_user['role']):
                        print(f"✅ Created {test_user['role']} user: {test_user['email']}")
                        self.created_user_ids.append(data['id'])
                        success_count += 1
                    else:
                        print(f"❌ Invalid response structure for user {i+1}")
                else:
                    print(f"❌ Failed to create user {i+1}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Exception creating user {i+1}: {str(e)}")
        
        # Test 2: Get all users
        print(f"\n📋 Testing user retrieval...")
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers={
                    'Authorization': self.basic_auth_header,
                    'X-Session-Token': self.admin_session_token
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ Retrieved {len(data)} users from database")
                    
                    # Find our created users
                    created_emails = [user['email'] for user in test_users]
                    found_users = [user for user in data if user.get('email') in created_emails]
                    print(f"✅ Found {len(found_users)} of our created test users")
                    
                    # Validate structure
                    if data:
                        user = data[0]
                        required_fields = ['id', 'email', 'name', 'role', 'created_at']
                        missing_fields = [field for field in required_fields if field not in user]
                        if not missing_fields:
                            print(f"✅ User data structure is correct")
                        else:
                            print(f"❌ Missing fields in user data: {missing_fields}")
                else:
                    print(f"❌ GET /users returned non-list response")
            else:
                print(f"❌ Failed to get users: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception getting users: {str(e)}")
        
        # Test 3: Test duplicate email
        print(f"\n🔄 Testing duplicate email handling...")
        try:
            duplicate_user = {
                "email": "test.manager@example.com",  # Same as first user
                "name": "Duplicate Manager",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.base_url}/users",
                json=duplicate_user,
                headers={
                    'Authorization': self.basic_auth_header,
                    'X-Session-Token': self.admin_session_token,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 400:
                response_data = response.json()
                if 'already exists' in response_data.get('detail', '').lower():
                    print(f"✅ Correctly rejected duplicate email with 400 error")
                else:
                    print(f"❌ Wrong error message for duplicate: {response_data}")
            else:
                print(f"❌ Expected 400 for duplicate email, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception testing duplicate email: {str(e)}")
        
        # Test 4: Test invalid role
        print(f"\n🚫 Testing invalid role handling...")
        try:
            invalid_role_user = {
                "email": "invalid.role@example.com",
                "name": "Invalid Role User",
                "role": "superuser"  # Invalid role
            }
            
            response = requests.post(
                f"{self.base_url}/users",
                json=invalid_role_user,
                headers={
                    'Authorization': self.basic_auth_header,
                    'X-Session-Token': self.admin_session_token,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 400:
                response_data = response.json()
                if 'invalid role' in response_data.get('detail', '').lower():
                    print(f"✅ Correctly rejected invalid role with 400 error")
                else:
                    print(f"❌ Wrong error message for invalid role: {response_data}")
            else:
                print(f"❌ Expected 400 for invalid role, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception testing invalid role: {str(e)}")
        
        return success_count, len(test_users)
    
    async def run_full_test(self):
        """Run the full test suite"""
        print(f"🚀 Starting Full User Whitelist Feature Test")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Create admin session
        if not await self.create_admin_session_directly():
            print("❌ Failed to create admin session. Cannot proceed with full test.")
            return False
        
        # Run full functionality test
        created, total = self.test_full_user_whitelist_functionality()
        
        print(f"\n" + "=" * 70)
        print(f"📊 FULL TEST RESULTS")
        print(f"=" * 70)
        print(f"✅ Created {created}/{total} test users successfully")
        print(f"✅ User Whitelist feature is {'WORKING' if created == total else 'PARTIALLY WORKING'}")
        
        if self.created_user_ids:
            print(f"📝 Created test users with IDs: {', '.join(self.created_user_ids)}")
        
        return created == total

async def main():
    tester = FullUserWhitelistTester()
    success = await tester.run_full_test()
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        exit(1)