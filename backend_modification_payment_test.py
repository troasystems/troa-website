#!/usr/bin/env python3
"""
Backend API Testing for Event Registration Modification Payment Method Display Fix
Tests the specific bug fix where modification payment method was not being displayed correctly in admin portal.

Bug context:
When a user creates an event registration with online payment, and then modifies their registration 
to add more people with offline payment, the admin portal was showing "Online Payment" instead of 
"Offline Payment" for the modification.

Test scenarios:
1. Create an event registration with online payment
2. Modify the registration to add a person with offline payment
3. Verify in admin portal that:
   - The "Pending Approvals" tab shows "Offline Payment" for the modification
   - The "All Events" view shows both "Online" (original) and "Mod: Offline" (modification) badges
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troa-residence.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
ADMIN_EMAIL = "troa.systems@gmail.com"

class EventModificationPaymentTester:
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

    def create_test_event(self):
        """Create a test event for registration modification testing"""
        print("\n🎯 Step 1: Creating test event...")
        
        try:
            # Create event with per_person payment type (so modifications require additional payment)
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            event_data = {
                "name": "Payment Method Test Event",
                "description": "Test event for payment method display bug fix",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "18:00",
                "amount": 50.0,  # ₹50 per person
                "payment_type": "per_person",  # This ensures modifications require payment
                "max_registrations": 100
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=event_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                event = response.json()
                self.created_event_id = event['id']
                self.log_success("/events", "POST", f"Created test event: {event['name']} (ID: {self.created_event_id})")
                return True
            else:
                self.log_error("/events", "POST", f"Failed to create event. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error("/events", "POST", f"Exception creating event: {str(e)}")
            return False

    def create_initial_registration_online(self):
        """Create initial event registration with online payment"""
        print("\n🎯 Step 2: Creating initial registration with online payment...")
        
        if not self.created_event_id:
            self.log_error("Registration", "SETUP", "No event ID available for registration")
            return False
            
        try:
            registration_data = {
                "event_id": self.created_event_id,  # Required field
                "registrants": [
                    {
                        "name": "John Doe",
                        "preferences": {
                            "dietary": "vegetarian"
                        }
                    }
                ],
                "payment_method": "online"  # Initial registration with online payment
            }
            
            response = requests.post(f"{self.base_url}/events/{self.created_event_id}/register", 
                                   json=registration_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                registration = response.json()
                self.created_registration_id = registration['id']
                self.log_success(f"/events/{self.created_event_id}/register", "POST", 
                               f"Created initial registration with online payment (ID: {self.created_registration_id})")
                
                # Verify the registration details
                if registration.get('payment_method') == 'online':
                    self.log_success("Registration", "VERIFY", "✓ Initial payment method correctly set to 'online'")
                else:
                    self.log_error("Registration", "VERIFY", f"Expected payment_method 'online', got '{registration.get('payment_method')}'")
                    
                if registration.get('total_amount') == 50.0:
                    self.log_success("Registration", "VERIFY", "✓ Initial amount correctly calculated (₹50 for 1 person)")
                else:
                    self.log_error("Registration", "VERIFY", f"Expected total_amount 50.0, got {registration.get('total_amount')}")
                    
                return True
            else:
                self.log_error(f"/events/{self.created_event_id}/register", "POST", 
                             f"Failed to create registration. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"/events/{self.created_event_id}/register", "POST", f"Exception: {str(e)}")
            return False

    def modify_registration_offline(self):
        """Modify registration to add more people with offline payment"""
        print("\n🎯 Step 3: Modifying registration to add person with offline payment...")
        
        if not self.created_registration_id:
            self.log_error("Modification", "SETUP", "No registration ID available for modification")
            return False
            
        try:
            # Add one more person (total 2 people) with offline payment method
            modification_data = {
                "registrants": [
                    {
                        "name": "John Doe",
                        "preferences": {
                            "dietary": "vegetarian"
                        }
                    },
                    {
                        "name": "Jane Smith",  # Adding second person
                        "preferences": {
                            "dietary": "non-vegetarian"
                        }
                    }
                ],
                "payment_method": "offline"  # Modification with offline payment
            }
            
            response = requests.patch(f"{self.base_url}/events/registrations/{self.created_registration_id}/modify", 
                                    json=modification_data, 
                                    headers=self.auth_headers,
                                    timeout=10)
            
            if response.status_code == 200:
                modification_result = response.json()
                self.log_success(f"/events/registrations/{self.created_registration_id}/modify", "PATCH", 
                               "Successfully created modification request with offline payment")
                
                # Verify modification details
                if modification_result.get('payment_method') == 'offline':
                    self.log_success("Modification", "VERIFY", "✓ Modification payment method correctly set to 'offline'")
                else:
                    self.log_error("Modification", "VERIFY", f"Expected payment_method 'offline', got '{modification_result.get('payment_method')}'")
                    
                if modification_result.get('additional_amount') == 50.0:
                    self.log_success("Modification", "VERIFY", "✓ Additional amount correctly calculated (₹50 for 1 additional person)")
                else:
                    self.log_error("Modification", "VERIFY", f"Expected additional_amount 50.0, got {modification_result.get('additional_amount')}")
                    
                if modification_result.get('requires_payment') == True:
                    self.log_success("Modification", "VERIFY", "✓ Correctly requires payment for additional person")
                else:
                    self.log_error("Modification", "VERIFY", "Expected requires_payment to be True")
                    
                return True
            else:
                self.log_error(f"/events/registrations/{self.created_registration_id}/modify", "PATCH", 
                             f"Failed to modify registration. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"/events/registrations/{self.created_registration_id}/modify", "PATCH", f"Exception: {str(e)}")
            return False

    def verify_pending_approvals_display(self):
        """Verify that pending approvals show the correct modification payment method"""
        print("\n🎯 Step 4: Verifying pending approvals display modification payment method...")
        
        try:
            response = requests.get(f"{self.base_url}/events/admin/pending-approvals", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                pending_approvals = response.json()
                self.log_success("/events/admin/pending-approvals", "GET", f"Retrieved {len(pending_approvals)} pending approvals")
                
                # Find our registration in the pending approvals
                our_registration = None
                for approval in pending_approvals:
                    if approval.get('id') == self.created_registration_id:
                        our_registration = approval
                        break
                
                if our_registration:
                    self.log_success("Pending Approvals", "FIND", "✓ Found our registration in pending approvals")
                    
                    # Check if modification_payment_method is present and correct
                    modification_payment_method = our_registration.get('modification_payment_method')
                    if modification_payment_method == 'offline':
                        self.log_success("Pending Approvals", "VERIFY", "✅ BUG FIX VERIFIED: modification_payment_method correctly shows 'offline'")
                    else:
                        self.log_error("Pending Approvals", "VERIFY", f"❌ BUG NOT FIXED: modification_payment_method is '{modification_payment_method}', expected 'offline'")
                    
                    # Check original payment method is still preserved
                    original_payment_method = our_registration.get('payment_method')
                    if original_payment_method == 'online':
                        self.log_success("Pending Approvals", "VERIFY", "✓ Original payment_method correctly preserved as 'online'")
                    else:
                        self.log_error("Pending Approvals", "VERIFY", f"Original payment_method should be 'online', got '{original_payment_method}'")
                    
                    # Check modification status
                    modification_status = our_registration.get('modification_status')
                    if modification_status == 'pending_modification_approval':
                        self.log_success("Pending Approvals", "VERIFY", "✓ Modification status correctly set to 'pending_modification_approval'")
                    else:
                        self.log_error("Pending Approvals", "VERIFY", f"Expected modification_status 'pending_modification_approval', got '{modification_status}'")
                    
                    # Log all relevant fields for debugging
                    self.log_info(f"Registration fields: payment_method='{original_payment_method}', modification_payment_method='{modification_payment_method}', modification_status='{modification_status}'")
                    
                    return True
                else:
                    self.log_error("Pending Approvals", "FIND", "Our registration not found in pending approvals")
                    return False
                    
            else:
                self.log_error("/events/admin/pending-approvals", "GET", 
                             f"Failed to get pending approvals. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error("/events/admin/pending-approvals", "GET", f"Exception: {str(e)}")
            return False

    def verify_database_fields(self):
        """Verify that the database contains the correct fields"""
        print("\n🎯 Step 5: Verifying database field storage...")
        
        try:
            # Get the specific registration to check database fields
            response = requests.get(f"{self.base_url}/events/my/registrations", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                registrations = response.json()
                self.log_success("/events/my/registrations", "GET", f"Retrieved {len(registrations)} user registrations")
                
                # Find our registration
                our_registration = None
                for reg in registrations:
                    if reg.get('id') == self.created_registration_id:
                        our_registration = reg
                        break
                
                if our_registration:
                    self.log_success("Database Fields", "FIND", "✓ Found our registration in user registrations")
                    
                    # Verify key database fields
                    fields_to_check = {
                        'payment_method': 'online',  # Original payment method
                        'modification_payment_method': 'offline',  # Modification payment method
                        'modification_status': 'pending_modification_approval'  # Modification status
                    }
                    
                    all_fields_correct = True
                    for field, expected_value in fields_to_check.items():
                        actual_value = our_registration.get(field)
                        if actual_value == expected_value:
                            self.log_success("Database Fields", "VERIFY", f"✓ {field} = '{actual_value}' (correct)")
                        else:
                            self.log_error("Database Fields", "VERIFY", f"❌ {field} = '{actual_value}', expected '{expected_value}'")
                            all_fields_correct = False
                    
                    # Check additional fields
                    additional_amount = our_registration.get('additional_amount')
                    if additional_amount == 50.0:
                        self.log_success("Database Fields", "VERIFY", f"✓ additional_amount = ₹{additional_amount} (correct)")
                    else:
                        self.log_error("Database Fields", "VERIFY", f"❌ additional_amount = ₹{additional_amount}, expected ₹50.0")
                        all_fields_correct = False
                    
                    return all_fields_correct
                else:
                    self.log_error("Database Fields", "FIND", "Our registration not found in user registrations")
                    return False
                    
            else:
                self.log_error("/events/my/registrations", "GET", 
                             f"Failed to get user registrations. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error("/events/my/registrations", "GET", f"Exception: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete the test event (this will also delete registrations)
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

    def run_payment_method_display_test(self):
        """Run the complete payment method display test"""
        print("🚀 Starting Event Registration Modification Payment Method Display Test")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 80)
        
        print("\n🎯 TEST SCENARIO:")
        print("1. Create event registration with ONLINE payment")
        print("2. Modify registration to add person with OFFLINE payment")
        print("3. Verify admin portal shows OFFLINE payment for modification")
        print("4. Verify database stores both payment methods correctly")
        
        # Run test steps
        success = True
        
        # Step 1: Create test event
        if not self.create_test_event():
            success = False
            
        # Step 2: Create initial registration with online payment
        if success and not self.create_initial_registration_online():
            success = False
            
        # Step 3: Modify registration with offline payment
        if success and not self.modify_registration_offline():
            success = False
            
        # Step 4: Verify pending approvals display
        if success and not self.verify_pending_approvals_display():
            success = False
            
        # Step 5: Verify database fields
        if success and not self.verify_database_fields():
            success = False
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print results
        self.print_test_results(success)
        
        return success

    def print_test_results(self, overall_success: bool):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 PAYMENT METHOD DISPLAY TEST RESULTS")
        print("=" * 80)
        
        if overall_success:
            print("🎉 ✅ ALL TESTS PASSED - BUG FIX VERIFIED!")
            print("\n✅ The payment method display fix is working correctly:")
            print("   • Original payment method (online) is preserved")
            print("   • Modification payment method (offline) is stored separately")
            print("   • Admin portal can distinguish between original and modification payments")
            print("   • Database fields are correctly populated")
        else:
            print("❌ SOME TESTS FAILED - BUG FIX NEEDS ATTENTION")
            
        if self.errors:
            print(f"\n🚨 ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        print(f"\n📈 Test completed with {'SUCCESS' if overall_success else 'FAILURES'}")
        
        return overall_success

if __name__ == "__main__":
    tester = EventModificationPaymentTester()
    success = tester.run_payment_method_display_test()
    exit(0 if success else 1)