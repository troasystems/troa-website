#!/usr/bin/env python3
"""
TROA Backend API Testing - Offline QR Code Payment System
Tests the newly implemented offline QR code payment functionality for invoices
"""

import requests
import sys
import json
from datetime import datetime

class TROAOfflinePaymentTester:
    def __init__(self, base_url="https://emailbuzz.preview.emergentagent.com"):
        self.base_url = base_url
        self.accountant_token = "e30e0d6d-d9a0-4d4f-90d5-7d718c1babd2"
        self.admin_token = "2222da03-770a-4485-8918-e9464bbed53c"
        self.user_token = "e30e0d6d-d9a0-4d4f-90d5-7d718c1babd2"  # Using accountant token as user for testing
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_invoice_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['X-Session-Token'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        result = response.json()
                        if isinstance(result, dict):
                            if 'message' in result:
                                print(f"   Message: {result['message']}")
                    except:
                        pass
                return True, response
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No error details')
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, response

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, None

    def test_offline_payment_qr_info(self):
        """Test QR code info endpoint"""
        print("\n" + "="*60)
        print("🔍 TESTING QR CODE INFO ENDPOINT")
        print("="*60)
        
        success, response = self.run_test(
            "Get Payment QR Info",
            "GET",
            "payment-qr-info",
            200
        )
        
        if success and response:
            try:
                result = response.json()
                print(f"   📊 QR Info Details:")
                print(f"      - UPI ID: {result.get('upi_id', 'N/A')}")
                print(f"      - Bank: {result.get('bank_name', 'N/A')}")
                print(f"      - Account: {result.get('account_name', 'N/A')}")
                print(f"      - Account Number: {result.get('account_number', 'N/A')}")
                print(f"      - IFSC: {result.get('ifsc_code', 'N/A')}")
                print(f"      - QR Image URL: {result.get('qr_image_url', 'N/A')}")
                print(f"      - Instructions: {len(result.get('instructions', []))} items")
                
                # Validate required fields
                required_fields = ['upi_id', 'bank_name', 'account_name', 'account_number', 'ifsc_code']
                missing_fields = [field for field in required_fields if not result.get(field)]
                if missing_fields:
                    print(f"   ⚠️  Missing fields: {', '.join(missing_fields)}")
                else:
                    print("   ✅ All required fields present")
            except Exception as e:
                print(f"   ❌ Error parsing response: {e}")

    def get_existing_pending_invoice(self):
        """Get an existing pending invoice for testing"""
        print("\n📝 Looking for existing pending invoice...")
        
        success, response = self.run_test(
            "Get Existing Invoices",
            "GET",
            "invoices?view=manage",
            200,
            token=self.admin_token
        )
        
        if success and response:
            try:
                invoices = response.json()
                # Look for a pending invoice
                pending_invoices = [inv for inv in invoices if inv.get('payment_status') == 'pending']
                if pending_invoices:
                    test_invoice = pending_invoices[0]
                    invoice_id = test_invoice.get('id')
                    invoice_number = test_invoice.get('invoice_number')
                    print(f"   ✅ Found pending invoice: {invoice_number} (ID: {invoice_id})")
                    return invoice_id
                else:
                    print("   ⚠️  No pending invoices found")
                    return None
            except:
                print("   ❌ Error parsing invoices response")
                return None
        else:
            print("   ❌ Failed to get existing invoices")
            return None

    def test_offline_payment_submission(self):
        """Test offline payment submission"""
        print("\n" + "="*60)
        print("💳 TESTING OFFLINE PAYMENT SUBMISSION")
        print("="*60)
        
        # Get an existing pending invoice if we don't have one
        if not self.test_invoice_id:
            self.test_invoice_id = self.get_existing_pending_invoice()
        
        if not self.test_invoice_id:
            print("   ❌ Cannot test offline payment without a pending invoice")
            self.failed_tests.append("Offline Payment Submission: No pending invoice available")
            return
        
        # Test 1: Submit offline payment
        payment_data = {
            "transaction_reference": f"TEST-TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        success, response = self.run_test(
            "Submit Offline Payment",
            "POST",
            f"invoices/{self.test_invoice_id}/pay-offline",
            200,
            data=payment_data,
            token=self.user_token
        )
        
        if success and response:
            try:
                result = response.json()
                print(f"   📊 Submission Result:")
                print(f"      - Message: {result.get('message', 'N/A')}")
                print(f"      - Invoice ID: {result.get('invoice_id', 'N/A')}")
            except:
                pass
        
        # Test 2: Try to submit again (should fail)
        self.run_test(
            "Submit Offline Payment Again (Should Fail)",
            "POST",
            f"invoices/{self.test_invoice_id}/pay-offline",
            400,  # Should fail with 400
            data=payment_data,
            token=self.user_token
        )

    def test_pending_approvals(self):
        """Test pending approvals endpoint"""
        print("\n" + "="*60)
        print("⏳ TESTING PENDING APPROVALS")
        print("="*60)
        
        # Test 1: Get pending approvals (admin access)
        success, response = self.run_test(
            "Get Pending Approvals (Admin)",
            "GET",
            "invoices/pending-approvals",
            200,
            token=self.admin_token
        )
        
        if success and response:
            try:
                result = response.json()
                print(f"   📊 Pending Approvals:")
                print(f"      - Count: {len(result)}")
                for approval in result[:3]:  # Show first 3
                    print(f"        * Invoice: {approval.get('invoice_number', 'N/A')}")
                    print(f"          User: {approval.get('user_name', 'N/A')}")
                    print(f"          Amount: ₹{approval.get('total_amount', 0)}")
                    print(f"          Reference: {approval.get('offline_transaction_reference', 'N/A')}")
            except:
                pass
        
        # Test 2: Try with user token (should fail)
        self.run_test(
            "Get Pending Approvals (User - Should Fail)",
            "GET",
            "invoices/pending-approvals",
            403,  # Should fail with 403
            token=self.user_token
        )

    def test_payment_approval_rejection(self):
        """Test payment approval and rejection"""
        print("\n" + "="*60)
        print("✅❌ TESTING PAYMENT APPROVAL/REJECTION")
        print("="*60)
        
        if not self.test_invoice_id:
            print("   ❌ Cannot test approval/rejection without a test invoice")
            self.failed_tests.append("Payment Approval/Rejection: No test invoice available")
            return
        
        # Test 1: Approve offline payment
        approval_data = {
            "approval_note": "Test approval - payment verified"
        }
        
        success, response = self.run_test(
            "Approve Offline Payment",
            "POST",
            f"invoices/{self.test_invoice_id}/approve-offline",
            200,
            data=approval_data,
            token=self.admin_token
        )
        
        if success and response:
            try:
                result = response.json()
                print(f"   📊 Approval Result:")
                print(f"      - Message: {result.get('message', 'N/A')}")
                print(f"      - Invoice ID: {result.get('invoice_id', 'N/A')}")
            except:
                pass
        
        # Get another pending invoice for rejection test
        rejection_invoice_id = self.get_existing_pending_invoice()
        if rejection_invoice_id and rejection_invoice_id != self.test_invoice_id:
            # Submit offline payment for rejection test
            payment_data = {
                "transaction_reference": f"REJECT-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            submit_success, _ = self.run_test(
                "Submit Payment for Rejection Test",
                "POST",
                f"invoices/{rejection_invoice_id}/pay-offline",
                200,
                data=payment_data,
                token=self.user_token
            )
            
            if submit_success:
                # Test 2: Reject offline payment
                rejection_data = {
                    "rejection_reason": "Test rejection - invalid transaction reference"
                }
                
                self.run_test(
                    "Reject Offline Payment",
                    "POST",
                    f"invoices/{rejection_invoice_id}/reject-offline",
                    200,
                    data=rejection_data,
                    token=self.admin_token
                )
        else:
            print("   ⚠️  No additional pending invoice found for rejection test")

    def test_invoice_status_flow(self):
        """Test the complete invoice status flow"""
        print("\n" + "="*60)
        print("🔄 TESTING INVOICE STATUS FLOW")
        print("="*60)
        
        # Create a fresh invoice for status flow testing
        flow_invoice_id = self.create_test_invoice()
        if not flow_invoice_id:
            print("   ❌ Cannot test status flow without a test invoice")
            return
        
        # Step 1: Check initial status (should be pending)
        success, response = self.run_test(
            "Check Initial Invoice Status",
            "GET",
            f"invoices?view=manage",
            200,
            token=self.admin_token
        )
        
        if success and response:
            try:
                invoices = response.json()
                test_invoice = next((inv for inv in invoices if inv['id'] == flow_invoice_id), None)
                if test_invoice:
                    print(f"   📊 Initial Status: {test_invoice.get('payment_status', 'N/A')}")
                    print(f"   📊 Offline Status: {test_invoice.get('offline_payment_status', 'None')}")
                else:
                    print("   ⚠️  Test invoice not found in list")
            except:
                pass
        
        # Step 2: Submit offline payment
        payment_data = {
            "transaction_reference": f"FLOW-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        submit_success, _ = self.run_test(
            "Submit Offline Payment (Flow Test)",
            "POST",
            f"invoices/{flow_invoice_id}/pay-offline",
            200,
            data=payment_data,
            token=self.user_token
        )
        
        if submit_success:
            # Step 3: Check status after submission (should be pending_approval)
            success, response = self.run_test(
                "Check Status After Submission",
                "GET",
                f"invoices?view=manage",
                200,
                token=self.admin_token
            )
            
            if success and response:
                try:
                    invoices = response.json()
                    test_invoice = next((inv for inv in invoices if inv['id'] == flow_invoice_id), None)
                    if test_invoice:
                        print(f"   📊 After Submission - Payment Status: {test_invoice.get('payment_status', 'N/A')}")
                        print(f"   📊 After Submission - Offline Status: {test_invoice.get('offline_payment_status', 'None')}")
                    else:
                        print("   ⚠️  Test invoice not found after submission")
                except:
                    pass
            
            # Step 4: Approve payment
            approval_data = {
                "approval_note": "Flow test approval"
            }
            
            approve_success, _ = self.run_test(
                "Approve Payment (Flow Test)",
                "POST",
                f"invoices/{flow_invoice_id}/approve-offline",
                200,
                data=approval_data,
                token=self.admin_token
            )
            
            if approve_success:
                # Step 5: Check final status (should be paid)
                success, response = self.run_test(
                    "Check Final Status After Approval",
                    "GET",
                    f"invoices?view=manage",
                    200,
                    token=self.admin_token
                )
                
                if success and response:
                    try:
                        invoices = response.json()
                        test_invoice = next((inv for inv in invoices if inv['id'] == flow_invoice_id), None)
                        if test_invoice:
                            print(f"   📊 Final - Payment Status: {test_invoice.get('payment_status', 'N/A')}")
                            print(f"   📊 Final - Offline Status: {test_invoice.get('offline_payment_status', 'None')}")
                            print(f"   📊 Final - Payment Method: {test_invoice.get('payment_method', 'None')}")
                            print(f"   📊 Final - Payment Date: {test_invoice.get('payment_date', 'None')}")
                        else:
                            print("   ⚠️  Test invoice not found after approval")
                    except:
                        pass

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting TROA Offline QR Payment API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🔑 Using tokens: User, Admin & Accountant")
        
        # Run test suites for offline payment system
        self.test_offline_payment_qr_info()
        self.test_offline_payment_submission()
        self.test_pending_approvals()
        self.test_payment_approval_rejection()
        self.test_invoice_status_flow()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\n🔍 Failed Tests:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 Overall Status: GOOD")
        elif success_rate >= 60:
            print("⚠️  Overall Status: NEEDS ATTENTION")
        else:
            print("🚨 Overall Status: CRITICAL ISSUES")
        
        return success_rate >= 80

def main():
    tester = TROAOfflinePaymentTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())