#!/usr/bin/env python3
"""
Backend API Testing for New Chat Features
Tests the 5 new features implemented:
1. Button text center alignment (frontend only)
2. Confirmation popup for joining/leaving groups (frontend only) 
3. User profile picture thumbnails next to messages
4. Read/unread message status with tick marks
5. Admin/managers can update group name and icon
"""

import requests
import json
import os
import base64
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
ADMIN_EMAIL = "troa.systems@gmail.com"

class ChatFeaturesAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'group_update': {'put_group_name': None, 'put_group_icon': None, 'put_group_description': None},
            'message_features': {'sender_picture_field': None, 'status_field': None, 'read_by_field': None},
            'message_status': {'sending_status': None, 'sent_status': None, 'read_status': None}
        }
        self.errors = []
        self.created_group_id = None
        self.created_message_id = None
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.session_token = "xBPTLcvN2wsTsXtfGxu1MJ4W7VmNi8oO5fUrLqqVT44"  # Valid admin session token
        self.auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
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

    def test_group_update_api(self):
        """Test PUT /api/chat/groups/{id} endpoint for updating group name/description/icon"""
        print("\n🧪 Testing Group Update API (PUT /api/chat/groups/{id})...")
        
        # First create a test group
        try:
            test_group = {
                "name": "Test Update Group",
                "description": "Group for testing updates",
                "is_mc_only": False,
                "initial_members": [],
                "icon": None
            }
            
            response = requests.post(f"{self.base_url}/chat/groups", 
                                   json=test_group, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.created_group_id = data['id']
                self.log_success("/chat/groups", "POST", f"- Created test group: {self.created_group_id}")
            else:
                self.log_error("/chat/groups", "POST", f"Failed to create test group: {response.status_code}")
                return
        except Exception as e:
            self.log_error("/chat/groups", "POST", f"Exception creating test group: {str(e)}")
            return

        # Test 1: Update group name
        try:
            update_data = {"name": "Updated Group Name"}
            response = requests.put(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                  json=update_data, 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('name') == "Updated Group Name":
                    self.test_results['group_update']['put_group_name'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- Updated group name successfully")
                else:
                    self.test_results['group_update']['put_group_name'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", "Name update not reflected in response")
            else:
                self.test_results['group_update']['put_group_name'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_update']['put_group_name'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Exception updating name: {str(e)}")

        # Test 2: Update group description
        try:
            update_data = {"description": "Updated group description for testing"}
            response = requests.put(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                  json=update_data, 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('description') == "Updated group description for testing":
                    self.test_results['group_update']['put_group_description'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- Updated group description successfully")
                else:
                    self.test_results['group_update']['put_group_description'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", "Description update not reflected in response")
            else:
                self.test_results['group_update']['put_group_description'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_update']['put_group_description'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Exception updating description: {str(e)}")

        # Test 3: Update group icon (base64 encoded)
        try:
            # Sample base64 encoded small image (1x1 pixel PNG)
            sample_icon = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            update_data = {"icon": sample_icon}
            response = requests.put(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                  json=update_data, 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('icon') == sample_icon:
                    self.test_results['group_update']['put_group_icon'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- Updated group icon successfully")
                else:
                    self.test_results['group_update']['put_group_icon'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", "Icon update not reflected in response")
            else:
                self.test_results['group_update']['put_group_icon'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_update']['put_group_icon'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Exception updating icon: {str(e)}")

    def test_message_features(self):
        """Test message features: sender_picture, status, and read_by fields"""
        print("\n🧪 Testing Message Features (sender_picture, status, read_by)...")
        
        if not self.created_group_id:
            self.log_error("Message Features", "SETUP", "No group created for testing messages")
            return

        # Test 1: Send a message and check response includes required fields
        try:
            message_data = {
                "content": "Test message for checking new features",
                "group_id": self.created_group_id
            }
            
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/messages", 
                                   json=message_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.created_message_id = data.get('id')
                
                # Check for sender_picture field
                if 'sender_picture' in data:
                    self.test_results['message_features']['sender_picture_field'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/messages", "POST", f"- sender_picture field present: {data.get('sender_picture')}")
                else:
                    self.test_results['message_features']['sender_picture_field'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", "sender_picture field missing")
                
                # Check for status field
                if 'status' in data:
                    self.test_results['message_features']['status_field'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/messages", "POST", f"- status field present: {data.get('status')}")
                else:
                    self.test_results['message_features']['status_field'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", "status field missing")
                
                # Check for read_by field
                if 'read_by' in data:
                    self.test_results['message_features']['read_by_field'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/messages", "POST", f"- read_by field present: {data.get('read_by')}")
                else:
                    self.test_results['message_features']['read_by_field'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", "read_by field missing")
                    
            else:
                self.test_results['message_features']['sender_picture_field'] = False
                self.test_results['message_features']['status_field'] = False
                self.test_results['message_features']['read_by_field'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['message_features']['sender_picture_field'] = False
            self.test_results['message_features']['status_field'] = False
            self.test_results['message_features']['read_by_field'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", f"Exception: {str(e)}")

        # Test 2: Get messages and verify fields are included
        try:
            response = requests.get(f"{self.base_url}/chat/groups/{self.created_group_id}/messages", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                messages = response.json()
                if messages and len(messages) > 0:
                    message = messages[-1]  # Get the last message (our test message)
                    
                    # Verify all required fields are present
                    required_fields = ['sender_picture', 'status', 'read_by']
                    missing_fields = [field for field in required_fields if field not in message]
                    
                    if not missing_fields:
                        self.log_success(f"/chat/groups/{self.created_group_id}/messages", "GET", f"- All new fields present in retrieved messages")
                        
                        # Check status values
                        status = message.get('status')
                        if status in ['sending', 'sent', 'delivered', 'read']:
                            self.test_results['message_status']['sent_status'] = True
                            self.log_success("Message Status", "VALIDATION", f"- Valid status value: {status}")
                        else:
                            self.test_results['message_status']['sent_status'] = False
                            self.log_error("Message Status", "VALIDATION", f"Invalid status value: {status}")
                            
                        # Check read_by is a list
                        read_by = message.get('read_by')
                        if isinstance(read_by, list):
                            self.test_results['message_status']['read_status'] = True
                            self.log_success("Message Status", "VALIDATION", f"- read_by is list with {len(read_by)} readers")
                        else:
                            self.test_results['message_status']['read_status'] = False
                            self.log_error("Message Status", "VALIDATION", f"read_by is not a list: {type(read_by)}")
                    else:
                        self.log_error(f"/chat/groups/{self.created_group_id}/messages", "GET", f"Missing fields in retrieved messages: {missing_fields}")
                else:
                    self.log_error(f"/chat/groups/{self.created_group_id}/messages", "GET", "No messages returned")
            else:
                self.log_error(f"/chat/groups/{self.created_group_id}/messages", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error(f"/chat/groups/{self.created_group_id}/messages", "GET", f"Exception: {str(e)}")

    def test_authentication_requirements(self):
        """Test that group update endpoints require admin/manager authentication"""
        print("\n🧪 Testing Authentication Requirements...")
        
        if not self.created_group_id:
            self.log_error("Authentication", "SETUP", "No group created for testing auth")
            return

        # Test without authentication (should fail)
        try:
            update_data = {"name": "Unauthorized Update"}
            response = requests.put(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                  json=update_data, 
                                  headers={'Content-Type': 'application/json'},
                                  timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_success(f"/chat/groups/{self.created_group_id}", "AUTH", "- Correctly requires authentication")
            else:
                self.log_error(f"/chat/groups/{self.created_group_id}", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error(f"/chat/groups/{self.created_group_id}", "AUTH", f"Exception: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test group created during testing"""
        print("\n🧹 Cleaning up test data...")
        
        if self.created_group_id:
            try:
                response = requests.delete(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                         headers=self.auth_headers,
                                         timeout=10)
                
                if response.status_code == 200:
                    self.log_success(f"/chat/groups/{self.created_group_id}", "DELETE", "- Test group cleaned up")
                else:
                    self.log_error(f"/chat/groups/{self.created_group_id}", "DELETE", f"Failed to cleanup: {response.status_code}")
            except Exception as e:
                self.log_error(f"/chat/groups/{self.created_group_id}", "DELETE", f"Exception during cleanup: {str(e)}")

    def run_all_tests(self):
        """Run all chat feature tests"""
        print("🚀 Starting Chat Features API Testing...")
        print(f"Backend URL: {self.base_url}")
        
        # Run tests
        self.test_group_update_api()
        self.test_message_features()
        self.test_authentication_requirements()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
        return self.test_results, self.errors

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 CHAT FEATURES API TEST SUMMARY")
        print("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            for test_name, result in tests.items():
                total_tests += 1
                if result is True:
                    passed_tests += 1
                    print(f"  ✅ {test_name}: PASSED")
                elif result is False:
                    print(f"  ❌ {test_name}: FAILED")
                else:
                    print(f"  ⚠️  {test_name}: NOT TESTED")
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "   Success Rate: 0%")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        print("="*60)

def main():
    """Main function to run the tests"""
    tester = ChatFeaturesAPITester()
    test_results, errors = tester.run_all_tests()
    
    # Return exit code based on results
    total_tests = sum(len(tests) for tests in test_results.values())
    passed_tests = sum(1 for tests in test_results.values() for result in tests.values() if result is True)
    
    if passed_tests == total_tests and total_tests > 0:
        return 0  # All tests passed
    else:
        return 1  # Some tests failed

if __name__ == "__main__":
    exit(main())