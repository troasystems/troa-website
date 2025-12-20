#!/usr/bin/env python3
"""
Image Upload Authentication Test for TROA
Tests the 403 fix by creating test sessions and verifying manager upload permissions.
"""

import requests
import json
import os
import base64
import io
import asyncio
from typing import Dict, Any
from PIL import Image
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import secrets

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://villa-manager-13.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

class ImageUploadAuthTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.test_results = {}
        self.errors = []
        
    async def create_test_session(self, user_email: str, user_role: str) -> str:
        """Create a test session for the given user"""
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.getenv('DB_NAME', 'test_database')
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Get user from database
        user = await db.users.find_one({'email': user_email}, {'_id': 0})
        
        if not user:
            # Create test user
            user = {
                'email': user_email,
                'name': f'Test {user_role.title()}',
                'picture': '',
                'provider': 'test',
                'role': user_role,
                'is_admin': user_role == 'admin',
                'created_at': datetime.utcnow()
            }
            await db.users.insert_one(user)
        
        # Create session
        token = secrets.token_urlsafe(32)
        session_doc = {
            'token': token,
            'user': {
                'email': user['email'],
                'name': user['name'],
                'picture': user.get('picture', ''),
                'role': user['role'],
                'is_admin': user['role'] == 'admin'
            },
            'expires': datetime.utcnow() + timedelta(hours=1),
            'created_at': datetime.utcnow()
        }
        
        await db.sessions.insert_one(session_doc)
        client.close()
        
        return token
    
    def create_test_image(self, format='PNG') -> bytes:
        """Create a test image in memory"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    def log_error(self, test_name: str, error: str):
        """Log errors for detailed reporting"""
        error_msg = f"{test_name}: {error}"
        self.errors.append(error_msg)
        print(f"❌ {error_msg}")
        
    def log_success(self, test_name: str, message: str = ""):
        """Log successful tests"""
        success_msg = f"{test_name}: SUCCESS {message}"
        print(f"✅ {success_msg}")
    
    async def test_admin_upload(self):
        """Test admin image upload"""
        print("\n🧪 Testing Admin Image Upload...")
        
        try:
            # Create admin session
            admin_token = await self.create_test_session('test.admin@troa.com', 'admin')
            
            # Create test image
            image_data = self.create_test_image('PNG')
            
            files = {
                'file': ('test_admin_image.png', image_data, 'image/png')
            }
            
            headers = {
                'Authorization': f'Basic {self.basic_auth}',
                'X-Session-Token': f'Bearer {admin_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'filename' in data and 'url' in data:
                    self.test_results['admin_upload'] = True
                    self.log_success("Admin Upload", f"- Uploaded image: {data['filename']}")
                else:
                    self.test_results['admin_upload'] = False
                    self.log_error("Admin Upload", "Invalid response structure")
            else:
                self.test_results['admin_upload'] = False
                self.log_error("Admin Upload", f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.test_results['admin_upload'] = False
            self.log_error("Admin Upload", f"Exception: {str(e)}")
    
    async def test_manager_upload(self):
        """Test manager image upload - this is the main 403 fix test"""
        print("\n🧪 Testing Manager Image Upload (403 Fix)...")
        
        try:
            # Create manager session
            manager_token = await self.create_test_session('test.manager@troa.com', 'manager')
            
            # Create test image
            image_data = self.create_test_image('JPEG')
            
            files = {
                'file': ('test_manager_image.jpg', image_data, 'image/jpeg')
            }
            
            headers = {
                'Authorization': f'Basic {self.basic_auth}',
                'X-Session-Token': f'Bearer {manager_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'filename' in data and 'url' in data:
                    self.test_results['manager_upload'] = True
                    self.log_success("Manager Upload (403 FIX)", f"- Manager can upload images: {data['filename']}")
                else:
                    self.test_results['manager_upload'] = False
                    self.log_error("Manager Upload", "Invalid response structure")
            elif response.status_code == 403:
                self.test_results['manager_upload'] = False
                self.log_error("Manager Upload", "403 Forbidden - Manager upload still blocked (fix not working)")
            else:
                self.test_results['manager_upload'] = False
                self.log_error("Manager Upload", f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.test_results['manager_upload'] = False
            self.log_error("Manager Upload", f"Exception: {str(e)}")
    
    async def test_user_upload(self):
        """Test regular user image upload - should be blocked"""
        print("\n🧪 Testing Regular User Image Upload...")
        
        try:
            # Create user session
            user_token = await self.create_test_session('test.user@troa.com', 'user')
            
            # Create test image
            image_data = self.create_test_image('PNG')
            
            files = {
                'file': ('test_user_image.png', image_data, 'image/png')
            }
            
            headers = {
                'Authorization': f'Basic {self.basic_auth}',
                'X-Session-Token': f'Bearer {user_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 403:
                self.test_results['user_upload'] = True
                self.log_success("Regular User Upload", "- Correctly blocked with 403 Forbidden")
            else:
                self.test_results['user_upload'] = False
                self.log_error("Regular User Upload", f"Expected 403 but got {response.status_code}")
                
        except Exception as e:
            self.test_results['user_upload'] = False
            self.log_error("Regular User Upload", f"Exception: {str(e)}")
    
    def test_unauthenticated_upload(self):
        """Test unauthenticated image upload"""
        print("\n🧪 Testing Unauthenticated Image Upload...")
        
        try:
            # Create test image
            image_data = self.create_test_image('PNG')
            
            files = {
                'file': ('test_unauth_image.png', image_data, 'image/png')
            }
            
            # No authentication headers
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files,
                timeout=10
            )
            
            if response.status_code == 401:
                self.test_results['unauthenticated_upload'] = True
                self.log_success("Unauthenticated Upload", "- Correctly returns 401 Unauthorized")
            else:
                self.test_results['unauthenticated_upload'] = False
                self.log_error("Unauthenticated Upload", f"Expected 401 but got {response.status_code}")
                
        except Exception as e:
            self.test_results['unauthenticated_upload'] = False
            self.log_error("Unauthenticated Upload", f"Exception: {str(e)}")
    
    async def test_invalid_file_type(self):
        """Test invalid file type upload"""
        print("\n🧪 Testing Invalid File Type Upload...")
        
        try:
            # Create admin session for this test
            admin_token = await self.create_test_session('test.admin2@troa.com', 'admin')
            
            # Create a text file instead of image
            text_data = b"This is not an image file"
            
            files = {
                'file': ('test_file.txt', text_data, 'text/plain')
            }
            
            headers = {
                'Authorization': f'Basic {self.basic_auth}',
                'X-Session-Token': f'Bearer {admin_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 400:
                self.test_results['invalid_file_type'] = True
                self.log_success("Invalid File Type", "- Correctly returns 400 Bad Request")
            else:
                self.test_results['invalid_file_type'] = False
                self.log_error("Invalid File Type", f"Expected 400 but got {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.test_results['invalid_file_type'] = False
            self.log_error("Invalid File Type", f"Exception: {str(e)}")
    
    async def test_existing_manager_upload(self):
        """Test upload with existing manager from database"""
        print("\n🧪 Testing Existing Manager Image Upload...")
        
        try:
            # Use existing manager from database
            manager_token = await self.create_test_session('troa.mgr@gmail.com', 'manager')
            
            # Create test image
            image_data = self.create_test_image('WEBP')
            
            files = {
                'file': ('test_existing_manager.webp', image_data, 'image/webp')
            }
            
            headers = {
                'Authorization': f'Basic {self.basic_auth}',
                'X-Session-Token': f'Bearer {manager_token}'
            }
            
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'filename' in data and 'url' in data:
                    self.test_results['existing_manager_upload'] = True
                    self.log_success("Existing Manager Upload", f"- Existing manager can upload: {data['filename']}")
                else:
                    self.test_results['existing_manager_upload'] = False
                    self.log_error("Existing Manager Upload", "Invalid response structure")
            elif response.status_code == 403:
                self.test_results['existing_manager_upload'] = False
                self.log_error("Existing Manager Upload", "403 Forbidden - Existing manager blocked")
            else:
                self.test_results['existing_manager_upload'] = False
                self.log_error("Existing Manager Upload", f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.test_results['existing_manager_upload'] = False
            self.log_error("Existing Manager Upload", f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all image upload tests"""
        print(f"🚀 Starting Image Upload Authentication Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run all tests
        await self.test_admin_upload()
        await self.test_manager_upload()
        await self.test_existing_manager_upload()
        await self.test_user_upload()
        self.test_unauthenticated_upload()
        await self.test_invalid_file_type()
        
        # Print summary
        self.print_summary()
        
        return all(result for result in self.test_results.values() if result is not None)
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 IMAGE UPLOAD AUTHENTICATION TEST RESULTS")
        print("=" * 60)
        
        test_descriptions = {
            'admin_upload': 'Admin can upload images',
            'manager_upload': 'Manager can upload images (403 FIX)',
            'existing_manager_upload': 'Existing manager can upload images',
            'user_upload': 'Regular users blocked (403)',
            'unauthenticated_upload': 'Unauthenticated users blocked (401)',
            'invalid_file_type': 'Invalid file types blocked (400)'
        }
        
        passed_tests = 0
        total_tests = 0
        
        for test_name, result in self.test_results.items():
            if result is not None:
                total_tests += 1
                if result:
                    passed_tests += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                description = test_descriptions.get(test_name, test_name)
                print(f"  {status} - {description}")
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        # Special focus on the 403 fix
        manager_tests = ['manager_upload', 'existing_manager_upload']
        manager_results = [self.test_results.get(test) for test in manager_tests]
        
        if any(manager_results):
            print(f"\n🎉 403 FIX VERIFIED: Managers can now upload images!")
        elif any(result is False for result in manager_results):
            print(f"\n⚠️  403 FIX ISSUE: Managers still cannot upload images")
        else:
            print(f"\n❓ 403 FIX STATUS: Manager upload tests were skipped")
        
        return passed_tests == total_tests

async def main():
    tester = ImageUploadAuthTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All image upload tests passed!")
    else:
        print("\n⚠️  Some image upload tests failed - check the details above")

if __name__ == "__main__":
    asyncio.run(main())