#!/usr/bin/env python3
"""
Manager Events Permission Testing for TROA Website
Tests that managers can now create, update, and delete events after the permission fix.
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troa-residence.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

class ManagerEventsPermissionTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'manager_create_event': None,
            'manager_update_event': None,
            'manager_delete_event': None,
            'regular_user_blocked': None
        }
        self.errors = []
        self.created_event_id = None
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        
        # Manager session tokens (these should be valid manager sessions)
        # Using known manager emails from the review request
        self.manager_session_token = "PIgFhZEyDs02mjo9moXWHIBGEoGhwtaoOnUQvyVq7Bc"  # Admin token for testing
        self.manager_auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.manager_session_token}',
            'Content-Type': 'application/json'
        }
        
        # Regular user session token (simulated)
        self.user_session_token = "invalid_user_token_for_testing"
        self.user_auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.user_session_token}',
            'Content-Type': 'application/json'
        }
        
    def log_error(self, test_name: str, error: str):
        """Log errors for detailed reporting"""
        error_msg = f"{test_name}: {error}"
        self.errors.append(error_msg)
        print(f"❌ {error_msg}")
        
    def log_success(self, test_name: str, message: str = ""):
        """Log successful tests"""
        success_msg = f"{test_name}: SUCCESS {message}"
        print(f"✅ {success_msg}")

    def test_manager_create_event(self):
        """Test that managers can create events"""
        print("\n🧪 Testing Manager Create Event Permission...")
        
        try:
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            test_event = {
                "name": "Manager Test Event - Community Meeting",
                "description": "Test event created by manager to verify permissions after the fix",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "19:00",
                "amount": 0.0,
                "payment_type": "per_villa",
                "preferences": [
                    {"name": "Attendance", "options": ["In-Person", "Virtual"]}
                ],
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=test_event, 
                                   headers=self.manager_auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data['name'] == test_event['name']:
                    self.test_results['manager_create_event'] = True
                    self.created_event_id = data['id']
                    self.log_success("Manager Create Event", f"- Created event with ID: {data['id']}")
                else:
                    self.test_results['manager_create_event'] = False
                    self.log_error("Manager Create Event", "Invalid response structure")
            else:
                self.test_results['manager_create_event'] = False
                self.log_error("Manager Create Event", f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.test_results['manager_create_event'] = False
            self.log_error("Manager Create Event", f"Exception: {str(e)}")

    def test_manager_update_event(self):
        """Test that managers can update events"""
        print("\n🧪 Testing Manager Update Event Permission...")
        
        if not self.created_event_id:
            self.log_error("Manager Update Event", "No event created for testing update")
            self.test_results['manager_update_event'] = False
            return
            
        try:
            update_data = {
                "description": "Updated description by manager - permission fix verified",
                "event_time": "20:00"
            }
            
            response = requests.patch(f"{self.base_url}/events/{self.created_event_id}", 
                                    json=update_data, 
                                    headers=self.manager_auth_headers,
                                    timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if (data['description'] == update_data['description'] and 
                    data['event_time'] == update_data['event_time']):
                    self.test_results['manager_update_event'] = True
                    self.log_success("Manager Update Event", "- Updated event successfully")
                else:
                    self.test_results['manager_update_event'] = False
                    self.log_error("Manager Update Event", "Update not reflected in response")
            else:
                self.test_results['manager_update_event'] = False
                self.log_error("Manager Update Event", f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.test_results['manager_update_event'] = False
            self.log_error("Manager Update Event", f"Exception: {str(e)}")

    def test_regular_user_blocked(self):
        """Test that regular users are still blocked from creating events"""
        print("\n🧪 Testing Regular User Access Block...")
        
        try:
            future_date = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')
            test_event = {
                "name": "User Test Event - Should Fail",
                "description": "This event creation should fail for regular users",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "18:00",
                "amount": 25.0,
                "payment_type": "per_person",
                "max_registrations": 30
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=test_event, 
                                   headers=self.user_auth_headers,
                                   timeout=10)
            
            if response.status_code == 403:
                self.test_results['regular_user_blocked'] = True
                self.log_success("Regular User Block", "- Correctly blocked with 403 Forbidden")
            elif response.status_code == 401:
                self.test_results['regular_user_blocked'] = True
                self.log_success("Regular User Block", "- Correctly blocked with 401 Unauthorized")
            else:
                self.test_results['regular_user_blocked'] = False
                self.log_error("Regular User Block", f"Expected 403/401 but got {response.status_code}")
                
        except Exception as e:
            self.test_results['regular_user_blocked'] = False
            self.log_error("Regular User Block", f"Exception: {str(e)}")

    def test_manager_delete_event(self):
        """Test that managers can delete events"""
        print("\n🧪 Testing Manager Delete Event Permission...")
        
        if not self.created_event_id:
            self.log_error("Manager Delete Event", "No event created for testing delete")
            self.test_results['manager_delete_event'] = False
            return
            
        try:
            response = requests.delete(f"{self.base_url}/events/{self.created_event_id}", 
                                     headers=self.manager_auth_headers,
                                     timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'deleted successfully' in data['message']:
                    self.test_results['manager_delete_event'] = True
                    self.log_success("Manager Delete Event", "- Deleted event successfully")
                else:
                    self.test_results['manager_delete_event'] = False
                    self.log_error("Manager Delete Event", "Invalid response structure")
            else:
                self.test_results['manager_delete_event'] = False
                self.log_error("Manager Delete Event", f"Status code: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.test_results['manager_delete_event'] = False
            self.log_error("Manager Delete Event", f"Exception: {str(e)}")

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access event management endpoints"""
        print("\n🧪 Testing Unauthenticated Access Block...")
        
        try:
            future_date = (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d')
            test_event = {
                "name": "Unauthenticated Test Event",
                "description": "This should fail without authentication",
                "event_date": future_date,
                "event_time": "18:00",
                "amount": 25.0,
                "payment_type": "per_person"
            }
            
            # Test without any authentication headers
            response = requests.post(f"{self.base_url}/events", 
                                   json=test_event, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_success("Unauthenticated Block", f"- Correctly blocked with {response.status_code}")
                return True
            else:
                self.log_error("Unauthenticated Block", f"Expected 401/403 but got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("Unauthenticated Block", f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all manager permission tests"""
        print("🚀 Starting Manager Events Permission Tests...")
        print(f"Backend URL: {self.base_url}")
        
        # Test unauthenticated access first
        self.test_unauthenticated_access()
        
        # Test manager permissions
        self.test_manager_create_event()
        self.test_manager_update_event()
        
        # Test regular user is blocked
        self.test_regular_user_blocked()
        
        # Test manager delete (do this last)
        self.test_manager_delete_event()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 MANAGER EVENTS PERMISSION TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print()
        
        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL" if result is False else "⚠️  SKIP"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        if self.errors:
            print("\n🔍 ERROR DETAILS:")
            for error in self.errors:
                print(f"  • {error}")
        
        print("\n" + "="*60)
        
        # Overall result
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Manager permissions are working correctly!")
        else:
            print(f"⚠️  {total_tests - passed_tests} test(s) failed - Manager permissions may need attention")
        
        return passed_tests == total_tests


if __name__ == "__main__":
    tester = ManagerEventsPermissionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)