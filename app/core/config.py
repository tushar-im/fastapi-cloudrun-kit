import os
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Settings
    APP_NAME: str = "FastAPI CloudRun Kit"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # CORS Settings
    BACKEND_CORS_ORIGINS: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
        ],
        description="List of allowed origins for CORS",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v or v.strip() == "":
                return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"]
            # Handle JSON array format
            if v.strip().startswith("["):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated format
            return [i.strip() for i in v.split(",") if i.strip()]
        return ["http://localhost:3000", "http://localhost:8000", "http://localhost:8080"]

    # Firebase Settings
    FIREBASE_PROJECT_ID: str = Field(description="Firebase project ID")
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(
        default=None, description="Path to Firebase service account JSON file"
    )
    FIREBASE_DATABASE_URL: Optional[str] = Field(
        default=None, description="Firebase Realtime Database URL"
    )

    # Firebase Emulator Settings
    USE_FIREBASE_EMULATOR: bool = Field(
        default=False, description="Whether to use Firebase emulator"
    )
    FIREBASE_AUTH_EMULATOR_HOST: Optional[str] = Field(
        default=None, description="Firebase Auth emulator host (e.g., localhost:9099)"
    )
    FIRESTORE_EMULATOR_HOST: Optional[str] = Field(
        default=None, description="Firestore emulator host (e.g., localhost:8080)"
    )
    FIREBASE_STORAGE_EMULATOR_HOST: Optional[str] = Field(
        default=None,
        description="Firebase Storage emulator host (e.g., localhost:9199)",
    )

    # Google Cloud Settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(
        default=None, description="Google Cloud project ID"
    )
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(
        default=None, description="Path to Google Cloud service account JSON file"
    )

    # Security Settings
    SECRET_KEY: str = Field(
        description="Secret key for JWT tokens and other cryptographic operations"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expiration time in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration time in days"
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100, description="Number of requests allowed per minute"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or console")

    # Health Check Settings
    HEALTH_CHECK_INTERVAL: int = Field(
        default=30, description="Health check interval in seconds"
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() == "test"

    @property
    def firebase_emulator_config(self) -> Dict[str, Any]:
        """Get Firebase emulator configuration."""
        config = {}

        if self.FIREBASE_AUTH_EMULATOR_HOST:
            os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = self.FIREBASE_AUTH_EMULATOR_HOST
            config["auth_emulator_host"] = self.FIREBASE_AUTH_EMULATOR_HOST

        if self.FIRESTORE_EMULATOR_HOST:
            os.environ["FIRESTORE_EMULATOR_HOST"] = self.FIRESTORE_EMULATOR_HOST
            config["firestore_emulator_host"] = self.FIRESTORE_EMULATOR_HOST

        if self.FIREBASE_STORAGE_EMULATOR_HOST:
            os.environ["FIREBASE_STORAGE_EMULATOR_HOST"] = (
                self.FIREBASE_STORAGE_EMULATOR_HOST
            )
            config["storage_emulator_host"] = self.FIREBASE_STORAGE_EMULATOR_HOST

        return config

    @property
    def should_use_emulator(self) -> bool:
        """Determine if we should use Firebase emulator based on environment."""
        # Auto-detect emulator usage if not explicitly set
        if self.USE_FIREBASE_EMULATOR is not None:
            return self.USE_FIREBASE_EMULATOR

        # Use emulator in development and testing environments
        # or if emulator hosts are configured
        return (
            self.is_development
            or self.is_testing
            or bool(self.FIREBASE_AUTH_EMULATOR_HOST)
            or bool(self.FIRESTORE_EMULATOR_HOST)
        )

    def model_dump_env(self) -> Dict[str, str]:
        """Export settings as environment variables."""
        env_vars = {}
        for field_name, field_value in self.model_dump().items():
            if field_value is not None:
                if isinstance(field_value, list):
                    env_vars[field_name] = ",".join(str(v) for v in field_value)
                else:
                    env_vars[field_name] = str(field_value)
        return env_vars


# Global settings instance
settings = Settings()