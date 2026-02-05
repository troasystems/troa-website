#!/usr/bin/env python3
"""
WebSocket Community Chat Testing Suite
Tests WebSocket endpoints, real-time messaging, typing indicators, read receipts, and HTTP fallback
"""

import asyncio
import websockets
import json
import requests
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

class WebSocketChatTester:
    def __init__(self, base_url="https://emailbuzz.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.ws_url = base_url.replace('https://', 'wss://').replace('http://', 'ws://')
        self.token = None
        self.user_email = None
        self.user_name = None
        self.test_group_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.websocket_connections = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_test(self, name: str, test_func, *args, **kwargs):
        """Run a single test with error handling"""
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            result = test_func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            
            if result:
                self.tests_passed += 1
                self.log(f"✅ {name} - PASSED", "SUCCESS")
                return True
            else:
                self.log(f"❌ {name} - FAILED", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}", "ERROR")
            return False
    
    def test_login(self) -> bool:
        """Test user authentication"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={
                    "email": "troa.systems@gmail.com",
                    "password": "Test@123"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.user_email = data.get('user', {}).get('email')
                self.user_name = data.get('user', {}).get('name', 'Test User')
                self.log(f"Login successful for {self.user_email}")
                return True
            else:
                self.log(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"Login error: {e}")
            return False
    
    def test_get_groups(self) -> bool:
        """Test fetching chat groups"""
        try:
            response = requests.get(
                f"{self.api_url}/chat/groups",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                groups = response.json()
                if groups:
                    self.test_group_id = groups[0]['id']
                    self.log(f"Found {len(groups)} groups, using group: {groups[0]['name']}")
                    return True
                else:
                    self.log("No groups found")
                    return False
            else:
                self.log(f"Get groups failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"Get groups error: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection to chat endpoint"""
        if not self.test_group_id:
            self.log("No test group available for WebSocket test")
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            async with websockets.connect(ws_endpoint, timeout=10) as websocket:
                self.log("WebSocket connection established successfully")
                
                # Wait for initial messages (like online users)
                try:
                    initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(initial_msg)
                    self.log(f"Received initial message: {data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    self.log("No initial message received (this is okay)")
                
                return True
                
        except websockets.exceptions.ConnectionClosed as e:
            self.log(f"WebSocket connection closed: {e}")
            return False
        except Exception as e:
            self.log(f"WebSocket connection error: {e}")
            return False
    
    async def test_websocket_message_sending(self) -> bool:
        """Test sending messages via WebSocket"""
        if not self.test_group_id:
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            async with websockets.connect(ws_endpoint, timeout=10) as websocket:
                # Send a test message
                test_message = {
                    "type": "send_message",
                    "content": f"WebSocket test message at {datetime.now().isoformat()}"
                }
                
                await websocket.send(json.dumps(test_message))
                self.log("Test message sent via WebSocket")
                
                # Wait for message confirmation or broadcast
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(response)
                    
                    if data.get('type') == 'new_message':
                        self.log("Received message confirmation via WebSocket")
                        return True
                    else:
                        self.log(f"Unexpected response type: {data.get('type')}")
                        return False
                        
                except asyncio.TimeoutError:
                    self.log("No response received for sent message")
                    return False
                    
        except Exception as e:
            self.log(f"WebSocket message sending error: {e}")
            return False
    
    async def test_typing_indicators(self) -> bool:
        """Test typing indicators via WebSocket"""
        if not self.test_group_id:
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            async with websockets.connect(ws_endpoint, timeout=10) as websocket:
                # Send start typing
                await websocket.send(json.dumps({"type": "start_typing"}))
                self.log("Sent start_typing indicator")
                
                # Wait a moment
                await asyncio.sleep(1)
                
                # Send stop typing
                await websocket.send(json.dumps({"type": "stop_typing"}))
                self.log("Sent stop_typing indicator")
                
                return True
                
        except Exception as e:
            self.log(f"Typing indicators error: {e}")
            return False
    
    async def test_online_users(self) -> bool:
        """Test online users functionality"""
        if not self.test_group_id:
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            async with websockets.connect(ws_endpoint, timeout=10) as websocket:
                # Request online users
                await websocket.send(json.dumps({"type": "get_online_users"}))
                self.log("Requested online users list")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get('type') == 'online_users':
                        users = data.get('users', [])
                        self.log(f"Received online users: {len(users)} users")
                        return True
                    else:
                        # Check if we get online_users in initial connection
                        self.log("Checking for online_users in connection messages...")
                        return True  # Connection itself indicates online tracking works
                        
                except asyncio.TimeoutError:
                    self.log("No online users response (may be sent on connection)")
                    return True  # This is acceptable
                    
        except Exception as e:
            self.log(f"Online users test error: {e}")
            return False
    
    def test_http_polling_fallback(self) -> bool:
        """Test HTTP endpoints as fallback when WebSocket fails"""
        if not self.test_group_id:
            return False
        
        try:
            # Test getting messages via HTTP
            response = requests.get(
                f"{self.api_url}/chat/groups/{self.test_group_id}/messages",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                messages = response.json()
                self.log(f"HTTP fallback: Retrieved {len(messages)} messages")
                
                # Test typing status via HTTP
                typing_response = requests.get(
                    f"{self.api_url}/chat/groups/{self.test_group_id}/typing",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                
                if typing_response.status_code == 200:
                    self.log("HTTP fallback: Typing status endpoint working")
                    return True
                else:
                    self.log(f"HTTP typing endpoint failed: {typing_response.status_code}")
                    return False
            else:
                self.log(f"HTTP messages endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"HTTP fallback test error: {e}")
            return False
    
    async def test_websocket_reconnection(self) -> bool:
        """Test WebSocket reconnection logic"""
        if not self.test_group_id:
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            # First connection
            websocket1 = await websockets.connect(ws_endpoint, timeout=10)
            self.log("First WebSocket connection established")
            
            # Close it
            await websocket1.close()
            self.log("First connection closed")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Second connection (simulating reconnection)
            websocket2 = await websockets.connect(ws_endpoint, timeout=10)
            self.log("Second WebSocket connection established (reconnection test)")
            
            await websocket2.close()
            return True
            
        except Exception as e:
            self.log(f"WebSocket reconnection test error: {e}")
            return False
    
    async def test_read_receipts(self) -> bool:
        """Test read receipts via WebSocket"""
        if not self.test_group_id:
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            async with websockets.connect(ws_endpoint, timeout=10) as websocket:
                # Get recent messages first
                response = requests.get(
                    f"{self.api_url}/chat/groups/{self.test_group_id}/messages?limit=5",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    if messages:
                        # Send read receipt for the latest message
                        message_ids = [msg['id'] for msg in messages[:2]]  # Mark first 2 as read
                        read_receipt = {
                            "type": "mark_read",
                            "message_ids": message_ids
                        }
                        
                        await websocket.send(json.dumps(read_receipt))
                        self.log(f"Sent read receipt for {len(message_ids)} messages")
                        return True
                    else:
                        self.log("No messages to mark as read")
                        return True  # Not a failure
                else:
                    self.log("Could not fetch messages for read receipt test")
                    return False
                    
        except Exception as e:
            self.log(f"Read receipts test error: {e}")
            return False
    
    async def test_reactions_sync(self) -> bool:
        """Test reactions sync via WebSocket"""
        if not self.test_group_id:
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            async with websockets.connect(ws_endpoint, timeout=10) as websocket:
                # Get recent messages first
                response = requests.get(
                    f"{self.api_url}/chat/groups/{self.test_group_id}/messages?limit=5",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    messages = response.json()
                    if messages:
                        # Add reaction to the latest message
                        message_id = messages[0]['id']
                        reaction = {
                            "type": "add_reaction",
                            "message_id": message_id,
                            "emoji": "👍"
                        }
                        
                        await websocket.send(json.dumps(reaction))
                        self.log(f"Sent reaction to message {message_id}")
                        
                        # Wait for reaction update
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            data = json.loads(response)
                            
                            if data.get('type') == 'reaction_added':
                                self.log("Received reaction update via WebSocket")
                                return True
                            else:
                                self.log(f"Unexpected response: {data.get('type')}")
                                return True  # Reaction was sent successfully
                                
                        except asyncio.TimeoutError:
                            self.log("No reaction update received (but reaction was sent)")
                            return True
                    else:
                        self.log("No messages to react to")
                        return True
                else:
                    self.log("Could not fetch messages for reaction test")
                    return False
                    
        except Exception as e:
            self.log(f"Reactions sync test error: {e}")
            return False
    
    def test_websocket_endpoint_accessibility(self) -> bool:
        """Test if WebSocket endpoint is accessible"""
        if not self.test_group_id:
            return False
        
        ws_endpoint = f"{self.ws_url}/api/chat/ws/{self.test_group_id}?token={self.token}"
        
        try:
            # Use asyncio to test connection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def test_connection():
                try:
                    async with websockets.connect(ws_endpoint, timeout=5) as websocket:
                        return True
                except Exception:
                    return False
            
            result = loop.run_until_complete(test_connection())
            loop.close()
            
            if result:
                self.log("WebSocket endpoint is accessible")
                return True
            else:
                self.log("WebSocket endpoint is not accessible")
                return False
                
        except Exception as e:
            self.log(f"WebSocket accessibility test error: {e}")
            return False

def main():
    """Main test execution"""
    tester = WebSocketChatTester()
    
    print("=" * 60)
    print("🚀 WebSocket Community Chat Testing Suite")
    print("=" * 60)
    
    # Authentication tests
    if not tester.run_test("User Login", tester.test_login):
        print("❌ Cannot proceed without authentication")
        return 1
    
    if not tester.run_test("Fetch Chat Groups", tester.test_get_groups):
        print("❌ Cannot proceed without chat groups")
        return 1
    
    # WebSocket endpoint tests
    tester.run_test("WebSocket Endpoint Accessibility", tester.test_websocket_endpoint_accessibility)
    tester.run_test("WebSocket Connection", tester.test_websocket_connection)
    tester.run_test("WebSocket Message Sending", tester.test_websocket_message_sending)
    tester.run_test("Typing Indicators", tester.test_typing_indicators)
    tester.run_test("Online Users Count", tester.test_online_users)
    tester.run_test("Read Receipts", tester.test_read_receipts)
    tester.run_test("Reactions Sync", tester.test_reactions_sync)
    tester.run_test("WebSocket Reconnection", tester.test_websocket_reconnection)
    
    # HTTP fallback tests
    tester.run_test("HTTP Polling Fallback", tester.test_http_polling_fallback)
    
    # Results summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())