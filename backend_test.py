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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troa-residence.preview.emergentagent.com')
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
            'amenity_booking': {'create_booking': None},
            'gridfs_storage': {'get_image': None, 'cache_headers': None, 'etag_support': None, 'not_modified': None},
            'unified_payment': {'offline_payment': None, 'get_offline_payments': None, 'approve_payment': None, 'reject_payment': None, 'amount_verification': None},
            'event_pricing': {'per_villa': None, 'uniform_per_person': None, 'adult_child': None, 'adult_child_registration': None, 'validation': None, 'per_villa_registration': None}
        }
        self.errors = []
        self.created_event_id = None
        self.created_registration_id = None
        self.created_payment_ids = []
        self.per_villa_event_id = None
        self.uniform_event_id = None
        self.adult_child_event_id = None
        self.adult_child_registration_id = None
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.session_token = "ymsHGpK7iiNm9K79Arw3qk8DY9Z8erRkR92dKxvDqv4"  # Valid admin session token
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

        # Test DELETE /api/events/{event_id} (admin only) - Test at the end
        # We'll test this after all other tests to avoid breaking the flow

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
        
        if not self.created_event_id:
            self.log_error("Payment Integration", "SETUP", "Missing event for testing")
            return

        # Create a new registration with online payment for testing payment order
        try:
            online_registration_data = {
                "event_id": self.created_event_id,
                "registrants": [
                    {"name": "Payment Test User", "preferences": {"Food Preference": "Vegetarian"}}
                ],
                "payment_method": "online"  # Online payment for testing payment order
            }
            
            response = requests.post(f"{self.base_url}/events/{self.created_event_id}/register", 
                                   json=online_registration_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                online_registration_id = data['id']
                
                # Test POST /api/events/{event_id}/create-payment-order
                response = requests.post(f"{self.base_url}/events/{self.created_event_id}/create-payment-order?registration_id={online_registration_id}", 
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
                
                # Test POST /api/events/registrations/{id}/complete-payment
                response = requests.post(f"{self.base_url}/events/registrations/{online_registration_id}/complete-payment?payment_id=test_payment_456", 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'message' in data:
                        self.test_results['payment_integration']['complete_payment'] = True
                        self.log_success(f"/events/registrations/{online_registration_id}/complete-payment", "POST", "- Completed payment")
                    else:
                        self.test_results['payment_integration']['complete_payment'] = False
                        self.log_error(f"/events/registrations/{online_registration_id}/complete-payment", "POST", "Invalid response structure")
                else:
                    self.test_results['payment_integration']['complete_payment'] = False
                    self.log_error(f"/events/registrations/{online_registration_id}/complete-payment", "POST", f"Status code: {response.status_code}")
                    
            else:
                self.test_results['payment_integration']['create_order'] = False
                self.test_results['payment_integration']['complete_payment'] = False
                self.log_error("Payment Integration", "SETUP", f"Failed to create online registration: {response.status_code}")
                
        except Exception as e:
            self.test_results['payment_integration']['create_order'] = False
            self.test_results['payment_integration']['complete_payment'] = False
            self.log_error("Payment Integration", "SETUP", f"Exception: {str(e)}")

    def test_amenity_booking_fix(self):
        """Test Amenity Booking with additional_guests (names instead of emails)"""
        print("\n🧪 Testing Amenity Booking Fix (additional_guests)...")
        
        try:
            future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            booking_data = {
                "amenity_id": "test-amenity-456",
                "amenity_name": "Tennis Court",
                "booking_date": future_date,
                "start_time": "14:00",  # Different time to avoid conflicts
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

    def test_gridfs_image_storage(self):
        """Test GridFS Image Storage system"""
        print("\n🧪 Testing GridFS Image Storage...")
        
        # Test existing image filenames from the review request
        test_filenames = [
            "87b85abf-1066-4288-8af4-0ad4075cedcd.webp",
            "4f5739a8-23c8-40ff-be81-a9f496a75e31.png", 
            "0deb1f66-a518-4ee2-b8d6-953328859b0f.jpeg"
        ]
        
        successful_tests = 0
        total_tests = len(test_filenames)
        
        for filename in test_filenames:
            try:
                # Test GET /api/upload/image/{filename}
                response = requests.get(f"{self.base_url}/upload/image/{filename}", timeout=10)
                
                if response.status_code == 200:
                    # Check if it's actually an image
                    content_type = response.headers.get('content-type', '')
                    if content_type.startswith('image/'):
                        successful_tests += 1
                        self.log_success(f"/upload/image/{filename}", "GET", f"- Served image successfully (Content-Type: {content_type})")
                        
                        # Test caching headers
                        cache_control = response.headers.get('cache-control', '')
                        etag = response.headers.get('etag', '')
                        
                        if 'max-age=2592000' in cache_control and 'public' in cache_control:
                            self.log_success(f"/upload/image/{filename}", "CACHE", "- Correct Cache-Control header (30 days)")
                        else:
                            self.log_error(f"/upload/image/{filename}", "CACHE", f"Invalid Cache-Control: {cache_control}")
                        
                        if etag:
                            self.log_success(f"/upload/image/{filename}", "ETAG", f"- ETag header present: {etag}")
                            
                            # Test 304 Not Modified response
                            try:
                                response_304 = requests.get(
                                    f"{self.base_url}/upload/image/{filename}",
                                    headers={'If-None-Match': etag},
                                    timeout=10
                                )
                                
                                if response_304.status_code == 304:
                                    self.log_success(f"/upload/image/{filename}", "304", "- Correctly returns 304 Not Modified with matching ETag")
                                else:
                                    self.log_error(f"/upload/image/{filename}", "304", f"Expected 304 but got {response_304.status_code}")
                            except Exception as e:
                                self.log_error(f"/upload/image/{filename}", "304", f"Exception testing 304: {str(e)}")
                        else:
                            self.log_error(f"/upload/image/{filename}", "ETAG", "Missing ETag header")
                    else:
                        self.log_error(f"/upload/image/{filename}", "GET", f"Invalid content type: {content_type}")
                elif response.status_code == 404:
                    self.log_error(f"/upload/image/{filename}", "GET", "Image not found in GridFS")
                else:
                    self.log_error(f"/upload/image/{filename}", "GET", f"Status code: {response.status_code}")
                    
            except Exception as e:
                self.log_error(f"/upload/image/{filename}", "GET", f"Exception: {str(e)}")
        
        # Set test results based on success rate
        if successful_tests == total_tests:
            self.test_results['gridfs_storage']['get_image'] = True
            self.test_results['gridfs_storage']['cache_headers'] = True
            self.test_results['gridfs_storage']['etag_support'] = True
            self.test_results['gridfs_storage']['not_modified'] = True
        elif successful_tests > 0:
            self.test_results['gridfs_storage']['get_image'] = True
            # Partial success for other features
        else:
            self.test_results['gridfs_storage']['get_image'] = False
            self.test_results['gridfs_storage']['cache_headers'] = False
            self.test_results['gridfs_storage']['etag_support'] = False
            self.test_results['gridfs_storage']['not_modified'] = False
        
        # Test non-existent image (should return 404)
        try:
            response = requests.get(f"{self.base_url}/upload/image/non-existent-image.jpg", timeout=10)
            if response.status_code == 404:
                self.log_success("/upload/image/non-existent", "GET", "- Correctly returns 404 for non-existent image")
            else:
                self.log_error("/upload/image/non-existent", "GET", f"Expected 404 but got {response.status_code}")
        except Exception as e:
            self.log_error("/upload/image/non-existent", "GET", f"Exception: {str(e)}")

    def test_unified_payment_system(self):
        """Test Unified Payment System endpoints"""
        print("\n🧪 Testing Unified Payment System...")
        
        # Test 1: Create offline payment requests for all payment types
        payment_types = [
            {
                'type': 'move_in',
                'expected_amount': 2360,
                'user_data': {
                    'name': 'John Smith',
                    'email': 'john.smith@email.com',
                    'phone': '+91-9876543210',
                    'villa_no': 'A-101',
                    'notes': 'Move-in payment for new resident'
                }
            },
            {
                'type': 'move_out',
                'expected_amount': 2360,
                'user_data': {
                    'name': 'Sarah Johnson',
                    'email': 'sarah.johnson@email.com',
                    'phone': '+91-9876543211',
                    'villa_no': 'B-205',
                    'notes': 'Move-out payment for departing resident'
                }
            },
            {
                'type': 'membership',
                'expected_amount': 11800,
                'user_data': {
                    'name': 'Michael Rodriguez',
                    'email': 'michael.rodriguez@email.com',
                    'phone': '+91-9876543212',
                    'villa_no': 'C-303',
                    'notes': 'Annual membership payment'
                }
            }
        ]
        
        # Test offline payment creation for each type
        for payment_data in payment_types:
            for payment_method in ['qr_code', 'cash_transfer']:
                try:
                    offline_payment_request = {
                        'payment_type': payment_data['type'],
                        'payment_method': payment_method,
                        'name': payment_data['user_data']['name'],
                        'email': payment_data['user_data']['email'],
                        'phone': payment_data['user_data']['phone'],
                        'villa_no': payment_data['user_data']['villa_no'],
                        'notes': f"{payment_data['user_data']['notes']} via {payment_method}"
                    }
                    
                    response = requests.post(f"{self.base_url}/payment/offline-payment", 
                                           json=offline_payment_request, 
                                           headers={'Content-Type': 'application/json'},
                                           timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if ('payment_id' in data and 
                            'amount' in data and 
                            float(data['amount']) == float(payment_data['expected_amount']) and
                            'success' in data and data['success'] and
                            'awaiting' in data.get('message', '').lower()):
                            
                            self.created_payment_ids.append(data['payment_id'])
                            self.log_success(f"/payment/offline-payment ({payment_data['type']}, {payment_method})", "POST", 
                                           f"- Created payment ID: {data['payment_id']}, Amount: ₹{data['amount']}")
                        else:
                            self.test_results['unified_payment']['offline_payment'] = False
                            self.log_error(f"/payment/offline-payment ({payment_data['type']}, {payment_method})", "POST", 
                                         f"Invalid response structure or amount. Expected: ₹{payment_data['expected_amount']}, Got: {data}")
                    else:
                        self.test_results['unified_payment']['offline_payment'] = False
                        self.log_error(f"/payment/offline-payment ({payment_data['type']}, {payment_method})", "POST", 
                                     f"Status code: {response.status_code}, Response: {response.text}")
                except Exception as e:
                    self.test_results['unified_payment']['offline_payment'] = False
                    self.log_error(f"/payment/offline-payment ({payment_data['type']}, {payment_method})", "POST", f"Exception: {str(e)}")
        
        # If we successfully created payments, mark offline_payment as successful
        if self.created_payment_ids:
            self.test_results['unified_payment']['offline_payment'] = True
            
        # Test 2: Get offline payments (admin only)
        try:
            response = requests.get(f"{self.base_url}/payment/offline-payments", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['unified_payment']['get_offline_payments'] = True
                    self.log_success("/payment/offline-payments", "GET", f"- Found {len(data)} offline payment requests")
                    
                    # Validate structure of payments if they exist
                    if data:
                        payment = data[0]
                        required_fields = ['id', 'payment_type', 'payment_method', 'amount', 'status', 'user_details', 'created_at']
                        missing_fields = [field for field in required_fields if field not in payment]
                        if missing_fields:
                            self.log_error("/payment/offline-payments", "GET", f"Missing required fields: {missing_fields}")
                        else:
                            self.log_success("/payment/offline-payments", "GET", f"- Payment structure validated")
                else:
                    self.test_results['unified_payment']['get_offline_payments'] = False
                    self.log_error("/payment/offline-payments", "GET", "Response is not a list")
            else:
                self.test_results['unified_payment']['get_offline_payments'] = False
                self.log_error("/payment/offline-payments", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['unified_payment']['get_offline_payments'] = False
            self.log_error("/payment/offline-payments", "GET", f"Exception: {str(e)}")
            
        # Test 3: Test admin approval/rejection
        if self.created_payment_ids:
            # Test approval
            try:
                approval_request = {
                    'payment_id': self.created_payment_ids[0],
                    'action': 'approve'
                }
                
                response = requests.post(f"{self.base_url}/payment/offline-payments/approve", 
                                       json=approval_request, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'success' in data and data['success'] and 'approved successfully' in data.get('message', ''):
                        self.test_results['unified_payment']['approve_payment'] = True
                        self.log_success("/payment/offline-payments/approve", "POST", f"- Approved payment: {self.created_payment_ids[0]}")
                    else:
                        self.test_results['unified_payment']['approve_payment'] = False
                        self.log_error("/payment/offline-payments/approve", "POST", "Invalid response structure")
                else:
                    self.test_results['unified_payment']['approve_payment'] = False
                    self.log_error("/payment/offline-payments/approve", "POST", f"Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.test_results['unified_payment']['approve_payment'] = False
                self.log_error("/payment/offline-payments/approve", "POST", f"Exception: {str(e)}")
            
            # Test rejection (if we have more than one payment)
            if len(self.created_payment_ids) > 1:
                try:
                    rejection_request = {
                        'payment_id': self.created_payment_ids[1],
                        'action': 'reject'
                    }
                    
                    response = requests.post(f"{self.base_url}/payment/offline-payments/approve", 
                                           json=rejection_request, 
                                           headers=self.auth_headers,
                                           timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'success' in data and data['success'] and 'rejected successfully' in data.get('message', ''):
                            self.test_results['unified_payment']['reject_payment'] = True
                            self.log_success("/payment/offline-payments/approve (reject)", "POST", f"- Rejected payment: {self.created_payment_ids[1]}")
                        else:
                            self.test_results['unified_payment']['reject_payment'] = False
                            self.log_error("/payment/offline-payments/approve (reject)", "POST", "Invalid response structure")
                    else:
                        self.test_results['unified_payment']['reject_payment'] = False
                        self.log_error("/payment/offline-payments/approve (reject)", "POST", f"Status code: {response.status_code}, Response: {response.text}")
                except Exception as e:
                    self.test_results['unified_payment']['reject_payment'] = False
                    self.log_error("/payment/offline-payments/approve (reject)", "POST", f"Exception: {str(e)}")
        
        # Test 4: Verify payment amounts are correct
        expected_amounts = {
            'move_in': 2360,    # ₹2000 + 18% GST = ₹2360
            'move_out': 2360,   # ₹2000 + 18% GST = ₹2360
            'membership': 11800  # ₹10000 + 18% GST = ₹11800
        }
        
        amount_verification_passed = True
        for payment_type, expected_amount in expected_amounts.items():
            try:
                test_request = {
                    'payment_type': payment_type,
                    'payment_method': 'qr_code',
                    'name': 'Amount Test User',
                    'email': 'amount.test@email.com',
                    'phone': '+91-9999999999',
                    'villa_no': 'TEST-001',
                    'notes': f'Amount verification test for {payment_type}'
                }
                
                response = requests.post(f"{self.base_url}/payment/offline-payment", 
                                       json=test_request, 
                                       headers={'Content-Type': 'application/json'},
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    actual_amount = data.get('amount')
                    if actual_amount == expected_amount:
                        self.log_success(f"Amount verification ({payment_type})", "TEST", f"- Correct amount: ₹{actual_amount}")
                    else:
                        amount_verification_passed = False
                        self.log_error(f"Amount verification ({payment_type})", "TEST", f"Expected: ₹{expected_amount}, Got: ₹{actual_amount}")
                else:
                    amount_verification_passed = False
                    self.log_error(f"Amount verification ({payment_type})", "TEST", f"Status code: {response.status_code}")
            except Exception as e:
                amount_verification_passed = False
                self.log_error(f"Amount verification ({payment_type})", "TEST", f"Exception: {str(e)}")
        
        self.test_results['unified_payment']['amount_verification'] = amount_verification_passed
        
        # Test 5: Test authentication requirements
        try:
            # Test GET /payment/offline-payments without authentication (should fail)
            response = requests.get(f"{self.base_url}/payment/offline-payments", timeout=10)
            if response.status_code in [401, 403]:
                self.log_success("/payment/offline-payments", "AUTH", "- Correctly requires admin authentication")
            else:
                self.log_error("/payment/offline-payments", "AUTH", f"Should require auth but got status: {response.status_code}")
                
            # Test POST /payment/offline-payments/approve without authentication (should fail)
            response = requests.post(f"{self.base_url}/payment/offline-payments/approve", 
                                   json={'payment_id': 'test', 'action': 'approve'}, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            if response.status_code in [401, 403]:
                self.log_success("/payment/offline-payments/approve", "AUTH", "- Correctly requires admin authentication")
            else:
                self.log_error("/payment/offline-payments/approve", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error("Payment Authentication", "TEST", f"Exception: {str(e)}")

    def test_event_pricing_options(self):
        """Test new event pricing options feature"""
        print("\n🧪 Testing Event Pricing Options Feature...")
        
        # Test 1: Create Event with Per Villa Pricing
        try:
            future_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
            per_villa_event = {
                "name": "Villa Pool Party",
                "description": "Exclusive pool party for the entire villa",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "16:00",
                "amount": 1000.0,
                "payment_type": "per_villa",
                "preferences": [
                    {"name": "Music Preference", "options": ["DJ", "Live Band", "Acoustic"]}
                ],
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=per_villa_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    data['payment_type'] == 'per_villa' and 
                    data['amount'] == 1000.0):
                    self.test_results['event_pricing'] = {'per_villa': True}
                    self.per_villa_event_id = data['id']
                    self.log_success("/events (per_villa)", "POST", f"- Created per villa event: {data['id']}")
                else:
                    self.test_results['event_pricing'] = {'per_villa': False}
                    self.log_error("/events (per_villa)", "POST", "Invalid response structure")
            else:
                self.test_results['event_pricing'] = {'per_villa': False}
                self.log_error("/events (per_villa)", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['event_pricing'] = {'per_villa': False}
            self.log_error("/events (per_villa)", "POST", f"Exception: {str(e)}")

        # Test 2: Create Event with Uniform Per Person Pricing
        try:
            future_date = (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
            uniform_per_person_event = {
                "name": "Community Yoga Session",
                "description": "Relaxing yoga session for all residents",
                "image": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=800",
                "event_date": future_date,
                "event_time": "07:00",
                "amount": 500.0,
                "payment_type": "per_person",
                "per_person_type": "uniform",
                "preferences": [
                    {"name": "Experience Level", "options": ["Beginner", "Intermediate", "Advanced"]}
                ],
                "max_registrations": 30
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=uniform_per_person_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    data['payment_type'] == 'per_person' and 
                    data['per_person_type'] == 'uniform' and
                    data['amount'] == 500.0):
                    self.test_results['event_pricing']['uniform_per_person'] = True
                    self.uniform_event_id = data['id']
                    self.log_success("/events (uniform per_person)", "POST", f"- Created uniform per person event: {data['id']}")
                else:
                    self.test_results['event_pricing']['uniform_per_person'] = False
                    self.log_error("/events (uniform per_person)", "POST", "Invalid response structure")
            else:
                self.test_results['event_pricing']['uniform_per_person'] = False
                self.log_error("/events (uniform per_person)", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['event_pricing']['uniform_per_person'] = False
            self.log_error("/events (uniform per_person)", "POST", f"Exception: {str(e)}")

        # Test 3: Create Event with Adult/Child Pricing
        try:
            future_date = (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d')
            adult_child_event = {
                "name": "Family Fun Day",
                "description": "Fun activities for the whole family with different pricing for adults and children",
                "image": "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800",
                "event_date": future_date,
                "event_time": "10:00",
                "amount": 0,  # Not used for adult_child pricing
                "payment_type": "per_person",
                "per_person_type": "adult_child",
                "adult_price": 500.0,
                "child_price": 250.0,
                "preferences": [
                    {"name": "Activity Preference", "options": ["Games", "Arts & Crafts", "Sports"]}
                ],
                "max_registrations": 100
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=adult_child_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    data['payment_type'] == 'per_person' and 
                    data['per_person_type'] == 'adult_child' and
                    data['adult_price'] == 500.0 and
                    data['child_price'] == 250.0):
                    self.test_results['event_pricing']['adult_child'] = True
                    self.adult_child_event_id = data['id']
                    self.log_success("/events (adult_child)", "POST", f"- Created adult/child pricing event: {data['id']}")
                else:
                    self.test_results['event_pricing']['adult_child'] = False
                    self.log_error("/events (adult_child)", "POST", "Invalid response structure")
            else:
                self.test_results['event_pricing']['adult_child'] = False
                self.log_error("/events (adult_child)", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['event_pricing']['adult_child'] = False
            self.log_error("/events (adult_child)", "POST", f"Exception: {str(e)}")

        # Test 4: Register for Adult/Child Event with Mixed Registrants
        if hasattr(self, 'adult_child_event_id'):
            try:
                registration_data = {
                    "event_id": self.adult_child_event_id,
                    "registrants": [
                        {
                            "name": "John Smith", 
                            "registrant_type": "adult",
                            "preferences": {"Activity Preference": "Games"}
                        },
                        {
                            "name": "Jane Smith", 
                            "registrant_type": "adult",
                            "preferences": {"Activity Preference": "Sports"}
                        },
                        {
                            "name": "Little Tommy", 
                            "registrant_type": "child",
                            "preferences": {"Activity Preference": "Arts & Crafts"}
                        }
                    ],
                    "payment_method": "offline"
                }
                
                response = requests.post(f"{self.base_url}/events/{self.adult_child_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    expected_total = (2 * 500) + (1 * 250)  # 2 adults + 1 child = 1250
                    if ('id' in data and 
                        data['total_amount'] == expected_total and
                        len(data['registrants']) == 3):
                        self.test_results['event_pricing']['adult_child_registration'] = True
                        self.adult_child_registration_id = data['id']
                        self.log_success(f"/events/{self.adult_child_event_id}/register", "POST", 
                                       f"- Registered with correct total: ₹{data['total_amount']} (2 adults + 1 child)")
                    else:
                        self.test_results['event_pricing']['adult_child_registration'] = False
                        self.log_error(f"/events/{self.adult_child_event_id}/register", "POST", 
                                     f"Incorrect total. Expected: ₹{expected_total}, Got: ₹{data.get('total_amount')}")
                else:
                    self.test_results['event_pricing']['adult_child_registration'] = False
                    self.log_error(f"/events/{self.adult_child_event_id}/register", "POST", 
                                 f"Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.test_results['event_pricing']['adult_child_registration'] = False
                self.log_error(f"/events/{self.adult_child_event_id}/register", "POST", f"Exception: {str(e)}")

        # Test 5: Validation Test - Create adult_child event without prices (should fail)
        try:
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            invalid_event = {
                "name": "Invalid Event",
                "description": "This should fail validation",
                "image": "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800",
                "event_date": future_date,
                "event_time": "10:00",
                "amount": 0,
                "payment_type": "per_person",
                "per_person_type": "adult_child"
                # Missing adult_price and child_price
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=invalid_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 400:
                self.test_results['event_pricing']['validation'] = True
                self.log_success("/events (validation)", "POST", "- Correctly rejected adult_child event without prices")
            else:
                self.test_results['event_pricing']['validation'] = False
                self.log_error("/events (validation)", "POST", f"Should reject invalid event but got status: {response.status_code}")
        except Exception as e:
            self.test_results['event_pricing']['validation'] = False
            self.log_error("/events (validation)", "POST", f"Exception: {str(e)}")

        # Test 6: Test Per Villa Registration (should use flat rate regardless of registrant count)
        if hasattr(self, 'per_villa_event_id'):
            try:
                villa_registration_data = {
                    "event_id": self.per_villa_event_id,
                    "registrants": [
                        {"name": "Villa Owner", "preferences": {"Music Preference": "DJ"}},
                        {"name": "Guest 1", "preferences": {"Music Preference": "DJ"}},
                        {"name": "Guest 2", "preferences": {"Music Preference": "Live Band"}},
                        {"name": "Guest 3", "preferences": {"Music Preference": "Acoustic"}}
                    ],
                    "payment_method": "online"
                }
                
                response = requests.post(f"{self.base_url}/events/{self.per_villa_event_id}/register", 
                                       json=villa_registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if ('id' in data and 
                        data['total_amount'] == 1000.0 and  # Should be flat rate regardless of 4 registrants
                        len(data['registrants']) == 4):
                        self.test_results['event_pricing']['per_villa_registration'] = True
                        self.log_success(f"/events/{self.per_villa_event_id}/register", "POST", 
                                       f"- Per villa registration correct: ₹{data['total_amount']} for {len(data['registrants'])} people")
                    else:
                        self.test_results['event_pricing']['per_villa_registration'] = False
                        self.log_error(f"/events/{self.per_villa_event_id}/register", "POST", 
                                     f"Incorrect per villa pricing. Expected: ₹1000, Got: ₹{data.get('total_amount')}")
                else:
                    self.test_results['event_pricing']['per_villa_registration'] = False
                    self.log_error(f"/events/{self.per_villa_event_id}/register", "POST", 
                                 f"Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.test_results['event_pricing']['per_villa_registration'] = False
                self.log_error(f"/events/{self.per_villa_event_id}/register", "POST", f"Exception: {str(e)}")

    def test_edge_cases(self):
        """Test edge cases and error scenarios"""
        print("\n🧪 Testing Edge Cases and Error Scenarios...")
        
        # Test creating event with past date (should fail)
        try:
            past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            past_event = {
                "name": "Past Event Test",
                "description": "This should fail",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": past_date,
                "event_time": "18:00",
                "amount": 25.0,
                "payment_type": "per_person"
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=past_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 400:
                self.log_success("/events", "POST", "- Correctly rejected event with past date")
            else:
                self.log_error("/events", "POST", f"Should reject past date but got status: {response.status_code}")
                
        except Exception as e:
            self.log_error("/events", "POST", f"Exception testing past date: {str(e)}")

        # Test registering for non-existent event (should fail)
        try:
            fake_event_id = "non-existent-event-123"
            registration_data = {
                "event_id": fake_event_id,
                "registrants": [{"name": "Test User", "preferences": {}}],
                "payment_method": "online"
            }
            
            response = requests.post(f"{self.base_url}/events/{fake_event_id}/register", 
                                   json=registration_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 404:
                self.log_success(f"/events/{fake_event_id}/register", "POST", "- Correctly returned 404 for non-existent event")
            else:
                self.log_error(f"/events/{fake_event_id}/register", "POST", f"Should return 404 but got status: {response.status_code}")
                
        except Exception as e:
            self.log_error(f"/events/{fake_event_id}/register", "POST", f"Exception: {str(e)}")

        # Test unauthenticated access to protected endpoints
        try:
            response = requests.get(f"{self.base_url}/events/my/registrations", timeout=10)
            if response.status_code == 401:
                self.log_success("/events/my/registrations", "GET", "- Correctly requires authentication")
            else:
                self.log_error("/events/my/registrations", "GET", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error("/events/my/registrations", "GET", f"Exception: {str(e)}")
            
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
        
        # Test new GridFS Image Storage feature
        self.test_gridfs_image_storage()
        
        # Test new Events feature
        self.test_events_crud()
        self.test_event_registration()
        self.test_admin_approval()
        self.test_payment_integration()
        self.test_event_withdrawal()
        
        # Test Amenity Booking fix
        self.test_amenity_booking_fix()
        
        # Test Unified Payment System
        self.test_unified_payment_system()
        
        # Test new Event Pricing Options feature
        self.test_event_pricing_options()
        
        # Test edge cases
        self.test_edge_cases()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        # Group results by category
        categories = {
            'Basic APIs': ['committee', 'amenities', 'gallery', 'membership'],
            'GridFS Image Storage': ['gridfs_storage'],
            'Events CRUD': ['events'],
            'Event Registration': ['event_registration'],
            'Admin Approval': ['admin_approval'],
            'Payment Integration': ['payment_integration'],
            'Unified Payment System': ['unified_payment'],
            'Event Pricing Options': ['event_pricing'],
            'Amenity Booking': ['amenity_booking']
        }
        
        for category, endpoints in categories.items():
            print(f"\n{category}:")
            for endpoint in endpoints:
                if endpoint in self.test_results:
                    methods = self.test_results[endpoint]
                    for method, result in methods.items():
                        total_tests += 1
                        if result:
                            passed_tests += 1
                            status = "✅ PASS"
                        elif result is False:
                            status = "❌ FAIL"
                        else:
                            status = "⏸️ SKIP"
                            total_tests -= 1  # Don't count skipped tests
                            continue
                        
                        # Format endpoint name for display
                        if endpoint == 'event_registration':
                            display_endpoint = f"events/{method}"
                        elif endpoint == 'admin_approval':
                            display_endpoint = f"events/admin/{method}"
                        elif endpoint == 'payment_integration':
                            display_endpoint = f"events/payment/{method}"
                        elif endpoint == 'amenity_booking':
                            display_endpoint = f"bookings/{method}"
                        elif endpoint == 'gridfs_storage':
                            display_endpoint = f"upload/image/{method}"
                        elif endpoint == 'unified_payment':
                            display_endpoint = f"payment/{method}"
                        else:
                            display_endpoint = f"{endpoint}/{method}"
                            
                        print(f"  {status} - {display_endpoint}")
        
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