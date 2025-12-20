import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

committee_members_data = [
    {
        "name": "Wilson Thomas",
        "position": "President",
        "image": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Sundar Ramakrishnan",
        "position": "Secretary",
        "image": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Shaveta Sharma",
        "position": "Treasurer",
        "image": "https://images.unsplash.com/photo-1611432579402-7037e3e2c1e4?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Renuka Shastry",
        "position": "Legal",
        "image": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Surendra Saxena",
        "position": "Systems",
        "image": "https://images.unsplash.com/photo-1629425733761-caae3b5f2e50?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Ganga Suresh",
        "position": "Waste Management",
        "image": "https://images.pexels.com/photos/2182970/pexels-photo-2182970.jpeg?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Leena Itty",
        "position": "Landscaping",
        "image": "https://images.pexels.com/photos/2381069/pexels-photo-2381069.jpeg?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Anu Ram",
        "position": "Club House",
        "image": "https://images.pexels.com/photos/762020/pexels-photo-762020.jpeg?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    },
    {
        "name": "Seena Ajit",
        "position": "Social Activities",
        "image": "https://images.unsplash.com/photo-1759886417237-5c4cb0dcc06b?w=400&q=80",
        "facebook": "#",
        "twitter": "#",
        "linkedin": "#"
    }
]

amenities_data = [
    {
        "name": "Swimming Pool",
        "description": "Olympic-sized swimming pool with dedicated lanes for lap swimming and a separate area for leisure swimming. Open daily from 6 AM to 10 PM.",
        "image": "https://images.unsplash.com/photo-1558617320-e695f0d420de?w=800&q=80"
    },
    {
        "name": "Club House",
        "description": "Modern clubhouse featuring meeting rooms, entertainment areas, and a fully-equipped kitchen for community events and gatherings.",
        "image": "https://images.unsplash.com/photo-1763463158922-f2a70d5a063b?w=800&q=80"
    },
    {
        "name": "Fitness Center",
        "description": "State-of-the-art gym with cardio equipment, weight training machines, and free weights. Personal training sessions available.",
        "image": "https://images.unsplash.com/photo-1536745511564-a5fa6e596e7b?w=800&q=80"
    },
    {
        "name": "Landscaped Gardens",
        "description": "Beautifully maintained gardens with walking paths, seating areas, and a variety of plants and flowers creating a serene environment.",
        "image": "https://images.unsplash.com/photo-1759702130803-b261e4e19e58?w=800&q=80"
    },
    {
        "name": "Children's Play Area",
        "description": "Safe and fun playground for children with modern equipment, soft flooring, and shaded seating areas for parents.",
        "image": "https://images.pexels.com/photos/1147124/pexels-photo-1147124.jpeg?w=800&q=80"
    },
    {
        "name": "Sports Courts",
        "description": "Multi-purpose sports courts for tennis, basketball, and badminton. Equipment rental available at the clubhouse.",
        "image": "https://images.pexels.com/photos/97047/pexels-photo-97047.jpeg?w=800&q=80"
    }
]

gallery_images_data = [
    {
        "title": "Community Dinner",
        "category": "Social Events",
        "url": "https://images.unsplash.com/photo-1528605248644-14dd04022da1?w=800&q=80"
    },
    {
        "title": "Annual Meet",
        "category": "Community Events",
        "url": "https://images.unsplash.com/photo-1519671282429-b44660ead0a7?w=800&q=80"
    },
    {
        "title": "Residents Gathering",
        "category": "Social Events",
        "url": "https://images.unsplash.com/photo-1511988617509-a57c8a288659?w=800&q=80"
    },
    {
        "title": "Backyard BBQ",
        "category": "Community Events",
        "url": "https://images.unsplash.com/photo-1621112904887-419379ce6824?w=800&q=80"
    },
    {
        "title": "Community Celebration",
        "category": "Festivals",
        "url": "https://images.unsplash.com/photo-1565813086292-604790c8a97b?w=800&q=80"
    },
    {
        "title": "Workshop Day",
        "category": "Activities",
        "url": "https://images.unsplash.com/photo-1544928147-79a2dbc1f389?w=800&q=80"
    },
    {
        "title": "Festival Celebration",
        "category": "Festivals",
        "url": "https://images.unsplash.com/photo-1472653431158-6364773b2a56?w=800&q=80"
    },
    {
        "title": "Social Gathering",
        "category": "Social Events",
        "url": "https://images.pexels.com/photos/1655329/pexels-photo-1655329.jpeg?w=800&q=80"
    }
]

async def seed_database():
    print("Starting database seeding...")
    
    # Clear existing data
    await db.committee_members.delete_many({})
    await db.amenities.delete_many({})
    await db.gallery_images.delete_many({})
    print("Cleared existing data")
    
    # Insert committee members
    if committee_members_data:
        await db.committee_members.insert_many(committee_members_data)
        print(f"Inserted {len(committee_members_data)} committee members")
    
    # Insert amenities
    if amenities_data:
        await db.amenities.insert_many(amenities_data)
        print(f"Inserted {len(amenities_data)} amenities")
    
    # Insert gallery images
    if gallery_images_data:
        await db.gallery_images.insert_many(gallery_images_data)
        print(f"Inserted {len(gallery_images_data)} gallery images")
    
    print("Database seeding completed successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
