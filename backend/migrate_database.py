"""
Database Migration Script
Copies all data from 'test_database' to 'troa_residence'
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

SOURCE_DB = "test_database"
TARGET_DB = "troa_residence"

async def migrate_database():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    source_db = client[SOURCE_DB]
    target_db = client[TARGET_DB]
    
    # Get all collections from source
    collections = await source_db.list_collection_names()
    
    print(f"Starting migration from '{SOURCE_DB}' to '{TARGET_DB}'")
    print(f"Found {len(collections)} collections to migrate\n")
    
    total_docs = 0
    
    for collection_name in collections:
        source_col = source_db[collection_name]
        target_col = target_db[collection_name]
        
        # Count documents in source
        source_count = await source_col.count_documents({})
        
        if source_count == 0:
            print(f"  ⏭️  {collection_name}: 0 documents (skipping)")
            continue
        
        # Check if target already has data
        target_count = await target_col.count_documents({})
        if target_count > 0:
            print(f"  ⚠️  {collection_name}: Target already has {target_count} docs, skipping to prevent duplicates")
            continue
        
        # Fetch all documents from source
        documents = await source_col.find({}).to_list(length=None)
        
        # Insert into target
        if documents:
            await target_col.insert_many(documents)
            total_docs += len(documents)
            print(f"  ✅ {collection_name}: Migrated {len(documents)} documents")
    
    print(f"\n{'='*50}")
    print(f"Migration complete! Total documents migrated: {total_docs}")
    
    # Verify migration
    print(f"\nVerifying migration...")
    for collection_name in collections:
        source_count = await source_db[collection_name].count_documents({})
        target_count = await target_db[collection_name].count_documents({})
        status = "✅" if source_count == target_count else "❌"
        print(f"  {status} {collection_name}: source={source_count}, target={target_count}")
    
    client.close()
    print(f"\nMigration verified successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_database())
