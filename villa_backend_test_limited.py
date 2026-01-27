#!/usr/bin/env python3
"""
Villa Management Backend API Testing for TROA - Authentication Limited Version
Tests what can be verified without valid authentication credentials.
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

class VillaManagementTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'endpoint_existence': {},
            'authentication_requirements': {},
            'api_structure': {},
            'public_endpoints': {}
        }
        self.errors = []
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
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

    def test_api_basic_structure(self):
        """Test basic API structure and availability"""
        print("\n🧪 Testing API Basic Structure...")
        
        # Test root API endpoint
        try:
            response = requests.get(f"{self.base_url}/", 
                                  headers={'Authorization': f'Basic {self.basic_auth}'},
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'TROA' in data['message']:
                    self.test_results['api_structure']['root_endpoint'] = True
                    self.log_success("/", "GET", "- API root endpoint working")
                else:
                    self.test_results['api_structure']['root_endpoint'] = False
                    self.log_error("/", "GET", "Invalid response format")
            else:
                self.test_results['api_structure']['root_endpoint'] = False
                self.log_error("/", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['api_structure']['root_endpoint'] = False
            self.log_error("/", "GET", f"Exception: {str(e)}")

        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.test_results['api_structure']['health_endpoint'] = True
                self.log_success("/health", "GET", "- Health endpoint working")
            else:
                self.test_results['api_structure']['health_endpoint'] = False
                self.log_error("/health", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['api_structure']['health_endpoint'] = False
            self.log_error("/health", "GET", f"Exception: {str(e)}")

    def test_villa_endpoints_existence(self):
        """Test that villa management endpoints exist and return proper authentication errors"""
        print("\n🧪 Testing Villa Endpoints Existence...")
        
        villa_endpoints = [
            ("/villas", "GET", "List all villas"),
            ("/villas", "POST", "Create villa"),
            ("/villas/TEST-123", "GET", "Get single villa"),
            ("/villas/TEST-123", "PATCH", "Update villa"),
            ("/villas/TEST-123/emails", "POST", "Add email to villa"),
            ("/villas/TEST-123/emails/test@example.com", "DELETE", "Remove email from villa"),
            ("/villas/lookup/by-email", "GET", "Lookup villa by email")
        ]
        
        for endpoint, method, description in villa_endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", 
                                          headers={'Authorization': f'Basic {self.basic_auth}'},
                                          timeout=10)
                elif method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           json={}, 
                                           headers=self.auth_headers,
                                           timeout=10)
                elif method == "PATCH":
                    response = requests.patch(f"{self.base_url}{endpoint}", 
                                            json={}, 
                                            headers=self.auth_headers,
                                            timeout=10)
                elif method == "DELETE":
                    response = requests.delete(f"{self.base_url}{endpoint}", 
                                             headers=self.auth_headers,
                                             timeout=10)
                
                # Check if endpoint exists (not 404) and requires authentication (401/403)
                if response.status_code == 404:
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = False
                    self.log_error(f"{endpoint}", method, f"Endpoint not found (404) - {description}")
                elif response.status_code in [401, 403]:
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = True
                    self.test_results['authentication_requirements'][f"{method} {endpoint}"] = True
                    self.log_success(f"{endpoint}", method, f"- Endpoint exists and requires auth - {description}")
                elif response.status_code == 422:
                    # Validation error - endpoint exists but data is invalid
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = True
                    self.test_results['authentication_requirements'][f"{method} {endpoint}"] = False
                    self.log_success(f"{endpoint}", method, f"- Endpoint exists (validation error) - {description}")
                else:
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = True
                    self.test_results['authentication_requirements'][f"{method} {endpoint}"] = False
                    self.log_success(f"{endpoint}", method, f"- Endpoint exists (status: {response.status_code}) - {description}")
                    
            except Exception as e:
                self.test_results['endpoint_existence'][f"{method} {endpoint}"] = False
                self.log_error(f"{endpoint}", method, f"Exception: {str(e)}")

    def test_invoice_endpoints_existence(self):
        """Test that invoice management endpoints exist"""
        print("\n🧪 Testing Invoice Endpoints Existence...")
        
        invoice_endpoints = [
            ("/invoices", "GET", "Get invoices with filtering"),
            ("/invoices/maintenance", "POST", "Create maintenance invoice"),
            ("/invoices/pay-multiple", "POST", "Multi-invoice payment order")
        ]
        
        for endpoint, method, description in invoice_endpoints:
            try:
                if method == "GET":
                    # Test with invoice_type parameter
                    response = requests.get(f"{self.base_url}{endpoint}?invoice_type=maintenance", 
                                          headers={'Authorization': f'Basic {self.basic_auth}'},
                                          timeout=10)
                elif method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           json={}, 
                                           headers=self.auth_headers,
                                           timeout=10)
                
                if response.status_code == 404:
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = False
                    self.log_error(f"{endpoint}", method, f"Endpoint not found (404) - {description}")
                elif response.status_code in [401, 403]:
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = True
                    self.test_results['authentication_requirements'][f"{method} {endpoint}"] = True
                    self.log_success(f"{endpoint}", method, f"- Endpoint exists and requires auth - {description}")
                elif response.status_code == 422:
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = True
                    self.log_success(f"{endpoint}", method, f"- Endpoint exists (validation error) - {description}")
                else:
                    self.test_results['endpoint_existence'][f"{method} {endpoint}"] = True
                    self.log_success(f"{endpoint}", method, f"- Endpoint exists (status: {response.status_code}) - {description}")
                    
            except Exception as e:
                self.test_results['endpoint_existence'][f"{method} {endpoint}"] = False
                self.log_error(f"{endpoint}", method, f"Exception: {str(e)}")

    def test_user_management_endpoints(self):
        """Test user management endpoints for accountant role validation"""
        print("\n🧪 Testing User Management Endpoints...")
        
        try:
            # Test POST /api/users (should require admin auth)
            test_user = {
                "email": "test.accountant@example.com",
                "name": "Test Accountant",
                "role": "accountant",
                "villa_number": "ACC-001"
            }
            
            response = requests.post(f"{self.base_url}/users", 
                                   json=test_user, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 404:
                self.test_results['endpoint_existence']['POST /users'] = False
                self.log_error("/users", "POST", "User management endpoint not found")
            elif response.status_code in [401, 403]:
                self.test_results['endpoint_existence']['POST /users'] = True
                self.test_results['authentication_requirements']['POST /users'] = True
                self.log_success("/users", "POST", "- User management endpoint exists and requires admin auth")
            elif response.status_code == 422:
                self.test_results['endpoint_existence']['POST /users'] = True
                self.log_success("/users", "POST", "- User management endpoint exists (validation error)")
            else:
                self.test_results['endpoint_existence']['POST /users'] = True
                self.log_success("/users", "POST", f"- User management endpoint exists (status: {response.status_code})")
                
        except Exception as e:
            self.test_results['endpoint_existence']['POST /users'] = False
            self.log_error("/users", "POST", f"Exception: {str(e)}")

    def test_public_endpoints(self):
        """Test public endpoints that should work without authentication"""
        print("\n🧪 Testing Public Endpoints...")
        
        public_endpoints = [
            ("/amenities", "GET", "Get amenities"),
            ("/committee", "GET", "Get committee members"),
            ("/gallery", "GET", "Get gallery images"),
            ("/events", "GET", "Get events")
        ]
        
        for endpoint, method, description in public_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      headers={'Authorization': f'Basic {self.basic_auth}'},
                                      timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self.test_results['public_endpoints'][f"{method} {endpoint}"] = True
                        self.log_success(f"{endpoint}", method, f"- {description} working, found {len(data)} items")
                    else:
                        self.test_results['public_endpoints'][f"{method} {endpoint}"] = False
                        self.log_error(f"{endpoint}", method, f"Invalid response format for {description}")
                else:
                    self.test_results['public_endpoints'][f"{method} {endpoint}"] = False
                    self.log_error(f"{endpoint}", method, f"Status code: {response.status_code} for {description}")
                    
            except Exception as e:
                self.test_results['public_endpoints'][f"{method} {endpoint}"] = False
                self.log_error(f"{endpoint}", method, f"Exception: {str(e)}")

    def test_authentication_behavior(self):
        """Test authentication behavior and error messages"""
        print("\n🧪 Testing Authentication Behavior...")
        
        # Test login endpoint
        try:
            login_data = {
                "email": "test@example.com",
                "password": "wrongpassword"
            }
            
            response = requests.post(f"{self.base_url}/auth/login", 
                                   json=login_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 401:
                data = response.json()
                if 'detail' in data:
                    self.test_results['authentication_requirements']['login_error_handling'] = True
                    self.log_success("/auth/login", "POST", "- Login endpoint properly handles invalid credentials")
                else:
                    self.test_results['authentication_requirements']['login_error_handling'] = False
                    self.log_error("/auth/login", "POST", "Invalid error response format")
            else:
                self.test_results['authentication_requirements']['login_error_handling'] = False
                self.log_error("/auth/login", "POST", f"Unexpected status code: {response.status_code}")
                
        except Exception as e:
            self.test_results['authentication_requirements']['login_error_handling'] = False
            self.log_error("/auth/login", "POST", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all available tests"""
        print("🚀 Starting Villa Management Backend API Tests (Authentication Limited)...")
        print(f"Backend URL: {self.base_url}")
        
        # Run tests in logical order
        self.test_api_basic_structure()
        self.test_public_endpoints()
        self.test_villa_endpoints_existence()
        self.test_invoice_endpoints_existence()
        self.test_user_management_endpoints()
        self.test_authentication_behavior()
        
        # Print summary
        return self.print_summary()

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
        if total_tests > 0:
            print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        else:
            print(f"   Success Rate: 0.0%")
        
        print(f"\n🔍 ANALYSIS:")
        endpoint_count = len([k for k in self.test_results.get('endpoint_existence', {}) if self.test_results['endpoint_existence'][k]])
        auth_count = len([k for k in self.test_results.get('authentication_requirements', {}) if self.test_results['authentication_requirements'][k]])
        
        print(f"   Villa Management Endpoints Found: {endpoint_count}")
        print(f"   Endpoints Requiring Authentication: {auth_count}")
        print(f"   Public Endpoints Working: {len([k for k in self.test_results.get('public_endpoints', {}) if self.test_results['public_endpoints'][k]])}")
        
        if self.errors:
            print(f"\n❌ ERRORS ENCOUNTERED ({len(self.errors)}):")
            for error in self.errors[-5:]:  # Show last 5 errors
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   ... and {len(self.errors) - 5} more errors")
        
        print("\n🎯 CONCLUSIONS:")
        if endpoint_count >= 7:  # Expected villa management endpoints
            print("   ✅ Villa management endpoints are implemented")
        else:
            print("   ❌ Some villa management endpoints may be missing")
            
        if auth_count >= 5:  # Most endpoints should require auth
            print("   ✅ Authentication requirements are properly implemented")
        else:
            print("   ⚠️  Authentication requirements may need review")
        
        print("\n" + "="*80)
        
        return passed_tests, total_tests

if __name__ == "__main__":
    tester = VillaManagementTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if passed >= total * 0.7 else 1  # 70% success rate threshold
    exit(exit_code)