#!/usr/bin/env python3
"""
Backend API Testing for New Chat Features: Typing Indicator & Unread Counts
Tests the new features implemented:
1. POST /api/chat/groups/{group_id}/typing - update typing status
2. GET /api/chat/groups/{group_id}/typing - get users currently typing
3. GET /api/chat/groups/unread-counts - get unread counts and latest message times
4. POST /api/chat/groups/{group_id}/mark-read - mark group as read
"""

import requests
import json
import os
import base64
import time
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
ADMIN_EMAIL = "troa.systems@gmail.com"
MEMBER_EMAIL = "abcde@gmail.com"

class ChatTypingUnreadAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'typing_indicator': {
                'post_typing_start': None,
                'post_typing_stop': None,
                'get_typing_users': None,
                'typing_timeout': None
            },
            'unread_counts': {
                'get_unread_counts': None,
                'mark_group_read': None,
                'unread_count_accuracy': None,
                'latest_message_time': None
            }
        }
        self.errors = []
        self.created_group_id = None
        self.created_message_id = None
        
        # Setup authentication headers for admin user
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.admin_session_token = "xBPTLcvN2wsTsXtfGxu1MJ4W7VmNi8oO5fUrLqqVT44"  # Valid admin session token
        self.admin_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.admin_session_token}',
            'Content-Type': 'application/json'
        }
        
        # Setup headers for member user (use same token for testing)
        self.member_session_token = "HVTQkdSZphVYtWmKVkq6MtFd3krZviaLbvOfSN4rqGA"  # Valid token
        self.member_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.member_session_token}',
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

    def setup_test_group(self):
        """Create a test group for testing"""
        print("\n🔧 Setting up test group...")
        
        try:
            test_group = {
                "name": "Typing & Unread Test Group",
                "description": "Group for testing typing indicator and unread counts",
                "group_type": "public",
                "initial_members": [MEMBER_EMAIL],  # Add member to group
                "icon": None
            }
            
            response = requests.post(f"{self.base_url}/chat/groups", 
                                   json=test_group, 
                                   headers=self.admin_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.created_group_id = data['id']
                self.log_success("/chat/groups", "POST", f"- Created test group: {self.created_group_id}")
                return True
            else:
                self.log_error("/chat/groups", "POST", f"Failed to create test group: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error("/chat/groups", "POST", f"Exception creating test group: {str(e)}")
            return False

    def test_typing_indicator_apis(self):
        """Test typing indicator APIs"""
        print("\n🧪 Testing Typing Indicator APIs...")
        
        if not self.created_group_id:
            self.log_error("Typing Indicator", "SETUP", "No group created for testing")
            return

        # Test 1: Start typing (POST with is_typing: true)
        try:
            typing_data = {"is_typing": True}
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/typing", 
                                   json=typing_data, 
                                   headers=self.admin_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.test_results['typing_indicator']['post_typing_start'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/typing", "POST", "- Started typing successfully")
                else:
                    self.test_results['typing_indicator']['post_typing_start'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/typing", "POST", f"Unexpected response: {data}")
            else:
                self.test_results['typing_indicator']['post_typing_start'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/typing", "POST", f"Status code: {response.status_code} - {response.text}")
        except Exception as e:
            self.test_results['typing_indicator']['post_typing_start'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/typing", "POST", f"Exception: {str(e)}")

        # Test 2: Get typing users (should show admin typing)
        try:
            response = requests.get(f"{self.base_url}/chat/groups/{self.created_group_id}/typing", 
                                  headers=self.member_headers,  # Use member to check who's typing
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                typing_users = data.get('typing_users', [])
                
                # Should show admin typing (but not the member themselves)
                admin_typing = any(user.get('email') == ADMIN_EMAIL for user in typing_users)
                if admin_typing:
                    self.test_results['typing_indicator']['get_typing_users'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/typing", "GET", f"- Found admin typing: {typing_users}")
                else:
                    self.test_results['typing_indicator']['get_typing_users'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/typing", "GET", f"Admin not found in typing users: {typing_users}")
            else:
                self.test_results['typing_indicator']['get_typing_users'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/typing", "GET", f"Status code: {response.status_code} - {response.text}")
        except Exception as e:
            self.test_results['typing_indicator']['get_typing_users'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/typing", "GET", f"Exception: {str(e)}")

        # Test 3: Stop typing (POST with is_typing: false)
        try:
            typing_data = {"is_typing": False}
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/typing", 
                                   json=typing_data, 
                                   headers=self.admin_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.test_results['typing_indicator']['post_typing_stop'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/typing", "POST", "- Stopped typing successfully")
                else:
                    self.test_results['typing_indicator']['post_typing_stop'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/typing", "POST", f"Unexpected response: {data}")
            else:
                self.test_results['typing_indicator']['post_typing_stop'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/typing", "POST", f"Status code: {response.status_code} - {response.text}")
        except Exception as e:
            self.test_results['typing_indicator']['post_typing_stop'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/typing", "POST", f"Exception: {str(e)}")

        # Test 4: Verify typing timeout (start typing and wait for auto-clear)
        try:
            # Start typing again
            typing_data = {"is_typing": True}
            requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/typing", 
                         json=typing_data, 
                         headers=self.admin_headers,
                         timeout=10)
            
            # Wait for timeout (should be 5 seconds according to code)
            print("   ⏳ Waiting 6 seconds for typing timeout...")
            time.sleep(6)
            
            # Check if typing status cleared
            response = requests.get(f"{self.base_url}/chat/groups/{self.created_group_id}/typing", 
                                  headers=self.member_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                typing_users = data.get('typing_users', [])
                
                # Should be empty after timeout
                if len(typing_users) == 0:
                    self.test_results['typing_indicator']['typing_timeout'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/typing", "TIMEOUT", "- Typing status cleared after timeout")
                else:
                    self.test_results['typing_indicator']['typing_timeout'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/typing", "TIMEOUT", f"Typing status not cleared: {typing_users}")
            else:
                self.test_results['typing_indicator']['typing_timeout'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/typing", "TIMEOUT", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['typing_indicator']['typing_timeout'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/typing", "TIMEOUT", f"Exception: {str(e)}")

    def test_unread_counts_apis(self):
        """Test unread counts and mark-read APIs"""
        print("\n🧪 Testing Unread Counts APIs...")
        
        if not self.created_group_id:
            self.log_error("Unread Counts", "SETUP", "No group created for testing")
            return

        # First, send a message from admin to create unread for member
        try:
            message_data = {
                "content": "Test message for unread count testing",
                "group_id": self.created_group_id
            }
            
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/messages", 
                                   json=message_data, 
                                   headers=self.admin_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.created_message_id = data.get('id')
                self.log_success(f"/chat/groups/{self.created_group_id}/messages", "POST", f"- Created test message: {self.created_message_id}")
                
                # Wait a moment for message to be processed
                time.sleep(1)
            else:
                self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", f"Failed to create message: {response.status_code}")
                return
        except Exception as e:
            self.log_error(f"/chat/groups/{self.created_group_id}/messages", "POST", f"Exception: {str(e)}")
            return

        # Test 1: Get unread counts (should show 1 unread for member)
        try:
            response = requests.get(f"{self.base_url}/chat/groups/unread-counts", 
                                  headers=self.member_headers,  # Use member to check their unread count
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                unread_counts = data.get('unread_counts', {})
                latest_message_times = data.get('latest_message_times', {})
                
                # Check if our group has unread count
                group_unread = unread_counts.get(self.created_group_id, 0)
                group_latest_time = latest_message_times.get(self.created_group_id)
                
                if group_unread > 0:
                    self.test_results['unread_counts']['get_unread_counts'] = True
                    self.test_results['unread_counts']['unread_count_accuracy'] = True
                    self.log_success("/chat/groups/unread-counts", "GET", f"- Found {group_unread} unread messages")
                else:
                    self.test_results['unread_counts']['get_unread_counts'] = True  # API worked
                    self.test_results['unread_counts']['unread_count_accuracy'] = False  # But count is wrong
                    self.log_error("/chat/groups/unread-counts", "GET", f"Expected unread count > 0, got: {group_unread}")
                
                if group_latest_time:
                    self.test_results['unread_counts']['latest_message_time'] = True
                    self.log_success("/chat/groups/unread-counts", "GET", f"- Latest message time: {group_latest_time}")
                else:
                    self.test_results['unread_counts']['latest_message_time'] = False
                    self.log_error("/chat/groups/unread-counts", "GET", "No latest message time found")
                    
            else:
                self.test_results['unread_counts']['get_unread_counts'] = False
                self.log_error("/chat/groups/unread-counts", "GET", f"Status code: {response.status_code} - {response.text}")
        except Exception as e:
            self.test_results['unread_counts']['get_unread_counts'] = False
            self.log_error("/chat/groups/unread-counts", "GET", f"Exception: {str(e)}")

        # Test 2: Mark group as read
        try:
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/mark-read", 
                                   json={},  # Empty body
                                   headers=self.member_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.test_results['unread_counts']['mark_group_read'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/mark-read", "POST", "- Marked group as read")
                    
                    # Wait a moment and check unread count again (should be 0)
                    time.sleep(1)
                    
                    response = requests.get(f"{self.base_url}/chat/groups/unread-counts", 
                                          headers=self.member_headers,
                                          timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        unread_counts = data.get('unread_counts', {})
                        group_unread = unread_counts.get(self.created_group_id, 0)
                        
                        if group_unread == 0:
                            self.log_success("/chat/groups/unread-counts", "VERIFY", f"- Unread count cleared after mark-read: {group_unread}")
                        else:
                            self.log_error("/chat/groups/unread-counts", "VERIFY", f"Unread count not cleared: {group_unread}")
                else:
                    self.test_results['unread_counts']['mark_group_read'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/mark-read", "POST", f"Unexpected response: {data}")
            else:
                self.test_results['unread_counts']['mark_group_read'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/mark-read", "POST", f"Status code: {response.status_code} - {response.text}")
        except Exception as e:
            self.test_results['unread_counts']['mark_group_read'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/mark-read", "POST", f"Exception: {str(e)}")

    def test_authentication_requirements(self):
        """Test that endpoints require proper authentication"""
        print("\n🧪 Testing Authentication Requirements...")
        
        if not self.created_group_id:
            self.log_error("Authentication", "SETUP", "No group created for testing auth")
            return

        # Test typing endpoint without auth
        try:
            typing_data = {"is_typing": True}
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/typing", 
                                   json=typing_data, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_success(f"/chat/groups/{self.created_group_id}/typing", "AUTH", "- Correctly requires authentication")
            else:
                self.log_error(f"/chat/groups/{self.created_group_id}/typing", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error(f"/chat/groups/{self.created_group_id}/typing", "AUTH", f"Exception: {str(e)}")

        # Test unread counts without auth
        try:
            response = requests.get(f"{self.base_url}/chat/groups/unread-counts", 
                                  headers={'Content-Type': 'application/json'},
                                  timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_success("/chat/groups/unread-counts", "AUTH", "- Correctly requires authentication")
            else:
                self.log_error("/chat/groups/unread-counts", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error("/chat/groups/unread-counts", "AUTH", f"Exception: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test group created during testing"""
        print("\n🧹 Cleaning up test data...")
        
        if self.created_group_id:
            try:
                response = requests.delete(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                         headers=self.admin_headers,
                                         timeout=10)
                
                if response.status_code == 200:
                    self.log_success(f"/chat/groups/{self.created_group_id}", "DELETE", "- Test group cleaned up")
                else:
                    self.log_error(f"/chat/groups/{self.created_group_id}", "DELETE", f"Failed to cleanup: {response.status_code}")
            except Exception as e:
                self.log_error(f"/chat/groups/{self.created_group_id}", "DELETE", f"Exception during cleanup: {str(e)}")

    def run_all_tests(self):
        """Run all typing indicator and unread count tests"""
        print("🚀 Starting Typing Indicator & Unread Counts API Testing...")
        print(f"Backend URL: {self.base_url}")
        
        # Setup
        if not self.setup_test_group():
            print("❌ Failed to setup test group, aborting tests")
            return self.test_results, self.errors
        
        # Run tests
        self.test_typing_indicator_apis()
        self.test_unread_counts_apis()
        self.test_authentication_requirements()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
        return self.test_results, self.errors

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TYPING INDICATOR & UNREAD COUNTS API TEST SUMMARY")
        print("="*70)
        
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
        
        print("="*70)

def main():
    """Main function to run the tests"""
    tester = ChatTypingUnreadAPITester()
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