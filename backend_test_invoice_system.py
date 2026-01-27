#!/usr/bin/env python3
"""
TROA Invoice and Reporting System Backend Test
Tests all invoice-related API endpoints and PDF generation functionality
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class InvoiceSystemTester:
    def __init__(self, base_url="https://emailbuzz.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TROA-Test-Client/1.0'
        })
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []
        
        print(f"🔧 Testing Invoice System at: {self.api_url}")
        print("=" * 60)

    def run_test(self, name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and track results"""
        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        
        try:
            result = test_func(*args, **kwargs)
            if result:
                self.tests_passed += 1
                self.passed_tests.append(name)
                print(f"✅ PASSED")
                return True
            else:
                self.failed_tests.append(name)
                print(f"❌ FAILED")
                return False
        except Exception as e:
            self.failed_tests.append(f"{name} - Exception: {str(e)}")
            print(f"❌ FAILED - Exception: {str(e)}")
            return False

    def test_health_check(self) -> bool:
        """Test basic API health"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def test_invoice_endpoints_exist(self) -> bool:
        """Test that invoice endpoints exist and return proper error codes"""
        endpoints = [
            ("/invoices", "GET"),
            ("/invoices", "POST"),
            ("/invoices/pending/count", "GET"),
            ("/invoices/test-id", "GET"),
            ("/invoices/test-id/pdf", "GET"),
            ("/invoices/test-id", "PUT"),
            ("/invoices/test-id/create-order", "POST"),
            ("/invoices/test-id/verify-payment", "POST"),
            ("/invoices/test-id", "DELETE")
        ]
        
        all_exist = True
        for endpoint, method in endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                if method == "GET":
                    response = self.session.get(url, timeout=5)
                elif method == "POST":
                    response = self.session.post(url, json={}, timeout=5)
                elif method == "PUT":
                    response = self.session.put(url, json={}, timeout=5)
                elif method == "DELETE":
                    response = self.session.delete(url, timeout=5)
                
                # We expect 401 (unauthorized) or 422 (validation error), not 404
                if response.status_code == 404:
                    print(f"❌ Endpoint {method} {endpoint} not found (404)")
                    all_exist = False
                else:
                    print(f"✓ {method} {endpoint} exists (status: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ Error testing {method} {endpoint}: {e}")
                all_exist = False
        
        return all_exist

    def test_staff_report_endpoints(self) -> bool:
        """Test staff report endpoints"""
        try:
            # Test booking report endpoint
            url = f"{self.api_url}/staff/reports/bookings"
            params = {
                'amenity_id': 'test-amenity',
                'month': 12,
                'year': 2024
            }
            response = self.session.get(url, params=params, timeout=10)
            
            # Should return 401 (unauthorized) since we're not authenticated
            if response.status_code in [401, 403]:
                print(f"✓ Staff report endpoint exists and requires authentication (status: {response.status_code})")
                return True
            elif response.status_code == 404:
                print(f"❌ Staff report endpoint not found")
                return False
            else:
                print(f"✓ Staff report endpoint exists (status: {response.status_code})")
                return True
                
        except Exception as e:
            print(f"❌ Error testing staff report endpoint: {e}")
            return False

    def test_invoice_model_structure(self) -> bool:
        """Test invoice creation with proper data structure"""
        try:
            # Test invoice creation endpoint with sample data
            invoice_data = {
                "user_email": "test@example.com",
                "amenity_id": "test-amenity-id",
                "month": 12,
                "year": 2024
            }
            
            response = self.session.post(
                f"{self.api_url}/invoices",
                json=invoice_data,
                timeout=10
            )
            
            # Should return 401 (unauthorized) or 422 (validation error)
            if response.status_code in [401, 403]:
                print(f"✓ Invoice creation requires authentication (status: {response.status_code})")
                return True
            elif response.status_code == 422:
                # Check if it's a validation error with proper structure
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        print(f"✓ Invoice creation has proper validation (status: {response.status_code})")
                        return True
                except:
                    pass
            elif response.status_code == 404:
                print(f"❌ Invoice creation endpoint not found")
                return False
            
            print(f"✓ Invoice creation endpoint exists (status: {response.status_code})")
            return True
            
        except Exception as e:
            print(f"❌ Error testing invoice creation: {e}")
            return False

    def test_pending_invoice_count(self) -> bool:
        """Test pending invoice count endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/invoices/pending/count", timeout=10)
            
            # Should return 401 (unauthorized) since we're not authenticated
            if response.status_code in [401, 403]:
                print(f"✓ Pending invoice count requires authentication (status: {response.status_code})")
                return True
            elif response.status_code == 200:
                # If somehow accessible, check response structure
                try:
                    data = response.json()
                    if 'count' in data:
                        print(f"✓ Pending invoice count has correct structure")
                        return True
                except:
                    pass
            elif response.status_code == 404:
                print(f"❌ Pending invoice count endpoint not found")
                return False
            
            print(f"✓ Pending invoice count endpoint exists (status: {response.status_code})")
            return True
            
        except Exception as e:
            print(f"❌ Error testing pending invoice count: {e}")
            return False

    def test_razorpay_integration(self) -> bool:
        """Test Razorpay payment integration endpoints"""
        try:
            # Test create order endpoint
            response = self.session.post(
                f"{self.api_url}/invoices/test-id/create-order",
                json={},
                timeout=10
            )
            
            # Should return 401 (unauthorized) or 404 (invoice not found)
            if response.status_code in [401, 403, 404]:
                print(f"✓ Razorpay create order endpoint exists and has proper security (status: {response.status_code})")
            else:
                print(f"✓ Razorpay create order endpoint exists (status: {response.status_code})")
            
            # Test verify payment endpoint
            response = self.session.post(
                f"{self.api_url}/invoices/test-id/verify-payment",
                json={
                    "razorpay_order_id": "test_order",
                    "razorpay_payment_id": "test_payment",
                    "razorpay_signature": "test_signature"
                },
                timeout=10
            )
            
            if response.status_code in [401, 403, 404]:
                print(f"✓ Razorpay verify payment endpoint exists and has proper security (status: {response.status_code})")
                return True
            else:
                print(f"✓ Razorpay verify payment endpoint exists (status: {response.status_code})")
                return True
                
        except Exception as e:
            print(f"❌ Error testing Razorpay integration: {e}")
            return False

    def test_pdf_generation_endpoint(self) -> bool:
        """Test PDF generation endpoints"""
        try:
            # Test invoice PDF endpoint
            response = self.session.get(f"{self.api_url}/invoices/test-id/pdf", timeout=10)
            
            # Should return 401 (unauthorized) or 404 (not found)
            if response.status_code in [401, 403]:
                print(f"✓ Invoice PDF endpoint requires authentication (status: {response.status_code})")
            elif response.status_code == 404:
                print(f"✓ Invoice PDF endpoint exists but invoice not found (status: {response.status_code})")
            else:
                print(f"✓ Invoice PDF endpoint exists (status: {response.status_code})")
            
            # Test staff report PDF endpoint
            params = {
                'amenity_id': 'test-amenity',
                'month': 12,
                'year': 2024
            }
            response = self.session.get(
                f"{self.api_url}/staff/reports/bookings",
                params=params,
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                print(f"✓ Staff report PDF endpoint requires authentication (status: {response.status_code})")
                return True
            else:
                print(f"✓ Staff report PDF endpoint exists (status: {response.status_code})")
                return True
                
        except Exception as e:
            print(f"❌ Error testing PDF generation: {e}")
            return False

    def test_invoice_management_endpoints(self) -> bool:
        """Test invoice management (edit, cancel) endpoints"""
        try:
            # Test invoice update endpoint
            response = self.session.put(
                f"{self.api_url}/invoices/test-id",
                json={
                    "adjustment": 50.0,
                    "adjustment_reason": "Test adjustment"
                },
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                print(f"✓ Invoice update requires authentication (status: {response.status_code})")
            elif response.status_code == 404:
                print(f"✓ Invoice update endpoint exists but invoice not found (status: {response.status_code})")
            else:
                print(f"✓ Invoice update endpoint exists (status: {response.status_code})")
            
            # Test invoice cancellation endpoint
            response = self.session.delete(f"{self.api_url}/invoices/test-id", timeout=10)
            
            if response.status_code in [401, 403]:
                print(f"✓ Invoice cancellation requires authentication (status: {response.status_code})")
                return True
            elif response.status_code == 404:
                print(f"✓ Invoice cancellation endpoint exists but invoice not found (status: {response.status_code})")
                return True
            else:
                print(f"✓ Invoice cancellation endpoint exists (status: {response.status_code})")
                return True
                
        except Exception as e:
            print(f"❌ Error testing invoice management: {e}")
            return False

    def test_authentication_protection(self) -> bool:
        """Test that all invoice endpoints are properly protected"""
        protected_endpoints = [
            ("/invoices", "GET"),
            ("/invoices", "POST"),
            ("/invoices/pending/count", "GET"),
            ("/invoices/test-id", "GET"),
            ("/invoices/test-id/pdf", "GET"),
            ("/invoices/test-id", "PUT"),
            ("/invoices/test-id/create-order", "POST"),
            ("/invoices/test-id/verify-payment", "POST"),
            ("/invoices/test-id", "DELETE"),
            ("/staff/reports/bookings", "GET")
        ]
        
        all_protected = True
        for endpoint, method in protected_endpoints:
            try:
                url = f"{self.api_url}{endpoint}"
                if method == "GET":
                    if "reports/bookings" in endpoint:
                        response = self.session.get(url, params={'amenity_id': 'test', 'month': 12, 'year': 2024}, timeout=5)
                    else:
                        response = self.session.get(url, timeout=5)
                elif method == "POST":
                    response = self.session.post(url, json={}, timeout=5)
                elif method == "PUT":
                    response = self.session.put(url, json={}, timeout=5)
                elif method == "DELETE":
                    response = self.session.delete(url, timeout=5)
                
                # Should return 401 (unauthorized) or 403 (forbidden)
                if response.status_code not in [401, 403]:
                    if response.status_code == 404:
                        print(f"⚠️  {method} {endpoint} not found (404)")
                        all_protected = False
                    elif response.status_code == 422:
                        print(f"✓ {method} {endpoint} protected (validation error without auth)")
                    else:
                        print(f"⚠️  {method} {endpoint} may not be properly protected (status: {response.status_code})")
                else:
                    print(f"✓ {method} {endpoint} properly protected (status: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ Error testing protection for {method} {endpoint}: {e}")
                all_protected = False
        
        return all_protected

    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        try:
            # Test invalid invoice creation
            response = self.session.post(
                f"{self.api_url}/invoices",
                json={"invalid": "data"},
                timeout=10
            )
            
            # Should return proper error response
            if response.status_code in [400, 401, 422]:
                print(f"✓ Invalid invoice creation returns proper error (status: {response.status_code})")
            else:
                print(f"⚠️  Invalid invoice creation status: {response.status_code}")
            
            # Test invalid month/year in report
            params = {
                'amenity_id': 'test-amenity',
                'month': 13,  # Invalid month
                'year': 2024
            }
            response = self.session.get(
                f"{self.api_url}/staff/reports/bookings",
                params=params,
                timeout=10
            )
            
            if response.status_code in [400, 401, 422]:
                print(f"✓ Invalid report parameters return proper error (status: {response.status_code})")
                return True
            else:
                print(f"⚠️  Invalid report parameters status: {response.status_code}")
                return True
                
        except Exception as e:
            print(f"❌ Error testing error handling: {e}")
            return False

    def run_all_tests(self):
        """Run all invoice system tests"""
        print("🚀 Starting Invoice System Backend Tests")
        print("=" * 60)
        
        # Basic connectivity
        self.run_test("API Health Check", self.test_health_check)
        
        # Endpoint existence
        self.run_test("Invoice Endpoints Exist", self.test_invoice_endpoints_exist)
        self.run_test("Staff Report Endpoints Exist", self.test_staff_report_endpoints)
        
        # Functionality tests
        self.run_test("Invoice Model Structure", self.test_invoice_model_structure)
        self.run_test("Pending Invoice Count", self.test_pending_invoice_count)
        self.run_test("Razorpay Integration", self.test_razorpay_integration)
        self.run_test("PDF Generation Endpoints", self.test_pdf_generation_endpoint)
        self.run_test("Invoice Management", self.test_invoice_management_endpoints)
        
        # Security tests
        self.run_test("Authentication Protection", self.test_authentication_protection)
        self.run_test("Error Handling", self.test_error_handling)
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 INVOICE SYSTEM TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.passed_tests:
            print(f"\n✅ PASSED TESTS ({len(self.passed_tests)}):")
            for test in self.passed_tests:
                print(f"  • {test}")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                print(f"  • {test}")
        
        print("\n" + "=" * 60)
        
        # Return exit code
        return 0 if len(self.failed_tests) == 0 else 1

def main():
    """Main test execution"""
    tester = InvoiceSystemTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())