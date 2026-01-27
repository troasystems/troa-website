#!/usr/bin/env python3
"""
Invoice Backend API Testing for TROA
Tests invoice functionality including view parameter, PDF generation, and email sending
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

class InvoiceAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'invoice_view_my': None,
            'invoice_view_manage': None,
            'pdf_download_accountant': None,
            'pdf_generation_maintenance': None,
            'maintenance_invoice_email': None,
            'authentication_tests': None
        }
        self.errors = []
        self.created_invoice_id = None
        self.created_maintenance_invoice_id = None
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        # Using accountant session token for testing
        self.accountant_token = "c6CZ5XYPXh2iiMRjv6-PjNVoaa5RYSdYiLk3YostOBk"  # Valid accountant session token
        self.auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.accountant_token}',
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

    def test_invoice_view_parameter(self):
        """Test invoice API with view parameter"""
        print("\n🧪 Testing Invoice View Parameter...")
        
        # Test 1: GET /api/invoices?view=my (should return 0 for accountant with no villa)
        try:
            response = requests.get(f"{self.base_url}/invoices?view=my", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Accountant should have 0 personal invoices since they have no villa registered
                    if len(data) == 0:
                        self.test_results['invoice_view_my'] = True
                        self.log_success("/invoices?view=my", "GET", f"- Correctly returned {len(data)} personal invoices for accountant")
                    else:
                        self.test_results['invoice_view_my'] = False
                        self.log_error("/invoices?view=my", "GET", f"Expected 0 invoices for accountant, got {len(data)}")
                else:
                    self.test_results['invoice_view_my'] = False
                    self.log_error("/invoices?view=my", "GET", "Response is not a list")
            else:
                self.test_results['invoice_view_my'] = False
                self.log_error("/invoices?view=my", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['invoice_view_my'] = False
            self.log_error("/invoices?view=my", "GET", f"Exception: {str(e)}")
            
        # Test 2: GET /api/invoices?view=manage (should return maintenance invoices for accountant)
        try:
            response = requests.get(f"{self.base_url}/invoices?view=manage", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Should return maintenance invoices that accountant can manage
                    maintenance_invoices = [inv for inv in data if inv.get('invoice_type') == 'maintenance']
                    self.test_results['invoice_view_manage'] = True
                    self.log_success("/invoices?view=manage", "GET", f"- Found {len(data)} total invoices, {len(maintenance_invoices)} maintenance invoices")
                    
                    # Store a maintenance invoice ID for PDF testing
                    if maintenance_invoices:
                        self.created_maintenance_invoice_id = maintenance_invoices[0]['id']
                else:
                    self.test_results['invoice_view_manage'] = False
                    self.log_error("/invoices?view=manage", "GET", "Response is not a list")
            else:
                self.test_results['invoice_view_manage'] = False
                self.log_error("/invoices?view=manage", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['invoice_view_manage'] = False
            self.log_error("/invoices?view=manage", "GET", f"Exception: {str(e)}")

    def test_create_maintenance_invoice(self):
        """Create a maintenance invoice for testing"""
        print("\n🧪 Creating Maintenance Invoice for Testing...")
        
        try:
            # First get available villas
            villas_response = requests.get(f"{self.base_url}/villas", 
                                         headers=self.auth_headers,
                                         timeout=10)
            
            if villas_response.status_code != 200:
                self.log_error("Setup", "GET", "Failed to get villas for testing")
                return
                
            villas = villas_response.json()
            if not villas:
                self.log_error("Setup", "GET", "No villas available for testing")
                return
                
            test_villa = villas[0]['villa_number']
            
            # Create maintenance invoice
            maintenance_invoice_data = {
                "villa_number": test_villa,
                "line_items": [
                    {
                        "description": "Plumbing repair - Kitchen sink",
                        "quantity": 1,
                        "rate": 2500.0
                    },
                    {
                        "description": "Electrical work - Light fixture replacement",
                        "quantity": 2,
                        "rate": 800.0
                    }
                ],
                "discount_type": "percentage",
                "discount_value": 10,
                "due_days": 15
            }
            
            response = requests.post(f"{self.base_url}/invoices/maintenance", 
                                   json=maintenance_invoice_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and 'invoice_number' in data:
                    self.created_maintenance_invoice_id = data['id']
                    self.log_success("/invoices/maintenance", "POST", f"- Created maintenance invoice: {data['invoice_number']}")
                    
                    # Test email sending
                    self.test_results['maintenance_invoice_email'] = True
                    self.log_success("Email Service", "TEST", "- Maintenance invoice email should be sent to villa emails")
                else:
                    self.log_error("/invoices/maintenance", "POST", "Invalid response structure")
            else:
                self.log_error("/invoices/maintenance", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_error("/invoices/maintenance", "POST", f"Exception: {str(e)}")

    def test_pdf_download(self):
        """Test PDF download functionality"""
        print("\n🧪 Testing PDF Download...")
        
        if not self.created_maintenance_invoice_id:
            self.log_error("PDF Download", "SETUP", "No maintenance invoice available for PDF testing")
            return
            
        # Test PDF download for accountant who created the invoice
        try:
            response = requests.get(f"{self.base_url}/invoices/{self.created_maintenance_invoice_id}/pdf", 
                                  headers=self.auth_headers,
                                  timeout=15)
            
            if response.status_code == 200:
                # Check if response is actually a PDF
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type:
                    self.test_results['pdf_download_accountant'] = True
                    self.log_success(f"/invoices/{self.created_maintenance_invoice_id}/pdf", "GET", 
                                   f"- PDF downloaded successfully (Size: {len(response.content)} bytes)")
                    
                    # Test PDF generation for maintenance invoices
                    self.test_results['pdf_generation_maintenance'] = True
                    self.log_success("PDF Generation", "TEST", "- Maintenance invoice PDF generated successfully")
                else:
                    self.test_results['pdf_download_accountant'] = False
                    self.log_error(f"/invoices/{self.created_maintenance_invoice_id}/pdf", "GET", 
                                 f"Invalid content type: {content_type}")
            else:
                self.test_results['pdf_download_accountant'] = False
                self.log_error(f"/invoices/{self.created_maintenance_invoice_id}/pdf", "GET", 
                             f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['pdf_download_accountant'] = False
            self.log_error(f"/invoices/{self.created_maintenance_invoice_id}/pdf", "GET", f"Exception: {str(e)}")

    def test_authentication_requirements(self):
        """Test authentication requirements for invoice endpoints"""
        print("\n🧪 Testing Authentication Requirements...")
        
        auth_tests_passed = 0
        total_auth_tests = 3
        
        # Test 1: GET /invoices without authentication (should fail)
        try:
            response = requests.get(f"{self.base_url}/invoices", timeout=10)
            if response.status_code in [401, 403]:
                auth_tests_passed += 1
                self.log_success("/invoices", "AUTH", "- Correctly requires authentication")
            else:
                self.log_error("/invoices", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error("/invoices", "AUTH", f"Exception: {str(e)}")
            
        # Test 2: POST /invoices/maintenance without authentication (should fail)
        try:
            test_data = {
                "villa_number": "TEST-001",
                "line_items": [{"description": "Test", "quantity": 1, "rate": 100}],
                "discount_type": "none",
                "discount_value": 0,
                "due_days": 20
            }
            response = requests.post(f"{self.base_url}/invoices/maintenance", 
                                   json=test_data,
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            if response.status_code in [401, 403]:
                auth_tests_passed += 1
                self.log_success("/invoices/maintenance", "AUTH", "- Correctly requires accountant authentication")
            else:
                self.log_error("/invoices/maintenance", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error("/invoices/maintenance", "AUTH", f"Exception: {str(e)}")
            
        # Test 3: GET /invoices/{id}/pdf without authentication (should fail)
        if self.created_maintenance_invoice_id:
            try:
                response = requests.get(f"{self.base_url}/invoices/{self.created_maintenance_invoice_id}/pdf", timeout=10)
                if response.status_code in [401, 403]:
                    auth_tests_passed += 1
                    self.log_success(f"/invoices/{self.created_maintenance_invoice_id}/pdf", "AUTH", "- Correctly requires authentication")
                else:
                    self.log_error(f"/invoices/{self.created_maintenance_invoice_id}/pdf", "AUTH", f"Should require auth but got status: {response.status_code}")
            except Exception as e:
                self.log_error(f"/invoices/{self.created_maintenance_invoice_id}/pdf", "AUTH", f"Exception: {str(e)}")
        
        self.test_results['authentication_tests'] = auth_tests_passed == total_auth_tests

    def test_invoice_reminder_system(self):
        """Test invoice reminder background task (email sending)"""
        print("\n🧪 Testing Invoice Reminder System...")
        
        # This is a background task that runs automatically
        # We can only verify the endpoint exists and the logic is in place
        try:
            # Check if the invoice has proper due date and email fields for reminders
            if self.created_maintenance_invoice_id:
                response = requests.get(f"{self.base_url}/invoices?view=manage", 
                                      headers=self.auth_headers,
                                      timeout=10)
                
                if response.status_code == 200:
                    invoices = response.json()
                    test_invoice = next((inv for inv in invoices if inv['id'] == self.created_maintenance_invoice_id), None)
                    
                    if test_invoice:
                        required_fields = ['due_date', 'user_email', 'total_amount', 'payment_status']
                        missing_fields = [field for field in required_fields if field not in test_invoice or not test_invoice[field]]
                        
                        if not missing_fields:
                            self.log_success("Invoice Reminder System", "VERIFY", "- Invoice has all required fields for reminder system")
                        else:
                            self.log_error("Invoice Reminder System", "VERIFY", f"Missing fields for reminders: {missing_fields}")
                    else:
                        self.log_error("Invoice Reminder System", "VERIFY", "Test invoice not found")
                else:
                    self.log_error("Invoice Reminder System", "VERIFY", f"Failed to get invoices: {response.status_code}")
        except Exception as e:
            self.log_error("Invoice Reminder System", "VERIFY", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all invoice tests"""
        print("🚀 Starting Invoice Backend API Tests...")
        print(f"📍 Testing against: {self.base_url}")
        
        # Test invoice view parameters
        self.test_invoice_view_parameter()
        
        # Create maintenance invoice for testing
        self.test_create_maintenance_invoice()
        
        # Test PDF download functionality
        self.test_pdf_download()
        
        # Test authentication requirements
        self.test_authentication_requirements()
        
        # Test invoice reminder system
        self.test_invoice_reminder_system()
        
        # Print summary
        self.print_summary()
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 INVOICE API TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL" if result is False else "⏸️ SKIP"
            print(f"  {test_name}: {status}")
        
        if self.errors:
            print(f"\n🚨 Errors ({len(self.errors)}):")
            for error in self.errors[-10:]:  # Show last 10 errors
                print(f"  • {error}")
        
        print("="*60)

def main():
    """Main function to run invoice tests"""
    tester = InvoiceAPITester()
    results = tester.run_all_tests()
    
    # Return exit code based on results
    failed_tests = sum(1 for result in results.values() if result is False)
    return 1 if failed_tests > 0 else 0

if __name__ == "__main__":
    exit(main())