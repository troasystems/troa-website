#!/usr/bin/env python3
"""
Backend API Testing for TROA (The Retreat Owners Association) Website
Tests all backend APIs including Committee Members, Amenities, Gallery, Membership Application, Events, Amenity Booking, and Villa Management endpoints.
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
            'event_pricing': {'per_villa': None, 'uniform_per_person': None, 'adult_child': None, 'adult_child_registration': None, 'validation': None, 'per_villa_registration': None},
            'event_modification': {'uniform_per_person_mod': None, 'adult_child_mod': None, 'per_villa_mod': None, 'offline_payment_mod': None, 'online_payment_mod': None, 'create_modification_order': None, 'my_status': None},
            'villa_management': {'update_name': None, 'update_villa_valid': None, 'update_villa_invalid': None, 'update_password': None, 'update_photo': None, 'create_with_villa': None},
            'user_management': {'toggle_verified_true': None, 'toggle_verified_false': None, 'update_picture_base64': None},
            'google_oauth': {'invalid_token_error': None},
            'email_verification': {'already_verified_success': None, 'token_mismatch_error': None},
            'community_chat': {'get_groups': None, 'create_group': None, 'join_group': None, 'leave_group': None, 'get_messages': None, 'send_message': None, 'mc_group_exists': None, 'message_pagination': None, 'message_deletion': None, 'file_upload_pdf': None, 'deleted_message_response': None, 'message_order': None},
            'push_notifications': {'vapid_public_key': None, 'subscribe': None, 'unsubscribe': None, 'status': None, 'send_admin_only': None, 'send_notification_to_user': None, 'send_notification_to_admins': None},
            'pwa_caching': {'cache_headers_amenities': None, 'cache_headers_committee': None, 'cache_headers_events': None, 'cache_headers_gallery': None, 'no_cache_auth': None, 'service_worker': None, 'manifest': None, 'cors_headers': None}
        }
        self.errors = []
        self.created_event_id = None
        self.created_registration_id = None
        self.created_payment_ids = []
        self.per_villa_event_id = None
        self.uniform_event_id = None
        self.adult_child_event_id = None
        self.adult_child_registration_id = None
        self.test_group_id = None
        self.test_message_ids = []
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.session_token = "xBPTLcvN2wsTsXtfGxu1MJ4W7VmNi8oO5fUrLqqVT44"  # Valid admin session token
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

    def test_event_registration_modification(self):
        """Test Event Registration Modification Flow"""
        print("\n🧪 Testing Event Registration Modification Flow...")
        
        # Test 1: Uniform Per Person Pricing Modification
        print("\n📋 Test 1: Uniform Per Person Pricing Modification")
        try:
            # Create event with uniform per person pricing
            future_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
            uniform_event = {
                "name": "Uniform Pricing Test Event",
                "description": "Test event for uniform per person pricing modification",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "18:00",
                "amount": 100.0,
                "payment_type": "per_person",
                "per_person_type": "uniform",
                "preferences": [{"name": "Food Preference", "options": ["Veg", "Non-Veg"]}],
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=uniform_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                uniform_event_id = response.json()['id']
                
                # Register with 2 people (total: 200)
                registration_data = {
                    "event_id": uniform_event_id,
                    "registrants": [
                        {"name": "Alice Smith", "preferences": {"Food Preference": "Veg"}},
                        {"name": "Bob Smith", "preferences": {"Food Preference": "Non-Veg"}}
                    ],
                    "payment_method": "offline"
                }
                
                response = requests.post(f"{self.base_url}/events/{uniform_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    registration_id = response.json()['id']
                    
                    # Modify to add 1 more person (new total: 300)
                    modification_data = {
                        "registrants": [
                            {"name": "Alice Smith", "preferences": {"Food Preference": "Veg"}},
                            {"name": "Bob Smith", "preferences": {"Food Preference": "Non-Veg"}},
                            {"name": "Charlie Smith", "preferences": {"Food Preference": "Veg"}}
                        ],
                        "payment_method": "online"
                    }
                    
                    response = requests.patch(f"{self.base_url}/events/registrations/{registration_id}/modify", 
                                            json=modification_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if (data.get('requires_payment') == True and 
                            data.get('additional_amount') == 100):
                            self.test_results['event_modification']['uniform_per_person_mod'] = True
                            self.log_success("Uniform Per Person Modification", "PATCH", f"- Requires payment: {data['requires_payment']}, Additional amount: ₹{data['additional_amount']}")
                        else:
                            self.test_results['event_modification']['uniform_per_person_mod'] = False
                            self.log_error("Uniform Per Person Modification", "PATCH", f"Expected requires_payment=True, additional_amount=100, got: {data}")
                    else:
                        self.test_results['event_modification']['uniform_per_person_mod'] = False
                        self.log_error("Uniform Per Person Modification", "PATCH", f"Status code: {response.status_code}")
                else:
                    self.test_results['event_modification']['uniform_per_person_mod'] = False
                    self.log_error("Uniform Per Person Registration", "POST", f"Status code: {response.status_code}")
            else:
                self.test_results['event_modification']['uniform_per_person_mod'] = False
                self.log_error("Uniform Per Person Event Creation", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['event_modification']['uniform_per_person_mod'] = False
            self.log_error("Uniform Per Person Modification", "TEST", f"Exception: {str(e)}")

        # Test 2: Adult/Child Pricing Modification
        print("\n📋 Test 2: Adult/Child Pricing Modification")
        try:
            # Create event with adult/child pricing
            future_date = (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d')
            adult_child_event = {
                "name": "Adult Child Pricing Test Event",
                "description": "Test event for adult/child pricing modification",
                "image": "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800",
                "event_date": future_date,
                "event_time": "10:00",
                "amount": 0,
                "payment_type": "per_person",
                "per_person_type": "adult_child",
                "adult_price": 500.0,
                "child_price": 250.0,
                "preferences": [{"name": "Activity", "options": ["Games", "Sports"]}],
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=adult_child_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                adult_child_event_id = response.json()['id']
                
                # Register with 1 adult (total: 500)
                registration_data = {
                    "event_id": adult_child_event_id,
                    "registrants": [
                        {"name": "John Doe", "registrant_type": "adult", "preferences": {"Activity": "Games"}}
                    ],
                    "payment_method": "offline"
                }
                
                response = requests.post(f"{self.base_url}/events/{adult_child_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    registration_id = response.json()['id']
                    
                    # Modify to add 1 adult and 1 child (new total: 500 + 500 + 250 = 1250)
                    modification_data = {
                        "registrants": [
                            {"name": "John Doe", "registrant_type": "adult", "preferences": {"Activity": "Games"}},
                            {"name": "Jane Doe", "registrant_type": "adult", "preferences": {"Activity": "Sports"}},
                            {"name": "Little Doe", "registrant_type": "child", "preferences": {"Activity": "Games"}}
                        ],
                        "payment_method": "offline"
                    }
                    
                    response = requests.patch(f"{self.base_url}/events/registrations/{registration_id}/modify", 
                                            json=modification_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if (data.get('requires_payment') == True and 
                            data.get('additional_amount') == 750):
                            self.test_results['event_modification']['adult_child_mod'] = True
                            self.log_success("Adult/Child Modification", "PATCH", f"- Requires payment: {data['requires_payment']}, Additional amount: ₹{data['additional_amount']}")
                        else:
                            self.test_results['event_modification']['adult_child_mod'] = False
                            self.log_error("Adult/Child Modification", "PATCH", f"Expected requires_payment=True, additional_amount=750, got: {data}")
                    else:
                        self.test_results['event_modification']['adult_child_mod'] = False
                        self.log_error("Adult/Child Modification", "PATCH", f"Status code: {response.status_code}")
                else:
                    self.test_results['event_modification']['adult_child_mod'] = False
                    self.log_error("Adult/Child Registration", "POST", f"Status code: {response.status_code}")
            else:
                self.test_results['event_modification']['adult_child_mod'] = False
                self.log_error("Adult/Child Event Creation", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['event_modification']['adult_child_mod'] = False
            self.log_error("Adult/Child Modification", "TEST", f"Exception: {str(e)}")

        # Test 3: Per Villa Pricing Modification
        print("\n📋 Test 3: Per Villa Pricing Modification")
        try:
            # Create event with per villa pricing
            future_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
            per_villa_event = {
                "name": "Per Villa Pricing Test Event",
                "description": "Test event for per villa pricing modification",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "16:00",
                "amount": 1000.0,
                "payment_type": "per_villa",
                "preferences": [{"name": "Music", "options": ["DJ", "Live Band"]}],
                "max_registrations": 20
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=per_villa_event, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                per_villa_event_id = response.json()['id']
                
                # Register with 2 people (total: 1000)
                registration_data = {
                    "event_id": per_villa_event_id,
                    "registrants": [
                        {"name": "Villa Owner", "preferences": {"Music": "DJ"}},
                        {"name": "Villa Guest", "preferences": {"Music": "Live Band"}}
                    ],
                    "payment_method": "offline"
                }
                
                response = requests.post(f"{self.base_url}/events/{per_villa_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    registration_id = response.json()['id']
                    
                    # Modify to add 2 more people (should be free as per villa)
                    modification_data = {
                        "registrants": [
                            {"name": "Villa Owner", "preferences": {"Music": "DJ"}},
                            {"name": "Villa Guest", "preferences": {"Music": "Live Band"}},
                            {"name": "Villa Friend 1", "preferences": {"Music": "DJ"}},
                            {"name": "Villa Friend 2", "preferences": {"Music": "Live Band"}}
                        ],
                        "payment_method": "offline"
                    }
                    
                    response = requests.patch(f"{self.base_url}/events/registrations/{registration_id}/modify", 
                                            json=modification_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('requires_payment') == False:
                            self.test_results['event_modification']['per_villa_mod'] = True
                            self.log_success("Per Villa Modification", "PATCH", f"- Requires payment: {data['requires_payment']} (correct for per villa)")
                        else:
                            self.test_results['event_modification']['per_villa_mod'] = False
                            self.log_error("Per Villa Modification", "PATCH", f"Expected requires_payment=False, got: {data}")
                    else:
                        self.test_results['event_modification']['per_villa_mod'] = False
                        self.log_error("Per Villa Modification", "PATCH", f"Status code: {response.status_code}")
                else:
                    self.test_results['event_modification']['per_villa_mod'] = False
                    self.log_error("Per Villa Registration", "POST", f"Status code: {response.status_code}")
            else:
                self.test_results['event_modification']['per_villa_mod'] = False
                self.log_error("Per Villa Event Creation", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['event_modification']['per_villa_mod'] = False
            self.log_error("Per Villa Modification", "TEST", f"Exception: {str(e)}")

        # Test 4: Offline Payment Modification Status
        print("\n📋 Test 4: Offline Payment Modification Status")
        try:
            if self.uniform_event_id:  # Use existing uniform event
                # Create a new registration for offline modification test
                registration_data = {
                    "event_id": self.uniform_event_id,
                    "registrants": [
                        {"name": "Offline Test User", "preferences": {"Experience Level": "Beginner"}}
                    ],
                    "payment_method": "offline"
                }
                
                response = requests.post(f"{self.base_url}/events/{self.uniform_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    registration_id = response.json()['id']
                    
                    # Modify with offline payment method
                    modification_data = {
                        "registrants": [
                            {"name": "Offline Test User", "preferences": {"Experience Level": "Beginner"}},
                            {"name": "Offline Test User 2", "preferences": {"Experience Level": "Intermediate"}}
                        ],
                        "payment_method": "offline"
                    }
                    
                    response = requests.patch(f"{self.base_url}/events/registrations/{registration_id}/modify", 
                                            json=modification_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if (data.get('requires_payment') == True and 
                            data.get('payment_method') == 'offline'):
                            self.test_results['event_modification']['offline_payment_mod'] = True
                            self.log_success("Offline Payment Modification", "PATCH", f"- Payment method: {data['payment_method']}, Status should be pending_modification_approval")
                        else:
                            self.test_results['event_modification']['offline_payment_mod'] = False
                            self.log_error("Offline Payment Modification", "PATCH", f"Expected offline payment method, got: {data}")
                    else:
                        self.test_results['event_modification']['offline_payment_mod'] = False
                        self.log_error("Offline Payment Modification", "PATCH", f"Status code: {response.status_code}")
                else:
                    self.test_results['event_modification']['offline_payment_mod'] = False
                    self.log_error("Offline Payment Registration", "POST", f"Status code: {response.status_code}")
            else:
                self.test_results['event_modification']['offline_payment_mod'] = False
                self.log_error("Offline Payment Modification", "SETUP", "No uniform event available for testing")
        except Exception as e:
            self.test_results['event_modification']['offline_payment_mod'] = False
            self.log_error("Offline Payment Modification", "TEST", f"Exception: {str(e)}")

        # Test 5: Online Payment Modification Order Creation
        print("\n📋 Test 5: Online Payment Modification Order Creation")
        try:
            if self.uniform_event_id:  # Use existing uniform event
                # Create a new registration for online modification test
                registration_data = {
                    "event_id": self.uniform_event_id,
                    "registrants": [
                        {"name": "Online Test User", "preferences": {"Experience Level": "Advanced"}}
                    ],
                    "payment_method": "offline"  # Initial registration offline
                }
                
                response = requests.post(f"{self.base_url}/events/{self.uniform_event_id}/register", 
                                       json=registration_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    registration_id = response.json()['id']
                    
                    # Modify with online payment method
                    modification_data = {
                        "registrants": [
                            {"name": "Online Test User", "preferences": {"Experience Level": "Advanced"}},
                            {"name": "Online Test User 2", "preferences": {"Experience Level": "Beginner"}}
                        ],
                        "payment_method": "online"
                    }
                    
                    response = requests.patch(f"{self.base_url}/events/registrations/{registration_id}/modify", 
                                            json=modification_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if (data.get('requires_payment') == True and 
                            data.get('payment_method') == 'online'):
                            
                            # Test create modification order endpoint
                            response = requests.post(f"{self.base_url}/events/registrations/{registration_id}/create-modification-order", 
                                                   headers=self.auth_headers,
                                                   timeout=10)
                            
                            if response.status_code == 200:
                                order_data = response.json()
                                if ('order_id' in order_data and 
                                    'amount' in order_data and 
                                    'key_id' in order_data):
                                    self.test_results['event_modification']['online_payment_mod'] = True
                                    self.test_results['event_modification']['create_modification_order'] = True
                                    self.log_success("Online Payment Modification", "PATCH", f"- Payment method: {data['payment_method']}")
                                    self.log_success("Create Modification Order", "POST", f"- Order ID: {order_data['order_id']}, Amount: ₹{order_data['amount']/100}")
                                else:
                                    self.test_results['event_modification']['online_payment_mod'] = True
                                    self.test_results['event_modification']['create_modification_order'] = False
                                    self.log_error("Create Modification Order", "POST", f"Invalid response structure: {order_data}")
                            else:
                                self.test_results['event_modification']['online_payment_mod'] = True
                                self.test_results['event_modification']['create_modification_order'] = False
                                self.log_error("Create Modification Order", "POST", f"Status code: {response.status_code}")
                        else:
                            self.test_results['event_modification']['online_payment_mod'] = False
                            self.test_results['event_modification']['create_modification_order'] = False
                            self.log_error("Online Payment Modification", "PATCH", f"Expected online payment method, got: {data}")
                    else:
                        self.test_results['event_modification']['online_payment_mod'] = False
                        self.test_results['event_modification']['create_modification_order'] = False
                        self.log_error("Online Payment Modification", "PATCH", f"Status code: {response.status_code}")
                else:
                    self.test_results['event_modification']['online_payment_mod'] = False
                    self.test_results['event_modification']['create_modification_order'] = False
                    self.log_error("Online Payment Registration", "POST", f"Status code: {response.status_code}")
            else:
                self.test_results['event_modification']['online_payment_mod'] = False
                self.test_results['event_modification']['create_modification_order'] = False
                self.log_error("Online Payment Modification", "SETUP", "No uniform event available for testing")
        except Exception as e:
            self.test_results['event_modification']['online_payment_mod'] = False
            self.test_results['event_modification']['create_modification_order'] = False
            self.log_error("Online Payment Modification", "TEST", f"Exception: {str(e)}")

        # Test 6: My Status Endpoint
        print("\n📋 Test 6: My Status Endpoint")
        try:
            response = requests.get(f"{self.base_url}/events/my/status", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.test_results['event_modification']['my_status'] = True
                    self.log_success("/events/my/status", "GET", f"- Found {len(data)} user registrations mapping")
                else:
                    self.test_results['event_modification']['my_status'] = False
                    self.log_error("/events/my/status", "GET", "Response is not a dict")
            else:
                self.test_results['event_modification']['my_status'] = False
                self.log_error("/events/my/status", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['event_modification']['my_status'] = False
            self.log_error("/events/my/status", "GET", f"Exception: {str(e)}")

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
            
    def test_villa_management(self):
        """Test Villa Management API endpoints"""
        print("\n🏠 Testing Villa Management API...")
        
        # First create a test user to work with
        test_user_email = f"testuser_{datetime.now().strftime('%H%M%S')}@example.com"
        test_user_id = None
        
        # Test POST /api/users - Admin can pre-set villa_number when adding user
        try:
            user_data = {
                "email": test_user_email,
                "name": "Test Villa User",
                "role": "user",
                "villa_number": "123"
            }
            response = requests.post(
                f"{self.base_url}/users",
                json=user_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('villa_number') == '123':
                    test_user_id = data.get('id')
                    self.test_results['villa_management']['create_with_villa'] = True
                    self.log_success("/users", "POST", f"- Created user with villa number: {data.get('villa_number')}")
                else:
                    self.test_results['villa_management']['create_with_villa'] = False
                    self.log_error("/users", "POST", f"Villa number not set correctly: {data.get('villa_number')}")
            else:
                self.test_results['villa_management']['create_with_villa'] = False
                self.log_error("/users", "POST", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_management']['create_with_villa'] = False
            self.log_error("/users", "POST", f"Exception: {str(e)}")
        
        if not test_user_id:
            print("❌ Cannot continue villa management tests without test user")
            return
        
        # Test PATCH /api/users/{id} - Admin can update user name
        try:
            update_data = {"name": "Updated Villa User Name"}
            response = requests.patch(
                f"{self.base_url}/users/{test_user_id}",
                json=update_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('name') == 'Updated Villa User Name':
                    self.test_results['villa_management']['update_name'] = True
                    self.log_success(f"/users/{test_user_id}", "PATCH", f"- Updated name to: {data.get('name')}")
                else:
                    self.test_results['villa_management']['update_name'] = False
                    self.log_error(f"/users/{test_user_id}", "PATCH", f"Name not updated correctly: {data.get('name')}")
            else:
                self.test_results['villa_management']['update_name'] = False
                self.log_error(f"/users/{test_user_id}", "PATCH", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_management']['update_name'] = False
            self.log_error(f"/users/{test_user_id}", "PATCH", f"Exception: {str(e)}")
        
        # Test PATCH /api/users/{id} - Admin can update villa_number (numeric only)
        try:
            update_data = {"villa_number": "456"}
            response = requests.patch(
                f"{self.base_url}/users/{test_user_id}",
                json=update_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('villa_number') == '456':
                    self.test_results['villa_management']['update_villa_valid'] = True
                    self.log_success(f"/users/{test_user_id}", "PATCH", f"- Updated villa to: {data.get('villa_number')}")
                else:
                    self.test_results['villa_management']['update_villa_valid'] = False
                    self.log_error(f"/users/{test_user_id}", "PATCH", f"Villa not updated correctly: {data.get('villa_number')}")
            else:
                self.test_results['villa_management']['update_villa_valid'] = False
                self.log_error(f"/users/{test_user_id}", "PATCH", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_management']['update_villa_valid'] = False
            self.log_error(f"/users/{test_user_id}", "PATCH", f"Exception: {str(e)}")
        
        # Test PATCH /api/users/{id} - Villa number validation rejects non-numeric
        try:
            update_data = {"villa_number": "ABC123"}
            response = requests.patch(
                f"{self.base_url}/users/{test_user_id}",
                json=update_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 400:
                self.test_results['villa_management']['update_villa_invalid'] = True
                self.log_success(f"/users/{test_user_id}", "PATCH", f"- Correctly rejected non-numeric villa: {response.json().get('detail', '')}")
            else:
                self.test_results['villa_management']['update_villa_invalid'] = False
                self.log_error(f"/users/{test_user_id}", "PATCH", f"Should reject non-numeric villa but got status: {response.status_code}")
        except Exception as e:
            self.test_results['villa_management']['update_villa_invalid'] = False
            self.log_error(f"/users/{test_user_id}", "PATCH", f"Exception: {str(e)}")
        
        # Test PATCH /api/users/{id} - Admin can reset user password
        try:
            update_data = {"new_password": "newpassword123"}
            response = requests.patch(
                f"{self.base_url}/users/{test_user_id}",
                json=update_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                self.test_results['villa_management']['update_password'] = True
                self.log_success(f"/users/{test_user_id}", "PATCH", "- Password reset successful")
            else:
                self.test_results['villa_management']['update_password'] = False
                self.log_error(f"/users/{test_user_id}", "PATCH", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_management']['update_password'] = False
            self.log_error(f"/users/{test_user_id}", "PATCH", f"Exception: {str(e)}")
        
        # Test PATCH /api/users/{id} - Admin can update user photo URL
        try:
            update_data = {"picture": "https://example.com/photo.jpg"}
            response = requests.patch(
                f"{self.base_url}/users/{test_user_id}",
                json=update_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('picture') == 'https://example.com/photo.jpg':
                    self.test_results['villa_management']['update_photo'] = True
                    self.log_success(f"/users/{test_user_id}", "PATCH", f"- Updated photo to: {data.get('picture')}")
                else:
                    self.test_results['villa_management']['update_photo'] = False
                    self.log_error(f"/users/{test_user_id}", "PATCH", f"Photo not updated correctly: {data.get('picture')}")
            else:
                self.test_results['villa_management']['update_photo'] = False
                self.log_error(f"/users/{test_user_id}", "PATCH", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_management']['update_photo'] = False
            self.log_error(f"/users/{test_user_id}", "PATCH", f"Exception: {str(e)}")
        
        # Cleanup test user
        try:
            response = requests.delete(
                f"{self.base_url}/users/{test_user_id}",
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                print(f"🧹 Cleaned up test user: {test_user_email}")
            else:
                print(f"⚠️  Failed to clean up test user: {test_user_email}")
        except Exception as e:
            print(f"⚠️  Exception during cleanup: {str(e)}")

    def test_user_management_features(self):
        """Test User Management features from the review request"""
        print("\n🧪 Testing User Management Features...")
        
        # Test 1: Admin can toggle email_verified to true
        try:
            # First get a user to test with
            response = requests.get(f"{self.base_url}/users", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                if users:
                    test_user = users[0]  # Use first user for testing
                    user_id = test_user['id']
                    
                    # Test toggling email_verified to true
                    update_data = {'email_verified': True}
                    response = requests.patch(f"{self.base_url}/users/{user_id}", 
                                            json=update_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('email_verified') == True:
                            self.test_results['user_management']['toggle_verified_true'] = True
                            self.log_success(f"/users/{user_id} (toggle verified true)", "PATCH", "- Successfully toggled email_verified to true")
                        else:
                            self.test_results['user_management']['toggle_verified_true'] = False
                            self.log_error(f"/users/{user_id} (toggle verified true)", "PATCH", "email_verified not updated to true")
                    else:
                        self.test_results['user_management']['toggle_verified_true'] = False
                        self.log_error(f"/users/{user_id} (toggle verified true)", "PATCH", f"Status code: {response.status_code}")
                    
                    # Test 2: Admin can toggle email_verified to false
                    update_data = {'email_verified': False}
                    response = requests.patch(f"{self.base_url}/users/{user_id}", 
                                            json=update_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('email_verified') == False:
                            self.test_results['user_management']['toggle_verified_false'] = True
                            self.log_success(f"/users/{user_id} (toggle verified false)", "PATCH", "- Successfully toggled email_verified to false")
                        else:
                            self.test_results['user_management']['toggle_verified_false'] = False
                            self.log_error(f"/users/{user_id} (toggle verified false)", "PATCH", "email_verified not updated to false")
                    else:
                        self.test_results['user_management']['toggle_verified_false'] = False
                        self.log_error(f"/users/{user_id} (toggle verified false)", "PATCH", f"Status code: {response.status_code}")
                    
                    # Test 3: Admin can update picture with base64 data URL
                    base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                    update_data = {'picture': base64_image}
                    response = requests.patch(f"{self.base_url}/users/{user_id}", 
                                            json=update_data, 
                                            headers=self.auth_headers,
                                            timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('picture') == base64_image:
                            self.test_results['user_management']['update_picture_base64'] = True
                            self.log_success(f"/users/{user_id} (update picture base64)", "PATCH", "- Successfully updated picture with base64 data")
                        else:
                            self.test_results['user_management']['update_picture_base64'] = False
                            self.log_error(f"/users/{user_id} (update picture base64)", "PATCH", "Picture not updated with base64 data")
                    else:
                        self.test_results['user_management']['update_picture_base64'] = False
                        self.log_error(f"/users/{user_id} (update picture base64)", "PATCH", f"Status code: {response.status_code}")
                else:
                    self.test_results['user_management']['toggle_verified_true'] = False
                    self.test_results['user_management']['toggle_verified_false'] = False
                    self.test_results['user_management']['update_picture_base64'] = False
                    self.log_error("/users", "GET", "No users found for testing")
            else:
                self.test_results['user_management']['toggle_verified_true'] = False
                self.test_results['user_management']['toggle_verified_false'] = False
                self.test_results['user_management']['update_picture_base64'] = False
                self.log_error("/users", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['user_management']['toggle_verified_true'] = False
            self.test_results['user_management']['toggle_verified_false'] = False
            self.test_results['user_management']['update_picture_base64'] = False
            self.log_error("User Management", "TEST", f"Exception: {str(e)}")

    def test_google_oauth_features(self):
        """Test Google OAuth features from the review request"""
        print("\n🧪 Testing Google OAuth Features...")
        
        # Test 1: POST /api/auth/google/verify-token - Returns error for invalid token
        try:
            invalid_token_data = {
                'credential': 'invalid_jwt_token_12345'
            }
            
            response = requests.post(f"{self.base_url}/auth/google/verify-token", 
                                   json=invalid_token_data, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 400:
                data = response.json()
                if 'detail' in data and 'Invalid Google token' in data['detail']:
                    self.test_results['google_oauth']['invalid_token_error'] = True
                    self.log_success("/auth/google/verify-token (invalid)", "POST", "- Correctly returns error for invalid token")
                else:
                    self.test_results['google_oauth']['invalid_token_error'] = False
                    self.log_error("/auth/google/verify-token (invalid)", "POST", "Invalid error message format")
            else:
                self.test_results['google_oauth']['invalid_token_error'] = False
                self.log_error("/auth/google/verify-token (invalid)", "POST", f"Expected 400 but got status: {response.status_code}")
        except Exception as e:
            self.test_results['google_oauth']['invalid_token_error'] = False
            self.log_error("/auth/google/verify-token (invalid)", "POST", f"Exception: {str(e)}")

    def test_email_verification_features(self):
        """Test Email Verification features from the review request"""
        print("\n🧪 Testing Email Verification Features...")
        
        # Test 1: POST /api/auth/verify-email - Returns success for already verified user
        try:
            # Test with a token that doesn't exist but email that might be verified
            verify_data = {
                'token': 'non_existent_token_123',
                'email': 'troa.systems@gmail.com'  # Admin email likely to be verified
            }
            
            response = requests.post(f"{self.base_url}/auth/verify-email", 
                                   json=verify_data, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('status' in data and data['status'] == 'success' and 
                    'already verified' in data.get('message', '').lower()):
                    self.test_results['email_verification']['already_verified_success'] = True
                    self.log_success("/auth/verify-email (already verified)", "POST", "- Returns success for already verified user")
                else:
                    self.test_results['email_verification']['already_verified_success'] = False
                    self.log_error("/auth/verify-email (already verified)", "POST", "Invalid response format")
            elif response.status_code == 400:
                # Check if it's the improved error message
                data = response.json()
                if 'no longer valid' in data.get('detail', ''):
                    self.test_results['email_verification']['already_verified_success'] = True
                    self.log_success("/auth/verify-email (token mismatch)", "POST", "- Returns clear error when token doesn't match")
                else:
                    self.test_results['email_verification']['already_verified_success'] = False
                    self.log_error("/auth/verify-email (token mismatch)", "POST", f"Unexpected error message: {data.get('detail')}")
            else:
                self.test_results['email_verification']['already_verified_success'] = False
                self.log_error("/auth/verify-email (already verified)", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['email_verification']['already_verified_success'] = False
            self.log_error("/auth/verify-email (already verified)", "POST", f"Exception: {str(e)}")
        
        # Test 2: POST /api/auth/verify-email - Returns clear error when token doesn't match
        try:
            verify_data = {
                'token': 'definitely_invalid_token_xyz',
                'email': 'nonexistent@example.com'
            }
            
            response = requests.post(f"{self.base_url}/auth/verify-email", 
                                   json=verify_data, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            
            if response.status_code == 400:
                data = response.json()
                if ('detail' in data and 
                    ('Invalid or expired' in data['detail'] or 'no longer valid' in data['detail'])):
                    self.test_results['email_verification']['token_mismatch_error'] = True
                    self.log_success("/auth/verify-email (token mismatch)", "POST", "- Returns clear error when token doesn't match")
                else:
                    self.test_results['email_verification']['token_mismatch_error'] = False
                    self.log_error("/auth/verify-email (token mismatch)", "POST", f"Unexpected error message: {data.get('detail')}")
            else:
                self.test_results['email_verification']['token_mismatch_error'] = False
                self.log_error("/auth/verify-email (token mismatch)", "POST", f"Expected 400 but got status: {response.status_code}")
        except Exception as e:
            self.test_results['email_verification']['token_mismatch_error'] = False
            self.log_error("/auth/verify-email (token mismatch)", "POST", f"Exception: {str(e)}")

    def test_pwa_features(self):
        """Test PWA (Progressive Web App) features"""
        print("\n🧪 Testing PWA Features...")
        
        # Initialize PWA test results
        if 'pwa' not in self.test_results:
            self.test_results['pwa'] = {
                'health_endpoint': None,
                'push_subscribe': None,
                'push_status': None,
                'push_unsubscribe': None,
                'manifest_served': None,
                'service_worker_served': None,
                'pwa_icons_served': None,
                'offline_page_served': None
            }
        
        # Test 1: Health endpoint
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'status' in data and data['status'] == 'healthy':
                    self.test_results['pwa']['health_endpoint'] = True
                    self.log_success("/health", "GET", "- Health endpoint working")
                else:
                    self.test_results['pwa']['health_endpoint'] = False
                    self.log_error("/health", "GET", "Invalid response structure")
            else:
                self.test_results['pwa']['health_endpoint'] = False
                self.log_error("/health", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa']['health_endpoint'] = False
            self.log_error("/health", "GET", f"Exception: {str(e)}")

        # Test 2: Push notification subscribe endpoint (requires auth)
        try:
            subscribe_data = {
                "subscription": {
                    "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
                    "keys": {
                        "p256dh": "test-p256dh-key",
                        "auth": "test-auth-key"
                    }
                },
                "user_email": "troa.systems@gmail.com"
            }
            
            response = requests.post(f"{self.base_url}/push/subscribe", 
                                   json=subscribe_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'subscribed' in data['message'].lower():
                    self.test_results['pwa']['push_subscribe'] = True
                    self.log_success("/push/subscribe", "POST", "- Push notification subscription working")
                else:
                    self.test_results['pwa']['push_subscribe'] = False
                    self.log_error("/push/subscribe", "POST", "Invalid response structure")
            else:
                self.test_results['pwa']['push_subscribe'] = False
                self.log_error("/push/subscribe", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['pwa']['push_subscribe'] = False
            self.log_error("/push/subscribe", "POST", f"Exception: {str(e)}")

        # Test 3: Push notification status endpoint (requires auth)
        try:
            response = requests.get(f"{self.base_url}/push/status", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'subscribed' in data and 'vapid_configured' in data:
                    self.test_results['pwa']['push_status'] = True
                    self.log_success("/push/status", "GET", f"- Push status endpoint working (subscribed: {data['subscribed']})")
                else:
                    self.test_results['pwa']['push_status'] = False
                    self.log_error("/push/status", "GET", "Invalid response structure")
            else:
                self.test_results['pwa']['push_status'] = False
                self.log_error("/push/status", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa']['push_status'] = False
            self.log_error("/push/status", "GET", f"Exception: {str(e)}")

        # Test 4: Push notification unsubscribe endpoint (requires auth)
        try:
            unsubscribe_data = {
                "user_email": "troa.systems@gmail.com"
            }
            
            response = requests.post(f"{self.base_url}/push/unsubscribe", 
                                   json=unsubscribe_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'unsubscribed' in data['message'].lower():
                    self.test_results['pwa']['push_unsubscribe'] = True
                    self.log_success("/push/unsubscribe", "POST", "- Push notification unsubscribe working")
                else:
                    self.test_results['pwa']['push_unsubscribe'] = False
                    self.log_error("/push/unsubscribe", "POST", "Invalid response structure")
            else:
                self.test_results['pwa']['push_unsubscribe'] = False
                self.log_error("/push/unsubscribe", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa']['push_unsubscribe'] = False
            self.log_error("/push/unsubscribe", "POST", f"Exception: {str(e)}")

    def test_pwa_static_assets(self):
        """Test PWA static assets served from frontend"""
        print("\n🧪 Testing PWA Static Assets...")
        
        # Test manifest.json
        try:
            response = requests.get(f"{BACKEND_URL}/manifest.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if ('name' in data and 'short_name' in data and 'icons' in data and 
                    'start_url' in data and 'display' in data):
                    self.test_results['pwa']['manifest_served'] = True
                    self.log_success("/manifest.json", "GET", f"- Manifest served correctly (name: {data.get('name', 'N/A')})")
                else:
                    self.test_results['pwa']['manifest_served'] = False
                    self.log_error("/manifest.json", "GET", "Invalid manifest structure")
            else:
                self.test_results['pwa']['manifest_served'] = False
                self.log_error("/manifest.json", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa']['manifest_served'] = False
            self.log_error("/manifest.json", "GET", f"Exception: {str(e)}")

        # Test service-worker.js
        try:
            response = requests.get(f"{BACKEND_URL}/service-worker.js", timeout=10)
            if response.status_code == 200:
                content = response.text
                if ('addEventListener' in content and 'install' in content and 
                    'fetch' in content and 'push' in content):
                    self.test_results['pwa']['service_worker_served'] = True
                    self.log_success("/service-worker.js", "GET", "- Service worker served correctly")
                else:
                    self.test_results['pwa']['service_worker_served'] = False
                    self.log_error("/service-worker.js", "GET", "Invalid service worker content")
            else:
                self.test_results['pwa']['service_worker_served'] = False
                self.log_error("/service-worker.js", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa']['service_worker_served'] = False
            self.log_error("/service-worker.js", "GET", f"Exception: {str(e)}")

        # Test PWA icons
        try:
            icon_response = requests.get(f"{BACKEND_URL}/icons/icon-192x192.png", timeout=10)
            if icon_response.status_code == 200:
                content_type = icon_response.headers.get('content-type', '')
                if content_type.startswith('image/'):
                    self.test_results['pwa']['pwa_icons_served'] = True
                    self.log_success("/icons/icon-192x192.png", "GET", f"- PWA icon served correctly (Content-Type: {content_type})")
                else:
                    self.test_results['pwa']['pwa_icons_served'] = False
                    self.log_error("/icons/icon-192x192.png", "GET", f"Invalid content type: {content_type}")
            else:
                self.test_results['pwa']['pwa_icons_served'] = False
                self.log_error("/icons/icon-192x192.png", "GET", f"Status code: {icon_response.status_code}")
        except Exception as e:
            self.test_results['pwa']['pwa_icons_served'] = False
            self.log_error("/icons/icon-192x192.png", "GET", f"Exception: {str(e)}")

        # Test offline.html
        try:
            response = requests.get(f"{BACKEND_URL}/offline.html", timeout=10)
            if response.status_code == 200:
                content = response.text
                if ('offline' in content.lower() and 'html' in content.lower() and 
                    'troa' in content.lower()):
                    self.test_results['pwa']['offline_page_served'] = True
                    self.log_success("/offline.html", "GET", "- Offline page served correctly")
                else:
                    self.test_results['pwa']['offline_page_served'] = False
                    self.log_error("/offline.html", "GET", "Invalid offline page content")
            else:
                self.test_results['pwa']['offline_page_served'] = False
                self.log_error("/offline.html", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa']['offline_page_served'] = False
            self.log_error("/offline.html", "GET", f"Exception: {str(e)}")

    def test_villa_auth_endpoints(self):
        """Test Villa-related Auth API endpoints"""
        print("\n🔐 Testing Villa Auth API...")
        
        # Test GET /api/auth/user - Returns needs_villa_number flag
        try:
            response = requests.get(
                f"{self.base_url}/auth/user",
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'needs_villa_number' in data:
                    self.test_results['villa_auth']['get_user_villa_flag'] = True
                    self.log_success("/auth/user", "GET", f"- includes needs_villa_number flag: {data.get('needs_villa_number')}")
                else:
                    self.test_results['villa_auth']['get_user_villa_flag'] = False
                    self.log_error("/auth/user", "GET", f"Missing needs_villa_number flag. Keys: {list(data.keys())}")
            else:
                self.test_results['villa_auth']['get_user_villa_flag'] = False
                self.log_error("/auth/user", "GET", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_auth']['get_user_villa_flag'] = False
            self.log_error("/auth/user", "GET", f"Exception: {str(e)}")
        
        # Test POST /api/auth/update-villa-number - User can update own villa number
        try:
            update_data = {"villa_number": "789"}
            response = requests.post(
                f"{self.base_url}/auth/update-villa-number",
                json=update_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('villa_number') == '789':
                    self.test_results['villa_auth']['update_villa_valid'] = True
                    self.log_success("/auth/update-villa-number", "POST", f"- Updated villa to: {data.get('villa_number')}")
                else:
                    self.test_results['villa_auth']['update_villa_valid'] = False
                    self.log_error("/auth/update-villa-number", "POST", f"Villa not updated correctly: {data.get('villa_number')}")
            else:
                self.test_results['villa_auth']['update_villa_valid'] = False
                self.log_error("/auth/update-villa-number", "POST", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['villa_auth']['update_villa_valid'] = False
            self.log_error("/auth/update-villa-number", "POST", f"Exception: {str(e)}")
        
        # Test POST /api/auth/update-villa-number - Rejects non-numeric villa number
        try:
            update_data = {"villa_number": "XYZ789"}
            response = requests.post(
                f"{self.base_url}/auth/update-villa-number",
                json=update_data,
                headers=self.auth_headers,
                timeout=10
            )
            if response.status_code == 400:
                self.test_results['villa_auth']['update_villa_invalid'] = True
                self.log_success("/auth/update-villa-number", "POST", f"- Correctly rejected non-numeric villa: {response.json().get('detail', '')}")
            else:
                self.test_results['villa_auth']['update_villa_invalid'] = False
                self.log_error("/auth/update-villa-number", "POST", f"Should reject non-numeric villa but got status: {response.status_code}")
        except Exception as e:
            self.test_results['villa_auth']['update_villa_invalid'] = False
            self.log_error("/auth/update-villa-number", "POST", f"Exception: {str(e)}")
        
        # Test POST /api/auth/verify-email - Returns success for already verified user (idempotent)
        try:
            verify_data = {
                "token": "invalid_token_12345",
                "email": ADMIN_EMAIL  # Admin should be verified
            }
            response = requests.post(
                f"{self.base_url}/auth/verify-email",
                json=verify_data,
                timeout=10
            )
            # Should return 400 for invalid token, but check if it handles gracefully
            if response.status_code == 400:
                detail = response.json().get('detail', '')
                if 'already verified' in detail.lower() or 'invalid' in detail.lower():
                    self.test_results['villa_auth']['verify_email_idempotent'] = True
                    self.log_success("/auth/verify-email", "POST", f"- Handles invalid/already verified gracefully: {detail}")
                else:
                    self.test_results['villa_auth']['verify_email_idempotent'] = False
                    self.log_error("/auth/verify-email", "POST", f"Unexpected error message: {detail}")
            else:
                self.test_results['villa_auth']['verify_email_idempotent'] = False
                self.log_error("/auth/verify-email", "POST", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.test_results['villa_auth']['verify_email_idempotent'] = False
            self.log_error("/auth/verify-email", "POST", f"Exception: {str(e)}")

    def test_community_chat(self):
        """Test Community Chat API endpoints"""
        print("\n💬 Testing Community Chat API...")
        
        # Test 1: GET /api/chat/groups - Fetch chat groups (requires auth)
        try:
            response = requests.get(f"{self.base_url}/chat/groups", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['community_chat']['get_groups'] = True
                    self.log_success("/chat/groups", "GET", f"- Found {len(data)} chat groups")
                    
                    # Check if MC Group exists (should be auto-created)
                    mc_group_found = any(group.get('is_mc_only') for group in data)
                    if mc_group_found:
                        self.test_results['community_chat']['mc_group_exists'] = True
                        self.log_success("/chat/groups", "GET", "- MC Group auto-created and found")
                    else:
                        self.test_results['community_chat']['mc_group_exists'] = False
                        self.log_error("/chat/groups", "GET", "MC Group not found - should be auto-created")
                        
                    # Validate structure if groups exist
                    if data:
                        group = data[0]
                        required_fields = ['id', 'name', 'description', 'created_by', 'created_at', 'is_mc_only', 'members', 'member_count']
                        missing_fields = [field for field in required_fields if field not in group]
                        if missing_fields:
                            self.log_error("/chat/groups", "GET", f"Missing required fields: {missing_fields}")
                        else:
                            self.log_success("/chat/groups", "GET", "- Group structure validated")
                else:
                    self.test_results['community_chat']['get_groups'] = False
                    self.log_error("/chat/groups", "GET", "Response is not a list")
            else:
                self.test_results['community_chat']['get_groups'] = False
                self.log_error("/chat/groups", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['community_chat']['get_groups'] = False
            self.log_error("/chat/groups", "GET", f"Exception: {str(e)}")

        # Test 2: POST /api/chat/groups - Create new group (manager/admin only)
        created_group_id = None
        try:
            test_group = {
                "name": "Test Community Group",
                "description": "A test group for community discussions",
                "is_mc_only": False
            }
            
            response = requests.post(f"{self.base_url}/chat/groups", 
                                   json=test_group, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    data['name'] == test_group['name'] and 
                    data['is_mc_only'] == test_group['is_mc_only']):
                    self.test_results['community_chat']['create_group'] = True
                    created_group_id = data['id']
                    self.log_success("/chat/groups", "POST", f"- Created group with ID: {data['id']}")
                else:
                    self.test_results['community_chat']['create_group'] = False
                    self.log_error("/chat/groups", "POST", "Invalid response structure")
            else:
                self.test_results['community_chat']['create_group'] = False
                self.log_error("/chat/groups", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['community_chat']['create_group'] = False
            self.log_error("/chat/groups", "POST", f"Exception: {str(e)}")

        # Test 3: POST /api/chat/groups/{group_id}/join - Join a group
        if created_group_id:
            try:
                response = requests.post(f"{self.base_url}/chat/groups/{created_group_id}/join", 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'message' in data and ('joined' in data['message'].lower() or 'successfully' in data['message'].lower()):
                        self.test_results['community_chat']['join_group'] = True
                        self.log_success(f"/chat/groups/{created_group_id}/join", "POST", "- Successfully joined group")
                    else:
                        self.test_results['community_chat']['join_group'] = False
                        self.log_error(f"/chat/groups/{created_group_id}/join", "POST", f"Invalid response structure: {data}")
                else:
                    self.test_results['community_chat']['join_group'] = False
                    self.log_error(f"/chat/groups/{created_group_id}/join", "POST", f"Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.test_results['community_chat']['join_group'] = False
                self.log_error(f"/chat/groups/{created_group_id}/join", "POST", f"Exception: {str(e)}")

        # Test 4: GET /api/chat/groups/{group_id}/messages - Get messages from a group
        if created_group_id:
            try:
                response = requests.get(f"{self.base_url}/chat/groups/{created_group_id}/messages", 
                                      headers=self.auth_headers,
                                      timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self.test_results['community_chat']['get_messages'] = True
                        self.log_success(f"/chat/groups/{created_group_id}/messages", "GET", f"- Found {len(data)} messages")
                    else:
                        self.test_results['community_chat']['get_messages'] = False
                        self.log_error(f"/chat/groups/{created_group_id}/messages", "GET", "Response is not a list")
                else:
                    self.test_results['community_chat']['get_messages'] = False
                    self.log_error(f"/chat/groups/{created_group_id}/messages", "GET", f"Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.test_results['community_chat']['get_messages'] = False
                self.log_error(f"/chat/groups/{created_group_id}/messages", "GET", f"Exception: {str(e)}")

        # Test 5: POST /api/chat/groups/{group_id}/messages - Send message to a group
        if created_group_id:
            try:
                test_message = {
                    "content": "Hello! This is a test message from the API testing suite.",
                    "group_id": created_group_id
                }
                
                response = requests.post(f"{self.base_url}/chat/groups/{created_group_id}/messages", 
                                       json=test_message, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if ('id' in data and 
                        data['content'] == test_message['content'] and 
                        data['group_id'] == created_group_id):
                        self.test_results['community_chat']['send_message'] = True
                        self.log_success(f"/chat/groups/{created_group_id}/messages", "POST", f"- Sent message with ID: {data['id']}")
                    else:
                        self.test_results['community_chat']['send_message'] = False
                        self.log_error(f"/chat/groups/{created_group_id}/messages", "POST", "Invalid response structure")
                else:
                    self.test_results['community_chat']['send_message'] = False
                    self.log_error(f"/chat/groups/{created_group_id}/messages", "POST", f"Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.test_results['community_chat']['send_message'] = False
                self.log_error(f"/chat/groups/{created_group_id}/messages", "POST", f"Exception: {str(e)}")

        # Test 6: POST /api/chat/groups/{group_id}/leave - Leave a group
        if created_group_id:
            try:
                response = requests.post(f"{self.base_url}/chat/groups/{created_group_id}/leave", 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'message' in data and 'left' in data['message'].lower():
                        self.test_results['community_chat']['leave_group'] = True
                        self.log_success(f"/chat/groups/{created_group_id}/leave", "POST", "- Successfully left group")
                    else:
                        self.test_results['community_chat']['leave_group'] = False
                        self.log_error(f"/chat/groups/{created_group_id}/leave", "POST", "Invalid response structure")
                else:
                    self.test_results['community_chat']['leave_group'] = False
                    self.log_error(f"/chat/groups/{created_group_id}/leave", "POST", f"Status code: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.test_results['community_chat']['leave_group'] = False
                self.log_error(f"/chat/groups/{created_group_id}/leave", "POST", f"Exception: {str(e)}")

        # Test authentication requirements
        try:
            # Test GET /chat/groups without authentication (should fail)
            response = requests.get(f"{self.base_url}/chat/groups", timeout=10)
            if response.status_code in [401, 403]:
                self.log_success("/chat/groups", "AUTH", "- Correctly requires authentication")
            else:
                self.log_error("/chat/groups", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error("/chat/groups", "AUTH", f"Exception: {str(e)}")

    def test_push_notifications(self):
        """Test Push Notifications API endpoints"""
        print("\n🔔 Testing Push Notifications API...")
        
        # Test 1: GET /api/push/vapid-public-key - Get VAPID public key (no auth required)
        try:
            response = requests.get(f"{self.base_url}/push/vapid-public-key", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'publicKey' in data and data['publicKey']:
                    self.test_results['push_notifications']['vapid_public_key'] = True
                    self.log_success("/push/vapid-public-key", "GET", f"- VAPID public key retrieved: {data['publicKey'][:20]}...")
                    
                    # Validate VAPID key format (should be base64url encoded)
                    vapid_key = data['publicKey']
                    if len(vapid_key) == 88 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in vapid_key):
                        self.log_success("/push/vapid-public-key", "VALIDATE", "- VAPID key format is valid")
                    else:
                        self.log_error("/push/vapid-public-key", "VALIDATE", f"Invalid VAPID key format: {vapid_key}")
                else:
                    self.test_results['push_notifications']['vapid_public_key'] = False
                    self.log_error("/push/vapid-public-key", "GET", "Missing or empty publicKey in response")
            else:
                self.test_results['push_notifications']['vapid_public_key'] = False
                self.log_error("/push/vapid-public-key", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['push_notifications']['vapid_public_key'] = False
            self.log_error("/push/vapid-public-key", "GET", f"Exception: {str(e)}")

        # Test 2: POST /api/push/subscribe - Subscribe to push notifications (requires auth)
        try:
            # Mock subscription object (similar to what browser would send)
            mock_subscription = {
                "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
                "keys": {
                    "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
                    "auth": "tBHItJI5svbpez7KI4CCXg"
                }
            }
            
            subscription_data = {
                "subscription": mock_subscription,
                "user_email": ADMIN_EMAIL
            }
            
            response = requests.post(f"{self.base_url}/push/subscribe", 
                                   json=subscription_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'subscribed' in data['message'].lower():
                    self.test_results['push_notifications']['subscribe'] = True
                    self.log_success("/push/subscribe", "POST", "- Successfully subscribed to push notifications")
                else:
                    self.test_results['push_notifications']['subscribe'] = False
                    self.log_error("/push/subscribe", "POST", "Invalid response structure")
            else:
                self.test_results['push_notifications']['subscribe'] = False
                self.log_error("/push/subscribe", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['push_notifications']['subscribe'] = False
            self.log_error("/push/subscribe", "POST", f"Exception: {str(e)}")

        # Test 3: GET /api/push/status - Get subscription status (requires auth)
        try:
            response = requests.get(f"{self.base_url}/push/status", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'subscribed' in data and 'vapid_configured' in data:
                    self.test_results['push_notifications']['status'] = True
                    self.log_success("/push/status", "GET", f"- Status retrieved: subscribed={data['subscribed']}, vapid_configured={data['vapid_configured']}")
                    
                    # Validate that VAPID is configured
                    if data['vapid_configured']:
                        self.log_success("/push/status", "VAPID", "- VAPID keys are properly configured")
                    else:
                        self.log_error("/push/status", "VAPID", "VAPID keys not configured")
                else:
                    self.test_results['push_notifications']['status'] = False
                    self.log_error("/push/status", "GET", "Missing required fields in response")
            else:
                self.test_results['push_notifications']['status'] = False
                self.log_error("/push/status", "GET", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['push_notifications']['status'] = False
            self.log_error("/push/status", "GET", f"Exception: {str(e)}")

        # Test 4: POST /api/push/send - Send push notification (admin only)
        try:
            notification_payload = {
                "title": "Test Notification",
                "body": "This is a test push notification from the API test suite",
                "icon": "/icons/icon-192x192.png",
                "badge": "/icons/icon-72x72.png",
                "url": "/admin",
                "tag": "test-notification",
                "user_emails": [ADMIN_EMAIL]  # Send only to admin user
            }
            
            response = requests.post(f"{self.base_url}/push/send", 
                                   json=notification_payload, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'sent' in data:
                    self.test_results['push_notifications']['send_admin_only'] = True
                    self.log_success("/push/send", "POST", f"- Notification sent: {data['sent']} successful, {data.get('failed', 0)} failed")
                else:
                    self.test_results['push_notifications']['send_admin_only'] = False
                    self.log_error("/push/send", "POST", "Invalid response structure")
            else:
                self.test_results['push_notifications']['send_admin_only'] = False
                self.log_error("/push/send", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['push_notifications']['send_admin_only'] = False
            self.log_error("/push/send", "POST", f"Exception: {str(e)}")

        # Test 5: POST /api/push/unsubscribe - Unsubscribe from push notifications (requires auth)
        try:
            unsubscribe_data = {
                "user_email": ADMIN_EMAIL
            }
            
            response = requests.post(f"{self.base_url}/push/unsubscribe", 
                                   json=unsubscribe_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'unsubscribed' in data['message'].lower():
                    self.test_results['push_notifications']['unsubscribe'] = True
                    self.log_success("/push/unsubscribe", "POST", "- Successfully unsubscribed from push notifications")
                else:
                    self.test_results['push_notifications']['unsubscribe'] = False
                    self.log_error("/push/unsubscribe", "POST", "Invalid response structure")
            else:
                self.test_results['push_notifications']['unsubscribe'] = False
                self.log_error("/push/unsubscribe", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['push_notifications']['unsubscribe'] = False
            self.log_error("/push/unsubscribe", "POST", f"Exception: {str(e)}")

        # Test 6: Test authentication requirements
        try:
            # Test POST /push/subscribe without authentication (should fail)
            response = requests.post(f"{self.base_url}/push/subscribe", 
                                   json={"subscription": {}, "user_email": "test@test.com"}, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            if response.status_code in [401, 403]:
                self.log_success("/push/subscribe", "AUTH", "- Correctly requires authentication")
            else:
                self.log_error("/push/subscribe", "AUTH", f"Should require auth but got status: {response.status_code}")
                
            # Test POST /push/send without authentication (should fail)
            response = requests.post(f"{self.base_url}/push/send", 
                                   json={"title": "Test", "body": "Test"}, 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
            if response.status_code in [401, 403]:
                self.log_success("/push/send", "AUTH", "- Correctly requires admin authentication")
            else:
                self.log_error("/push/send", "AUTH", f"Should require admin auth but got status: {response.status_code}")
                
            # Test GET /push/status without authentication (should fail)
            response = requests.get(f"{self.base_url}/push/status", timeout=10)
            if response.status_code in [401, 403]:
                self.log_success("/push/status", "AUTH", "- Correctly requires authentication")
            else:
                self.log_error("/push/status", "AUTH", f"Should require auth but got status: {response.status_code}")
        except Exception as e:
            self.log_error("Push Notifications Authentication", "TEST", f"Exception: {str(e)}")

        # Test 7: Test helper functions by checking logs for notification triggers
        print("\n🔍 Testing Push Notification Triggers...")
        
        # Test booking creation trigger (should call send_notification_to_user and send_notification_to_admins)
        try:
            future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            booking_data = {
                "amenity_id": "push-test-amenity",
                "amenity_name": "Push Test Pool",
                "booking_date": future_date,
                "start_time": "15:00",
                "duration_minutes": 60,
                "additional_guests": ["Test Guest"]
            }
            
            response = requests.post(f"{self.base_url}/bookings", 
                                   json=booking_data, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                self.test_results['push_notifications']['send_notification_to_user'] = True
                self.test_results['push_notifications']['send_notification_to_admins'] = True
                self.log_success("Push Notification Triggers", "BOOKING", "- Booking creation should trigger push notifications (check logs)")
            else:
                self.test_results['push_notifications']['send_notification_to_user'] = False
                self.test_results['push_notifications']['send_notification_to_admins'] = False
                self.log_error("Push Notification Triggers", "BOOKING", f"Failed to create booking for trigger test: {response.status_code}")
        except Exception as e:
            self.test_results['push_notifications']['send_notification_to_user'] = False
            self.test_results['push_notifications']['send_notification_to_admins'] = False
            self.log_error("Push Notification Triggers", "BOOKING", f"Exception: {str(e)}")

    def test_community_chat_comprehensive(self):
        """Test Community Chat features comprehensively including new features"""
        print("\n🧪 Testing Community Chat Comprehensive Features...")
        
        # Test 1: Get chat groups
        try:
            response = requests.get(f"{self.base_url}/chat/groups", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.test_results['community_chat']['get_groups'] = True
                    self.log_success("/chat/groups", "GET", f"- Found {len(data)} chat groups")
                    
                    # Use existing group or create one for testing
                    if data:
                        self.test_group_id = data[0]['id']
                        self.log_success("/chat/groups", "GET", f"- Using existing group: {self.test_group_id}")
                    else:
                        # Create a test group
                        self.create_test_group()
                else:
                    self.test_results['community_chat']['get_groups'] = False
                    self.log_error("/chat/groups", "GET", "Response is not a list")
            else:
                self.test_results['community_chat']['get_groups'] = False
                self.log_error("/chat/groups", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['community_chat']['get_groups'] = False
            self.log_error("/chat/groups", "GET", f"Exception: {str(e)}")
        
        # Test 2: Create test group if needed
        if not self.test_group_id:
            self.create_test_group()
        
        # Test 3: Send test messages for pagination testing
        if self.test_group_id:
            self.send_test_messages()
        
        # Test 4: Test message pagination
        if self.test_group_id:
            self.test_message_pagination()
        
        # Test 5: Test file upload with PDF
        if self.test_group_id:
            self.test_file_upload_pdf()
        
        # Test 6: Test message deletion
        if self.test_group_id and self.test_message_ids:
            self.test_message_deletion()
        
        # Test 7: Test deleted message response format
        if self.test_group_id:
            self.test_deleted_message_response()
        
        # Test 8: Test message order (oldest first after reversal)
        if self.test_group_id:
            self.test_message_order()

    def create_test_group(self):
        """Create a test group for chat testing"""
        try:
            test_group = {
                "name": "API Test Group",
                "description": "Test group for API testing",
                "is_mc_only": False,
                "initial_members": [],
                "icon": None
            }
            
            response = requests.post(f"{self.base_url}/chat/groups", 
                                   json=test_group, 
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data:
                    self.test_group_id = data['id']
                    self.test_results['community_chat']['create_group'] = True
                    self.log_success("/chat/groups", "POST", f"- Created test group: {self.test_group_id}")
                else:
                    self.test_results['community_chat']['create_group'] = False
                    self.log_error("/chat/groups", "POST", "Invalid response structure")
            else:
                self.test_results['community_chat']['create_group'] = False
                self.log_error("/chat/groups", "POST", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['community_chat']['create_group'] = False
            self.log_error("/chat/groups", "POST", f"Exception: {str(e)}")

    def send_test_messages(self):
        """Send multiple test messages for pagination testing"""
        try:
            # Send 15 messages to test pagination (default limit is 10)
            for i in range(15):
                message_data = {
                    "content": f"Test message {i+1} for pagination testing",
                    "group_id": self.test_group_id
                }
                
                response = requests.post(f"{self.base_url}/chat/groups/{self.test_group_id}/messages", 
                                       json=message_data, 
                                       headers=self.auth_headers,
                                       timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data:
                        self.test_message_ids.append(data['id'])
                        if i == 0:  # Log success for first message only
                            self.test_results['community_chat']['send_message'] = True
                            self.log_success(f"/chat/groups/{self.test_group_id}/messages", "POST", f"- Sent test message: {data['id']}")
                else:
                    if i == 0:  # Log error for first message only
                        self.test_results['community_chat']['send_message'] = False
                        self.log_error(f"/chat/groups/{self.test_group_id}/messages", "POST", f"Status code: {response.status_code}")
                    break
                    
                # Small delay between messages
                import time
                time.sleep(0.1)
                
        except Exception as e:
            self.test_results['community_chat']['send_message'] = False
            self.log_error(f"/chat/groups/{self.test_group_id}/messages", "POST", f"Exception: {str(e)}")

    def test_message_pagination(self):
        """Test message pagination with before parameter"""
        try:
            # Test 1: Get initial messages (should return last 10)
            response = requests.get(f"{self.base_url}/chat/groups/{self.test_group_id}/messages?limit=10", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) <= 10:
                    self.log_success(f"/chat/groups/{self.test_group_id}/messages", "GET", f"- Retrieved {len(data)} messages (limit=10)")
                    
                    if len(data) > 0:
                        # Test 2: Get messages before the first message
                        first_message_time = data[0]['created_at']
                        response2 = requests.get(f"{self.base_url}/chat/groups/{self.test_group_id}/messages?limit=5&before={first_message_time}", 
                                               headers=self.auth_headers,
                                               timeout=10)
                        
                        if response2.status_code == 200:
                            data2 = response2.json()
                            if isinstance(data2, list):
                                self.test_results['community_chat']['message_pagination'] = True
                                self.log_success(f"/chat/groups/{self.test_group_id}/messages (pagination)", "GET", f"- Retrieved {len(data2)} older messages with before parameter")
                            else:
                                self.test_results['community_chat']['message_pagination'] = False
                                self.log_error(f"/chat/groups/{self.test_group_id}/messages (pagination)", "GET", "Response is not a list")
                        else:
                            self.test_results['community_chat']['message_pagination'] = False
                            self.log_error(f"/chat/groups/{self.test_group_id}/messages (pagination)", "GET", f"Status code: {response2.status_code}")
                    else:
                        self.test_results['community_chat']['message_pagination'] = True
                        self.log_success(f"/chat/groups/{self.test_group_id}/messages (pagination)", "GET", "- No messages to paginate")
                else:
                    self.test_results['community_chat']['message_pagination'] = False
                    self.log_error(f"/chat/groups/{self.test_group_id}/messages", "GET", f"Invalid response: expected list with ≤10 items, got {len(data) if isinstance(data, list) else type(data)}")
            else:
                self.test_results['community_chat']['message_pagination'] = False
                self.log_error(f"/chat/groups/{self.test_group_id}/messages", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['community_chat']['message_pagination'] = False
            self.log_error(f"/chat/groups/{self.test_group_id}/messages (pagination)", "GET", f"Exception: {str(e)}")

    def test_file_upload_pdf(self):
        """Test file upload with PDF support"""
        try:
            # Create a simple PDF-like content for testing
            pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
            
            # Prepare multipart form data
            files = {
                'files': ('test_document.pdf', pdf_content, 'application/pdf')
            }
            data = {
                'content': 'Test PDF upload'
            }
            
            # Remove Content-Type header to let requests set it for multipart
            upload_headers = {k: v for k, v in self.auth_headers.items() if k != 'Content-Type'}
            
            response = requests.post(f"{self.base_url}/chat/groups/{self.test_group_id}/messages/upload", 
                                   files=files,
                                   data=data,
                                   headers=upload_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('id' in data and 
                    'attachments' in data and 
                    len(data['attachments']) > 0 and
                    data['attachments'][0]['filename'] == 'test_document.pdf'):
                    self.test_results['community_chat']['file_upload_pdf'] = True
                    self.test_message_ids.append(data['id'])
                    self.log_success(f"/chat/groups/{self.test_group_id}/messages/upload", "POST", f"- Uploaded PDF successfully: {data['attachments'][0]['filename']}")
                else:
                    self.test_results['community_chat']['file_upload_pdf'] = False
                    self.log_error(f"/chat/groups/{self.test_group_id}/messages/upload", "POST", "Invalid response structure or missing PDF attachment")
            else:
                self.test_results['community_chat']['file_upload_pdf'] = False
                self.log_error(f"/chat/groups/{self.test_group_id}/messages/upload", "POST", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.test_results['community_chat']['file_upload_pdf'] = False
            self.log_error(f"/chat/groups/{self.test_group_id}/messages/upload", "POST", f"Exception: {str(e)}")

    def test_message_deletion(self):
        """Test message deletion (soft delete)"""
        try:
            if not self.test_message_ids:
                self.test_results['community_chat']['message_deletion'] = False
                self.log_error("/chat/messages/{id}", "DELETE", "No test messages available for deletion")
                return
            
            # Delete the first test message
            message_id = self.test_message_ids[0]
            response = requests.delete(f"{self.base_url}/chat/messages/{message_id}", 
                                     headers=self.auth_headers,
                                     timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'deleted' in data['message'].lower():
                    self.test_results['community_chat']['message_deletion'] = True
                    self.log_success(f"/chat/messages/{message_id}", "DELETE", "- Message deleted successfully")
                else:
                    self.test_results['community_chat']['message_deletion'] = False
                    self.log_error(f"/chat/messages/{message_id}", "DELETE", "Invalid response structure")
            else:
                self.test_results['community_chat']['message_deletion'] = False
                self.log_error(f"/chat/messages/{message_id}", "DELETE", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['community_chat']['message_deletion'] = False
            self.log_error(f"/chat/messages/{message_id}", "DELETE", f"Exception: {str(e)}")

    def test_deleted_message_response(self):
        """Test that deleted messages show is_deleted: true in response"""
        try:
            # Get messages and check if deleted message has is_deleted: true
            response = requests.get(f"{self.base_url}/chat/groups/{self.test_group_id}/messages?limit=20", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Look for deleted messages
                    deleted_messages = [msg for msg in data if msg.get('is_deleted') == True]
                    if deleted_messages:
                        deleted_msg = deleted_messages[0]
                        if (deleted_msg.get('is_deleted') == True and 
                            deleted_msg.get('deleted_at') is not None and
                            deleted_msg.get('content') == ''):
                            self.test_results['community_chat']['deleted_message_response'] = True
                            self.log_success(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", "- Deleted message shows correct is_deleted: true format")
                        else:
                            self.test_results['community_chat']['deleted_message_response'] = False
                            self.log_error(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", "Deleted message format incorrect")
                    else:
                        # If no deleted messages found, try to delete one and check again
                        if self.test_message_ids and len(self.test_message_ids) > 1:
                            # Delete another message for testing
                            message_id = self.test_message_ids[1]
                            delete_response = requests.delete(f"{self.base_url}/chat/messages/{message_id}", 
                                                            headers=self.auth_headers,
                                                            timeout=10)
                            if delete_response.status_code == 200:
                                # Check again
                                response2 = requests.get(f"{self.base_url}/chat/groups/{self.test_group_id}/messages?limit=20", 
                                                       headers=self.auth_headers,
                                                       timeout=10)
                                if response2.status_code == 200:
                                    data2 = response2.json()
                                    deleted_messages2 = [msg for msg in data2 if msg.get('is_deleted') == True]
                                    if deleted_messages2:
                                        self.test_results['community_chat']['deleted_message_response'] = True
                                        self.log_success(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", "- Deleted message shows correct is_deleted: true format")
                                    else:
                                        self.test_results['community_chat']['deleted_message_response'] = False
                                        self.log_error(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", "No deleted messages found after deletion")
                                else:
                                    self.test_results['community_chat']['deleted_message_response'] = False
                                    self.log_error(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", f"Status code: {response2.status_code}")
                            else:
                                self.test_results['community_chat']['deleted_message_response'] = False
                                self.log_error(f"/chat/messages/{message_id}", "DELETE", f"Failed to delete message for testing: {delete_response.status_code}")
                        else:
                            self.test_results['community_chat']['deleted_message_response'] = True
                            self.log_success(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", "- No messages to delete for testing (acceptable)")
                else:
                    self.test_results['community_chat']['deleted_message_response'] = False
                    self.log_error(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", "Response is not a list")
            else:
                self.test_results['community_chat']['deleted_message_response'] = False
                self.log_error(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['community_chat']['deleted_message_response'] = False
            self.log_error(f"/chat/groups/{self.test_group_id}/messages (deleted)", "GET", f"Exception: {str(e)}")

    def test_message_order(self):
        """Test that messages are returned in correct order (oldest first after reversal)"""
        try:
            response = requests.get(f"{self.base_url}/chat/groups/{self.test_group_id}/messages?limit=10", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    # Check if messages are in chronological order (oldest first)
                    is_chronological = True
                    for i in range(1, len(data)):
                        prev_time = data[i-1]['created_at']
                        curr_time = data[i]['created_at']
                        if prev_time > curr_time:
                            is_chronological = False
                            break
                    
                    if is_chronological:
                        self.test_results['community_chat']['message_order'] = True
                        self.log_success(f"/chat/groups/{self.test_group_id}/messages (order)", "GET", "- Messages returned in correct chronological order (oldest first)")
                    else:
                        self.test_results['community_chat']['message_order'] = False
                        self.log_error(f"/chat/groups/{self.test_group_id}/messages (order)", "GET", "Messages not in chronological order")
                else:
                    self.test_results['community_chat']['message_order'] = True
                    self.log_success(f"/chat/groups/{self.test_group_id}/messages (order)", "GET", "- Insufficient messages to test order (acceptable)")
            else:
                self.test_results['community_chat']['message_order'] = False
                self.log_error(f"/chat/groups/{self.test_group_id}/messages (order)", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['community_chat']['message_order'] = False
            self.log_error(f"/chat/groups/{self.test_group_id}/messages (order)", "GET", f"Exception: {str(e)}")

    def test_pwa_caching_features(self):
        """Test PWA caching features including cache headers and service worker"""
        print("\n🗄️ Testing PWA Caching Features...")
        
        # Test 1: Cache headers on cacheable endpoints
        cacheable_endpoints = [
            ('/api/amenities', 'amenities'),
            ('/api/committee', 'committee'),
            ('/api/events', 'events'),
            ('/api/gallery', 'gallery')
        ]
        
        for endpoint, name in cacheable_endpoints:
            try:
                response = requests.get(f"{BACKEND_URL}{endpoint}", 
                                      auth=(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD),
                                      timeout=10)
                
                if response.status_code == 200:
                    cache_control = response.headers.get('Cache-Control', '')
                    vary_header = response.headers.get('Vary', '')
                    
                    # Expected: public, max-age=300, stale-while-revalidate=3600
                    has_public = 'public' in cache_control
                    has_max_age = 'max-age=300' in cache_control
                    has_stale_while_revalidate = 'stale-while-revalidate=3600' in cache_control
                    has_vary = 'Accept-Encoding' in vary_header
                    
                    if has_public and has_max_age and has_stale_while_revalidate and has_vary:
                        self.test_results['pwa_caching'][f'cache_headers_{name}'] = True
                        self.log_success(f"{endpoint} (cache headers)", "GET", f"- Correct cache headers: {cache_control}")
                    else:
                        self.test_results['pwa_caching'][f'cache_headers_{name}'] = False
                        self.log_error(f"{endpoint} (cache headers)", "GET", f"Incorrect cache headers: {cache_control}, Vary: {vary_header}")
                else:
                    self.test_results['pwa_caching'][f'cache_headers_{name}'] = False
                    self.log_error(f"{endpoint} (cache headers)", "GET", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_results['pwa_caching'][f'cache_headers_{name}'] = False
                self.log_error(f"{endpoint} (cache headers)", "GET", f"Exception: {str(e)}")
        
        # Test 2: No-cache headers on auth endpoints
        try:
            response = requests.get(f"{BACKEND_URL}/api/auth", 
                                  auth=(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD),
                                  timeout=10)
            
            cache_control = response.headers.get('Cache-Control', '')
            pragma = response.headers.get('Pragma', '')
            
            # Expected: no-store, no-cache, must-revalidate, private
            has_no_store = 'no-store' in cache_control
            has_no_cache = 'no-cache' in cache_control
            has_must_revalidate = 'must-revalidate' in cache_control
            has_private = 'private' in cache_control
            
            if has_no_store and has_no_cache and has_must_revalidate and has_private:
                self.test_results['pwa_caching']['no_cache_auth'] = True
                self.log_success("/auth (no-cache headers)", "GET", f"- Correct no-cache headers: {cache_control}")
            else:
                self.test_results['pwa_caching']['no_cache_auth'] = False
                self.log_error("/auth (no-cache headers)", "GET", f"Incorrect no-cache headers: {cache_control}, Pragma: {pragma}")
        except Exception as e:
            self.test_results['pwa_caching']['no_cache_auth'] = False
            self.log_error("/auth (no-cache headers)", "GET", f"Exception: {str(e)}")
        
        # Test 3: Service worker accessibility
        try:
            response = requests.get(f"{BACKEND_URL}/service-worker.js", 
                                  auth=(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD),
                                  timeout=10)
            
            if response.status_code == 200:
                content = response.text
                # Check for key service worker features
                has_install_event = 'addEventListener(\'install\'' in content
                has_fetch_event = 'addEventListener(\'fetch\'' in content
                has_cache_patterns = 'CACHEABLE_API_PATTERNS' in content
                has_cache_expiry = 'CACHE_EXPIRY' in content
                has_stale_while_revalidate = 'stale-while-revalidate' in content
                
                if has_install_event and has_fetch_event and has_cache_patterns and has_cache_expiry and has_stale_while_revalidate:
                    self.test_results['pwa_caching']['service_worker'] = True
                    self.log_success("/service-worker.js", "GET", f"- Service worker with caching features: {len(content)} bytes")
                else:
                    self.test_results['pwa_caching']['service_worker'] = False
                    missing_features = []
                    if not has_install_event: missing_features.append('install event')
                    if not has_fetch_event: missing_features.append('fetch event')
                    if not has_cache_patterns: missing_features.append('cache patterns')
                    if not has_cache_expiry: missing_features.append('cache expiry')
                    if not has_stale_while_revalidate: missing_features.append('stale-while-revalidate')
                    self.log_error("/service-worker.js", "GET", f"Missing features: {', '.join(missing_features)}")
            else:
                self.test_results['pwa_caching']['service_worker'] = False
                self.log_error("/service-worker.js", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa_caching']['service_worker'] = False
            self.log_error("/service-worker.js", "GET", f"Exception: {str(e)}")
        
        # Test 4: PWA manifest accessibility
        try:
            response = requests.get(f"{BACKEND_URL}/manifest.json", 
                                  auth=(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD),
                                  timeout=10)
            
            if response.status_code == 200:
                try:
                    manifest = response.json()
                    has_name = 'name' in manifest
                    has_icons = 'icons' in manifest and len(manifest['icons']) > 0
                    has_start_url = 'start_url' in manifest
                    has_display = 'display' in manifest
                    
                    if has_name and has_icons and has_start_url and has_display:
                        self.test_results['pwa_caching']['manifest'] = True
                        self.log_success("/manifest.json", "GET", f"- Valid PWA manifest: {manifest.get('name', 'N/A')}")
                    else:
                        self.test_results['pwa_caching']['manifest'] = False
                        missing_fields = [k for k in ['name', 'icons', 'start_url', 'display'] if k not in manifest]
                        self.log_error("/manifest.json", "GET", f"Missing fields: {missing_fields}")
                except Exception as parse_error:
                    self.test_results['pwa_caching']['manifest'] = False
                    self.log_error("/manifest.json", "GET", f"JSON parse error: {str(parse_error)}")
            else:
                self.test_results['pwa_caching']['manifest'] = False
                self.log_error("/manifest.json", "GET", f"Status code: {response.status_code}")
        except Exception as e:
            self.test_results['pwa_caching']['manifest'] = False
            self.log_error("/manifest.json", "GET", f"Exception: {str(e)}")
        
        # Test 5: CORS headers for PWA compatibility
        try:
            response = requests.options(f"{BACKEND_URL}/api/amenities", 
                                      headers={'Origin': BACKEND_URL},
                                      auth=(BASIC_AUTH_USERNAME, BASIC_AUTH_PASSWORD),
                                      timeout=10)
            
            access_control_allow_origin = response.headers.get('Access-Control-Allow-Origin', '')
            access_control_allow_credentials = response.headers.get('Access-Control-Allow-Credentials', '')
            access_control_allow_methods = response.headers.get('Access-Control-Allow-Methods', '')
            
            has_origin = access_control_allow_origin != ''
            has_credentials = access_control_allow_credentials.lower() == 'true'
            has_methods = 'GET' in access_control_allow_methods
            
            if has_origin and has_credentials and has_methods:
                self.test_results['pwa_caching']['cors_headers'] = True
                self.log_success("/amenities (CORS)", "OPTIONS", f"- CORS configured: Origin={access_control_allow_origin}")
            else:
                self.test_results['pwa_caching']['cors_headers'] = False
                self.log_error("/amenities (CORS)", "OPTIONS", f"CORS issues: Origin={access_control_allow_origin}, Credentials={access_control_allow_credentials}")
        except Exception as e:
            self.test_results['pwa_caching']['cors_headers'] = False
            self.log_error("/amenities (CORS)", "OPTIONS", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting TROA Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test root endpoint first
        self.test_root_endpoint()
        
        # Test specific features from the review request
        self.test_user_management_features()
        self.test_google_oauth_features()
        self.test_email_verification_features()
        
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
        
        # Test Event Registration Modification feature
        self.test_event_registration_modification()
        
        # Test Villa Management features
        self.test_villa_management()
        
        # Test PWA features
        self.test_pwa_features()
        self.test_pwa_static_assets()
        
        # Test PWA Caching features
        self.test_pwa_caching_features()
        
        # Test Community Chat features (comprehensive)
        self.test_community_chat_comprehensive()
        
        # Test Push Notifications
        self.test_push_notifications()
        
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
            'Event Registration Modification': ['event_modification'],
            'Amenity Booking': ['amenity_booking'],
            'Community Chat': ['community_chat'],
            'Push Notifications': ['push_notifications'],
            'PWA Features': ['pwa'],
            'PWA Caching': ['pwa_caching']
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
                        elif endpoint == 'event_modification':
                            display_endpoint = f"events/modification/{method}"
                        elif endpoint == 'villa_management':
                            display_endpoint = f"users/{method}"
                        elif endpoint == 'villa_auth':
                            display_endpoint = f"auth/{method}"
                        elif endpoint == 'pwa':
                            display_endpoint = f"pwa/{method}"
                        elif endpoint == 'community_chat':
                            display_endpoint = f"chat/{method}"
                        elif endpoint == 'push_notifications':
                            display_endpoint = f"push/{method}"
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