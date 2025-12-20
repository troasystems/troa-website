#!/usr/bin/env python3
"""
Backend API Testing for Event Registration Modification Admin Approval Flow
Tests the complete flow including admin approval of offline modification payments.
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://villa-manager-13.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
ADMIN_EMAIL = "troa.systems@gmail.com"

class EventModificationApprovalTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.errors = []
        self.created_event_id = None
        self.created_registration_id = None
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.session_token = "Pb9guhRQHpv1_efx7KeNLcDqxEZiUssG8ODNENQI_jY"  # Valid admin session token
        self.auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.session_token}',
            'Content-Type': 'application/json'
        }
        
    def log_success(self, endpoint: str, method: str, message: str):
        """Log successful test result"""
        print(f"✅ {method} {endpoint}: {message}")
        
    def log_error(self, endpoint: str, method: str, message: str):
        """Log error and add to errors list"""
        error_msg = f"{method} {endpoint}: {message}"
        print(f"❌ {error_msg}")
        self.errors.append(error_msg)
        
    def log_info(self, message: str):
        """Log informational message"""
        print(f"ℹ️  {message}")

    def create_test_scenario(self):
        """Create the complete test scenario: event + registration + modification"""
        print("\n🎯 Setting up test scenario...")
        
        # Step 1: Create event
        try:
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            event_data = {
                "name": "Approval Flow Test Event",
                "description": "Test event for admin approval flow",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "19:00",
                "amount": 75.0,  # ₹75 per person
                "payment_type": "per_person",
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=event_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                event = response.json()
                self.created_event_id = event['id']
                self.log_success("/events", "POST", f"Created test event (ID: {self.created_event_id})")
            else:
                self.log_error("/events", "POST", f"Failed to create event. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("/events", "POST", f"Exception: {str(e)}")
            return False

        # Step 2: Create initial registration with online payment
        try:
            registration_data = {
                "event_id": self.created_event_id,
                "registrants": [
                    {
                        "name": "Alice Johnson",
                        "preferences": {
                            "dietary": "vegan"
                        }
                    }
                ],
                "payment_method": "online"
            }
            
            response = requests.post(f"{self.base_url}/events/{self.created_event_id}/register", 
                                   json=registration_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                registration = response.json()
                self.created_registration_id = registration['id']
                self.log_success(f"/events/{self.created_event_id}/register", "POST", 
                               f"Created initial registration (ID: {self.created_registration_id})")
            else:
                self.log_error(f"/events/{self.created_event_id}/register", "POST", 
                             f"Failed to create registration. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"/events/{self.created_event_id}/register", "POST", f"Exception: {str(e)}")
            return False

        # Step 3: Modify registration to add people with offline payment
        try:
            modification_data = {
                "registrants": [
                    {
                        "name": "Alice Johnson",
                        "preferences": {
                            "dietary": "vegan"
                        }
                    },
                    {
                        "name": "Bob Wilson",
                        "preferences": {
                            "dietary": "vegetarian"
                        }
                    },
                    {
                        "name": "Carol Davis",
                        "preferences": {
                            "dietary": "non-vegetarian"
                        }
                    }
                ],
                "payment_method": "offline"  # Offline payment for modification
            }
            
            response = requests.patch(f"{self.base_url}/events/registrations/{self.created_registration_id}/modify", 
                                    json=modification_data, 
                                    headers=self.auth_headers,
                                    timeout=10)
            
            if response.status_code == 200:
                modification_result = response.json()
                self.log_success(f"/events/registrations/{self.created_registration_id}/modify", "PATCH", 
                               f"Created modification request (adding 2 people, ₹{modification_result.get('additional_amount', 0)})")
            else:
                self.log_error(f"/events/registrations/{self.created_registration_id}/modify", "PATCH", 
                             f"Failed to modify registration. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"/events/registrations/{self.created_registration_id}/modify", "PATCH", f"Exception: {str(e)}")
            return False

        return True

    def test_admin_approval_flow(self):
        """Test the admin approval flow for offline modification payments"""
        print("\n🎯 Testing admin approval flow...")
        
        # Step 1: Verify modification appears in pending approvals
        try:
            response = requests.get(f"{self.base_url}/events/admin/pending-approvals", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                pending_approvals = response.json()
                self.log_success("/events/admin/pending-approvals", "GET", f"Retrieved {len(pending_approvals)} pending approvals")
                
                # Find our registration
                our_registration = None
                for approval in pending_approvals:
                    if approval.get('id') == self.created_registration_id:
                        our_registration = approval
                        break
                
                if not our_registration:
                    self.log_error("Pending Approvals", "FIND", "Our registration not found in pending approvals")
                    return False
                    
                # Verify it's a modification (not initial registration)
                if our_registration.get('modification_status') == 'pending_modification_approval':
                    self.log_success("Pending Approvals", "VERIFY", "✓ Registration correctly marked as pending modification approval")
                else:
                    self.log_error("Pending Approvals", "VERIFY", f"Expected modification_status 'pending_modification_approval', got '{our_registration.get('modification_status')}'")
                    return False
                    
            else:
                self.log_error("/events/admin/pending-approvals", "GET", f"Failed to get pending approvals. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("/events/admin/pending-approvals", "GET", f"Exception: {str(e)}")
            return False

        # Step 2: Approve the modification
        try:
            response = requests.post(f"{self.base_url}/events/registrations/{self.created_registration_id}/approve-modification", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                self.log_success(f"/events/registrations/{self.created_registration_id}/approve-modification", "POST", 
                               "Successfully approved offline modification payment")
            else:
                self.log_error(f"/events/registrations/{self.created_registration_id}/approve-modification", "POST", 
                             f"Failed to approve modification. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"/events/registrations/{self.created_registration_id}/approve-modification", "POST", f"Exception: {str(e)}")
            return False

        # Step 3: Verify modification is no longer in pending approvals
        try:
            response = requests.get(f"{self.base_url}/events/admin/pending-approvals", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                pending_approvals = response.json()
                
                # Our registration should not be in pending approvals anymore
                found_in_pending = False
                for approval in pending_approvals:
                    if approval.get('id') == self.created_registration_id:
                        found_in_pending = True
                        break
                
                if not found_in_pending:
                    self.log_success("Pending Approvals", "VERIFY", "✓ Registration no longer in pending approvals after approval")
                else:
                    self.log_error("Pending Approvals", "VERIFY", "Registration still in pending approvals after approval")
                    return False
                    
            else:
                self.log_error("/events/admin/pending-approvals", "GET", f"Failed to get pending approvals. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("/events/admin/pending-approvals", "GET", f"Exception: {str(e)}")
            return False

        # Step 4: Verify the registration has been updated with approved modification
        try:
            response = requests.get(f"{self.base_url}/events/my/registrations", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                registrations = response.json()
                
                # Find our registration
                our_registration = None
                for reg in registrations:
                    if reg.get('id') == self.created_registration_id:
                        our_registration = reg
                        break
                
                if our_registration:
                    # Verify the modification has been applied
                    registrants = our_registration.get('registrants', [])
                    if len(registrants) == 3:
                        self.log_success("Registration Update", "VERIFY", f"✓ Registration now has {len(registrants)} people (modification applied)")
                        
                        # Check names
                        names = [r.get('name') for r in registrants]
                        expected_names = ['Alice Johnson', 'Bob Wilson', 'Carol Davis']
                        if all(name in names for name in expected_names):
                            self.log_success("Registration Update", "VERIFY", "✓ All expected registrants present")
                        else:
                            self.log_error("Registration Update", "VERIFY", f"Expected names {expected_names}, got {names}")
                            return False
                    else:
                        self.log_error("Registration Update", "VERIFY", f"Expected 3 registrants, got {len(registrants)}")
                        return False
                    
                    # Verify total amount has been updated
                    total_amount = our_registration.get('total_amount')
                    expected_amount = 75.0 * 3  # ₹75 per person × 3 people
                    if total_amount == expected_amount:
                        self.log_success("Registration Update", "VERIFY", f"✓ Total amount updated to ₹{total_amount}")
                    else:
                        self.log_error("Registration Update", "VERIFY", f"Expected total_amount ₹{expected_amount}, got ₹{total_amount}")
                        return False
                    
                    # Verify modification fields are cleared
                    if not our_registration.get('modification_status'):
                        self.log_success("Registration Update", "VERIFY", "✓ Modification status cleared after approval")
                    else:
                        self.log_error("Registration Update", "VERIFY", f"Modification status should be cleared, got '{our_registration.get('modification_status')}'")
                        return False
                        
                else:
                    self.log_error("Registration Update", "FIND", "Our registration not found in user registrations")
                    return False
                    
            else:
                self.log_error("/events/my/registrations", "GET", f"Failed to get user registrations. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("/events/my/registrations", "GET", f"Exception: {str(e)}")
            return False

        return True

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        if self.created_event_id:
            try:
                response = requests.delete(f"{self.base_url}/events/{self.created_event_id}", 
                                         headers=self.auth_headers,
                                         timeout=10)
                if response.status_code == 200:
                    self.log_success(f"/events/{self.created_event_id}", "DELETE", "Test event and registrations cleaned up")
                else:
                    self.log_error(f"/events/{self.created_event_id}", "DELETE", f"Failed to delete test event. Status: {response.status_code}")
            except Exception as e:
                self.log_error(f"/events/{self.created_event_id}", "DELETE", f"Exception: {str(e)}")

    def run_approval_flow_test(self):
        """Run the complete admin approval flow test"""
        print("🚀 Starting Event Registration Modification Admin Approval Flow Test")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        print("\n🎯 TEST SCENARIO:")
        print("1. Create event registration with ONLINE payment (1 person)")
        print("2. Modify registration to add 2 more people with OFFLINE payment")
        print("3. Verify modification appears in admin pending approvals")
        print("4. Admin approves the offline modification payment")
        print("5. Verify modification is applied and no longer pending")
        
        # Run test steps
        success = True
        
        # Setup test scenario
        if not self.create_test_scenario():
            success = False
            
        # Test admin approval flow
        if success and not self.test_admin_approval_flow():
            success = False
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print results
        self.print_test_results(success)
        
        return success

    def print_test_results(self, overall_success: bool):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 ADMIN APPROVAL FLOW TEST RESULTS")
        print("=" * 80)
        
        if overall_success:
            print("🎉 ✅ ALL TESTS PASSED - ADMIN APPROVAL FLOW WORKING!")
            print("\n✅ The complete modification approval flow is working correctly:")
            print("   • Offline modifications appear in pending approvals")
            print("   • Admin can approve offline modification payments")
            print("   • Approved modifications are applied to registrations")
            print("   • Modification fields are properly cleared after approval")
            print("   • Total amounts are correctly updated")
        else:
            print("❌ SOME TESTS FAILED - APPROVAL FLOW NEEDS ATTENTION")
            
        if self.errors:
            print(f"\n🚨 ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        print(f"\n📈 Test completed with {'SUCCESS' if overall_success else 'FAILURES'}")
        
        return overall_success

if __name__ == "__main__":
    tester = EventModificationApprovalTester()
    success = tester.run_approval_flow_test()
    exit(0 if success else 1)