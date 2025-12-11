#!/usr/bin/env python3
"""
User Whitelist Feature Testing for TROA Website
Tests the newly implemented User Whitelist functionality including:
- POST /api/users (Add user to whitelist)
- GET /api/users (List all users)
- Authentication requirements (Basic Auth + Session Token)
- Error handling for invalid data, duplicate emails, invalid roles
"""

import requests
import json
import os
import base64
import sys
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tenant-assist-6.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Basic Auth credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

class UserWhitelistTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.basic_auth_header = self._create_basic_auth_header()
        self.admin_session_token = None
        self.test_results = {
            'auth_setup': None,
            'post_users_auth': None,
            'post_users_valid': None,
            'post_users_duplicate': None,
            'post_users_invalid_role': None,
            'post_users_invalid_email': None,
            'get_users_auth': None,
            'get_users_valid': None
        }
        self.errors = []
        self.created_user_ids = []  # Track created users for cleanup
        
    def _create_basic_auth_header(self) -> str:
        """Create Basic Auth header"""
        credentials = f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
        
    def log_error(self, test_name: str, error: str):
        """Log errors for detailed reporting"""
        error_msg = f"{test_name}: {error}"
        self.errors.append(error_msg)
        print(f"❌ {error_msg}")
        
    def log_success(self, test_name: str, message: str = ""):
        """Log successful tests"""
        success_msg = f"{test_name}: SUCCESS {message}"
        print(f"✅ {success_msg}")
        
    def setup_admin_session(self):
        """Setup admin session token for testing"""
        print("\n🔐 Setting up admin authentication...")
        
        try:
            # First, try to get Google OAuth login URL to verify OAuth is working
            response = requests.get(
                f"{self.base_url}/auth/google/login",
                headers={'Authorization': self.basic_auth_header},
                allow_redirects=False,
                timeout=10
            )
            
            if response.status_code in [302, 307]:
                self.log_success("OAuth Setup", "- Google OAuth redirect working")
                
                # Create a real admin session for testing
                admin_user_data = {
                    'email': 'troa.systems@gmail.com',
                    'name': 'TROA Admin',
                    'picture': '',
                    'role': 'admin',
                    'is_admin': True
                }
                
                # Create session using the auth module
                session_token = create_session(admin_user_data)
                self.admin_session_token = f"Bearer {session_token}"
                
                self.log_success("Admin Session", f"- Created real admin session token")
                self.test_results['auth_setup'] = True
                return True
            else:
                self.log_error("OAuth Setup", f"OAuth redirect failed: {response.status_code}")
                self.test_results['auth_setup'] = False
                return False
                
        except Exception as e:
            self.log_error("OAuth Setup", f"Exception: {str(e)}")
            self.test_results['auth_setup'] = False
            return False
    
    def test_post_users_authentication(self):
        """Test POST /api/users authentication requirements"""
        print("\n🧪 Testing POST /api/users authentication...")
        
        test_user = {
            "email": "test.auth@example.com",
            "name": "Test Auth User",
            "role": "user"
        }
        
        # Test 1: No Basic Auth
        try:
            response = requests.post(
                f"{self.base_url}/users",
                json=test_user,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_success("POST /users No Basic Auth", "- Correctly returns 401 without Basic Auth")
            else:
                self.log_error("POST /users No Basic Auth", f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_error("POST /users No Basic Auth", f"Exception: {str(e)}")
        
        # Test 2: Basic Auth only (no session token)
        try:
            response = requests.post(
                f"{self.base_url}/users",
                json=test_user,
                headers={
                    'Authorization': self.basic_auth_header,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_success("POST /users Basic Auth Only", f"- Correctly returns {response.status_code} without session token")
                self.test_results['post_users_auth'] = True
            else:
                self.log_error("POST /users Basic Auth Only", f"Expected 401/403, got {response.status_code}")
                self.test_results['post_users_auth'] = False
                
        except Exception as e:
            self.log_error("POST /users Basic Auth Only", f"Exception: {str(e)}")
            self.test_results['post_users_auth'] = False
    
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
                        self.log_success(f"POST /users Valid Data {i+1}", f"- Created {test_user['role']} user: {test_user['email']}")
                        self.created_user_ids.append(data['id'])
                        success_count += 1
                    else:
                        self.log_error(f"POST /users Valid Data {i+1}", "Invalid response structure")
                else:
                    self.log_error(f"POST /users Valid Data {i+1}", f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_error(f"POST /users Valid Data {i+1}", f"Exception: {str(e)}")
        
        self.test_results['post_users_valid'] = success_count == len(test_users)
    
    def test_post_users_duplicate_email(self):
        """Test POST /api/users with duplicate email"""
        print("\n🧪 Testing POST /api/users duplicate email handling...")
        
        duplicate_user = {
            "email": "alice.manager@example.com",  # Same as created above
            "name": "Alice Duplicate",
            "role": "user"
        }
        
        try:
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
                    self.log_success("POST /users Duplicate Email", "- Correctly returns 400 for duplicate email")
                    self.test_results['post_users_duplicate'] = True
                else:
                    self.log_error("POST /users Duplicate Email", f"Wrong error message: {response_data}")
                    self.test_results['post_users_duplicate'] = False
            else:
                self.log_error("POST /users Duplicate Email", f"Expected 400, got {response.status_code}")
                self.test_results['post_users_duplicate'] = False
                
        except Exception as e:
            self.log_error("POST /users Duplicate Email", f"Exception: {str(e)}")
            self.test_results['post_users_duplicate'] = False
    
    def test_post_users_invalid_role(self):
        """Test POST /api/users with invalid role"""
        print("\n🧪 Testing POST /api/users invalid role handling...")
        
        invalid_role_user = {
            "email": "invalid.role@example.com",
            "name": "Invalid Role User",
            "role": "superuser"  # Invalid role
        }
        
        try:
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
                    self.log_success("POST /users Invalid Role", "- Correctly returns 400 for invalid role")
                    self.test_results['post_users_invalid_role'] = True
                else:
                    self.log_error("POST /users Invalid Role", f"Wrong error message: {response_data}")
                    self.test_results['post_users_invalid_role'] = False
            else:
                self.log_error("POST /users Invalid Role", f"Expected 400, got {response.status_code}")
                self.test_results['post_users_invalid_role'] = False
                
        except Exception as e:
            self.log_error("POST /users Invalid Role", f"Exception: {str(e)}")
            self.test_results['post_users_invalid_role'] = False
    
    def test_post_users_invalid_email(self):
        """Test POST /api/users with invalid email format"""
        print("\n🧪 Testing POST /api/users invalid email handling...")
        
        invalid_email_user = {
            "email": "not-an-email",  # Invalid email format
            "name": "Invalid Email User",
            "role": "user"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/users",
                json=invalid_email_user,
                headers={
                    'Authorization': self.basic_auth_header,
                    'X-Session-Token': self.admin_session_token,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            
            if response.status_code == 422:
                self.log_success("POST /users Invalid Email", "- Correctly returns 422 for invalid email format")
                self.test_results['post_users_invalid_email'] = True
            else:
                self.log_error("POST /users Invalid Email", f"Expected 422, got {response.status_code}")
                self.test_results['post_users_invalid_email'] = False
                
        except Exception as e:
            self.log_error("POST /users Invalid Email", f"Exception: {str(e)}")
            self.test_results['post_users_invalid_email'] = False
    
    def test_get_users_authentication(self):
        """Test GET /api/users authentication requirements"""
        print("\n🧪 Testing GET /api/users authentication...")
        
        # Test 1: No Basic Auth
        try:
            response = requests.get(
                f"{self.base_url}/users",
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_success("GET /users No Basic Auth", "- Correctly returns 401 without Basic Auth")
            else:
                self.log_error("GET /users No Basic Auth", f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_error("GET /users No Basic Auth", f"Exception: {str(e)}")
        
        # Test 2: Basic Auth only (no session token)
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers={'Authorization': self.basic_auth_header},
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_success("GET /users Basic Auth Only", f"- Correctly returns {response.status_code} without session token")
                self.test_results['get_users_auth'] = True
            else:
                self.log_error("GET /users Basic Auth Only", f"Expected 401/403, got {response.status_code}")
                self.test_results['get_users_auth'] = False
                
        except Exception as e:
            self.log_error("GET /users Basic Auth Only", f"Exception: {str(e)}")
            self.test_results['get_users_auth'] = False
    
    def test_get_users_valid(self):
        """Test GET /api/users with valid authentication"""
        print("\n🧪 Testing GET /api/users with valid authentication...")
        
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
                    # Check if our created users are in the list
                    created_emails = ["alice.manager@example.com", "bob.user@example.com", "charlie.admin@example.com"]
                    found_users = [user for user in data if user.get('email') in created_emails]
                    
                    if len(found_users) >= 3:  # Should find at least our 3 created users
                        self.log_success("GET /users Valid", f"- Retrieved {len(data)} users, including {len(found_users)} created test users")
                        self.test_results['get_users_valid'] = True
                        
                        # Validate user structure
                        for user in found_users[:1]:  # Check first user structure
                            required_fields = ['id', 'email', 'name', 'role', 'created_at']
                            missing_fields = [field for field in required_fields if field not in user]
                            if missing_fields:
                                self.log_error("GET /users Valid", f"Missing required fields: {missing_fields}")
                                self.test_results['get_users_valid'] = False
                                break
                    else:
                        self.log_error("GET /users Valid", f"Expected to find created users, found {len(found_users)}")
                        self.test_results['get_users_valid'] = False
                else:
                    self.log_error("GET /users Valid", "Response is not a list")
                    self.test_results['get_users_valid'] = False
            else:
                self.log_error("GET /users Valid", f"Status: {response.status_code}, Response: {response.text}")
                self.test_results['get_users_valid'] = False
                
        except Exception as e:
            self.log_error("GET /users Valid", f"Exception: {str(e)}")
            self.test_results['get_users_valid'] = False
    
    def run_all_tests(self):
        """Run all User Whitelist tests"""
        print(f"🚀 Starting TROA User Whitelist Feature Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Setup authentication
        if not self.setup_admin_session():
            print("❌ Failed to setup admin authentication. Skipping remaining tests.")
            return False
        
        # Run all tests
        self.test_post_users_authentication()
        self.test_post_users_valid_data()
        self.test_post_users_duplicate_email()
        self.test_post_users_invalid_role()
        self.test_post_users_invalid_email()
        self.test_get_users_authentication()
        self.test_get_users_valid()
        
        # Print summary
        return self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 70)
        print("📊 USER WHITELIST FEATURE TEST RESULTS")
        print("=" * 70)
        
        test_descriptions = {
            'auth_setup': 'Authentication Setup',
            'post_users_auth': 'POST /users Authentication Required',
            'post_users_valid': 'POST /users Valid Data Creation',
            'post_users_duplicate': 'POST /users Duplicate Email Handling',
            'post_users_invalid_role': 'POST /users Invalid Role Handling',
            'post_users_invalid_email': 'POST /users Invalid Email Handling',
            'get_users_auth': 'GET /users Authentication Required',
            'get_users_valid': 'GET /users Valid Data Retrieval'
        }
        
        total_tests = 0
        passed_tests = 0
        
        for test_key, result in self.test_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
                status = "✅ PASS"
            elif result is False:
                status = "❌ FAIL"
            else:
                status = "⚠️  SKIP"
            
            description = test_descriptions.get(test_key, test_key)
            print(f"{status} - {description}")
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n🎉 All tests passed successfully!")
        
        # Print created users for reference
        if self.created_user_ids:
            print(f"\n📝 Created {len(self.created_user_ids)} test users (IDs: {', '.join(self.created_user_ids[:3])}...)")
            
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = UserWhitelistTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)