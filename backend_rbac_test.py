#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Testing for TROA Admin Portal
Tests access control for different user roles: Admin, Manager, and Regular User
"""

import requests
import json
import os
import base64
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troa-residence.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

# Test user credentials (from auth.py)
ADMIN_EMAIL = "troa.systems@gmail.com"
MANAGER_EMAILS = [
    "troa.mgr@gmail.com",
    "troa.secretary@gmail.com", 
    "troa.treasurer@gmail.com",
    "president.troa@gmail.com"
]

class RBACTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'manager_membership_access': {'get': None, 'post': None, 'patch': None, 'delete': None},
            'manager_offline_payments_access': {'get': None, 'post': None},
            'manager_events_access': {'get': None, 'post': None, 'patch': None},
            'manager_feedback_forbidden': {'get': None, 'post': None, 'delete': None},
            'manager_users_forbidden': {'get': None, 'post': None, 'patch': None, 'delete': None},
            'admin_full_access': {'feedback': None, 'users': None, 'all_manager_endpoints': None}
        }
        self.errors = []
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        
        # Mock session tokens for different user roles
        # In real scenario, these would be obtained through OAuth login
        self.admin_token = "admin_session_token_mock_123"
        self.manager_token = "manager_session_token_mock_456"
        self.user_token = "user_session_token_mock_789"
        
        # Headers for different user types
        self.admin_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }
        
        self.manager_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.manager_token}',
            'Content-Type': 'application/json'
        }
        
        self.user_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.user_token}',
            'Content-Type': 'application/json'
        }
        
        # No auth headers for testing unauthorized access
        self.no_auth_headers = {
            'Content-Type': 'application/json'
        }
        
    def log_error(self, test_name: str, error: str):
        """Log errors for detailed reporting"""
        error_msg = f"{test_name}: {error}"
        self.errors.append(error_msg)
        print(f"❌ {error_msg}")
        
    def log_success(self, test_name: str, message: str = ""):
        """Log successful tests"""
        success_msg = f"{test_name}: SUCCESS {message}"
        print(f"✅ {success_msg}")
        
    def test_manager_membership_applications_access(self):
        """Test that managers can access membership applications endpoints"""
        print("\n🧪 Testing Manager Access to Membership Applications...")
        
        # Test GET /api/membership (should work for managers)
        try:
            response = requests.get(f"{self.base_url}/membership", 
                                  headers=self.manager_headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                self.test_results['manager_membership_access']['get'] = True
                self.log_success("Manager GET /api/membership", f"- Status: {response.status_code}")
            elif response.status_code in [401, 403]:
                self.test_results['manager_membership_access']['get'] = False
                self.log_error("Manager GET /api/membership", f"Access denied - Status: {response.status_code}")
            else:
                self.test_results['manager_membership_access']['get'] = False
                self.log_error("Manager GET /api/membership", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.test_results['manager_membership_access']['get'] = False
            self.log_error("Manager GET /api/membership", f"Exception: {str(e)}")
            
        # Test PATCH /api/membership/{id} (should work for managers)
        try:
            # First create a membership application to update
            test_application = {
                "firstName": "RBAC",
                "lastName": "TestUser",
                "email": "rbac.test@email.com",
                "phone": "+1-555-RBAC",
                "villaNo": "RBAC-01",
                "message": "Test application for RBAC testing"
            }
            
            create_response = requests.post(f"{self.base_url}/membership", 
                                          json=test_application, 
                                          headers={'Content-Type': 'application/json'},
                                          timeout=10)
            
            if create_response.status_code == 200:
                app_data = create_response.json()
                app_id = app_data['id']
                
                # Now test PATCH with manager credentials
                update_data = {"status": "approved"}
                response = requests.patch(f"{self.base_url}/membership/{app_id}", 
                                        json=update_data,
                                        headers=self.manager_headers, 
                                        timeout=10)
                
                if response.status_code == 200:
                    self.test_results['manager_membership_access']['patch'] = True
                    self.log_success("Manager PATCH /api/membership/{id}", f"- Status: {response.status_code}")
                elif response.status_code in [401, 403]:
                    self.test_results['manager_membership_access']['patch'] = False
                    self.log_error("Manager PATCH /api/membership/{id}", f"Access denied - Status: {response.status_code}")
                else:
                    self.test_results['manager_membership_access']['patch'] = False
                    self.log_error("Manager PATCH /api/membership/{id}", f"Unexpected status: {response.status_code}")
                    
                # Test DELETE /api/membership/{id} (should work for managers)
                response = requests.delete(f"{self.base_url}/membership/{app_id}", 
                                         headers=self.manager_headers, 
                                         timeout=10)
                
                if response.status_code == 200:
                    self.test_results['manager_membership_access']['delete'] = True
                    self.log_success("Manager DELETE /api/membership/{id}", f"- Status: {response.status_code}")
                elif response.status_code in [401, 403]:
                    self.test_results['manager_membership_access']['delete'] = False
                    self.log_error("Manager DELETE /api/membership/{id}", f"Access denied - Status: {response.status_code}")
                else:
                    self.test_results['manager_membership_access']['delete'] = False
                    self.log_error("Manager DELETE /api/membership/{id}", f"Unexpected status: {response.status_code}")
            else:
                self.test_results['manager_membership_access']['patch'] = False
                self.test_results['manager_membership_access']['delete'] = False
                self.log_error("Manager membership PATCH/DELETE", f"Failed to create test application: {create_response.status_code}")
                
        except Exception as e:
            self.test_results['manager_membership_access']['patch'] = False
            self.test_results['manager_membership_access']['delete'] = False
            self.log_error("Manager membership PATCH/DELETE", f"Exception: {str(e)}")

    def test_manager_offline_payments_access(self):
        """Test that managers can access offline payments endpoints"""
        print("\n🧪 Testing Manager Access to Offline Payments...")
        
        # Test GET /api/payment/offline-payments (should work for managers)
        try:
            response = requests.get(f"{self.base_url}/payment/offline-payments", 
                                  headers=self.manager_headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                self.test_results['manager_offline_payments_access']['get'] = True
                self.log_success("Manager GET /api/payment/offline-payments", f"- Status: {response.status_code}")
            elif response.status_code in [401, 403]:
                self.test_results['manager_offline_payments_access']['get'] = False
                self.log_error("Manager GET /api/payment/offline-payments", f"Access denied - Status: {response.status_code}")
            else:
                self.test_results['manager_offline_payments_access']['get'] = False
                self.log_error("Manager GET /api/payment/offline-payments", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.test_results['manager_offline_payments_access']['get'] = False
            self.log_error("Manager GET /api/payment/offline-payments", f"Exception: {str(e)}")
            
        # Test POST /api/payment/offline-payments/approve (should work for managers)
        try:
            # First create an offline payment to approve
            payment_request = {
                'payment_type': 'membership',
                'payment_method': 'qr_code',
                'name': 'RBAC Test User',
                'email': 'rbac.payment@email.com',
                'phone': '+91-9999999999',
                'villa_no': 'RBAC-PAY-01',
                'notes': 'Test payment for RBAC testing'
            }
            
            create_response = requests.post(f"{self.base_url}/payment/offline-payment", 
                                          json=payment_request, 
                                          headers={'Content-Type': 'application/json'},
                                          timeout=10)
            
            if create_response.status_code == 200:
                payment_data = create_response.json()
                payment_id = payment_data['payment_id']
                
                # Now test approval with manager credentials
                approval_request = {
                    'payment_id': payment_id,
                    'action': 'approve'
                }
                
                response = requests.post(f"{self.base_url}/payment/offline-payments/approve", 
                                       json=approval_request,
                                       headers=self.manager_headers, 
                                       timeout=10)
                
                if response.status_code == 200:
                    self.test_results['manager_offline_payments_access']['post'] = True
                    self.log_success("Manager POST /api/payment/offline-payments/approve", f"- Status: {response.status_code}")
                elif response.status_code in [401, 403]:
                    self.test_results['manager_offline_payments_access']['post'] = False
                    self.log_error("Manager POST /api/payment/offline-payments/approve", f"Access denied - Status: {response.status_code}")
                else:
                    self.test_results['manager_offline_payments_access']['post'] = False
                    self.log_error("Manager POST /api/payment/offline-payments/approve", f"Unexpected status: {response.status_code}")
            else:
                self.test_results['manager_offline_payments_access']['post'] = False
                self.log_error("Manager offline payments approve", f"Failed to create test payment: {create_response.status_code}")
                
        except Exception as e:
            self.test_results['manager_offline_payments_access']['post'] = False
            self.log_error("Manager offline payments approve", f"Exception: {str(e)}")

    def test_manager_events_access(self):
        """Test that managers can access events management endpoints"""
        print("\n🧪 Testing Manager Access to Events Management...")
        
        # Test GET /api/events (public access - should work)
        try:
            response = requests.get(f"{self.base_url}/events", 
                                  headers=self.manager_headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                self.test_results['manager_events_access']['get'] = True
                self.log_success("Manager GET /api/events", f"- Status: {response.status_code}")
            else:
                self.test_results['manager_events_access']['get'] = False
                self.log_error("Manager GET /api/events", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.test_results['manager_events_access']['get'] = False
            self.log_error("Manager GET /api/events", f"Exception: {str(e)}")
            
        # Test POST /api/events (should work for managers)
        try:
            from datetime import datetime, timedelta
            future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            test_event = {
                "name": "RBAC Test Event",
                "description": "Test event for RBAC testing",
                "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                "event_date": future_date,
                "event_time": "18:00",
                "amount": 50.0,
                "payment_type": "per_person",
                "max_registrations": 50
            }
            
            response = requests.post(f"{self.base_url}/events", 
                                   json=test_event,
                                   headers=self.manager_headers, 
                                   timeout=10)
            
            if response.status_code == 200:
                self.test_results['manager_events_access']['post'] = True
                event_data = response.json()
                event_id = event_data['id']
                self.log_success("Manager POST /api/events", f"- Status: {response.status_code}, Event ID: {event_id}")
                
                # Test PATCH /api/events/{id} (should work for managers)
                update_data = {"description": "Updated description for RBAC test"}
                response = requests.patch(f"{self.base_url}/events/{event_id}", 
                                        json=update_data,
                                        headers=self.manager_headers, 
                                        timeout=10)
                
                if response.status_code == 200:
                    self.test_results['manager_events_access']['patch'] = True
                    self.log_success("Manager PATCH /api/events/{id}", f"- Status: {response.status_code}")
                elif response.status_code in [401, 403]:
                    self.test_results['manager_events_access']['patch'] = False
                    self.log_error("Manager PATCH /api/events/{id}", f"Access denied - Status: {response.status_code}")
                else:
                    self.test_results['manager_events_access']['patch'] = False
                    self.log_error("Manager PATCH /api/events/{id}", f"Unexpected status: {response.status_code}")
                    
            elif response.status_code in [401, 403]:
                self.test_results['manager_events_access']['post'] = False
                self.test_results['manager_events_access']['patch'] = False
                self.log_error("Manager POST /api/events", f"Access denied - Status: {response.status_code}")
            else:
                self.test_results['manager_events_access']['post'] = False
                self.test_results['manager_events_access']['patch'] = False
                self.log_error("Manager POST /api/events", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.test_results['manager_events_access']['post'] = False
            self.test_results['manager_events_access']['patch'] = False
            self.log_error("Manager events POST/PATCH", f"Exception: {str(e)}")

    def test_manager_feedback_forbidden(self):
        """Test that managers CANNOT access feedback endpoints (admin only)"""
        print("\n🧪 Testing Manager FORBIDDEN Access to Feedback...")
        
        # Test GET /api/feedback (should be forbidden for managers)
        try:
            response = requests.get(f"{self.base_url}/feedback", 
                                  headers=self.manager_headers, 
                                  timeout=10)
            
            if response.status_code == 403:
                self.test_results['manager_feedback_forbidden']['get'] = True
                self.log_success("Manager GET /api/feedback FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 401:
                self.test_results['manager_feedback_forbidden']['get'] = True
                self.log_success("Manager GET /api/feedback FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 200:
                self.test_results['manager_feedback_forbidden']['get'] = False
                self.log_error("Manager GET /api/feedback", f"Should be forbidden but got access - Status: {response.status_code}")
            else:
                self.test_results['manager_feedback_forbidden']['get'] = False
                self.log_error("Manager GET /api/feedback", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.test_results['manager_feedback_forbidden']['get'] = False
            self.log_error("Manager GET /api/feedback", f"Exception: {str(e)}")
            
        # Test POST /api/feedback (should work for authenticated users, including managers)
        try:
            feedback_data = {
                "rating": 5,
                "works_well": "RBAC testing works well",
                "needs_improvement": "Nothing for this test",
                "feature_suggestions": "More RBAC tests"
            }
            
            response = requests.post(f"{self.base_url}/feedback", 
                                   json=feedback_data,
                                   headers=self.manager_headers, 
                                   timeout=10)
            
            if response.status_code == 200:
                self.test_results['manager_feedback_forbidden']['post'] = True
                feedback_response = response.json()
                feedback_id = feedback_response['id']
                self.log_success("Manager POST /api/feedback", f"- Allowed to submit feedback: {response.status_code}")
                
                # Test DELETE /api/feedback/{id} (should be forbidden for managers)
                response = requests.delete(f"{self.base_url}/feedback/{feedback_id}", 
                                         headers=self.manager_headers, 
                                         timeout=10)
                
                if response.status_code == 403:
                    self.test_results['manager_feedback_forbidden']['delete'] = True
                    self.log_success("Manager DELETE /api/feedback/{id} FORBIDDEN", f"- Correctly denied access: {response.status_code}")
                elif response.status_code == 401:
                    self.test_results['manager_feedback_forbidden']['delete'] = True
                    self.log_success("Manager DELETE /api/feedback/{id} FORBIDDEN", f"- Correctly denied access: {response.status_code}")
                elif response.status_code == 200:
                    self.test_results['manager_feedback_forbidden']['delete'] = False
                    self.log_error("Manager DELETE /api/feedback/{id}", f"Should be forbidden but got access - Status: {response.status_code}")
                else:
                    self.test_results['manager_feedback_forbidden']['delete'] = False
                    self.log_error("Manager DELETE /api/feedback/{id}", f"Unexpected status: {response.status_code}")
                    
            elif response.status_code in [401, 403]:
                self.test_results['manager_feedback_forbidden']['post'] = False
                self.test_results['manager_feedback_forbidden']['delete'] = False
                self.log_error("Manager POST /api/feedback", f"Should be allowed but got denied - Status: {response.status_code}")
            else:
                self.test_results['manager_feedback_forbidden']['post'] = False
                self.test_results['manager_feedback_forbidden']['delete'] = False
                self.log_error("Manager POST /api/feedback", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.test_results['manager_feedback_forbidden']['post'] = False
            self.test_results['manager_feedback_forbidden']['delete'] = False
            self.log_error("Manager feedback POST/DELETE", f"Exception: {str(e)}")

    def test_manager_users_forbidden(self):
        """Test that managers CANNOT access user management endpoints (admin only)"""
        print("\n🧪 Testing Manager FORBIDDEN Access to User Management...")
        
        # Test GET /api/users (should be forbidden for managers)
        try:
            response = requests.get(f"{self.base_url}/users", 
                                  headers=self.manager_headers, 
                                  timeout=10)
            
            if response.status_code == 403:
                self.test_results['manager_users_forbidden']['get'] = True
                self.log_success("Manager GET /api/users FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 401:
                self.test_results['manager_users_forbidden']['get'] = True
                self.log_success("Manager GET /api/users FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 200:
                self.test_results['manager_users_forbidden']['get'] = False
                self.log_error("Manager GET /api/users", f"Should be forbidden but got access - Status: {response.status_code}")
            else:
                self.test_results['manager_users_forbidden']['get'] = False
                self.log_error("Manager GET /api/users", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.test_results['manager_users_forbidden']['get'] = False
            self.log_error("Manager GET /api/users", f"Exception: {str(e)}")
            
        # Test POST /api/users (should be forbidden for managers)
        try:
            user_data = {
                "email": "rbac.test.user@email.com",
                "name": "RBAC Test User",
                "role": "user"
            }
            
            response = requests.post(f"{self.base_url}/users", 
                                   json=user_data,
                                   headers=self.manager_headers, 
                                   timeout=10)
            
            if response.status_code == 403:
                self.test_results['manager_users_forbidden']['post'] = True
                self.log_success("Manager POST /api/users FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 401:
                self.test_results['manager_users_forbidden']['post'] = True
                self.log_success("Manager POST /api/users FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 200:
                self.test_results['manager_users_forbidden']['post'] = False
                self.log_error("Manager POST /api/users", f"Should be forbidden but got access - Status: {response.status_code}")
            else:
                self.test_results['manager_users_forbidden']['post'] = False
                self.log_error("Manager POST /api/users", f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.test_results['manager_users_forbidden']['post'] = False
            self.log_error("Manager POST /api/users", f"Exception: {str(e)}")
            
        # Test PATCH and DELETE would require creating a user first, but since POST is forbidden,
        # we'll test with a mock user ID to verify the endpoints are also forbidden
        try:
            mock_user_id = "mock-user-id-123"
            
            # Test PATCH /api/users/{id}
            update_data = {"role": "manager"}
            response = requests.patch(f"{self.base_url}/users/{mock_user_id}", 
                                    json=update_data,
                                    headers=self.manager_headers, 
                                    timeout=10)
            
            if response.status_code in [401, 403]:
                self.test_results['manager_users_forbidden']['patch'] = True
                self.log_success("Manager PATCH /api/users/{id} FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 404:
                # 404 means the endpoint was reached but user not found, which means access was granted
                self.test_results['manager_users_forbidden']['patch'] = False
                self.log_error("Manager PATCH /api/users/{id}", f"Should be forbidden but got access (404 means endpoint reached)")
            else:
                self.test_results['manager_users_forbidden']['patch'] = False
                self.log_error("Manager PATCH /api/users/{id}", f"Unexpected status: {response.status_code}")
                
            # Test DELETE /api/users/{id}
            response = requests.delete(f"{self.base_url}/users/{mock_user_id}", 
                                     headers=self.manager_headers, 
                                     timeout=10)
            
            if response.status_code in [401, 403]:
                self.test_results['manager_users_forbidden']['delete'] = True
                self.log_success("Manager DELETE /api/users/{id} FORBIDDEN", f"- Correctly denied access: {response.status_code}")
            elif response.status_code == 404:
                # 404 means the endpoint was reached but user not found, which means access was granted
                self.test_results['manager_users_forbidden']['delete'] = False
                self.log_error("Manager DELETE /api/users/{id}", f"Should be forbidden but got access (404 means endpoint reached)")
            else:
                self.test_results['manager_users_forbidden']['delete'] = False
                self.log_error("Manager DELETE /api/users/{id}", f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.test_results['manager_users_forbidden']['patch'] = False
            self.test_results['manager_users_forbidden']['delete'] = False
            self.log_error("Manager users PATCH/DELETE", f"Exception: {str(e)}")

    def test_admin_full_access(self):
        """Test that admin can access all endpoints including feedback and user management"""
        print("\n🧪 Testing Admin Full Access...")
        
        # Test admin access to feedback endpoints
        try:
            # Test GET /api/feedback
            response = requests.get(f"{self.base_url}/feedback", 
                                  headers=self.admin_headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                feedback_access = True
                self.log_success("Admin GET /api/feedback", f"- Status: {response.status_code}")
            else:
                feedback_access = False
                self.log_error("Admin GET /api/feedback", f"Unexpected status: {response.status_code}")
                
            self.test_results['admin_full_access']['feedback'] = feedback_access
            
        except Exception as e:
            self.test_results['admin_full_access']['feedback'] = False
            self.log_error("Admin feedback access", f"Exception: {str(e)}")
            
        # Test admin access to user management endpoints
        try:
            # Test GET /api/users
            response = requests.get(f"{self.base_url}/users", 
                                  headers=self.admin_headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                users_access = True
                self.log_success("Admin GET /api/users", f"- Status: {response.status_code}")
            else:
                users_access = False
                self.log_error("Admin GET /api/users", f"Unexpected status: {response.status_code}")
                
            self.test_results['admin_full_access']['users'] = users_access
            
        except Exception as e:
            self.test_results['admin_full_access']['users'] = False
            self.log_error("Admin users access", f"Exception: {str(e)}")
            
        # Test admin access to all manager endpoints (should also work for admin)
        try:
            # Test membership applications
            response = requests.get(f"{self.base_url}/membership", 
                                  headers=self.admin_headers, 
                                  timeout=10)
            
            membership_ok = response.status_code == 200
            
            # Test offline payments
            response = requests.get(f"{self.base_url}/payment/offline-payments", 
                                  headers=self.admin_headers, 
                                  timeout=10)
            
            payments_ok = response.status_code == 200
            
            # Test events
            response = requests.get(f"{self.base_url}/events", 
                                  headers=self.admin_headers, 
                                  timeout=10)
            
            events_ok = response.status_code == 200
            
            if membership_ok and payments_ok and events_ok:
                self.test_results['admin_full_access']['all_manager_endpoints'] = True
                self.log_success("Admin access to manager endpoints", "- All manager endpoints accessible")
            else:
                self.test_results['admin_full_access']['all_manager_endpoints'] = False
                self.log_error("Admin access to manager endpoints", f"Some endpoints failed - Membership: {membership_ok}, Payments: {payments_ok}, Events: {events_ok}")
                
        except Exception as e:
            self.test_results['admin_full_access']['all_manager_endpoints'] = False
            self.log_error("Admin manager endpoints access", f"Exception: {str(e)}")

    def test_unauthorized_access(self):
        """Test that endpoints correctly deny access without authentication"""
        print("\n🧪 Testing Unauthorized Access (No Authentication)...")
        
        protected_endpoints = [
            ('GET', '/membership', 'Membership Applications'),
            ('GET', '/payment/offline-payments', 'Offline Payments'),
            ('POST', '/events', 'Create Event'),
            ('GET', '/feedback', 'Feedback'),
            ('GET', '/users', 'User Management')
        ]
        
        for method, endpoint, description in protected_endpoints:
            try:
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{endpoint}", 
                                          headers=self.no_auth_headers, 
                                          timeout=10)
                elif method == 'POST':
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           json={},
                                           headers=self.no_auth_headers, 
                                           timeout=10)
                
                if response.status_code in [401, 403]:
                    self.log_success(f"Unauthorized {method} {endpoint}", f"- Correctly denied access: {response.status_code}")
                else:
                    self.log_error(f"Unauthorized {method} {endpoint}", f"Should deny access but got: {response.status_code}")
                    
            except Exception as e:
                self.log_error(f"Unauthorized {method} {endpoint}", f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all RBAC tests"""
        print(f"🚀 Starting TROA Role-Based Access Control (RBAC) Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 70)
        
        print("\n📋 RBAC Test Scenarios:")
        print("1. Manager users can access: Membership Applications, Offline Payments, Events Management")
        print("2. Manager users CANNOT access: User Feedback (admin only), User Management (admin only)")
        print("3. Admin user can access: Everything (all manager endpoints + feedback + user management)")
        print("4. Unauthorized users cannot access protected endpoints")
        
        print("\n🔑 Test User Roles:")
        print(f"   Admin: {ADMIN_EMAIL}")
        print(f"   Managers: {', '.join(MANAGER_EMAILS)}")
        print("   Note: Using mock session tokens for testing")
        
        # Test unauthorized access first
        self.test_unauthorized_access()
        
        # Test manager access to allowed endpoints
        self.test_manager_membership_applications_access()
        self.test_manager_offline_payments_access()
        self.test_manager_events_access()
        
        # Test manager forbidden access to admin-only endpoints
        self.test_manager_feedback_forbidden()
        self.test_manager_users_forbidden()
        
        # Test admin full access
        self.test_admin_full_access()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 70)
        print("📊 RBAC TEST RESULTS SUMMARY")
        print("=" * 70)
        
        total_tests = 0
        passed_tests = 0
        
        # Manager Access Tests (Should PASS)
        print("\n✅ Manager Access Tests (Should PASS):")
        manager_access_categories = [
            ('Membership Applications', 'manager_membership_access'),
            ('Offline Payments', 'manager_offline_payments_access'),
            ('Events Management', 'manager_events_access')
        ]
        
        for category, key in manager_access_categories:
            print(f"\n  {category}:")
            if key in self.test_results:
                for method, result in self.test_results[key].items():
                    total_tests += 1
                    if result:
                        passed_tests += 1
                        print(f"    ✅ {method.upper()}: PASS")
                    elif result is False:
                        print(f"    ❌ {method.upper()}: FAIL")
                    else:
                        print(f"    ⏸️ {method.upper()}: SKIP")
                        total_tests -= 1
        
        # Manager Forbidden Tests (Should PASS when access is denied)
        print("\n🚫 Manager Forbidden Access Tests (Should PASS when denied):")
        manager_forbidden_categories = [
            ('User Feedback (Admin Only)', 'manager_feedback_forbidden'),
            ('User Management (Admin Only)', 'manager_users_forbidden')
        ]
        
        for category, key in manager_forbidden_categories:
            print(f"\n  {category}:")
            if key in self.test_results:
                for method, result in self.test_results[key].items():
                    total_tests += 1
                    if result:
                        passed_tests += 1
                        if method in ['get', 'delete', 'patch']:
                            print(f"    ✅ {method.upper()}: CORRECTLY FORBIDDEN")
                        else:
                            print(f"    ✅ {method.upper()}: PASS")
                    elif result is False:
                        if method in ['get', 'delete', 'patch']:
                            print(f"    ❌ {method.upper()}: SHOULD BE FORBIDDEN")
                        else:
                            print(f"    ❌ {method.upper()}: FAIL")
                    else:
                        print(f"    ⏸️ {method.upper()}: SKIP")
                        total_tests -= 1
        
        # Admin Access Tests (Should PASS)
        print("\n👑 Admin Full Access Tests (Should PASS):")
        if 'admin_full_access' in self.test_results:
            for test_type, result in self.test_results['admin_full_access'].items():
                total_tests += 1
                if result:
                    passed_tests += 1
                    print(f"    ✅ {test_type.replace('_', ' ').title()}: PASS")
                elif result is False:
                    print(f"    ❌ {test_type.replace('_', ' ').title()}: FAIL")
                else:
                    print(f"    ⏸️ {test_type.replace('_', ' ').title()}: SKIP")
                    total_tests -= 1
        
        print(f"\n📈 Overall RBAC Test Results: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 RBAC ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n🎉 All RBAC tests passed successfully!")
            
        # Summary of what was tested
        print(f"\n📋 RBAC Test Summary:")
        print(f"   ✅ Manager access to allowed endpoints: Membership, Payments, Events")
        print(f"   🚫 Manager forbidden access to admin-only endpoints: Feedback, Users")
        print(f"   👑 Admin full access to all endpoints")
        print(f"   🔒 Unauthorized access properly denied")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = RBACTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎯 RBAC Testing Complete: ALL TESTS PASSED")
        exit(0)
    else:
        print(f"\n⚠️ RBAC Testing Complete: SOME TESTS FAILED")
        exit(1)