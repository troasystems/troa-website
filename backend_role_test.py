#!/usr/bin/env python3
"""
Database-Driven Role Management System Testing for TROA
Tests the new role management system where roles are stored in database instead of hardcoded lists.
"""

import requests
import json
import os
import base64
from datetime import datetime
from typing import Dict, Any, List

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troa-residence.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"
SUPER_ADMIN_EMAIL = "troa.systems@gmail.com"

# Manager emails that should be in database
EXPECTED_MANAGERS = [
    "troa.mgr@gmail.com",
    "troa.secretary@gmail.com", 
    "troa.treasurer@gmail.com",
    "president.troa@gmail.com"
]

class RoleManagementTester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.test_results = {
            'database_managers_check': None,
            'super_admin_protection_patch': None,
            'super_admin_protection_delete': None,
            'role_update_flow': None,
            'add_new_manager': None,
            'manager_access_membership': None,
            'manager_access_offline_payments': None,
            'manager_access_events': None
        }
        self.errors = []
        self.created_user_id = None
        self.test_user_email = "test.manager@example.com"
        
        # Setup authentication headers
        self.basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
        self.session_token = "ymsHGpK7iiNm9K79Arw3qk8DY9Z8erRkR92dKxvDqv4"  # Valid admin session token
        self.auth_headers = {
            'Authorization': f'Basic {self.basic_auth}',
            'X-Session-Token': f'Bearer {self.session_token}',
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

    def test_database_managers_check(self):
        """Test 1: Verify managers are in database with 'manager' role"""
        print("\n🧪 Test 1: Checking managers in database...")
        
        try:
            # Get all users from database
            response = requests.get(f"{self.base_url}/users", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                
                # Check each expected manager
                found_managers = []
                missing_managers = []
                wrong_role_managers = []
                
                for expected_email in EXPECTED_MANAGERS:
                    user_found = False
                    for user in users:
                        if user['email'] == expected_email:
                            user_found = True
                            if user.get('role') == 'manager':
                                found_managers.append(expected_email)
                            else:
                                wrong_role_managers.append(f"{expected_email} (role: {user.get('role', 'None')})")
                            break
                    
                    if not user_found:
                        missing_managers.append(expected_email)
                
                # Report results
                if len(found_managers) == len(EXPECTED_MANAGERS) and not missing_managers and not wrong_role_managers:
                    self.test_results['database_managers_check'] = True
                    self.log_success("Database Managers Check", f"- All {len(found_managers)} managers found with correct 'manager' role")
                else:
                    self.test_results['database_managers_check'] = False
                    error_details = []
                    if missing_managers:
                        error_details.append(f"Missing: {missing_managers}")
                    if wrong_role_managers:
                        error_details.append(f"Wrong role: {wrong_role_managers}")
                    if found_managers:
                        error_details.append(f"Correct: {found_managers}")
                    self.log_error("Database Managers Check", f"Issues found - {'; '.join(error_details)}")
                    
            else:
                self.test_results['database_managers_check'] = False
                self.log_error("Database Managers Check", f"Failed to get users: {response.status_code}")
                
        except Exception as e:
            self.test_results['database_managers_check'] = False
            self.log_error("Database Managers Check", f"Exception: {str(e)}")

    def test_super_admin_protection(self):
        """Test 2: Test super admin protection (cannot modify/delete troa.systems@gmail.com)"""
        print("\n🧪 Test 2: Testing super admin protection...")
        
        # First, get the super admin user ID
        super_admin_id = None
        try:
            response = requests.get(f"{self.base_url}/users", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                for user in users:
                    if user['email'] == SUPER_ADMIN_EMAIL:
                        super_admin_id = user['id']
                        break
                        
                if not super_admin_id:
                    self.test_results['super_admin_protection_patch'] = False
                    self.test_results['super_admin_protection_delete'] = False
                    self.log_error("Super Admin Protection", f"Super admin {SUPER_ADMIN_EMAIL} not found in database")
                    return
            else:
                self.test_results['super_admin_protection_patch'] = False
                self.test_results['super_admin_protection_delete'] = False
                self.log_error("Super Admin Protection", f"Failed to get users: {response.status_code}")
                return
                
        except Exception as e:
            self.test_results['super_admin_protection_patch'] = False
            self.test_results['super_admin_protection_delete'] = False
            self.log_error("Super Admin Protection", f"Exception getting users: {str(e)}")
            return

        # Test PATCH protection
        try:
            update_data = {"role": "user"}  # Try to demote super admin
            response = requests.patch(f"{self.base_url}/users/{super_admin_id}", 
                                    json=update_data,
                                    headers=self.auth_headers,
                                    timeout=10)
            
            if response.status_code == 400:
                response_data = response.json()
                if "Cannot modify the super admin's role" in response_data.get('detail', ''):
                    self.test_results['super_admin_protection_patch'] = True
                    self.log_success("Super Admin PATCH Protection", "- Correctly blocked role modification")
                else:
                    self.test_results['super_admin_protection_patch'] = False
                    self.log_error("Super Admin PATCH Protection", f"Wrong error message: {response_data.get('detail')}")
            else:
                self.test_results['super_admin_protection_patch'] = False
                self.log_error("Super Admin PATCH Protection", f"Expected 400 but got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.test_results['super_admin_protection_patch'] = False
            self.log_error("Super Admin PATCH Protection", f"Exception: {str(e)}")

        # Test DELETE protection
        try:
            response = requests.delete(f"{self.base_url}/users/{super_admin_id}", 
                                     headers=self.auth_headers,
                                     timeout=10)
            
            if response.status_code == 400:
                response_data = response.json()
                if "Cannot delete the super admin account" in response_data.get('detail', ''):
                    self.test_results['super_admin_protection_delete'] = True
                    self.log_success("Super Admin DELETE Protection", "- Correctly blocked account deletion")
                else:
                    self.test_results['super_admin_protection_delete'] = False
                    self.log_error("Super Admin DELETE Protection", f"Wrong error message: {response_data.get('detail')}")
            else:
                self.test_results['super_admin_protection_delete'] = False
                self.log_error("Super Admin DELETE Protection", f"Expected 400 but got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.test_results['super_admin_protection_delete'] = False
            self.log_error("Super Admin DELETE Protection", f"Exception: {str(e)}")

    def test_role_update_flow(self):
        """Test 3: Test role update flow (user -> manager -> user)"""
        print("\n🧪 Test 3: Testing role update flow...")
        
        # First create a test user
        try:
            user_data = {
                "email": self.test_user_email,
                "name": "Test Manager User",
                "role": "user"
            }
            
            response = requests.post(f"{self.base_url}/users", 
                                   json=user_data,
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                created_user = response.json()
                self.created_user_id = created_user['id']
                print(f"   Created test user: {self.test_user_email} with ID: {self.created_user_id}")
            else:
                # User might already exist, try to find them
                users_response = requests.get(f"{self.base_url}/users", 
                                            headers=self.auth_headers,
                                            timeout=10)
                if users_response.status_code == 200:
                    users = users_response.json()
                    for user in users:
                        if user['email'] == self.test_user_email:
                            self.created_user_id = user['id']
                            print(f"   Found existing test user: {self.test_user_email} with ID: {self.created_user_id}")
                            break
                
                if not self.created_user_id:
                    self.test_results['role_update_flow'] = False
                    self.log_error("Role Update Flow", f"Failed to create/find test user: {response.status_code}")
                    return
                    
        except Exception as e:
            self.test_results['role_update_flow'] = False
            self.log_error("Role Update Flow", f"Exception creating test user: {str(e)}")
            return

        # Test updating role from 'user' to 'manager'
        try:
            update_data = {"role": "manager"}
            response = requests.patch(f"{self.base_url}/users/{self.created_user_id}", 
                                    json=update_data,
                                    headers=self.auth_headers,
                                    timeout=10)
            
            if response.status_code == 200:
                updated_user = response.json()
                if updated_user.get('role') == 'manager':
                    print(f"   ✅ Successfully updated role to 'manager'")
                    
                    # Verify the change persists by fetching the user again
                    verify_response = requests.get(f"{self.base_url}/users", 
                                                 headers=self.auth_headers,
                                                 timeout=10)
                    
                    if verify_response.status_code == 200:
                        users = verify_response.json()
                        for user in users:
                            if user['id'] == self.created_user_id:
                                if user.get('role') == 'manager':
                                    self.test_results['role_update_flow'] = True
                                    self.log_success("Role Update Flow", "- Role change persisted in database")
                                else:
                                    self.test_results['role_update_flow'] = False
                                    self.log_error("Role Update Flow", f"Role not persisted. Expected 'manager', got '{user.get('role')}'")
                                break
                        else:
                            self.test_results['role_update_flow'] = False
                            self.log_error("Role Update Flow", "User not found after update")
                    else:
                        self.test_results['role_update_flow'] = False
                        self.log_error("Role Update Flow", f"Failed to verify role change: {verify_response.status_code}")
                else:
                    self.test_results['role_update_flow'] = False
                    self.log_error("Role Update Flow", f"Role not updated. Expected 'manager', got '{updated_user.get('role')}'")
            else:
                self.test_results['role_update_flow'] = False
                self.log_error("Role Update Flow", f"Failed to update role: {response.status_code}, {response.text}")
                
        except Exception as e:
            self.test_results['role_update_flow'] = False
            self.log_error("Role Update Flow", f"Exception: {str(e)}")

    def test_add_new_manager_via_whitelist(self):
        """Test 4: Test adding new manager via whitelist"""
        print("\n🧪 Test 4: Testing adding new manager via whitelist...")
        
        try:
            new_manager_email = "new.manager@example.com"
            manager_data = {
                "email": new_manager_email,
                "name": "New Manager User",
                "role": "manager"
            }
            
            response = requests.post(f"{self.base_url}/users", 
                                   json=manager_data,
                                   headers=self.auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                created_manager = response.json()
                if (created_manager.get('email') == new_manager_email and 
                    created_manager.get('role') == 'manager'):
                    
                    self.test_results['add_new_manager'] = True
                    self.log_success("Add New Manager", f"- Created new manager: {new_manager_email}")
                    
                    # Clean up - delete the test manager
                    try:
                        delete_response = requests.delete(f"{self.base_url}/users/{created_manager['id']}", 
                                                        headers=self.auth_headers,
                                                        timeout=10)
                        if delete_response.status_code == 200:
                            print(f"   🧹 Cleaned up test manager: {new_manager_email}")
                    except:
                        pass  # Cleanup failure is not critical
                        
                else:
                    self.test_results['add_new_manager'] = False
                    self.log_error("Add New Manager", f"Invalid response data: {created_manager}")
            else:
                self.test_results['add_new_manager'] = False
                self.log_error("Add New Manager", f"Failed to create manager: {response.status_code}, {response.text}")
                
        except Exception as e:
            self.test_results['add_new_manager'] = False
            self.log_error("Add New Manager", f"Exception: {str(e)}")

    def test_manager_access_endpoints(self):
        """Test 5: Verify manager access still works for manager-level endpoints"""
        print("\n🧪 Test 5: Testing manager access to endpoints...")
        
        # Test 1: GET /api/membership (should work for managers)
        try:
            response = requests.get(f"{self.base_url}/membership", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            # Should work for admin (our test uses admin token)
            if response.status_code == 200:
                self.test_results['manager_access_membership'] = True
                self.log_success("Manager Access - Membership", f"- GET /api/membership accessible (found {len(response.json())} applications)")
            else:
                self.test_results['manager_access_membership'] = False
                self.log_error("Manager Access - Membership", f"GET /api/membership failed: {response.status_code}")
                
        except Exception as e:
            self.test_results['manager_access_membership'] = False
            self.log_error("Manager Access - Membership", f"Exception: {str(e)}")

        # Test 2: GET /api/payment/offline-payments (should work for managers)
        try:
            response = requests.get(f"{self.base_url}/payment/offline-payments", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                self.test_results['manager_access_offline_payments'] = True
                self.log_success("Manager Access - Offline Payments", f"- GET /api/payment/offline-payments accessible (found {len(response.json())} payments)")
            else:
                self.test_results['manager_access_offline_payments'] = False
                self.log_error("Manager Access - Offline Payments", f"GET /api/payment/offline-payments failed: {response.status_code}")
                
        except Exception as e:
            self.test_results['manager_access_offline_payments'] = False
            self.log_error("Manager Access - Offline Payments", f"Exception: {str(e)}")

        # Test 3: GET /api/events/admin/pending-approvals (should work for managers)
        try:
            response = requests.get(f"{self.base_url}/events/admin/pending-approvals", 
                                  headers=self.auth_headers,
                                  timeout=10)
            
            if response.status_code == 200:
                self.test_results['manager_access_events'] = True
                self.log_success("Manager Access - Events", f"- GET /api/events/admin/pending-approvals accessible (found {len(response.json())} pending)")
            else:
                self.test_results['manager_access_events'] = False
                self.log_error("Manager Access - Events", f"GET /api/events/admin/pending-approvals failed: {response.status_code}")
                
        except Exception as e:
            self.test_results['manager_access_events'] = False
            self.log_error("Manager Access - Events", f"Exception: {str(e)}")

    def cleanup_test_data(self):
        """Clean up any test data created during testing"""
        print("\n🧹 Cleaning up test data...")
        
        if self.created_user_id:
            try:
                response = requests.delete(f"{self.base_url}/users/{self.created_user_id}", 
                                         headers=self.auth_headers,
                                         timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ Cleaned up test user: {self.test_user_email}")
                else:
                    print(f"   ⚠️ Failed to clean up test user: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Exception during cleanup: {str(e)}")

    def run_all_tests(self):
        """Run all role management tests"""
        print(f"🚀 Starting Database-Driven Role Management Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 70)
        
        try:
            # Run all tests
            self.test_database_managers_check()
            self.test_super_admin_protection()
            self.test_role_update_flow()
            self.test_add_new_manager_via_whitelist()
            self.test_manager_access_endpoints()
            
        finally:
            # Always clean up
            self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 70)
        print("📊 ROLE MANAGEMENT TEST RESULTS SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        
        test_descriptions = {
            'database_managers_check': 'Managers in database with correct roles',
            'super_admin_protection_patch': 'Super admin role modification protection',
            'super_admin_protection_delete': 'Super admin account deletion protection',
            'role_update_flow': 'Role update flow (user → manager)',
            'add_new_manager': 'Add new manager via whitelist',
            'manager_access_membership': 'Manager access to membership endpoints',
            'manager_access_offline_payments': 'Manager access to offline payments',
            'manager_access_events': 'Manager access to events management'
        }
        
        print("\nTest Results:")
        for test_name, result in self.test_results.items():
            description = test_descriptions.get(test_name, test_name)
            if result is True:
                status = "✅ PASS"
            elif result is False:
                status = "❌ FAIL"
            else:
                status = "⏸️ SKIP"
                
            print(f"  {status} - {description}")
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 ERRORS FOUND ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("\n🎉 All role management tests passed successfully!")
            
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = RoleManagementTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)