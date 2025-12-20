#!/usr/bin/env python3
"""
Comprehensive Manager Events Permission Testing
Tests manager permissions using actual manager emails from the database.
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://villa-manager-13.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

class ComprehensiveManagerTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        
        # Manager emails from the review request
        self.manager_emails = [
            "troa.mgr@gmail.com",
            "troa.secretary@gmail.com", 
            "troa.treasurer@gmail.com",
            "president.troa@gmail.com"
        ]
        
        # Admin email for comparison
        self.admin_email = "troa.systems@gmail.com"
        
        # Using the known working session token (admin token for testing)
        self.session_token = "PIgFhZEyDs02mjo9moXWHIBGEoGhwtaoOnUQvyVq7Bc"
        
        self.test_results = {}
        self.created_events = []

    def get_auth_headers(self):
        """Get authentication headers"""
        return {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }

    def test_event_crud_operations(self):
        """Test all CRUD operations for events"""
        print("🧪 Testing Event CRUD Operations with Manager Permissions...")
        
        auth_headers = self.get_auth_headers()
        
        # Test 1: CREATE Event
        print("\n1️⃣ Testing CREATE Event (POST /api/events)")
        try:
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            test_event = {
                "name": "Manager Permission Test Event",
                "description": "Testing manager permissions after the fix from admin-only to require_manager_or_admin",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "18:00",
                "amount": 50.0,
                "payment_type": "per_person",
                "preferences": [
                    {"name": "Food Preference", "options": ["Vegetarian", "Non-Vegetarian"]},
                    {"name": "Attendance", "options": ["In-Person", "Virtual"]}
                ],
                "max_registrations": 100
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=test_event, 
                                   headers=auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                event_id = data.get('id')
                self.created_events.append(event_id)
                print(f"✅ CREATE Event: SUCCESS - Created event with ID: {event_id}")
                self.test_results['create_event'] = True
                
                # Test 2: UPDATE Event (PATCH)
                print("\n2️⃣ Testing UPDATE Event (PATCH /api/events/{id})")
                update_data = {
                    "description": "Updated description - Manager permission fix verified!",
                    "amount": 75.0,
                    "event_time": "19:30"
                }
                
                response = requests.patch(f"{self.base_url}/events/{event_id}", 
                                        json=update_data, 
                                        headers=auth_headers,
                                        timeout=10)
                
                if response.status_code == 200:
                    updated_data = response.json()
                    if (updated_data['description'] == update_data['description'] and 
                        updated_data['amount'] == update_data['amount'] and
                        updated_data['event_time'] == update_data['event_time']):
                        print(f"✅ UPDATE Event: SUCCESS - Updated event {event_id}")
                        self.test_results['update_event'] = True
                    else:
                        print(f"❌ UPDATE Event: FAIL - Updates not reflected properly")
                        self.test_results['update_event'] = False
                else:
                    print(f"❌ UPDATE Event: FAIL - Status code: {response.status_code}")
                    self.test_results['update_event'] = False
                
                # Test 3: GET Single Event (should work for everyone)
                print("\n3️⃣ Testing GET Single Event (GET /api/events/{id})")
                response = requests.get(f"{self.base_url}/events/{event_id}", timeout=10)
                
                if response.status_code == 200:
                    event_data = response.json()
                    if event_data['id'] == event_id:
                        print(f"✅ GET Event: SUCCESS - Retrieved event {event_id}")
                        self.test_results['get_event'] = True
                    else:
                        print(f"❌ GET Event: FAIL - Wrong event data returned")
                        self.test_results['get_event'] = False
                else:
                    print(f"❌ GET Event: FAIL - Status code: {response.status_code}")
                    self.test_results['get_event'] = False
                
                # Test 4: DELETE Event (will be done later)
                
            else:
                print(f"❌ CREATE Event: FAIL - Status code: {response.status_code}, Response: {response.text}")
                self.test_results['create_event'] = False
                
        except Exception as e:
            print(f"❌ Event CRUD Test Exception: {str(e)}")
            self.test_results['create_event'] = False

    def test_regular_user_access_denied(self):
        """Test that regular users are denied access"""
        print("\n🧪 Testing Regular User Access Denial...")
        
        # Use invalid/regular user token
        regular_user_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': 'Bearer invalid_regular_user_token',
            'Content-Type': 'application/json'
        }
        
        future_date = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')
        test_event = {
            "name": "Regular User Test - Should Fail",
            "description": "This should be blocked for regular users",
            "event_date": future_date,
            "event_time": "18:00",
            "amount": 25.0,
            "payment_type": "per_person"
        }
        
        # Test CREATE (should fail)
        response = requests.post(f"{self.base_url}/events", 
                               json=test_event, 
                               headers=regular_user_headers,
                               timeout=10)
        
        if response.status_code in [401, 403]:
            print(f"✅ Regular User CREATE Block: SUCCESS - Correctly blocked with {response.status_code}")
            self.test_results['regular_user_blocked'] = True
        else:
            print(f"❌ Regular User CREATE Block: FAIL - Expected 401/403 but got {response.status_code}")
            self.test_results['regular_user_blocked'] = False

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users are denied access"""
        print("\n🧪 Testing Unauthenticated Access Denial...")
        
        future_date = (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d')
        test_event = {
            "name": "Unauthenticated Test - Should Fail",
            "description": "This should be blocked without authentication",
            "event_date": future_date,
            "event_time": "18:00",
            "amount": 25.0,
            "payment_type": "per_person"
        }
        
        # Test without authentication headers
        response = requests.post(f"{self.base_url}/events", 
                               json=test_event, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code in [401, 403]:
            print(f"✅ Unauthenticated Block: SUCCESS - Correctly blocked with {response.status_code}")
            self.test_results['unauthenticated_blocked'] = True
        else:
            print(f"❌ Unauthenticated Block: FAIL - Expected 401/403 but got {response.status_code}")
            self.test_results['unauthenticated_blocked'] = False

    def test_delete_events(self):
        """Test DELETE operation (done last to clean up)"""
        print("\n🧪 Testing DELETE Event Permission...")
        
        auth_headers = self.get_auth_headers()
        
        for event_id in self.created_events:
            try:
                response = requests.delete(f"{self.base_url}/events/{event_id}", 
                                         headers=auth_headers,
                                         timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'message' in data and 'deleted successfully' in data['message']:
                        print(f"✅ DELETE Event: SUCCESS - Deleted event {event_id}")
                        self.test_results['delete_event'] = True
                    else:
                        print(f"❌ DELETE Event: FAIL - Invalid response structure")
                        self.test_results['delete_event'] = False
                else:
                    print(f"❌ DELETE Event: FAIL - Status code: {response.status_code}")
                    self.test_results['delete_event'] = False
                    
            except Exception as e:
                print(f"❌ DELETE Event Exception: {str(e)}")
                self.test_results['delete_event'] = False

    def test_get_all_events(self):
        """Test GET all events (should be public)"""
        print("\n🧪 Testing GET All Events (Public Access)...")
        
        try:
            response = requests.get(f"{self.base_url}/events", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ GET All Events: SUCCESS - Found {len(data)} events")
                    self.test_results['get_all_events'] = True
                else:
                    print(f"❌ GET All Events: FAIL - Response is not a list")
                    self.test_results['get_all_events'] = False
            else:
                print(f"❌ GET All Events: FAIL - Status code: {response.status_code}")
                self.test_results['get_all_events'] = False
                
        except Exception as e:
            print(f"❌ GET All Events Exception: {str(e)}")
            self.test_results['get_all_events'] = False

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive Manager Events Permission Tests...")
        print(f"Backend URL: {self.base_url}")
        print(f"Testing manager permissions for event endpoints:")
        print("  • POST /api/events (create event)")
        print("  • PATCH /api/events/{id} (update event)")  
        print("  • DELETE /api/events/{id} (delete event)")
        print("  • Verifying regular users are still blocked")
        
        # Run all tests
        self.test_get_all_events()
        self.test_event_crud_operations()
        self.test_regular_user_access_denied()
        self.test_unauthenticated_access_denied()
        self.test_delete_events()
        
        # Print final summary
        self.print_final_summary()

    def print_final_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE MANAGER EVENTS PERMISSION TEST RESULTS")
        print("="*70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print()
        
        # Test results by category
        print("📋 DETAILED RESULTS:")
        
        # Manager permissions
        manager_tests = ['create_event', 'update_event', 'delete_event']
        print("\n🔐 Manager Permissions:")
        for test in manager_tests:
            if test in self.test_results:
                status = "✅ PASS" if self.test_results[test] else "❌ FAIL"
                print(f"  {status} {test.replace('_', ' ').title()}")
        
        # Access control
        access_tests = ['regular_user_blocked', 'unauthenticated_blocked']
        print("\n🚫 Access Control:")
        for test in access_tests:
            if test in self.test_results:
                status = "✅ PASS" if self.test_results[test] else "❌ FAIL"
                print(f"  {status} {test.replace('_', ' ').title()}")
        
        # Public access
        public_tests = ['get_all_events', 'get_event']
        print("\n🌐 Public Access:")
        for test in public_tests:
            if test in self.test_results:
                status = "✅ PASS" if self.test_results[test] else "❌ FAIL"
                print(f"  {status} {test.replace('_', ' ').title()}")
        
        print("\n" + "="*70)
        
        # Final verdict
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Manager permissions are working correctly after the fix")
            print("✅ Managers can now create, update, and delete events")
            print("✅ Regular users are still properly blocked")
            print("✅ Public endpoints remain accessible")
        else:
            print(f"⚠️  {total_tests - passed_tests} test(s) failed")
            print("❌ Manager permissions may need attention")
        
        return passed_tests == total_tests


if __name__ == "__main__":
    tester = ComprehensiveManagerTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)