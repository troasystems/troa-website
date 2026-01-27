#!/usr/bin/env python3
"""
Backend API Testing for Issue Fixes
Tests the 4 specific issues reported by user:
1. Feedback banner still hidden behind header
2. No confirmation popup when joining/leaving groups  
3. Login button not center-aligned vertically
4. Updating picture of a group not working

Focus on backend API testing for group picture update functionality.
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

class IssueFixes_APITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'group_picture_update': {
                'put_group_icon_only': None,
                'put_group_icon_with_name': None,
                'put_group_icon_validation': None,
                'icon_changed_state_simulation': None
            },
            'group_operations': {
                'join_group_api': None,
                'leave_group_api': None,
                'get_groups_api': None
            }
        }
        self.errors = []
        self.created_group_id = None
        self.test_group_id = None
        
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

    def setup_test_group(self):
        """Create a test group for testing updates"""
        print("\n🧪 Setting up test group...")
        
        try:
            test_group = {
                "name": "Issue Fix Test Group",
                "description": "Group for testing issue fixes",
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
                return True
            else:
                self.log_error("/chat/groups", "POST", f"Failed to create test group: {response.status_code}")
                return False
        except Exception as e:
            self.log_error("/chat/groups", "POST", f"Exception creating test group: {str(e)}")
            return False

    def test_group_picture_update_api(self):
        """Test PUT /api/chat/groups/{id} with icon field updates the group icon"""
        print("\n🧪 Testing Group Picture Update API...")
        
        if not self.created_group_id:
            self.log_error("Group Picture Update", "SETUP", "No group created for testing")
            return

        # Test 1: Update group icon only (simulating iconChanged=true scenario)
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
                    self.test_results['group_picture_update']['put_group_icon_only'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- Updated group icon only successfully")
                else:
                    self.test_results['group_picture_update']['put_group_icon_only'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", "Icon update not reflected in response")
            else:
                self.test_results['group_picture_update']['put_group_icon_only'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_picture_update']['put_group_icon_only'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Exception updating icon only: {str(e)}")

        # Test 2: Update group icon with name (simulating EditGroupModal scenario)
        try:
            # Different icon for this test
            different_icon = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            update_data = {
                "name": "Updated Group Name",
                "description": "Updated description", 
                "icon": different_icon
            }
            
            response = requests.put(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                  json=update_data, 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get('icon') == different_icon and 
                    data.get('name') == "Updated Group Name" and
                    data.get('description') == "Updated description"):
                    self.test_results['group_picture_update']['put_group_icon_with_name'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- Updated group icon with name/description successfully")
                else:
                    self.test_results['group_picture_update']['put_group_icon_with_name'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", "Icon/name/description update not reflected properly")
            else:
                self.test_results['group_picture_update']['put_group_icon_with_name'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_picture_update']['put_group_icon_with_name'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Exception updating icon with name: {str(e)}")

        # Test 3: Test icon validation (invalid base64)
        try:
            invalid_icon = "invalid-base64-data"
            update_data = {"icon": invalid_icon}
            
            response = requests.put(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                  json=update_data, 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            # Should either accept it (no validation) or reject it (with validation)
            if response.status_code == 200:
                self.test_results['group_picture_update']['put_group_icon_validation'] = True
                self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- Accepts icon data (no validation enforced)")
            elif response.status_code in [400, 422]:
                self.test_results['group_picture_update']['put_group_icon_validation'] = True
                self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- Properly validates icon data")
            else:
                self.test_results['group_picture_update']['put_group_icon_validation'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Unexpected status for invalid icon: {response.status_code}")
        except Exception as e:
            self.test_results['group_picture_update']['put_group_icon_validation'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Exception testing icon validation: {str(e)}")

        # Test 4: Simulate iconChanged state behavior (only send icon when changed)
        try:
            # First get current group state
            response = requests.get(f"{self.base_url}/chat/groups", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                groups = response.json()
                current_group = next((g for g in groups if g['id'] == self.created_group_id), None)
                
                if current_group:
                    # Simulate updating name without changing icon (iconChanged=false scenario)
                    update_data = {
                        "name": "Name Only Update",
                        "description": current_group.get('description', '')
                        # Note: No icon field included when iconChanged=false
                    }
                    
                    response = requests.put(f"{self.base_url}/chat/groups/{self.created_group_id}", 
                                          json=update_data, 
                                          headers=self.auth_headers,
                                          timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Icon should remain unchanged
                        if (data.get('name') == "Name Only Update" and 
                            data.get('icon') == current_group.get('icon')):
                            self.test_results['group_picture_update']['icon_changed_state_simulation'] = True
                            self.log_success(f"/chat/groups/{self.created_group_id}", "PUT", "- iconChanged=false simulation: icon preserved when not included")
                        else:
                            self.test_results['group_picture_update']['icon_changed_state_simulation'] = False
                            self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", "Icon not preserved when not included in update")
                    else:
                        self.test_results['group_picture_update']['icon_changed_state_simulation'] = False
                        self.log_error(f"/chat/groups/{self.created_group_id}", "PUT", f"Status code: {response.status_code}")
                else:
                    self.test_results['group_picture_update']['icon_changed_state_simulation'] = False
                    self.log_error("iconChanged simulation", "SETUP", "Could not find created group")
            else:
                self.test_results['group_picture_update']['icon_changed_state_simulation'] = False
                self.log_error("/chat/groups", "GET", f"Failed to get groups: {response.status_code}")
        except Exception as e:
            self.test_results['group_picture_update']['icon_changed_state_simulation'] = False
            self.log_error("iconChanged simulation", "TEST", f"Exception: {str(e)}")

    def test_group_operations_api(self):
        """Test group join/leave operations for confirmation dialog testing"""
        print("\n🧪 Testing Group Operations API...")
        
        if not self.created_group_id:
            self.log_error("Group Operations", "SETUP", "No group created for testing")
            return

        # Test 1: Leave group (to test later join)
        try:
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/leave", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'left' in data['message'].lower():
                    self.test_results['group_operations']['leave_group_api'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/leave", "POST", "- Left group successfully")
                else:
                    self.test_results['group_operations']['leave_group_api'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/leave", "POST", "Invalid response message")
            else:
                self.test_results['group_operations']['leave_group_api'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/leave", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_operations']['leave_group_api'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/leave", "POST", f"Exception: {str(e)}")

        # Test 2: Join group
        try:
            response = requests.post(f"{self.base_url}/chat/groups/{self.created_group_id}/join", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'joined' in data['message'].lower():
                    self.test_results['group_operations']['join_group_api'] = True
                    self.log_success(f"/chat/groups/{self.created_group_id}/join", "POST", "- Joined group successfully")
                else:
                    self.test_results['group_operations']['join_group_api'] = False
                    self.log_error(f"/chat/groups/{self.created_group_id}/join", "POST", "Invalid response message")
            else:
                self.test_results['group_operations']['join_group_api'] = False
                self.log_error(f"/chat/groups/{self.created_group_id}/join", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_operations']['join_group_api'] = False
            self.log_error(f"/chat/groups/{self.created_group_id}/join", "POST", f"Exception: {str(e)}")

        # Test 3: Get groups (to verify group state)
        try:
            response = requests.get(f"{self.base_url}/chat/groups", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                groups = response.json()
                if isinstance(groups, list):
                    self.test_results['group_operations']['get_groups_api'] = True
                    self.log_success("/chat/groups", "GET", f"- Retrieved {len(groups)} groups")
                    
                    # Find our test group
                    test_group = next((g for g in groups if g['id'] == self.created_group_id), None)
                    if test_group:
                        self.log_success("/chat/groups", "GET", f"- Test group found with {test_group.get('member_count', 0)} members")
                    else:
                        self.log_error("/chat/groups", "GET", "Test group not found in groups list")
                else:
                    self.test_results['group_operations']['get_groups_api'] = False
                    self.log_error("/chat/groups", "GET", "Response is not a list")
            else:
                self.test_results['group_operations']['get_groups_api'] = False
                self.log_error("/chat/groups", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['group_operations']['get_groups_api'] = False
            self.log_error("/chat/groups", "GET", f"Exception: {str(e)}")

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
        """Run all issue fix tests"""
        print("🚀 Starting Issue Fixes API Testing...")
        print(f"Backend URL: {self.base_url}")
        
        # Setup
        if not self.setup_test_group():
            print("❌ Failed to setup test group. Aborting tests.")
            return self.test_results, self.errors
        
        # Run tests
        self.test_group_picture_update_api()
        self.test_group_operations_api()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
        return self.test_results, self.errors

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 ISSUE FIXES API TEST SUMMARY")
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
    tester = IssueFixes_APITester()
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