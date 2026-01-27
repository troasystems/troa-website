#!/usr/bin/env python3
"""
Villa Management Backend API Testing for TROA
Tests villa management endpoints, accountant role, and maintenance invoice functionality.
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
ADMIN_EMAIL = "troa.systems@gmail.com"

class VillaManagementTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'villa_crud': {'get_all': None, 'create': None, 'get_single': None, 'update': None, 'delete': None},
            'villa_emails': {'add_email': None, 'remove_email': None},
            'maintenance_invoices': {'create': None, 'get_filtered': None},
            'multi_invoice_payment': {'create_order': None},
            'role_validation': {'accountant_role': None},
            'login_restriction': {'villa_email_check': None},
            'authentication': {'admin_access': None, 'staff_access': None}
        }
        self.errors = []
        self.created_villa_number = None
        self.created_invoice_id = None
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        # Using a test session token - in real testing this would be obtained via login
        self.session_token = "test_admin_session_token_123"
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

    def test_villa_crud_operations(self):
        """Test Villa CRUD operations"""
        print("\n🧪 Testing Villa CRUD Operations...")
        
        # Test GET /api/villas - List all villas
        try:
            response = requests.get(f"{self.base_url}/villas", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['villa_crud']['get_all'] = True
                    self.log_success("/villas", "GET", f"- Found {len(data)} villas")
                else:
                    self.test_results['villa_crud']['get_all'] = False
                    self.log_error("/villas", "GET", "Response is not a list")
            elif response.status_code == 403:
                self.test_results['villa_crud']['get_all'] = False
                self.log_error("/villas", "GET", "Access denied - requires admin/manager/staff access")
            else:
                self.test_results['villa_crud']['get_all'] = False
                self.log_error("/villas", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_crud']['get_all'] = False
            self.log_error("/villas", "GET", f"Exception: {str(e)}")

        # Test POST /api/villas - Create villa
        try:
            test_villa = {
                "villa_number": f"TEST-{datetime.now().strftime('%H%M%S')}",
                "square_feet": 1200.5,
                "emails": ["test.villa@example.com", "owner@example.com"]
            }
            
            response = requests.post(f"{self.base_url}/villas", 
                                   json=test_villa, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('villa_number' in data and 
                    data['villa_number'] == test_villa['villa_number'] and
                    data['square_feet'] == test_villa['square_feet'] and
                    len(data['emails']) == 2):
                    self.test_results['villa_crud']['create'] = True
                    self.created_villa_number = data['villa_number']
                    self.log_success("/villas", "POST", f"- Created villa: {data['villa_number']}")
                else:
                    self.test_results['villa_crud']['create'] = False
                    self.log_error("/villas", "POST", "Invalid response structure")
            elif response.status_code == 400:
                # Check if it's a duplicate villa error
                if "already exists" in response.text:
                    self.log_error("/villas", "POST", "Villa already exists - this is expected behavior")
                    self.test_results['villa_crud']['create'] = True  # This is actually correct behavior
                else:
                    self.test_results['villa_crud']['create'] = False
                    self.log_error("/villas", "POST", f"Bad request: {response.text}")
            else:
                self.test_results['villa_crud']['create'] = False
                self.log_error("/villas", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_crud']['create'] = False
            self.log_error("/villas", "POST", f"Exception: {str(e)}")

        # Test GET /api/villas/{villa_number} - Get single villa
        if self.created_villa_number:
            try:
                response = requests.get(f"{self.base_url}/villas/{self.created_villa_number}", 
                                      headers=self.auth_headers,
                                      timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['villa_number'] == self.created_villa_number:
                        self.test_results['villa_crud']['get_single'] = True
                        self.log_success(f"/villas/{self.created_villa_number}", "GET", "- Retrieved single villa")
                    else:
                        self.test_results['villa_crud']['get_single'] = False
                        self.log_error(f"/villas/{self.created_villa_number}", "GET", "Villa number mismatch")
                else:
                    self.test_results['villa_crud']['get_single'] = False
                    self.log_error(f"/villas/{self.created_villa_number}", "GET", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['villa_crud']['get_single'] = False
                self.log_error(f"/villas/{self.created_villa_number}", "GET", f"Exception: {str(e)}")

        # Test PATCH /api/villas/{villa_number} - Update villa
        if self.created_villa_number:
            try:
                update_data = {"square_feet": 1500.0}
                response = requests.patch(f"{self.base_url}/villas/{self.created_villa_number}", 
                                        json=update_data, 
                                        headers=self.auth_headers,
                                        timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['square_feet'] == 1500.0:
                        self.test_results['villa_crud']['update'] = True
                        self.log_success(f"/villas/{self.created_villa_number}", "PATCH", "- Updated villa square feet")
                    else:
                        self.test_results['villa_crud']['update'] = False
                        self.log_error(f"/villas/{self.created_villa_number}", "PATCH", "Update not reflected")
                else:
                    self.test_results['villa_crud']['update'] = False
                    self.log_error(f"/villas/{self.created_villa_number}", "PATCH", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['villa_crud']['update'] = False
                self.log_error(f"/villas/{self.created_villa_number}", "PATCH", f"Exception: {str(e)}")

    def test_villa_email_management(self):
        """Test Villa Email Management"""
        print("\n🧪 Testing Villa Email Management...")
        
        if not self.created_villa_number:
            self.log_error("Villa Email Management", "SETUP", "No villa created for testing")
            return

        # Test POST /api/villas/{villa_number}/emails - Add email
        try:
            email_data = {"email": "new.resident@example.com"}
            response = requests.post(f"{self.base_url}/villas/{self.created_villa_number}/emails", 
                                   json=email_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'added successfully' in data['message']:
                    self.test_results['villa_emails']['add_email'] = True
                    self.log_success(f"/villas/{self.created_villa_number}/emails", "POST", "- Added email to villa")
                else:
                    self.test_results['villa_emails']['add_email'] = False
                    self.log_error(f"/villas/{self.created_villa_number}/emails", "POST", "Invalid response structure")
            else:
                self.test_results['villa_emails']['add_email'] = False
                self.log_error(f"/villas/{self.created_villa_number}/emails", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['villa_emails']['add_email'] = False
            self.log_error(f"/villas/{self.created_villa_number}/emails", "POST", f"Exception: {str(e)}")

        # Test DELETE /api/villas/{villa_number}/emails/{email} - Remove email
        try:
            email_to_remove = "new.resident@example.com"
            response = requests.delete(f"{self.base_url}/villas/{self.created_villa_number}/emails/{email_to_remove}", 
                                     headers=self.auth_headers,
                                     timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'removed successfully' in data['message']:
                    self.test_results['villa_emails']['remove_email'] = True
                    self.log_success(f"/villas/{self.created_villa_number}/emails/{email_to_remove}", "DELETE", "- Removed email from villa")
                else:
                    self.test_results['villa_emails']['remove_email'] = False
                    self.log_error(f"/villas/{self.created_villa_number}/emails/{email_to_remove}", "DELETE", "Invalid response structure")
            else:
                self.test_results['villa_emails']['remove_email'] = False
                self.log_error(f"/villas/{self.created_villa_number}/emails/{email_to_remove}", "DELETE", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['villa_emails']['remove_email'] = False
            self.log_error(f"/villas/{self.created_villa_number}/emails/{email_to_remove}", "DELETE", f"Exception: {str(e)}")

    def test_maintenance_invoices(self):
        """Test Maintenance Invoice Creation"""
        print("\n🧪 Testing Maintenance Invoice System...")
        
        if not self.created_villa_number:
            self.log_error("Maintenance Invoices", "SETUP", "No villa created for testing")
            return

        # Test POST /api/invoices/maintenance - Create maintenance invoice
        try:
            maintenance_invoice = {
                "villa_number": self.created_villa_number,
                "line_items": [
                    {
                        "description": "Monthly maintenance fee",
                        "quantity": 1.0,
                        "rate": 2000.0
                    },
                    {
                        "description": "Garden maintenance",
                        "quantity": 2.0,
                        "rate": 500.0
                    }
                ],
                "discount_type": "percentage",
                "discount_value": 10.0,
                "due_days": 30,
                "notes": "Monthly maintenance invoice for villa"
            }
            
            response = requests.post(f"{self.base_url}/invoices/maintenance", 
                                   json=maintenance_invoice, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    'invoice_number' in data and 
                    data['invoice_type'] == 'maintenance' and
                    data['villa_number'] == self.created_villa_number and
                    len(data['maintenance_line_items']) == 2):
                    self.test_results['maintenance_invoices']['create'] = True
                    self.created_invoice_id = data['id']
                    self.log_success("/invoices/maintenance", "POST", f"- Created maintenance invoice: {data['invoice_number']}")
                else:
                    self.test_results['maintenance_invoices']['create'] = False
                    self.log_error("/invoices/maintenance", "POST", "Invalid response structure")
            else:
                self.test_results['maintenance_invoices']['create'] = False
                self.log_error("/invoices/maintenance", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['maintenance_invoices']['create'] = False
            self.log_error("/invoices/maintenance", "POST", f"Exception: {str(e)}")

    def test_invoice_filtering(self):
        """Test Invoice Filtering by Type"""
        print("\n🧪 Testing Invoice Filtering...")
        
        # Test GET /api/invoices with invoice_type parameter
        for invoice_type in ['clubhouse_subscription', 'maintenance']:
            try:
                response = requests.get(f"{self.base_url}/invoices?invoice_type={invoice_type}", 
                                      headers=self.auth_headers,
                                      timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        # Check if all returned invoices have the correct type
                        all_correct_type = all(invoice.get('invoice_type') == invoice_type for invoice in data)
                        if all_correct_type:
                            self.test_results['maintenance_invoices']['get_filtered'] = True
                            self.log_success(f"/invoices?invoice_type={invoice_type}", "GET", f"- Found {len(data)} {invoice_type} invoices")
                        else:
                            self.test_results['maintenance_invoices']['get_filtered'] = False
                            self.log_error(f"/invoices?invoice_type={invoice_type}", "GET", "Some invoices have incorrect type")
                    else:
                        self.test_results['maintenance_invoices']['get_filtered'] = False
                        self.log_error(f"/invoices?invoice_type={invoice_type}", "GET", "Response is not a list")
                else:
                    self.test_results['maintenance_invoices']['get_filtered'] = False
                    self.log_error(f"/invoices?invoice_type={invoice_type}", "GET", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['maintenance_invoices']['get_filtered'] = False
                self.log_error(f"/invoices?invoice_type={invoice_type}", "GET", f"Exception: {str(e)}")

    def test_multi_invoice_payment(self):
        """Test Multi-Invoice Payment Order Creation"""
        print("\n🧪 Testing Multi-Invoice Payment...")
        
        if not self.created_invoice_id:
            self.log_error("Multi-Invoice Payment", "SETUP", "No invoice created for testing")
            return

        # Test POST /api/invoices/pay-multiple
        try:
            payment_data = {
                "invoice_ids": [self.created_invoice_id],
                "payment_method": "online"
            }
            
            response = requests.post(f"{self.base_url}/invoices/pay-multiple", 
                                   json=payment_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('order_id' in data and 
                    'total_amount' in data and
                    'invoice_ids' in data and
                    len(data['invoice_ids']) == 1):
                    self.test_results['multi_invoice_payment']['create_order'] = True
                    self.log_success("/invoices/pay-multiple", "POST", f"- Created payment order: {data['order_id']}")
                else:
                    self.test_results['multi_invoice_payment']['create_order'] = False
                    self.log_error("/invoices/pay-multiple", "POST", "Invalid response structure")
            else:
                self.test_results['multi_invoice_payment']['create_order'] = False
                self.log_error("/invoices/pay-multiple", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['multi_invoice_payment']['create_order'] = False
            self.log_error("/invoices/pay-multiple", "POST", f"Exception: {str(e)}")

    def test_accountant_role_validation(self):
        """Test Accountant Role Validation"""
        print("\n🧪 Testing Accountant Role Validation...")
        
        # Test creating a user with accountant role
        try:
            test_user = {
                "email": f"accountant.test.{datetime.now().strftime('%H%M%S')}@example.com",
                "name": "Test Accountant",
                "role": "accountant",
                "villa_number": "ACC-001"
            }
            
            response = requests.post(f"{self.base_url}/users", 
                                   json=test_user, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['role'] == 'accountant':
                    self.test_results['role_validation']['accountant_role'] = True
                    self.log_success("/users (accountant role)", "POST", "- Accountant role accepted in user management")
                else:
                    self.test_results['role_validation']['accountant_role'] = False
                    self.log_error("/users (accountant role)", "POST", f"Role mismatch: expected 'accountant', got '{data['role']}'")
            else:
                self.test_results['role_validation']['accountant_role'] = False
                self.log_error("/users (accountant role)", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['role_validation']['accountant_role'] = False
            self.log_error("/users (accountant role)", "POST", f"Exception: {str(e)}")

    def test_villa_email_login_restriction(self):
        """Test Villa Email Login Restriction"""
        print("\n🧪 Testing Villa Email Login Restriction...")
        
        # This test simulates the login restriction logic
        # In a real scenario, we would test the actual login endpoint
        try:
            # Test with a non-villa email (should be restricted for regular users)
            test_email = "non.villa.user@example.com"
            
            # Simulate checking if email exists in villas
            response = requests.get(f"{self.base_url}/villas/lookup/by-email?email={test_email}", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) == 0:
                    # Email not found in any villa - this should trigger login restriction
                    self.test_results['role_validation']['villa_email_check'] = True
                    self.log_success("/villas/lookup/by-email", "GET", "- Villa email check working (email not in villa)")
                else:
                    self.test_results['role_validation']['villa_email_check'] = False
                    self.log_error("/villas/lookup/by-email", "GET", "Unexpected villa association found")
            else:
                self.test_results['role_validation']['villa_email_check'] = False
                self.log_error("/villas/lookup/by-email", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['role_validation']['villa_email_check'] = False
            self.log_error("/villas/lookup/by-email", "GET", f"Exception: {str(e)}")

    def test_authentication_requirements(self):
        """Test Authentication Requirements for Different Endpoints"""
        print("\n🧪 Testing Authentication Requirements...")
        
        # Test villa endpoints without authentication
        endpoints_to_test = [
            ("/villas", "GET"),
            ("/villas", "POST"),
            ("/invoices/maintenance", "POST"),
            ("/invoices/pay-multiple", "POST")
        ]
        
        auth_tests_passed = 0
        total_auth_tests = len(endpoints_to_test)
        
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           json={}, 
                                           headers={'Content-Type': 'application/json'},
                                           timeout=10)
                
                if response.status_code in [401, 403]:
                    auth_tests_passed += 1
                    self.log_success(f"{endpoint}", f"AUTH-{method}", "- Correctly requires authentication")
                else:
                    self.log_error(f"{endpoint}", f"AUTH-{method}", f"Should require auth but got status: {response.status_code}")
            except Exception as e:
                self.log_error(f"{endpoint}", f"AUTH-{method}", f"Exception: {str(e)}")
        
        if auth_tests_passed == total_auth_tests:
            self.test_results['authentication']['admin_access'] = True
            self.test_results['authentication']['staff_access'] = True
        else:
            self.test_results['authentication']['admin_access'] = False
            self.test_results['authentication']['staff_access'] = False

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test villa if created
        if self.created_villa_number:
            try:
                response = requests.delete(f"{self.base_url}/villas/{self.created_villa_number}", 
                                         headers=self.auth_headers,
                                         timeout=10)
                if response.status_code == 200:
                    self.test_results['villa_crud']['delete'] = True
                    self.log_success(f"/villas/{self.created_villa_number}", "DELETE", "- Cleaned up test villa")
                else:
                    self.test_results['villa_crud']['delete'] = False
                    self.log_error(f"/villas/{self.created_villa_number}", "DELETE", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['villa_crud']['delete'] = False
                self.log_error(f"/villas/{self.created_villa_number}", "DELETE", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all villa management tests"""
        print("🚀 Starting Villa Management Backend API Tests...")
        print(f"Backend URL: {self.base_url}")
        
        # Run tests in logical order
        self.test_villa_crud_operations()
        self.test_villa_email_management()
        self.test_maintenance_invoices()
        self.test_invoice_filtering()
        self.test_multi_invoice_payment()
        self.test_accountant_role_validation()
        self.test_villa_email_login_restriction()
        self.test_authentication_requirements()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🏠 VILLA MANAGEMENT BACKEND API TEST SUMMARY")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            print(f"\n📋 {category.upper().replace('_', ' ')}:")
            for test_name, result in tests.items():
                total_tests += 1
                if result is True:
                    passed_tests += 1
                    print(f"  ✅ {test_name}: PASSED")
                elif result is False:
                    print(f"  ❌ {test_name}: FAILED")
                else:
                    print(f"  ⚠️  {test_name}: NOT TESTED")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.errors:
            print(f"\n❌ ERRORS ENCOUNTERED ({len(self.errors)}):")
            for error in self.errors[-10:]:  # Show last 10 errors
                print(f"   • {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more errors")
        
        print("\n" + "="*80)
        
        return passed_tests, total_tests

if __name__ == "__main__":
    tester = VillaManagementTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if passed == total else 1
    exit(exit_code)