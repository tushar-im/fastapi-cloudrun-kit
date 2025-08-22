#!/usr/bin/env python3
"""
Database seeding script for development and testing.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

# Set environment before importing app modules
os.environ["ENVIRONMENT"] = os.environ.get("ENVIRONMENT", "development")
os.environ["USE_FIREBASE_EMULATOR"] = "true"
os.environ["FIREBASE_PROJECT_ID"] = "demo-project"
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "localhost:9199"

from app.services.firebase import initialize_firebase
from app.services.auth import get_auth_service
from app.services.firestore import get_firestore_service


class DataSeeder:
    """Database seeder for development data."""

    def __init__(self):
        self.auth_service = get_auth_service()
        self.firestore_service = get_firestore_service()
        self.created_users = []
        self.created_items = []

    async def clear_data(self):
        """Clear existing data."""
        print("🗑️  Clearing existing data...")

        collections = ["users", "items", "item_interactions"]

        for collection in collections:
            try:
                docs = await self.firestore_service.query_documents(
                    collection, limit=1000
                )

                for doc in docs:
                    await self.firestore_service.delete_document(collection, doc["id"])

                print(f"   Cleared {len(docs)} documents from {collection}")

            except Exception as e:
                print(f"   Error clearing {collection}: {e}")

        print("✅ Data clearing completed")

    async def seed_users(self) -> List[Dict[str, Any]]:
        """Seed user data."""
        print("👥 Seeding users...")

        users_data = [
            {
                "email": "admin@example.com",
                "password": "AdminPassword123!",
                "display_name": "Admin User",
                "roles": ["admin"],
                "custom_claims": {"roles": ["admin"]},
                "email_verified": True,
                "profile": {
                    "bio": "System administrator",
                    "company": "FastAPI Corp",
                    "job_title": "System Administrator",
                },
            },
            {
                "email": "moderator@example.com",
                "password": "ModPassword123!",
                "display_name": "Moderator User",
                "roles": ["moderator"],
                "custom_claims": {"roles": ["moderator"]},
                "email_verified": True,
                "profile": {
                    "bio": "Content moderator",
                    "company": "FastAPI Corp",
                    "job_title": "Moderator",
                },
            },
            {
                "email": "john.doe@example.com",
                "password": "UserPassword123!",
                "display_name": "John Doe",
                "email_verified": True,
                "profile": {
                    "bio": "Software developer passionate about Python and FastAPI",
                    "location": "San Francisco, CA",
                    "website": "https://johndoe.dev",
                    "company": "Tech Startup Inc",
                    "job_title": "Senior Developer",
                },
                "preferences": {"notifications_email": True, "theme": "dark"},
            },
            {
                "email": "jane.smith@example.com",
                "password": "UserPassword123!",
                "display_name": "Jane Smith",
                "email_verified": True,
                "profile": {
                    "bio": "Product manager with a love for clean APIs",
                    "location": "New York, NY",
                    "company": "Product Co",
                    "job_title": "Product Manager",
                },
            },
            {
                "email": "demo@example.com",
                "password": "DemoPassword123!",
                "display_name": "Demo User",
                "email_verified": False,
                "profile": {"bio": "Demo account for testing purposes"},
            },
        ]

        created_users = []

        for user_data in users_data:
            try:
                user = await self.auth_service.create_user(**user_data)
                created_users.append(user)
                print(f"   ✅ Created user: {user['email']}")

            except Exception as e:
                print(f"   ❌ Failed to create user {user_data['email']}: {e}")

        self.created_users = created_users
        print(f"✅ Created {len(created_users)} users")
        return created_users

    async def seed_items(self) -> List[Dict[str, Any]]:
        """Seed item data."""
        print("📦 Seeding items...")

        if not self.created_users:
            print("   ⚠️  No users available for item creation")
            return []

        items_data = [
            {
                "title": "Getting Started with FastAPI",
                "description": "A comprehensive guide to building APIs with FastAPI framework",
                "category": "tech",
                "priority": "high",
                "status": "active",
                "tags": ["fastapi", "python", "api", "tutorial"],
                "is_public": True,
                "metadata": {"difficulty": "beginner", "estimated_time": "30 minutes"},
            },
            {
                "title": "Firebase Integration Best Practices",
                "description": "Learn how to effectively integrate Firebase with your applications",
                "category": "tech",
                "priority": "medium",
                "status": "active",
                "tags": ["firebase", "database", "authentication"],
                "is_public": True,
                "metadata": {"difficulty": "intermediate"},
            },
            {
                "title": "Project Planning Template",
                "description": "A template for planning software development projects",
                "category": "business",
                "priority": "medium",
                "status": "draft",
                "tags": ["planning", "template", "management"],
                "is_public": True,
            },
            {
                "title": "API Security Checklist",
                "description": "Essential security measures for production APIs",
                "category": "tech",
                "priority": "high",
                "status": "active",
                "tags": ["security", "api", "checklist"],
                "is_public": True,
                "metadata": {"importance": "critical"},
            },
            {
                "title": "Personal Development Goals",
                "description": "My personal goals for learning new technologies",
                "category": "personal",
                "priority": "low",
                "status": "draft",
                "tags": ["goals", "learning"],
                "is_public": False,
            },
            {
                "title": "Team Meeting Notes",
                "description": "Notes from weekly team synchronization",
                "category": "business",
                "priority": "medium",
                "status": "active",
                "tags": ["meeting", "notes", "team"],
                "is_public": False,
            },
            {
                "title": "Code Review Guidelines",
                "description": "Best practices for conducting effective code reviews",
                "category": "tech",
                "priority": "medium",
                "status": "active",
                "tags": ["code-review", "guidelines", "quality"],
                "is_public": True,
            },
            {
                "title": "Archived Old Project",
                "description": "Legacy project that is no longer active",
                "category": "other",
                "priority": "low",
                "status": "archived",
                "tags": ["archived", "legacy"],
                "is_public": False,
            },
        ]

        created_items = []

        for i, item_data in enumerate(items_data):
            try:
                # Assign items to different users
                owner = self.created_users[i % len(self.created_users)]
                item_data["owner_uid"] = owner["uid"]

                # Add timestamps
                item_data["view_count"] = i * 5  # Simulate some views
                item_data["like_count"] = max(0, i * 2 - 1)  # Simulate some likes
                item_data["share_count"] = max(0, i - 2)  # Simulate some shares

                item_id = await self.firestore_service.create_document(
                    "items", data=item_data
                )

                # Add the ID to the item data for reference
                item_data["id"] = item_id
                created_items.append(item_data)

                print(f"   ✅ Created item: {item_data['title']}")

            except Exception as e:
                print(f"   ❌ Failed to create item {item_data['title']}: {e}")

        self.created_items = created_items
        print(f"✅ Created {len(created_items)} items")
        return created_items

    async def seed_interactions(self):
        """Seed item interactions."""
        print("🤝 Seeding item interactions...")

        if not self.created_users or not self.created_items:
            print("   ⚠️  No users or items available for interaction creation")
            return

        interactions = []

        # Create some realistic interactions
        for item in self.created_items[:5]:  # Only for first 5 items
            for user in self.created_users[:3]:  # Only first 3 users
                # Skip if user owns the item
                if user["uid"] == item["owner_uid"]:
                    continue

                # Create view interactions
                interaction_data = {
                    "item_id": item["id"],
                    "user_uid": user["uid"],
                    "interaction_type": "view",
                    "timestamp": datetime.now(timezone.utc),
                    "metadata": {"source": "seed_data"},
                }

                try:
                    interaction_id = await self.firestore_service.create_document(
                        "item_interactions", data=interaction_data
                    )
                    interactions.append(interaction_id)

                except Exception as e:
                    print(f"   ❌ Failed to create interaction: {e}")

        print(f"✅ Created {len(interactions)} interactions")

    async def seed_all(self, clear_existing: bool = True):
        """Seed all data."""
        print("🌱 Starting data seeding...")
        print("=" * 50)

        try:
            if clear_existing:
                await self.clear_data()
                print()

            users = await self.seed_users()
            print()

            items = await self.seed_items()
            print()

            await self.seed_interactions()
            print()

            print("=" * 50)
            print("🎉 Data seeding completed successfully!")
            print(f"   👥 Users: {len(users)}")
            print(f"   📦 Items: {len(items)}")
            print()
            print("Sample accounts:")
            print("   Admin: admin@example.com / AdminPassword123!")
            print("   Moderator: moderator@example.com / ModPassword123!")
            print("   User: john.doe@example.com / UserPassword123!")
            print("   Demo: demo@example.com / DemoPassword123!")

        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            raise


async def main():
    """Main seeding function."""
    # Check if Firebase emulators are running
    try:
        import requests

        response = requests.get("http://localhost:4000", timeout=2)
        if response.status_code != 200:
            raise Exception("Emulator UI not accessible")
    except Exception:
        print("❌ Firebase emulators don't seem to be running")
        print("   Please start them first with:")
        print("   python scripts/firebase.py start")
        print("   OR: uv run firebase-emulator")
        return 1

    # Initialize Firebase
    initialize_firebase()

    # Parse arguments
    clear_existing = "--no-clear" not in sys.argv

    # Create seeder and run
    seeder = DataSeeder()
    await seeder.seed_all(clear_existing=clear_existing)

    return 0


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Data Seeding Script

Usage: python scripts/seed.py [OPTIONS]

OPTIONS:
    --no-clear     Don't clear existing data before seeding
    --help, -h     Show this help message

This script will populate your Firebase emulators with sample data
including users, items, and interactions for development and testing.

Make sure Firebase emulators are running before executing this script.
""")
        sys.exit(0)

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
