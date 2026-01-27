"""
TROA Villa Migration Script
Run this script to migrate existing user villa_number data to the new villas collection.

Usage:
    python migrate_villas.py

This script will:
1. Create villa records from existing users' villa_number field
2. Link user emails to their respective villas
3. Report migration statistics
"""

import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')


async def migrate_villas():
    """Migrate existing users' villa_number to create villa records."""
    print(f"Connecting to MongoDB: {MONGO_URL}")
    print(f"Database: {DB_NAME}")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Get all users with villa_number set
        users = await db.users.find(
            {"villa_number": {"$exists": True, "$ne": ""}},
            {"_id": 0, "email": 1, "villa_number": 1, "name": 1}
        ).to_list(10000)
        
        print(f"\nFound {len(users)} users with villa numbers")
        
        created_villas = 0
        updated_villas = 0
        skipped = 0
        errors = []
        
        # Group users by villa_number
        villa_users = {}
        for user in users:
            villa_number = user.get("villa_number", "").strip()
            email = user.get("email", "").lower().strip()
            
            if not villa_number or not email:
                skipped += 1
                continue
            
            if villa_number not in villa_users:
                villa_users[villa_number] = []
            villa_users[villa_number].append(email)
        
        print(f"Found {len(villa_users)} unique villa numbers")
        
        # Create or update villas
        for villa_number, emails in villa_users.items():
            try:
                existing = await db.villas.find_one({"villa_number": villa_number})
                
                if existing:
                    # Add emails that aren't already present
                    current_emails = set(e.lower() for e in existing.get("emails", []))
                    new_emails = [e for e in emails if e.lower() not in current_emails]
                    
                    if new_emails:
                        await db.villas.update_one(
                            {"villa_number": villa_number},
                            {
                                "$push": {"emails": {"$each": new_emails}},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        updated_villas += 1
                        print(f"  Updated villa {villa_number}: added {len(new_emails)} email(s)")
                else:
                    # Create new villa
                    villa_doc = {
                        "villa_number": villa_number,
                        "square_feet": 0.0,
                        "emails": list(set(emails)),  # Dedupe
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    await db.villas.insert_one(villa_doc)
                    created_villas += 1
                    print(f"  Created villa {villa_number} with {len(villa_doc['emails'])} email(s)")
                    
            except Exception as e:
                errors.append(f"Villa {villa_number}: {str(e)}")
        
        # Create index on villa_number for faster lookups
        await db.villas.create_index("villa_number", unique=True)
        await db.villas.create_index("emails")
        
        print("\n" + "="*50)
        print("MIGRATION SUMMARY")
        print("="*50)
        print(f"Users processed: {len(users)}")
        print(f"Unique villas found: {len(villa_users)}")
        print(f"Villas created: {created_villas}")
        print(f"Villas updated: {updated_villas}")
        print(f"Skipped (no villa/email): {skipped}")
        
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for error in errors[:10]:
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        
        # Verify migration
        total_villas = await db.villas.count_documents({})
        print(f"\nTotal villas in database: {total_villas}")
        
        return {
            "success": True,
            "created": created_villas,
            "updated": updated_villas,
            "total_villas": total_villas,
            "errors": errors
        }
        
    finally:
        client.close()


async def add_invoice_type_to_existing():
    """Add invoice_type field to existing invoices (mark as clubhouse_subscription)."""
    print("\nMigrating existing invoices...")
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Update all invoices without invoice_type to be clubhouse_subscription
        result = await db.invoices.update_many(
            {"invoice_type": {"$exists": False}},
            {"$set": {"invoice_type": "clubhouse_subscription"}}
        )
        
        print(f"Updated {result.modified_count} invoices with invoice_type='clubhouse_subscription'")
        
        # Also add villa_number from user_villa if not set
        invoices_without_villa = await db.invoices.find(
            {"villa_number": {"$in": [None, ""]}},
            {"_id": 1, "user_villa": 1}
        ).to_list(10000)
        
        updated = 0
        for inv in invoices_without_villa:
            if inv.get("user_villa"):
                await db.invoices.update_one(
                    {"_id": inv["_id"]},
                    {"$set": {"villa_number": inv["user_villa"]}}
                )
                updated += 1
        
        print(f"Updated {updated} invoices with villa_number from user_villa")
        
        return {"success": True, "invoices_updated": result.modified_count + updated}
        
    finally:
        client.close()


async def verify_migration():
    """Verify the migration was successful."""
    print("\n" + "="*50)
    print("VERIFICATION")
    print("="*50)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Count villas
        villa_count = await db.villas.count_documents({})
        print(f"Total villas: {villa_count}")
        
        # Count villas with emails
        villas_with_emails = await db.villas.count_documents({"emails.0": {"$exists": True}})
        print(f"Villas with at least 1 email: {villas_with_emails}")
        
        # Sample villas
        print("\nSample villas:")
        sample_villas = await db.villas.find({}, {"_id": 0}).limit(5).to_list(5)
        for villa in sample_villas:
            print(f"  Villa {villa['villa_number']}: {len(villa.get('emails', []))} email(s), {villa.get('square_feet', 0)} sq.ft")
        
        # Invoice types
        clubhouse_count = await db.invoices.count_documents({"invoice_type": "clubhouse_subscription"})
        maintenance_count = await db.invoices.count_documents({"invoice_type": "maintenance"})
        no_type_count = await db.invoices.count_documents({"invoice_type": {"$exists": False}})
        
        print(f"\nInvoice types:")
        print(f"  Clubhouse subscription: {clubhouse_count}")
        print(f"  Maintenance: {maintenance_count}")
        print(f"  No type (needs migration): {no_type_count}")
        
        # User roles
        role_counts = {}
        for role in ['admin', 'manager', 'clubhouse_staff', 'accountant', 'user']:
            count = await db.users.count_documents({"role": role})
            role_counts[role] = count
        
        print(f"\nUser roles:")
        for role, count in role_counts.items():
            print(f"  {role}: {count}")
        
        return True
        
    finally:
        client.close()


async def main():
    print("="*50)
    print("TROA VILLA MIGRATION SCRIPT")
    print("="*50)
    
    # Run villa migration
    await migrate_villas()
    
    # Migrate invoice types
    await add_invoice_type_to_existing()
    
    # Verify
    await verify_migration()
    
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    asyncio.run(main())
