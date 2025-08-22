import os
from typing import Dict, Optional

import firebase_admin
from firebase_admin import credentials, initialize_app
from google.cloud.firestore import Client as FirestoreClient

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FirebaseService:
    """Firebase service for managing Firebase Admin SDK initialization."""

    def __init__(self):
        self._app: Optional[firebase_admin.App] = None
        self._firestore_client: Optional[FirestoreClient] = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize Firebase Admin SDK."""
        if self._initialized:
            logger.info("Firebase already initialized")
            return

        try:
            # Set up emulator environment variables if using emulator
            if settings.should_use_emulator:
                self._setup_emulator_environment()
                logger.info(
                    "Using Firebase emulators",
                    emulator_config=settings.firebase_emulator_config,
                )

            # Initialize Firebase app
            if settings.FIREBASE_CREDENTIALS_PATH and os.path.exists(
                settings.FIREBASE_CREDENTIALS_PATH
            ):
                # Use service account credentials
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                self._app = initialize_app(
                    cred,
                    {
                        "projectId": settings.FIREBASE_PROJECT_ID,
                        "databaseURL": settings.FIREBASE_DATABASE_URL,
                    },
                )
                logger.info("Firebase initialized with service account credentials")
            elif settings.should_use_emulator:
                # Use default credentials for emulator
                self._app = initialize_app(
                    options={
                        "projectId": settings.FIREBASE_PROJECT_ID,
                    }
                )
                logger.info("Firebase initialized for emulator")
            else:
                # Use default credentials (for Cloud Run deployment)
                self._app = initialize_app(
                    options={
                        "projectId": settings.FIREBASE_PROJECT_ID,
                        "databaseURL": settings.FIREBASE_DATABASE_URL,
                    }
                )
                logger.info("Firebase initialized with default credentials")

            self._initialized = True
            logger.info(
                "Firebase service initialized successfully",
                project_id=settings.FIREBASE_PROJECT_ID,
            )

        except Exception as e:
            logger.error("Failed to initialize Firebase", error=str(e), exc_info=e)
            raise

    def _setup_emulator_environment(self) -> None:
        """Set up environment variables for Firebase emulators."""
        emulator_config = settings.firebase_emulator_config

        # Set environment variables for emulators
        for key, value in emulator_config.items():
            if value:
                env_key = key.upper().replace("_HOST", "_EMULATOR_HOST")
                os.environ[env_key] = value
                logger.debug(
                    "Set emulator environment variable", key=env_key, value=value
                )

    @property
    def app(self) -> firebase_admin.App:
        """Get the Firebase app instance."""
        if not self._initialized:
            self.initialize()
        return self._app

    @property
    def is_initialized(self) -> bool:
        """Check if Firebase is initialized."""
        return self._initialized

    def health_check(self) -> Dict[str, str]:
        """Perform Firebase health check."""
        try:
            if not self._initialized:
                return {"status": "error", "message": "Firebase not initialized"}

            # Try to access Firebase services
            from firebase_admin import firestore

            db = firestore.client(app=self._app)

            # Simple read operation to test connectivity
            # This will work with both emulator and production
            health_doc = db.collection("health").document("check")
            health_doc.get()  # This will create connection

            return {
                "status": "healthy",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "using_emulator": str(settings.should_use_emulator),
            }
        except Exception as e:
            logger.error("Firebase health check failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}


# Global Firebase service instance
firebase_service = FirebaseService()


def get_firebase_app() -> firebase_admin.App:
    """Get the Firebase app instance."""
    return firebase_service.app


def initialize_firebase() -> None:
    """Initialize Firebase service."""
    firebase_service.initialize()


def get_firebase_health() -> Dict[str, str]:
    """Get Firebase health status."""
    return firebase_service.health_check()
