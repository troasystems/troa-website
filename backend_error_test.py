#!/usr/bin/env python3
"""
Backend API Error Handling Tests for TROA
Tests error scenarios and validation for all endpoints.
"""

import requests
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troa-residence.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class TROAErrorTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.errors_found = []
        
    def log_result(self, test_name: str, expected: bool, actual: bool, details: str = ""):
        """Log test results"""
        if expected == actual:
            print(f"✅ {test_name}: PASS {details}")
        else:
            error_msg = f"❌ {test_name}: FAIL - Expected {expected}, got {actual} {details}"
            print(error_msg)
            self.errors_found.append(error_msg)
            
    def test_invalid_endpoints(self):
        """Test invalid endpoints return 404"""
        print("\n🧪 Testing Invalid Endpoints...")
        
        invalid_endpoints = [
            "/api/invalid",
            "/api/committee/invalid",
            "/api/nonexistent"
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                expected_404 = response.status_code == 404
                self.log_result(f"GET {endpoint}", True, expected_404, f"(Status: {response.status_code})")
            except Exception as e:
                self.log_result(f"GET {endpoint}", True, False, f"Exception: {str(e)}")
                
    def test_invalid_post_data(self):
        """Test POST endpoints with invalid data"""
        print("\n🧪 Testing Invalid POST Data...")
        
        # Test committee with missing required fields
        try:
            invalid_member = {"name": "Test"}  # Missing position and image
            response = requests.post(f"{self.base_url}/committee", 
                                   json=invalid_member, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            expected_error = response.status_code in [400, 422]  # Validation error
            self.log_result("POST /committee (invalid data)", True, expected_error, 
                          f"(Status: {response.status_code})")
        except Exception as e:
            self.log_result("POST /committee (invalid data)", True, False, f"Exception: {str(e)}")
            
        # Test amenity with missing required fields
        try:
            invalid_amenity = {"name": "Test"}  # Missing description and image
            response = requests.post(f"{self.base_url}/amenities", 
                                   json=invalid_amenity, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            expected_error = response.status_code in [400, 422]
            self.log_result("POST /amenities (invalid data)", True, expected_error, 
                          f"(Status: {response.status_code})")
        except Exception as e:
            self.log_result("POST /amenities (invalid data)", True, False, f"Exception: {str(e)}")
            
        # Test gallery with missing required fields
        try:
            invalid_image = {"title": "Test"}  # Missing category and url
            response = requests.post(f"{self.base_url}/gallery", 
                                   json=invalid_image, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            expected_error = response.status_code in [400, 422]
            self.log_result("POST /gallery (invalid data)", True, expected_error, 
                          f"(Status: {response.status_code})")
        except Exception as e:
            self.log_result("POST /gallery (invalid data)", True, False, f"Exception: {str(e)}")
            
        # Test membership with invalid email
        try:
            invalid_application = {
                "firstName": "Test",
                "email": "invalid-email",  # Invalid email format
                "phone": "123",
                "villaNo": "V1"
            }
            response = requests.post(f"{self.base_url}/membership", 
                                   json=invalid_application, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            expected_error = response.status_code in [400, 422]
            self.log_result("POST /membership (invalid email)", True, expected_error, 
                          f"(Status: {response.status_code})")
        except Exception as e:
            self.log_result("POST /membership (invalid email)", True, False, f"Exception: {str(e)}")
            
    def test_empty_post_data(self):
        """Test POST endpoints with empty data"""
        print("\n🧪 Testing Empty POST Data...")
        
        endpoints = ["/committee", "/amenities", "/gallery", "/membership"]
        
        for endpoint in endpoints:
            try:
                response = requests.post(f"{self.base_url}{endpoint}", 
                                       json={}, 
                                       headers={'Content-Type': 'application/json'},
                                       timeout=10)
                expected_error = response.status_code in [400, 422]
                self.log_result(f"POST {endpoint} (empty data)", True, expected_error, 
                              f"(Status: {response.status_code})")
            except Exception as e:
                self.log_result(f"POST {endpoint} (empty data)", True, False, f"Exception: {str(e)}")
                
    def test_malformed_json(self):
        """Test endpoints with malformed JSON"""
        print("\n🧪 Testing Malformed JSON...")
        
        endpoints = ["/committee", "/amenities", "/gallery", "/membership"]
        
        for endpoint in endpoints:
            try:
                response = requests.post(f"{self.base_url}{endpoint}", 
                                       data="invalid json", 
                                       headers={'Content-Type': 'application/json'},
                                       timeout=10)
                expected_error = response.status_code in [400, 422]
                self.log_result(f"POST {endpoint} (malformed JSON)", True, expected_error, 
                              f"(Status: {response.status_code})")
            except Exception as e:
                self.log_result(f"POST {endpoint} (malformed JSON)", True, False, f"Exception: {str(e)}")
                
    def run_all_tests(self):
        """Run all error handling tests"""
        print(f"🚀 Starting TROA Backend Error Handling Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        self.test_invalid_endpoints()
        self.test_invalid_post_data()
        self.test_empty_post_data()
        self.test_malformed_json()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 ERROR HANDLING TEST SUMMARY")
        print("=" * 60)
        
        if self.errors_found:
            print(f"🚨 ISSUES FOUND ({len(self.errors_found)}):")
            for error in self.errors_found:
                print(f"   • {error}")
        else:
            print("🎉 All error handling tests passed!")
            
        return len(self.errors_found) == 0

if __name__ == "__main__":
    tester = TROAErrorTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)