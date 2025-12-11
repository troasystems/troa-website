#!/usr/bin/env python3
"""
User Whitelist Feature Testing using FastAPI TestClient
This test uses FastAPI's TestClient to properly test the User Whitelist functionality
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.append('/app/backend')

from fastapi.testclient import TestClient
from server import app
from auth import create_session
import json

class UserWhitelistTestClient:
    def __init__(self):
        self.client = TestClient(app)
        self.admin_session_token = None
        self.created_user_ids = []
        
    def setup_admin_session(self):
        """Create admin session for testing"""
        try:
            # Create admin user data
            admin_user_data = {
                'email': 'troa.systems@gmail.com',
                'name': 'TROA Admin',
                'picture': '',
                'role': 'admin',
                'is_admin': True
            }
            
            # Create session using the auth module
            session_token = create_session(admin_user_data)
            self.admin_session_token = session_token
            
            print(f"✅ Created admin session token for testing")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create admin session: {str(e)}")
            return False
    
    def test_post_users_authentication(self):
        """Test POST /api/users authentication requirements"""
        print("\n🧪 Testing POST /api/users authentication...")
        
        test_user = {
            "email": "test.auth@example.com",
            "name": "Test Auth User",
            "role": "user"
        }
        
        # Test 1: No authentication
        response = self.client.post("/api/users", json=test_user)
        if response.status_code == 401:
            print("✅ Correctly returns 401 without authentication")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            
        # Test 2: With admin session token
        response = self.client.post(
            "/api/users", 
            json=test_user,
            headers={"X-Session-Token": f"Bearer {self.admin_session_token}"}
        )
        
        if response.status_code in [200, 201]:
            print("✅ Admin can create users with valid session")
            data = response.json()
            if data.get('email') == test_user['email']:
                self.created_user_ids.append(data.get('id'))
                return True
        else:
            print(f"❌ Failed to create user with admin session: {response.status_code} - {response.text}")
            
        return False
    
    def test_post_users_valid_data(self):
        """Test POST /api/users with valid data"""
        print("\n🧪 Testing POST /api/users with valid data...")
        
        test_users = [
            {
                "email": "alice.manager@example.com",
                "name": "Alice Manager",
                "role": "manager"
            },
            {
                "email": "bob.user@example.com",
                "name": "Bob User", 
                "role": "user"
            },
            {
                "email": "charlie.admin@example.com",
                "name": "Charlie Admin",
                "role": "admin"
            }
        ]
        
        success_count = 0
        
        for i, test_user in enumerate(test_users):
            response = self.client.post(
                "/api/users",
                json=test_user,
                headers={"X-Session-Token": f"Bearer {self.admin_session_token}"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                if (data.get('email') == test_user['email'] and 
                    data.get('role') == test_user['role']):
                    print(f"✅ Created {test_user['role']} user: {test_user['email']}")
                    self.created_user_ids.append(data.get('id'))
                    success_count += 1
                else:
                    print(f"❌ Invalid response structure for user {i+1}")
            else:
                print(f"❌ Failed to create user {i+1}: {response.status_code} - {response.text}")
        
        return success_count == len(test_users)
    
    def test_post_users_duplicate_email(self):
        """Test POST /api/users with duplicate email"""
        print("\n🧪 Testing POST /api/users duplicate email handling...")
        
        # Use existing admin email
        duplicate_user = {
            "email": "troa.systems@gmail.com",
            "name": "Duplicate Admin",
            "role": "user"
        }
        
        response = self.client.post(
            "/api/users",
            json=duplicate_user,
            headers={"X-Session-Token": f"Bearer {self.admin_session_token}"}
        )
        
        if response.status_code == 400:
            response_data = response.json()
            if 'already exists' in response_data.get('detail', '').lower():
                print("✅ Correctly returns 400 for duplicate email")
                return True
            else:
                print(f"❌ Wrong error message: {response_data}")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
            
        return False
    
    def test_post_users_invalid_role(self):
        """Test POST /api/users with invalid role"""
        print("\n🧪 Testing POST /api/users invalid role handling...")
        
        invalid_role_user = {
            "email": "invalid.role@example.com",
            "name": "Invalid Role User",
            "role": "superuser"  # Invalid role
        }
        
        response = self.client.post(
            "/api/users",
            json=invalid_role_user,
            headers={"X-Session-Token": f"Bearer {self.admin_session_token}"}
        )
        
        if response.status_code == 400:
            response_data = response.json()
            if 'invalid role' in response_data.get('detail', '').lower():
                print("✅ Correctly returns 400 for invalid role")
                return True
            else:
                print(f"❌ Wrong error message: {response_data}")
        else:
            print(f"❌ Expected 400, got {response.status_code}")
            
        return False
    
    def test_post_users_invalid_email(self):
        """Test POST /api/users with invalid email format"""
        print("\n🧪 Testing POST /api/users invalid email handling...")
        
        invalid_email_user = {
            "email": "not-an-email",  # Invalid email format
            "name": "Invalid Email User",
            "role": "user"
        }
        
        response = self.client.post(
            "/api/users",
            json=invalid_email_user,
            headers={"X-Session-Token": f"Bearer {self.admin_session_token}"}
        )
        
        if response.status_code == 422:
            print("✅ Correctly returns 422 for invalid email format")
            return True
        else:
            print(f"❌ Expected 422, got {response.status_code}")
            
        return False
    
    def test_get_users(self):
        """Test GET /api/users"""
        print("\n🧪 Testing GET /api/users...")
        
        # Test without authentication
        response = self.client.get("/api/users")
        if response.status_code == 401:
            print("✅ Correctly returns 401 without authentication")
        else:
            print(f"❌ Expected 401 without auth, got {response.status_code}")
        
        # Test with admin authentication
        response = self.client.get(
            "/api/users",
            headers={"X-Session-Token": f"Bearer {self.admin_session_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✅ Retrieved {len(data)} users from database")
                
                # Check if our created users are in the list
                created_emails = ["alice.manager@example.com", "bob.user@example.com", "charlie.admin@example.com"]
                found_users = [user for user in data if user.get('email') in created_emails]
                print(f"✅ Found {len(found_users)} of our created test users")
                
                # Validate structure
                if data:
                    user = data[0]
                    required_fields = ['id', 'email', 'name', 'role', 'created_at']
                    missing_fields = [field for field in required_fields if field not in user]
                    if not missing_fields:
                        print("✅ User data structure is correct")
                        return True
                    else:
                        print(f"❌ Missing fields in user data: {missing_fields}")
            else:
                print("❌ Response is not a list")
        else:
            print(f"❌ Failed to get users: {response.status_code} - {response.text}")
            
        return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting User Whitelist Feature Tests with TestClient")
        print("=" * 70)
        
        # Setup admin session
        if not self.setup_admin_session():
            print("❌ Failed to setup admin session. Cannot proceed.")
            return False
        
        # Run all tests
        results = []
        results.append(("Authentication", self.test_post_users_authentication()))
        results.append(("Valid Data Creation", self.test_post_users_valid_data()))
        results.append(("Duplicate Email Handling", self.test_post_users_duplicate_email()))
        results.append(("Invalid Role Handling", self.test_post_users_invalid_role()))
        results.append(("Invalid Email Handling", self.test_post_users_invalid_email()))
        results.append(("Get Users", self.test_get_users()))
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        print(f"\n📈 Overall: {passed}/{total} tests passed")
        
        if self.created_user_ids:
            print(f"📝 Created {len(self.created_user_ids)} test users")
        
        success = passed == total
        print(f"\n🎉 User Whitelist feature is {'WORKING CORRECTLY' if success else 'PARTIALLY WORKING'}")
        
        return success

if __name__ == "__main__":
    tester = UserWhitelistTestClient()
    success = tester.run_all_tests()
    exit(0 if success else 1)