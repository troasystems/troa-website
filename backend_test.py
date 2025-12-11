#!/usr/bin/env python3
"""
Backend API Testing for TROA (The Retreat Owners Association) Website
Tests all backend APIs including Committee Members, Amenities, Gallery, and Membership Application endpoints.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tenant-assist-6.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class TROAAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'committee': {'get': None, 'post': None},
            'amenities': {'get': None, 'post': None},
            'gallery': {'get': None, 'post': None},
            'membership': {'get': None, 'post': None}
        }
        self.errors = []
        
    def log_error(self, endpoint: str, method: str, error: str):
        """Log errors for detailed reporting"""
        error_msg = f"{method.upper()} {endpoint}: {error}"
        self.errors.append(error_msg)
        print(f"❌ {error_msg}")
        
    def log_success(self, endpoint: str, method: str, message: str = ""):
        """Log successful tests"""
        success_msg = f"{method.upper()} {endpoint}: SUCCESS {message}"
        print(f"✅ {success_msg}")
        
    def test_committee_members(self):
        """Test Committee Members API endpoints"""
        print("\n🧪 Testing Committee Members API...")
        
        # Test GET /api/committee
        try:
            response = requests.get(f"{self.base_url}/committee", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['committee']['get'] = True
                    self.log_success("/committee", "GET", f"- Found {len(data)} committee members")
                    
                    # Validate structure of first member if exists
                    if data:
                        member = data[0]
                        required_fields = ['id', 'name', 'position', 'image', 'created_at']
                        missing_fields = [field for field in required_fields if field not in member]
                        if missing_fields:
                            self.log_error("/committee", "GET", f"Missing required fields: {missing_fields}")
                            self.test_results['committee']['get'] = False
                else:
                    self.test_results['committee']['get'] = False
                    self.log_error("/committee", "GET", "Response is not a list")
            else:
                self.test_results['committee']['get'] = False
                self.log_error("/committee", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['committee']['get'] = False
            self.log_error("/committee", "GET", f"Exception: {str(e)}")
            
        # Test POST /api/committee
        try:
            test_member = {
                "name": "Sarah Johnson",
                "position": "Community Manager", 
                "image": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400",
                "facebook": "https://facebook.com/sarah.johnson",
                "twitter": "https://twitter.com/sarahjohnson",
                "linkedin": "https://linkedin.com/in/sarah-johnson"
            }
            
            response = requests.post(f"{self.base_url}/committee", 
                                   json=test_member, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data['name'] == test_member['name']:
                    self.test_results['committee']['post'] = True
                    self.log_success("/committee", "POST", f"- Created member with ID: {data['id']}")
                else:
                    self.test_results['committee']['post'] = False
                    self.log_error("/committee", "POST", "Invalid response structure")
            else:
                self.test_results['committee']['post'] = False
                self.log_error("/committee", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['committee']['post'] = False
            self.log_error("/committee", "POST", f"Exception: {str(e)}")
            
    def test_amenities(self):
        """Test Amenities API endpoints"""
        print("\n🧪 Testing Amenities API...")
        
        # Test GET /api/amenities
        try:
            response = requests.get(f"{self.base_url}/amenities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['amenities']['get'] = True
                    self.log_success("/amenities", "GET", f"- Found {len(data)} amenities")
                    
                    # Validate structure if data exists
                    if data:
                        amenity = data[0]
                        required_fields = ['id', 'name', 'description', 'image', 'created_at']
                        missing_fields = [field for field in required_fields if field not in amenity]
                        if missing_fields:
                            self.log_error("/amenities", "GET", f"Missing required fields: {missing_fields}")
                            self.test_results['amenities']['get'] = False
                else:
                    self.test_results['amenities']['get'] = False
                    self.log_error("/amenities", "GET", "Response is not a list")
            else:
                self.test_results['amenities']['get'] = False
                self.log_error("/amenities", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['amenities']['get'] = False
            self.log_error("/amenities", "GET", f"Exception: {str(e)}")
            
        # Test POST /api/amenities
        try:
            test_amenity = {
                "name": "Infinity Pool",
                "description": "A stunning infinity pool overlooking the ocean with crystal clear waters and comfortable lounging areas.",
                "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800"
            }
            
            response = requests.post(f"{self.base_url}/amenities", 
                                   json=test_amenity, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data['name'] == test_amenity['name']:
                    self.test_results['amenities']['post'] = True
                    self.log_success("/amenities", "POST", f"- Created amenity with ID: {data['id']}")
                else:
                    self.test_results['amenities']['post'] = False
                    self.log_error("/amenities", "POST", "Invalid response structure")
            else:
                self.test_results['amenities']['post'] = False
                self.log_error("/amenities", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['amenities']['post'] = False
            self.log_error("/amenities", "POST", f"Exception: {str(e)}")
            
    def test_gallery(self):
        """Test Gallery API endpoints"""
        print("\n🧪 Testing Gallery API...")
        
        # Test GET /api/gallery
        try:
            response = requests.get(f"{self.base_url}/gallery", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['gallery']['get'] = True
                    self.log_success("/gallery", "GET", f"- Found {len(data)} gallery images")
                    
                    # Validate structure if data exists
                    if data:
                        image = data[0]
                        required_fields = ['id', 'title', 'category', 'url', 'created_at']
                        missing_fields = [field for field in required_fields if field not in image]
                        if missing_fields:
                            self.log_error("/gallery", "GET", f"Missing required fields: {missing_fields}")
                            self.test_results['gallery']['get'] = False
                else:
                    self.test_results['gallery']['get'] = False
                    self.log_error("/gallery", "GET", "Response is not a list")
            else:
                self.test_results['gallery']['get'] = False
                self.log_error("/gallery", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['gallery']['get'] = False
            self.log_error("/gallery", "GET", f"Exception: {str(e)}")
            
        # Test POST /api/gallery
        try:
            test_image = {
                "title": "Sunset Villa View",
                "category": "Exterior",
                "url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800"
            }
            
            response = requests.post(f"{self.base_url}/gallery", 
                                   json=test_image, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data['title'] == test_image['title']:
                    self.test_results['gallery']['post'] = True
                    self.log_success("/gallery", "POST", f"- Created gallery image with ID: {data['id']}")
                else:
                    self.test_results['gallery']['post'] = False
                    self.log_error("/gallery", "POST", "Invalid response structure")
            else:
                self.test_results['gallery']['post'] = False
                self.log_error("/gallery", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['gallery']['post'] = False
            self.log_error("/gallery", "POST", f"Exception: {str(e)}")
            
    def test_membership(self):
        """Test Membership Application API endpoints"""
        print("\n🧪 Testing Membership Application API...")
        
        # Test POST /api/membership first (create before get)
        try:
            test_application = {
                "firstName": "Michael",
                "lastName": "Rodriguez",
                "email": "michael.rodriguez@email.com",
                "phone": "+1-555-0123",
                "villaNo": "Villa-42",
                "message": "I am interested in joining TROA and would like to learn more about the community benefits and activities."
            }
            
            response = requests.post(f"{self.base_url}/membership", 
                                   json=test_application, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data['email'] == test_application['email']:
                    self.test_results['membership']['post'] = True
                    self.log_success("/membership", "POST", f"- Created application with ID: {data['id']}")
                else:
                    self.test_results['membership']['post'] = False
                    self.log_error("/membership", "POST", "Invalid response structure")
            else:
                self.test_results['membership']['post'] = False
                self.log_error("/membership", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['membership']['post'] = False
            self.log_error("/membership", "POST", f"Exception: {str(e)}")
            
        # Test GET /api/membership
        try:
            response = requests.get(f"{self.base_url}/membership", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['membership']['get'] = True
                    self.log_success("/membership", "GET", f"- Found {len(data)} membership applications")
                    
                    # Validate structure if data exists
                    if data:
                        app = data[0]
                        required_fields = ['id', 'firstName', 'email', 'phone', 'villaNo', 'status', 'created_at']
                        missing_fields = [field for field in required_fields if field not in app]
                        if missing_fields:
                            self.log_error("/membership", "GET", f"Missing required fields: {missing_fields}")
                            self.test_results['membership']['get'] = False
                else:
                    self.test_results['membership']['get'] = False
                    self.log_error("/membership", "GET", "Response is not a list")
            else:
                self.test_results['membership']['get'] = False
                self.log_error("/membership", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['membership']['get'] = False
            self.log_error("/membership", "GET", f"Exception: {str(e)}")
            
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        print("\n🧪 Testing Root API endpoint...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'TROA' in data['message']:
                    self.log_success("/", "GET", "- Root endpoint working")
                    return True
                else:
                    self.log_error("/", "GET", "Invalid response format")
                    return False
            else:
                self.log_error("/", "GET", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_error("/", "GET", f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting TROA Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test root endpoint first
        self.test_root_endpoint()
        
        # Test all endpoints
        self.test_committee_members()
        self.test_amenities()
        self.test_gallery()
        self.test_membership()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for endpoint, methods in self.test_results.items():
            for method, result in methods.items():
                total_tests += 1
                if result:
                    passed_tests += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                print(f"{status} - {method.upper()} /api/{endpoint}")
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n🎉 All tests passed successfully!")
            
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = TROAAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)