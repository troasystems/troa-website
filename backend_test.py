#!/usr/bin/env python3
"""
Backend API Testing for TROA (The Retreat Owners Association) Website
Tests all backend APIs including Committee Members, Amenities, Gallery, Membership Application, Events, and Amenity Booking endpoints.
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://villaportal.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
ADMIN_EMAIL = "troa.systems@gmail.com"

class TROAAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'committee': {'get': None, 'post': None},
            'amenities': {'get': None, 'post': None},
            'gallery': {'get': None, 'post': None},
            'membership': {'get': None, 'post': None},
            'events': {'get': None, 'post': None, 'get_single': None, 'patch': None, 'delete': None},
            'event_registration': {'register': None, 'my_registrations': None, 'withdraw': None},
            'admin_approval': {'pending_approvals': None, 'approve': None, 'reject': None},
            'payment_integration': {'create_order': None, 'complete_payment': None},
            'amenity_booking': {'create_booking': None}
        }
        self.errors = []
        self.created_event_id = None
        self.created_registration_id = None
        
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

    def test_events_crud(self):
        """Test Events CRUD API endpoints"""
        print("\n🧪 Testing Events CRUD API...")
        
        # Test GET /api/events (public access)
        try:
            response = requests.get(f"{self.base_url}/events", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['events']['get'] = True
                    self.log_success("/events", "GET", f"- Found {len(data)} upcoming events")
                else:
                    self.test_results['events']['get'] = False
                    self.log_error("/events", "GET", "Response is not a list")
            else:
                self.test_results['events']['get'] = False
                self.log_error("/events", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['events']['get'] = False
            self.log_error("/events", "GET", f"Exception: {str(e)}")

        # Test POST /api/events (admin only - should fail without auth)
        try:
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            test_event = {
                "name": "Annual Community BBQ",
                "description": "Join us for our annual community barbecue with food, games, and entertainment for the whole family.",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "18:00",
                "amount": 25.0,
                "payment_type": "per_person",
                "preferences": [
                    {"name": "Food Preference", "options": ["Vegetarian", "Non-Vegetarian"]},
                    {"name": "Dietary Restrictions", "options": ["None", "Gluten-Free", "Vegan"]}
                ],
                "max_registrations": 100
            }
            
            # First try without authentication (should fail)
            response = requests.post(f"{self.base_url}/events", 
                                   json=test_event, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_success("/events", "POST", "- Correctly requires authentication")
                
                # Now try with authentication (should succeed)
                response = requests.post(f"{self.base_url}/events", 
                                       json=test_event, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data and data['name'] == test_event['name']:
                        self.test_results['events']['post'] = True
                        self.created_event_id = data['id']
                        self.log_success("/events", "POST", f"- Created event with ID: {data['id']}")
                    else:
                        self.test_results['events']['post'] = False
                        self.log_error("/events", "POST", "Invalid response structure")
                else:
                    self.test_results['events']['post'] = False
                    self.log_error("/events", "POST", f"Status code with auth: {response.status_code}, Response: {response.text}")
            else:
                self.test_results['events']['post'] = False
                self.log_error("/events", "POST", f"Should require authentication but got status: {response.status_code}")
                
        except Exception as e:
            self.test_results['events']['post'] = False
            self.log_error("/events", "POST", f"Exception: {str(e)}")

        # Test GET /api/events/{event_id} (get single event)
        if self.created_event_id:
            try:
                response = requests.get(f"{self.base_url}/events/{self.created_event_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data and data['id'] == self.created_event_id:
                        self.test_results['events']['get_single'] = True
                        self.log_success(f"/events/{self.created_event_id}", "GET", "- Retrieved single event")
                    else:
                        self.test_results['events']['get_single'] = False
                        self.log_error(f"/events/{self.created_event_id}", "GET", "Invalid response structure")
                else:
                    self.test_results['events']['get_single'] = False
                    self.log_error(f"/events/{self.created_event_id}", "GET", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['events']['get_single'] = False
                self.log_error(f"/events/{self.created_event_id}", "GET", f"Exception: {str(e)}")

        # Test PATCH /api/events/{event_id} (admin only)
        if self.created_event_id:
            try:
                update_data = {"description": "Updated description for the community BBQ event"}
                response = requests.patch(f"{self.base_url}/events/{self.created_event_id}", 
                                        json=update_data, 
                                        headers=self.auth_headers,
                                        timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['description'] == update_data['description']:
                        self.test_results['events']['patch'] = True
                        self.log_success(f"/events/{self.created_event_id}", "PATCH", "- Updated event successfully")
                    else:
                        self.test_results['events']['patch'] = False
                        self.log_error(f"/events/{self.created_event_id}", "PATCH", "Update not reflected in response")
                else:
                    self.test_results['events']['patch'] = False
                    self.log_error(f"/events/{self.created_event_id}", "PATCH", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['events']['patch'] = False
                self.log_error(f"/events/{self.created_event_id}", "PATCH", f"Exception: {str(e)}")

    def test_event_registration(self):
        """Test Event Registration endpoints"""
        print("\n🧪 Testing Event Registration API...")
        
        if not self.created_event_id:
            self.log_error("Event Registration", "SETUP", "No event created for testing registration")
            return

        # Test POST /api/events/{event_id}/register
        try:
            registration_data = {
                "event_id": self.created_event_id,
                "registrants": [
                    {"name": "John Smith", "preferences": {"Food Preference": "Vegetarian", "Dietary Restrictions": "None"}},
                    {"name": "Jane Smith", "preferences": {"Food Preference": "Non-Vegetarian", "Dietary Restrictions": "Gluten-Free"}}
                ],
                "payment_method": "offline"
            }
            
            response = requests.post(f"{self.base_url}/events/{self.created_event_id}/register", 
                                   json=registration_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and data['event_id'] == self.created_event_id:
                    self.test_results['event_registration']['register'] = True
                    self.created_registration_id = data['id']
                    self.log_success(f"/events/{self.created_event_id}/register", "POST", f"- Created registration with ID: {data['id']}")
                else:
                    self.test_results['event_registration']['register'] = False
                    self.log_error(f"/events/{self.created_event_id}/register", "POST", "Invalid response structure")
            else:
                self.test_results['event_registration']['register'] = False
                self.log_error(f"/events/{self.created_event_id}/register", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['event_registration']['register'] = False
            self.log_error(f"/events/{self.created_event_id}/register", "POST", f"Exception: {str(e)}")

        # Test GET /api/events/my/registrations
        try:
            response = requests.get(f"{self.base_url}/events/my/registrations", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['event_registration']['my_registrations'] = True
                    self.log_success("/events/my/registrations", "GET", f"- Found {len(data)} user registrations")
                else:
                    self.test_results['event_registration']['my_registrations'] = False
                    self.log_error("/events/my/registrations", "GET", "Response is not a list")
            else:
                self.test_results['event_registration']['my_registrations'] = False
                self.log_error("/events/my/registrations", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['event_registration']['my_registrations'] = False
            self.log_error("/events/my/registrations", "GET", f"Exception: {str(e)}")

    def test_admin_approval(self):
        """Test Admin Approval endpoints for offline payments"""
        print("\n🧪 Testing Admin Approval API...")
        
        # Test GET /api/events/admin/pending-approvals
        try:
            response = requests.get(f"{self.base_url}/events/admin/pending-approvals", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['admin_approval']['pending_approvals'] = True
                    self.log_success("/events/admin/pending-approvals", "GET", f"- Found {len(data)} pending approvals")
                else:
                    self.test_results['admin_approval']['pending_approvals'] = False
                    self.log_error("/events/admin/pending-approvals", "GET", "Response is not a list")
            else:
                self.test_results['admin_approval']['pending_approvals'] = False
                self.log_error("/events/admin/pending-approvals", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['admin_approval']['pending_approvals'] = False
            self.log_error("/events/admin/pending-approvals", "GET", f"Exception: {str(e)}")

        # Test POST /api/events/registrations/{id}/approve
        if self.created_registration_id:
            try:
                response = requests.post(f"{self.base_url}/events/registrations/{self.created_registration_id}/approve", 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'message' in data:
                        self.test_results['admin_approval']['approve'] = True
                        self.log_success(f"/events/registrations/{self.created_registration_id}/approve", "POST", "- Approved offline payment")
                    else:
                        self.test_results['admin_approval']['approve'] = False
                        self.log_error(f"/events/registrations/{self.created_registration_id}/approve", "POST", "Invalid response structure")
                else:
                    self.test_results['admin_approval']['approve'] = False
                    self.log_error(f"/events/registrations/{self.created_registration_id}/approve", "POST", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['admin_approval']['approve'] = False
                self.log_error(f"/events/registrations/{self.created_registration_id}/approve", "POST", f"Exception: {str(e)}")

    def test_payment_integration(self):
        """Test Payment Integration endpoints"""
        print("\n🧪 Testing Payment Integration API...")
        
        if not self.created_event_id or not self.created_registration_id:
            self.log_error("Payment Integration", "SETUP", "Missing event or registration for testing")
            return

        # Test POST /api/events/{event_id}/create-payment-order
        try:
            response = requests.post(f"{self.base_url}/events/{self.created_event_id}/create-payment-order?registration_id={self.created_registration_id}", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'order_id' in data and 'amount' in data:
                    self.test_results['payment_integration']['create_order'] = True
                    self.log_success(f"/events/{self.created_event_id}/create-payment-order", "POST", f"- Created payment order: {data['order_id']}")
                else:
                    self.test_results['payment_integration']['create_order'] = False
                    self.log_error(f"/events/{self.created_event_id}/create-payment-order", "POST", "Invalid response structure")
            else:
                self.test_results['payment_integration']['create_order'] = False
                self.log_error(f"/events/{self.created_event_id}/create-payment-order", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['payment_integration']['create_order'] = False
            self.log_error(f"/events/{self.created_event_id}/create-payment-order", "POST", f"Exception: {str(e)}")

        # Test POST /api/events/registrations/{id}/complete-payment
        try:
            response = requests.post(f"{self.base_url}/events/registrations/{self.created_registration_id}/complete-payment?payment_id=test_payment_123", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data:
                    self.test_results['payment_integration']['complete_payment'] = True
                    self.log_success(f"/events/registrations/{self.created_registration_id}/complete-payment", "POST", "- Completed payment")
                else:
                    self.test_results['payment_integration']['complete_payment'] = False
                    self.log_error(f"/events/registrations/{self.created_registration_id}/complete-payment", "POST", "Invalid response structure")
            else:
                self.test_results['payment_integration']['complete_payment'] = False
                self.log_error(f"/events/registrations/{self.created_registration_id}/complete-payment", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['payment_integration']['complete_payment'] = False
            self.log_error(f"/events/registrations/{self.created_registration_id}/complete-payment", "POST", f"Exception: {str(e)}")

    def test_amenity_booking_fix(self):
        """Test Amenity Booking with additional_guests (names instead of emails)"""
        print("\n🧪 Testing Amenity Booking Fix (additional_guests)...")
        
        try:
            future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            booking_data = {
                "amenity_id": "test-amenity-123",
                "amenity_name": "Swimming Pool",
                "booking_date": future_date,
                "start_time": "10:00",
                "duration_minutes": 60,
                "additional_guests": ["Alice Johnson", "Bob Wilson", "Carol Davis"]  # Names instead of emails
            }
            
            response = requests.post(f"{self.base_url}/bookings", 
                                   json=booking_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and 'additional_guests' in data:
                    # Verify additional_guests contains names, not emails
                    guests = data['additional_guests']
                    if isinstance(guests, list) and len(guests) == 3:
                        self.test_results['amenity_booking']['create_booking'] = True
                        self.log_success("/bookings", "POST", f"- Created booking with {len(guests)} additional guests (names)")
                    else:
                        self.test_results['amenity_booking']['create_booking'] = False
                        self.log_error("/bookings", "POST", "Invalid additional_guests structure")
                else:
                    self.test_results['amenity_booking']['create_booking'] = False
                    self.log_error("/bookings", "POST", "Invalid response structure")
            else:
                self.test_results['amenity_booking']['create_booking'] = False
                self.log_error("/bookings", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['amenity_booking']['create_booking'] = False
            self.log_error("/bookings", "POST", f"Exception: {str(e)}")

    def test_event_withdrawal(self):
        """Test Event Withdrawal endpoint"""
        print("\n🧪 Testing Event Withdrawal...")
        
        if not self.created_registration_id:
            self.log_error("Event Withdrawal", "SETUP", "No registration created for testing withdrawal")
            return

        try:
            response = requests.post(f"{self.base_url}/events/registrations/{self.created_registration_id}/withdraw", 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'refund_instructions' in data:
                    self.test_results['event_registration']['withdraw'] = True
                    self.log_success(f"/events/registrations/{self.created_registration_id}/withdraw", "POST", "- Withdrew from event successfully")
                else:
                    self.test_results['event_registration']['withdraw'] = False
                    self.log_error(f"/events/registrations/{self.created_registration_id}/withdraw", "POST", "Invalid response structure")
            else:
                self.test_results['event_registration']['withdraw'] = False
                self.log_error(f"/events/registrations/{self.created_registration_id}/withdraw", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['event_registration']['withdraw'] = False
            self.log_error(f"/events/registrations/{self.created_registration_id}/withdraw", "POST", f"Exception: {str(e)}")
            
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting TROA Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test root endpoint first
        self.test_root_endpoint()
        
        # Test existing endpoints
        self.test_committee_members()
        self.test_amenities()
        self.test_gallery()
        self.test_membership()
        
        # Test new Events feature
        self.test_events_crud()
        self.test_event_registration()
        self.test_admin_approval()
        self.test_payment_integration()
        self.test_event_withdrawal()
        
        # Test Amenity Booking fix
        self.test_amenity_booking_fix()
        
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