#!/usr/bin/env python3
"""
Mark as Paid Endpoint Testing for TROA Event Registrations
Tests the new POST /api/events/registrations/{registration_id}/mark-paid endpoint
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://villa-manager-13.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
ADMIN_EMAIL = "troa.systems@gmail.com"

class MarkAsPaidTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.errors = []
        self.test_results = {
            'mark_pending_paid': None,
            'already_paid_error': None,
            'withdrawn_error': None,
            'unauthorized_access': None,
            'audit_log_creation': None
        }
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.session_token = "PIgFhZEyDs02mjo9moXWHIBGEoGhwtaoOnUQvyVq7Bc"  # Valid admin session token
        self.auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.session_token}',
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

    def test_mark_as_paid_endpoint(self):
        """Test all scenarios for the Mark as Paid endpoint"""
        print("🧪 Testing Mark as Paid Endpoint for Event Registrations...")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # First, create an event and registration for testing
        test_event_id = None
        test_registration_id = None
        
        try:
            # Create a test event
            future_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
            test_event = {
                "name": "Mark as Paid Test Event",
                "description": "Test event for mark as paid functionality",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "15:00",
                "amount": 100.0,
                "payment_type": "per_person",
                "preferences": [{"name": "Test Preference", "options": ["Option1", "Option2"]}],
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=test_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                test_event_id = response.json()['id']
                self.log_success("Setup - Create Event", f"Created test event: {test_event_id}")
                
                # Create a registration with pending payment status
                registration_data = {
                    "event_id": test_event_id,
                    "registrants": [
                        {"name": "Test User for Mark as Paid", "preferences": {"Test Preference": "Option1"}}
                    ],
                    "payment_method": "offline"  # This will create a pending payment
                }
                
                response = requests.post(f"{self.base_url}/events/{test_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    test_registration_id = response.json()['id']
                    self.log_success("Setup - Create Registration", f"Created test registration: {test_registration_id}")
                else:
                    self.log_error("Setup - Create Registration", f"Status code: {response.status_code}, Response: {response.text}")
                    return
            else:
                self.log_error("Setup - Create Event", f"Status code: {response.status_code}, Response: {response.text}")
                return
                
        except Exception as e:
            self.log_error("Setup", f"Exception: {str(e)}")
            return
        
        # Test 1: Mark registration as paid (admin/manager)
        print("\n📋 Test 1: Mark pending registration as paid")
        try:
            response = requests.post(f"{self.base_url}/events/registrations/{test_registration_id}/mark-paid", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'registration_id' in data:
                    self.test_results['mark_pending_paid'] = True
                    self.log_success("Mark Pending as Paid", f"Successfully marked registration as paid. Response: {data}")
                    
                    # Verify the registration is now marked as completed
                    response = requests.get(f"{self.base_url}/events/my/registrations", 
                                          headers=self.auth_headers,
                                          timeout=10)
                    
                    if response.status_code == 200:
                        registrations = response.json()
                        marked_registration = next((r for r in registrations if r['id'] == test_registration_id), None)
                        if marked_registration and marked_registration.get('payment_status') == 'completed':
                            self.test_results['audit_log_creation'] = True
                            self.log_success("Payment Status Verification", "Payment status correctly updated to 'completed'")
                            
                            # Check if audit log was created
                            if 'audit_log' in marked_registration and marked_registration['audit_log']:
                                audit_entries = marked_registration['audit_log']
                                mark_paid_entry = next((entry for entry in audit_entries if entry.get('action') == 'payment_marked_completed'), None)
                                if mark_paid_entry:
                                    self.log_success("Audit Log Verification", f"Audit log entry created by {mark_paid_entry.get('by_email')} at {mark_paid_entry.get('timestamp')}")
                                else:
                                    self.test_results['audit_log_creation'] = False
                                    self.log_error("Audit Log Verification", "No audit log entry found for mark as paid action")
                            else:
                                self.test_results['audit_log_creation'] = False
                                self.log_error("Audit Log Verification", "No audit_log field found in registration")
                        else:
                            self.test_results['audit_log_creation'] = False
                            self.log_error("Payment Status Verification", f"Payment status not updated correctly: {marked_registration.get('payment_status') if marked_registration else 'Registration not found'}")
                    else:
                        self.test_results['audit_log_creation'] = False
                        self.log_error("Payment Status Verification", f"Failed to get registrations: {response.status_code}")
                else:
                    self.test_results['mark_pending_paid'] = False
                    self.log_error("Mark Pending as Paid", f"Invalid response structure: {data}")
            else:
                self.test_results['mark_pending_paid'] = False
                self.log_error("Mark Pending as Paid", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['mark_pending_paid'] = False
            self.log_error("Mark Pending as Paid", f"Exception: {str(e)}")
        
        # Test 2: Attempt to mark already paid registration (should return 400)
        print("\n📋 Test 2: Attempt to mark already paid registration")
        try:
            response = requests.post(f"{self.base_url}/events/registrations/{test_registration_id}/mark-paid", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 400:
                data = response.json()
                if 'already marked as paid' in data.get('detail', '').lower():
                    self.test_results['already_paid_error'] = True
                    self.log_success("Already Paid Error Test", f"Correctly returns 400 for already paid registration: {data.get('detail')}")
                else:
                    self.test_results['already_paid_error'] = False
                    self.log_error("Already Paid Error Test", f"Wrong error message: {data.get('detail')}")
            else:
                self.test_results['already_paid_error'] = False
                self.log_error("Already Paid Error Test", f"Expected 400 but got {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['already_paid_error'] = False
            self.log_error("Already Paid Error Test", f"Exception: {str(e)}")
        
        # Test 3: Create a withdrawn registration and test marking it as paid (should return 400)
        print("\n📋 Test 3: Attempt to mark withdrawn registration as paid")
        try:
            # Create a separate event for withdrawal test to avoid duplicate registration issues
            future_date = (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d')
            withdrawal_test_event = {
                "name": "Withdrawal Test Event",
                "description": "Test event for withdrawal functionality",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "16:00",
                "amount": 50.0,
                "payment_type": "per_person",
                "preferences": [{"name": "Test Preference", "options": ["Option1", "Option2"]}],
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=withdrawal_test_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                withdrawal_event_id = response.json()['id']
                self.log_success("Withdrawn Test Setup", f"Created separate event for withdrawal test: {withdrawal_event_id}")
                
                # Create registration for withdrawal test
                registration_data = {
                    "event_id": withdrawal_event_id,
                    "registrants": [
                        {"name": "Test User for Withdrawal", "preferences": {"Test Preference": "Option2"}}
                    ],
                    "payment_method": "offline"
                }
                
                response = requests.post(f"{self.base_url}/events/{withdrawal_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    withdrawn_registration_id = response.json()['id']
                    self.log_success("Withdrawn Test Setup", f"Created registration for withdrawal test: {withdrawn_registration_id}")
                    
                    # Withdraw the registration
                    response = requests.post(f"{self.base_url}/events/registrations/{withdrawn_registration_id}/withdraw", 
                                           headers=self.auth_headers,
                                           timeout=10)
                    
                    if response.status_code == 200:
                        self.log_success("Withdrawn Test Setup", "Successfully withdrew registration")
                        
                        # Now try to mark the withdrawn registration as paid
                        response = requests.post(f"{self.base_url}/events/registrations/{withdrawn_registration_id}/mark-paid", 
                                               headers=self.auth_headers,
                                               timeout=10)
                        
                        if response.status_code == 400:
                            data = response.json()
                            if 'withdrawn' in data.get('detail', '').lower():
                                self.test_results['withdrawn_error'] = True
                                self.log_success("Withdrawn Registration Error Test", f"Correctly returns 400 for withdrawn registration: {data.get('detail')}")
                            else:
                                self.test_results['withdrawn_error'] = False
                                self.log_error("Withdrawn Registration Error Test", f"Wrong error message: {data.get('detail')}")
                        else:
                            self.test_results['withdrawn_error'] = False
                            self.log_error("Withdrawn Registration Error Test", f"Expected 400 but got {response.status_code}, Response: {response.text}")
                    else:
                        self.test_results['withdrawn_error'] = False
                        self.log_error("Withdrawn Test Setup", f"Failed to withdraw registration: {response.status_code}")
                        
                    # Clean up withdrawal test event
                    try:
                        requests.delete(f"{self.base_url}/events/{withdrawal_event_id}", 
                                      headers=self.auth_headers, timeout=10)
                        self.log_success("Withdrawn Test Cleanup", f"Cleaned up withdrawal test event: {withdrawal_event_id}")
                    except:
                        pass
                else:
                    self.test_results['withdrawn_error'] = False
                    self.log_error("Withdrawn Test Setup", f"Failed to create registration: {response.status_code}, Response: {response.text}")
            else:
                self.test_results['withdrawn_error'] = False
                self.log_error("Withdrawn Test Setup", f"Failed to create withdrawal test event: {response.status_code}")
        except Exception as e:
            self.test_results['withdrawn_error'] = False
            self.log_error("Withdrawn Registration Error Test", f"Exception: {str(e)}")
        
        # Test 4: Unauthorized access (should get 401/403)
        print("\n📋 Test 4: Test unauthorized access")
        try:
            # Test without authentication headers
            response = requests.post(f"{self.base_url}/events/registrations/{test_registration_id}/mark-paid", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code in [401, 403]:
                self.test_results['unauthorized_access'] = True
                self.log_success("Unauthorized Access Test", f"Correctly returns {response.status_code} for unauthorized access")
            else:
                self.test_results['unauthorized_access'] = False
                self.log_error("Unauthorized Access Test", f"Expected 401/403 but got {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['unauthorized_access'] = False
            self.log_error("Unauthorized Access Test", f"Exception: {str(e)}")
        
        # Test 5: Test with non-existent registration ID
        print("\n📋 Test 5: Test with non-existent registration ID")
        try:
            fake_registration_id = "non-existent-registration-id"
            response = requests.post(f"{self.base_url}/events/registrations/{fake_registration_id}/mark-paid", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 404:
                self.log_success("Non-existent Registration Test", "Correctly returns 404 for non-existent registration")
            else:
                self.log_error("Non-existent Registration Test", f"Expected 404 but got {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_error("Non-existent Registration Test", f"Exception: {str(e)}")
        
        # Clean up test event
        if test_event_id:
            try:
                response = requests.delete(f"{self.base_url}/events/{test_event_id}", 
                                         headers=self.auth_headers,
                                         timeout=10)
                if response.status_code == 200:
                    self.log_success("Cleanup", f"Successfully cleaned up test event: {test_event_id}")
                else:
                    self.log_error("Cleanup", f"Failed to delete test event: {response.status_code}")
            except Exception as e:
                self.log_error("Cleanup", f"Exception during cleanup: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 MARK AS PAID TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            if result is True:
                passed_tests += 1
                status = "✅ PASS"
            elif result is False:
                status = "❌ FAIL"
            else:
                status = "⏸️ SKIP"
                total_tests -= 1  # Don't count skipped tests
                continue
            
            # Format test name for display
            display_name = test_name.replace('_', ' ').title()
            print(f"  {status} - {display_name}")
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n🎉 All mark as paid tests passed successfully!")
            
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = MarkAsPaidTester()
    success = tester.test_mark_as_paid_endpoint()
    exit(0 if success else 1)