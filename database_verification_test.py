#!/usr/bin/env python3
"""
Database Verification Test for TROA Committee Members
Verifies that all committee members have proper UUIDs and can be updated.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'test_database')

async def verify_committee_members():
    """Verify committee members in database"""
    print("🔍 Verifying Committee Members in Database...")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get all committee members
        members = await db.committee_members.find().to_list(100)
        print(f"📊 Found {len(members)} committee members in database")
        
        issues_found = []
        valid_members = []
        
        for i, member in enumerate(members, 1):
            member_id = member.get('id')
            name = member.get('name', 'Unknown')
            position = member.get('position', 'Unknown')
            
            print(f"\n{i}. {name} - {position}")
            print(f"   ID: {member_id}")
            
            # Check if ID exists and is valid UUID format
            if not member_id:
                issues_found.append(f"❌ {name}: Missing ID")
                continue
            
            # Check if it's a valid UUID format
            try:
                uuid.UUID(member_id)
                print(f"   ✅ Valid UUID format")
                valid_members.append(member)
            except ValueError:
                issues_found.append(f"❌ {name}: Invalid UUID format: {member_id}")
                continue
            
            # Check required fields
            required_fields = ['name', 'position', 'image', 'created_at']
            missing_fields = [field for field in required_fields if not member.get(field)]
            
            if missing_fields:
                issues_found.append(f"⚠️  {name}: Missing fields: {missing_fields}")
            else:
                print(f"   ✅ All required fields present")
        
        print(f"\n📈 Summary:")
        print(f"   Total members: {len(members)}")
        print(f"   Valid members: {len(valid_members)}")
        print(f"   Issues found: {len(issues_found)}")
        
        if issues_found:
            print(f"\n🚨 Issues Found:")
            for issue in issues_found:
                print(f"   {issue}")
        else:
            print(f"\n🎉 All committee members have proper UUIDs!")
        
        # Find Wilson Thomas for testing
        wilson_member = None
        for member in valid_members:
            if 'Wilson' in member.get('name', '') and 'President' in member.get('position', ''):
                wilson_member = member
                break
        
        if wilson_member:
            print(f"\n🎯 Wilson Thomas found:")
            print(f"   Name: {wilson_member['name']}")
            print(f"   Position: {wilson_member['position']}")
            print(f"   ID: {wilson_member['id']}")
            print(f"   Image: {wilson_member.get('image', 'N/A')}")
        else:
            print(f"\n⚠️  Wilson Thomas (President) not found in database")
            if valid_members:
                print(f"   Available members:")
                for member in valid_members[:5]:  # Show first 5
                    print(f"   - {member['name']} ({member['position']}) - ID: {member['id']}")
        
        return valid_members, wilson_member
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return [], None
    finally:
        client.close()

async def test_committee_member_update_simulation():
    """Simulate committee member update in database"""
    print(f"\n🧪 Testing Committee Member Update Simulation...")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Find Wilson Thomas or first member
        member = await db.committee_members.find_one({
            "$or": [
                {"name": {"$regex": "Wilson", "$options": "i"}},
                {"position": {"$regex": "President", "$options": "i"}}
            ]
        })
        
        if not member:
            # Get first member
            member = await db.committee_members.find_one()
        
        if not member:
            print("❌ No committee members found for testing")
            return False
        
        member_id = member['id']
        original_name = member['name']
        
        print(f"🎯 Testing update for: {original_name} (ID: {member_id})")
        
        # Simulate update
        test_name = f"{original_name} - Updated Test"
        update_result = await db.committee_members.update_one(
            {"id": member_id},
            {"$set": {"name": test_name, "updated_at": datetime.utcnow()}}
        )
        
        if update_result.modified_count == 1:
            print(f"✅ Update successful: Modified {update_result.modified_count} document")
            
            # Verify update
            updated_member = await db.committee_members.find_one({"id": member_id})
            if updated_member and updated_member['name'] == test_name:
                print(f"✅ Verification successful: Name updated to '{test_name}'")
                
                # Restore original name
                restore_result = await db.committee_members.update_one(
                    {"id": member_id},
                    {"$set": {"name": original_name}, "$unset": {"updated_at": ""}}
                )
                
                if restore_result.modified_count == 1:
                    print(f"✅ Restored original name: '{original_name}'")
                    return True
                else:
                    print(f"⚠️  Failed to restore original name")
                    return False
            else:
                print(f"❌ Verification failed: Update not reflected")
                return False
        else:
            print(f"❌ Update failed: Modified {update_result.modified_count} documents")
            return False
            
    except Exception as e:
        print(f"❌ Update test error: {e}")
        return False
    finally:
        client.close()

async def main():
    """Main test function"""
    print("🚀 Starting Database Verification Tests")
    print(f"📍 MongoDB URL: {mongo_url}")
    print(f"📍 Database: {db_name}")
    print("=" * 60)
    
    # Verify committee members
    valid_members, wilson_member = await verify_committee_members()
    
    # Test update simulation
    update_success = await test_committee_member_update_simulation()
    
    print(f"\n" + "=" * 60)
    print("📊 DATABASE VERIFICATION RESULTS")
    print("=" * 60)
    print(f"✅ Committee members with valid UUIDs: {len(valid_members)}")
    print(f"{'✅' if wilson_member else '⚠️ '} Wilson Thomas (President) found: {'Yes' if wilson_member else 'No'}")
    print(f"{'✅' if update_success else '❌'} Database update test: {'PASS' if update_success else 'FAIL'}")
    
    if valid_members and update_success:
        print(f"\n🎉 Database is properly configured for committee member updates!")
        return True
    else:
        print(f"\n⚠️  Database issues found - may affect committee member updates")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)