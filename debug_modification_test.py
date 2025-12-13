#!/usr/bin/env python3
"""
Debug script for event registration modification testing
"""

import requests
import json
import os
import base64
from datetime import datetime, timedelta

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://troa-residence.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

# Authentication credentials
BASIC_AUTH_USERNAME = "dogfooding"
BASIC_AUTH_PASSWORD = "skywalker"

# Setup authentication headers
basic_auth = base64.b64encode(f"{BASIC_AUTH_USERNAME}:{BASIC_AUTH_PASSWORD}".encode()).decode()
session_token = "PIgFhZEyDs02mjo9moXWHIBGEoGhwtaoOnUQvyVq7Bc"  # Valid admin session token
auth_headers = {
    'Authorization': f'Basic {basic_auth}',
    'X-Session-Token': f'Bearer {session_token}',
    'Content-Type': 'application/json'
}

def test_online_modification():
    """Test online payment modification specifically"""
    print("🧪 Testing Online Payment Modification...")
    
    try:
        # Create a new event for testing
        future_date = (datetime.now() + timedelta(days=16)).strftime('%Y-%m-%d')
        test_event = {
            "name": "Online Modification Test Event",
            "description": "Test event for online modification",
            "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
            "event_date": future_date,
            "event_time": "19:00",
            "amount": 200.0,
            "payment_type": "per_person",
            "per_person_type": "uniform",
            "preferences": [{"name": "Test Preference", "options": ["Option1", "Option2"]}],
            "max_registrations": 50
        }
        
        print("Creating test event...")
        response = requests.post(f"{API_BASE_URL}/events", 
                               json=test_event, 
                               headers=auth_headers,
                               timeout=10)
        
        if response.status_code == 200:
            event_id = response.json()['id']
            print(f"✅ Created event: {event_id}")
            
            # Create initial registration with offline payment
            registration_data = {
                "event_id": event_id,
                "registrants": [
                    {"name": "Test User Online", "preferences": {"Test Preference": "Option1"}}
                ],
                "payment_method": "offline"
            }
            
            print("Creating initial registration...")
            response = requests.post(f"{API_BASE_URL}/events/{event_id}/register", 
                                   json=registration_data, 
                                   headers=auth_headers,
                                   timeout=10)
            
            if response.status_code == 200:
                registration_id = response.json()['id']
                print(f"✅ Created registration: {registration_id}")
                
                # Try to modify with online payment
                modification_data = {
                    "registrants": [
                        {"name": "Test User Online", "preferences": {"Test Preference": "Option1"}},
                        {"name": "Test User Online 2", "preferences": {"Test Preference": "Option2"}}
                    ],
                    "payment_method": "online"
                }
                
                print("Attempting modification with online payment...")
                response = requests.patch(f"{API_BASE_URL}/events/registrations/{registration_id}/modify", 
                                        json=modification_data, 
                                        headers=auth_headers,
                                        timeout=10)
                
                print(f"Modification response status: {response.status_code}")
                print(f"Modification response: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Modification successful: {data}")
                    
                    # Try to create modification order
                    print("Attempting to create modification order...")
                    response = requests.post(f"{API_BASE_URL}/events/registrations/{registration_id}/create-modification-order", 
                                           headers=auth_headers,
                                           timeout=10)
                    
                    print(f"Create order response status: {response.status_code}")
                    print(f"Create order response: {response.text}")
                else:
                    print(f"❌ Modification failed: {response.status_code} - {response.text}")
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
        else:
            print(f"❌ Event creation failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_online_modification()