import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient

# Set test environment before importing app modules
os.environ["ENVIRONMENT"] = "test"

from app.main import app
from app.core.config import settings
from app.services.firebase import initialize_firebase
from app.services.firestore import get_firestore_service


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_firebase():
    """Initialize Firebase for testing."""
    # Ensure Firebase emulator environment variables are set
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = "localhost:9199"
    os.environ["FIREBASE_PROJECT_ID"] = "demo-project"

    # Initialize Firebase with emulator settings
    initialize_firebase()

    yield

    # Cleanup would go here if needed


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def firestore_service():
    """Get Firestore service for testing."""
    return get_firestore_service()


@pytest.fixture
async def clean_firestore():
    """Clean Firestore collections after each test."""
    firestore_service = get_firestore_service()

    # Clean up before test
    await cleanup_collections(firestore_service)

    yield firestore_service

    # Clean up after test
    await cleanup_collections(firestore_service)


async def cleanup_collections(firestore_service):
    """Clean up test collections."""
    collections = ["users", "items", "item_interactions"]

    for collection in collections:
        try:
            # Get all documents in collection
            docs = await firestore_service.query_documents(collection, limit=100)

            # Delete all documents
            for doc in docs:
                await firestore_service.delete_document(collection, doc["id"])

        except Exception as e:
            # Ignore errors during cleanup
            pass


@pytest.fixture
async def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "display_name": "Test User",
        "phone_number": "+1234567890",
    }


@pytest.fixture
async def test_item_data():
    """Sample item data for testing."""
    return {
        "title": "Test Item",
        "description": "This is a test item",
        "category": "general",
        "priority": "medium",
        "status": "draft",
        "tags": ["test", "sample"],
        "is_public": True,
    }


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user_data: dict, clean_firestore):
    """Create authenticated user and return auth headers."""
    # Register user
    register_response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert register_response.status_code == 200
    user = register_response.json()

    # For testing, we'll create a mock token
    # In a real test, you'd use Firebase Auth emulator to get a real token
    from app.core.security import create_access_token

    token = create_access_token(subject=user["uid"])

    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
async def admin_user(client: AsyncClient, clean_firestore):
    """Create an admin user for testing."""
    from app.services.auth import get_auth_service

    auth_service = get_auth_service()

    admin_data = {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "display_name": "Admin User",
        "roles": ["admin"],
        "custom_claims": {"roles": ["admin"]},
    }

    user = await auth_service.create_user(**admin_data)

    # Create access token
    from app.core.security import create_access_token

    token = create_access_token(subject=user["uid"])

    return {
        "user": user,
        "token": token,
        "headers": {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    }


# Mock decorators for testing
class MockFirebaseUser:
    """Mock Firebase user for testing."""

    def __init__(self, uid: str, email: str = None, roles: list = None):
        self.uid = uid
        self.email = email or f"{uid}@example.com"
        self.roles = roles or []
        self.custom_claims = {"roles": self.roles}
        self.email_verified = True
        self.disabled = False


# Test configuration validation
def test_settings():
    """Test that settings are properly configured for testing."""
    assert settings.ENVIRONMENT == "test"
    assert settings.should_use_emulator == True
    assert settings.FIREBASE_PROJECT_ID == "demo-project"


# Pytest markers
pytest_plugins = []


# Custom markers
def pytest_configure(config):
    config.addinivalue_line("markers", "auth: mark test as requiring authentication")
    config.addinivalue_line("markers", "admin: mark test as requiring admin privileges")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line(
        "markers", "firebase: mark test as requiring Firebase emulator"
    )
