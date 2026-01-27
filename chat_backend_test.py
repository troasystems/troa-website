#!/usr/bin/env python3
"""
Chat Backend API Testing for TROA
Tests chat functionality including file upload, member management, and user search
"""

import requests
import json
import os
import base64
import io
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

class ChatAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'get_groups': None,
            'create_group': None,
            'join_group': None,
            'leave_group': None,
            'get_messages': None,
            'send_message': None,
            'file_upload': None,
            'add_member': None,
            'remove_member': None,
            'user_search': None,
            'get_attachment': None,
            'group_with_initial_members': None
        }
        self.errors = []
        self.created_group_id = None
        self.created_message_id = None
        self.created_attachment_id = None
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.session_token = "xBPTLcvN2wsTsXtfGxu1MJ4W7VmNi8oO5fUrLqqVT44"  # Valid admin session token
        self.auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.session_token}'
        }
        
    def log_error(self, endpoint: str, method: str, error: str):
        """Log errors for detailed reporting"""
        error_msg = f"{method.upper()} {endpoint}: {error}"
        self.errors.append(error_msg)
        print(f"❌ {error_msg}")
        
    def log_success(self, endpoint: str, method: str, message: str = ""):
        """Log successful tests"""
        success_msg = f"{method.upper()} {endpoint}: SUCCESS {message}"
        print(f"✅ {success_msg}")

    def test_get_groups(self):
        """Test GET /api/chat/groups"""
        print("\n🧪 Testing Get Chat Groups...")
        try:
            response = requests.get(f"{self.base_url}/chat/groups", 
                                  headers=self.auth_headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['get_groups'] = True
                    self.log_success("/chat/groups", "GET", f"- Found {len(data)} groups")
                else:
                    self.test_results['get_groups'] = False
                    self.log_error("/chat/groups", "GET", "Response is not a list")
            else:
                self.test_results['get_groups'] = False
                self.log_error("/chat/groups", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['get_groups'] = False
            self.log_error("/chat/groups", "GET", f"Exception: {str(e)}")

    def test_create_group(self):
        """Test POST /api/chat/groups"""
        print("\n🧪 Testing Create Chat Group...")
        try:
            group_data = {
                "name": "Test Group",
                "description": "A test group for API testing",
                "is_mc_only": False,
                "initial_members": []
            }
            
            response = requests.post(f"{self.base_url}/chat/groups", 
                                   json=group_data,
                                   headers={**self.auth_headers, 'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data['name'] == group_data['name']:
                    self.test_results['create_group'] = True
                    self.created_group_id = data['id']
                    self.log_success("/chat/groups", "POST", f"- Created group with ID: {data['id']}")
                else:
                    self.test_results['create_group'] = False
                    self.log_error("/chat/groups", "POST", "Invalid response structure")
            else:
                self.test_results['create_group'] = False
                self.log_error("/chat/groups", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['create_group'] = False
            self.log_error("/chat/groups", "POST", f"Exception: {str(e)}")

    def test_create_group_with_initial_members(self):
        """Test POST /api/chat/groups with initial_members"""
        print("\n🧪 Testing Create Group with Initial Members...")
        try:
            group_data = {
                "name": "Test Group with Members",
                "description": "A test group with initial members",
                "is_mc_only": False,
                "initial_members": ["troa.systems@gmail.com"]  # Admin email
            }
            
            response = requests.post(f"{self.base_url}/chat/groups", 
                                   json=group_data,
                                   headers={**self.auth_headers, 'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    data['name'] == group_data['name'] and
                    'members' in data and
                    len(data['members']) >= 1):
                    self.test_results['group_with_initial_members'] = True
                    self.log_success("/chat/groups (with initial members)", "POST", f"- Created group with {len(data['members'])} members")
                else:
                    self.test_results['group_with_initial_members'] = False
                    self.log_error("/chat/groups (with initial members)", "POST", "Invalid response structure or missing members")
            else:
                self.test_results['group_with_initial_members'] = False
                self.log_error("/chat/groups (with initial members)", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_with_initial_members'] = False
            self.log_error("/chat/groups (with initial members)", "POST", f"Exception: {str(e)}")

    def test_send_message(self):
        """Test POST /api/chat/groups/{id}/messages"""
        if not self.created_group_id:
            self.log_error("Send Message", "SETUP", "No group created for testing")
            return
            
        print("\n🧪 Testing Send Message...")
        try:
            message_data = {
                "content": "Hello, this is a test message!",
                "group_id": self.created_group_id
            }
            
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/messages", 
                                   json=message_data,
                                   headers={**self.auth_headers, 'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    data['content'] == message_data['content'] and
                    data['group_id'] == self.created_group_id):
                    self.test_results['send_message'] = True
                    self.created_message_id = data['id']
                    self.log_success(f"/chat/groups/{self.created_group_id}/messages", "POST", f"- Sent message with ID: {data['id']}")
                else:
                    self.test_results['send_message'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", "Invalid response structure")
            else:
                self.test_results['send_message'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['send_message'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", f"Exception: {str(e)}")

    def test_get_messages(self):
        """Test GET /api/chat/groups/{id}/messages"""
        if not self.created_group_id:
            self.log_error("Get Messages", "SETUP", "No group created for testing")
            return
            
        print("\n🧪 Testing Get Messages...")
        try:
            response = requests.get(f"{self.base_url}/chat/groups/{self.created_group_id}/messages", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['get_messages'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/messages", "GET", f"- Found {len(data)} messages")
                else:
                    self.test_results['get_messages'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/messages", "GET", "Response is not a list")
            else:
                self.test_results['get_messages'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/messages", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['get_messages'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/messages", "GET", f"Exception: {str(e)}")

    def test_file_upload(self):
        """Test POST /api/chat/groups/{id}/messages/upload"""
        if not self.created_group_id:
            self.log_error("File Upload", "SETUP", "No group created for testing")
            return
            
        print("\n🧪 Testing File Upload...")
        try:
            # Create a test image file
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            
            # Prepare multipart form data
            files = {
                'files': ('test_image.png', io.BytesIO(test_image_data), 'image/png')
            }
            data = {
                'content': 'Test message with file attachment'
            }
            
            # Remove Content-Type header to let requests set it for multipart
            headers = {k: v for k, v in self.auth_headers.items() if k != 'Content-Type'}
            
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/messages/upload", 
                                   files=files,
                                   data=data,
                                   headers=headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    'attachments' in data and
                    len(data['attachments']) > 0):
                    self.test_results['file_upload'] = True
                    self.created_attachment_id = data['attachments'][0]['id']
                    self.log_success(f"/chat/groups/{self.created_group_id}/messages/upload", "POST", f"- Uploaded file with attachment ID: {self.created_attachment_id}")
                else:
                    self.test_results['file_upload'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/messages/upload", "POST", "Invalid response structure or no attachments")
            else:
                self.test_results['file_upload'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/messages/upload", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['file_upload'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/messages/upload", "POST", f"Exception: {str(e)}")

    def test_get_attachment(self):
        """Test GET /api/chat/attachments/{id}"""
        if not self.created_attachment_id:
            self.log_error("Get Attachment", "SETUP", "No attachment created for testing")
            return
            
        print("\n🧪 Testing Get Attachment...")
        try:
            response = requests.get(f"{self.base_url}/chat/attachments/{self.created_attachment_id}", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    'filename' in data and
                    'data' in data):
                    self.test_results['get_attachment'] = True
                    self.log_success(f"/chat/attachments/{self.created_attachment_id}", "GET", f"- Retrieved attachment: {data['filename']}")
                else:
                    self.test_results['get_attachment'] = False
                    self.log_error(f"/chat/attachments/{self.created_attachment_id}", "GET", "Invalid response structure")
            else:
                self.test_results['get_attachment'] = False
                self.log_error(f"/chat/attachments/{self.created_attachment_id}", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['get_attachment'] = False
            self.log_error(f"/chat/attachments/{self.created_attachment_id}", "GET", f"Exception: {str(e)}")

    def test_user_search(self):
        """Test GET /api/chat/users/search"""
        print("\n🧪 Testing User Search...")
        try:
            response = requests.get(f"{self.base_url}/chat/users/search?q=troa", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['user_search'] = True
                    self.log_success("/chat/users/search", "GET", f"- Found {len(data)} users matching 'troa'")
                else:
                    self.test_results['user_search'] = False
                    self.log_error("/chat/users/search", "GET", "Response is not a list")
            else:
                self.test_results['user_search'] = False
                self.log_error("/chat/users/search", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['user_search'] = False
            self.log_error("/chat/users/search", "GET", f"Exception: {str(e)}")

    def test_add_member(self):
        """Test POST /api/chat/groups/{id}/add-member"""
        if not self.created_group_id:
            self.log_error("Add Member", "SETUP", "No group created for testing")
            return
            
        print("\n🧪 Testing Add Member...")
        try:
            member_data = {
                "email": "troa.systems@gmail.com"  # Admin email
            }
            
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/add-member", 
                                   json=member_data,
                                   headers={**self.auth_headers, 'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data:
                    self.test_results['add_member'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/add-member", "POST", f"- Added member: {member_data['email']}")
                else:
                    self.test_results['add_member'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/add-member", "POST", "Invalid response structure")
            else:
                self.test_results['add_member'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/add-member", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['add_member'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/add-member", "POST", f"Exception: {str(e)}")

    def test_remove_member(self):
        """Test POST /api/chat/groups/{id}/remove-member"""
        if not self.created_group_id:
            self.log_error("Remove Member", "SETUP", "No group created for testing")
            return
            
        print("\n🧪 Testing Remove Member...")
        try:
            member_data = {
                "email": "troa.systems@gmail.com"  # Admin email
            }
            
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/remove-member", 
                                   json=member_data,
                                   headers={**self.auth_headers, 'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data:
                    self.test_results['remove_member'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/remove-member", "POST", f"- Removed member: {member_data['email']}")
                else:
                    self.test_results['remove_member'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/remove-member", "POST", "Invalid response structure")
            else:
                self.test_results['remove_member'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/remove-member", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['remove_member'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/remove-member", "POST", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all chat API tests"""
        print("🚀 Starting Chat API Tests...")
        
        # Test basic functionality
        self.test_get_groups()
        self.test_create_group()
        self.test_create_group_with_initial_members()
        self.test_user_search()
        
        # Test messaging
        self.test_send_message()
        self.test_get_messages()
        self.test_file_upload()
        self.test_get_attachment()
        
        # Test member management
        self.test_add_member()
        self.test_remove_member()
        
        # Print summary
        print("\n📊 Chat API Test Results:")
        passed = sum(1 for result in self.test_results.values() if result is True)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL" if result is False else "⏭️ SKIP"
            print(f"  {test_name}: {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if self.errors:
            print(f"\n🚨 Errors encountered:")
            for error in self.errors:
                print(f"  - {error}")
        
        return passed == total

def main():
    tester = ChatAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())