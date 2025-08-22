from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr, field_validator


class UserRole(BaseModel):
    """User role model."""

    name: str = Field(..., description="Role name")
    permissions: List[str] = Field(default_factory=list, description="Role permissions")
    description: Optional[str] = Field(None, description="Role description")


class UserProfile(BaseModel):
    """Extended user profile information."""

    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    website: Optional[str] = Field(None, description="User website URL")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    company: Optional[str] = Field(None, max_length=100, description="User company")
    job_title: Optional[str] = Field(None, max_length=100, description="User job title")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(default="en", description="Preferred language")
    theme: Optional[str] = Field(default="light", description="UI theme preference")

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(("http://", "https://")):
            return f"https://{v}"
        return v


class UserPreferences(BaseModel):
    """User preferences and settings."""

    notifications_email: bool = Field(
        default=True, description="Email notifications enabled"
    )
    notifications_push: bool = Field(
        default=True, description="Push notifications enabled"
    )
    marketing_emails: bool = Field(
        default=False, description="Marketing emails enabled"
    )
    data_sharing: bool = Field(default=False, description="Data sharing consent")
    analytics: bool = Field(default=True, description="Analytics tracking consent")


class UserBase(BaseModel):
    """Base user model with common fields."""

    email: EmailStr = Field(..., description="User email address")
    display_name: Optional[str] = Field(
        None, max_length=100, description="Display name"
    )
    phone_number: Optional[str] = Field(
        None, description="Phone number with country code"
    )
    photo_url: Optional[str] = Field(None, description="Profile photo URL")

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Display name must be at least 2 characters long")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Basic phone number validation
            v = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not v.startswith("+"):
                raise ValueError(
                    "Phone number must include country code (start with +)"
                )
            if len(v) < 10:
                raise ValueError("Phone number is too short")
        return v


class UserCreate(UserBase):
    """User creation model."""

    password: Optional[str] = Field(None, min_length=8, description="User password")
    email_verified: bool = Field(default=False, description="Email verification status")
    disabled: bool = Field(default=False, description="Account disabled status")
    roles: List[str] = Field(default_factory=list, description="User roles")
    custom_claims: Dict[str, Any] = Field(
        default_factory=dict, description="Custom user claims"
    )
    profile: Optional[UserProfile] = Field(
        default_factory=UserProfile, description="User profile"
    )
    preferences: Optional[UserPreferences] = Field(
        default_factory=UserPreferences, description="User preferences"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not any(c.isupper() for c in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in v):
                raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """User update model."""

    email: Optional[EmailStr] = Field(None, description="User email address")
    display_name: Optional[str] = Field(
        None, max_length=100, description="Display name"
    )
    phone_number: Optional[str] = Field(
        None, description="Phone number with country code"
    )
    photo_url: Optional[str] = Field(None, description="Profile photo URL")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    email_verified: Optional[bool] = Field(
        None, description="Email verification status"
    )
    disabled: Optional[bool] = Field(None, description="Account disabled status")
    roles: Optional[List[str]] = Field(None, description="User roles")
    custom_claims: Optional[Dict[str, Any]] = Field(
        None, description="Custom user claims"
    )
    profile: Optional[UserProfile] = Field(None, description="User profile")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Display name must be at least 2 characters long")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if not v.startswith("+"):
                raise ValueError(
                    "Phone number must include country code (start with +)"
                )
            if len(v) < 10:
                raise ValueError("Phone number is too short")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not any(c.isupper() for c in v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in v):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in v):
                raise ValueError("Password must contain at least one digit")
        return v


class User(UserBase):
    """Full user model with all fields."""

    uid: str = Field(..., description="Firebase user UID")
    email_verified: bool = Field(default=False, description="Email verification status")
    disabled: bool = Field(default=False, description="Account disabled status")
    roles: List[str] = Field(default_factory=list, description="User roles")
    custom_claims: Dict[str, Any] = Field(
        default_factory=dict, description="Custom user claims"
    )
    profile: UserProfile = Field(
        default_factory=UserProfile, description="User profile"
    )
    preferences: UserPreferences = Field(
        default_factory=UserPreferences, description="User preferences"
    )
    provider: str = Field(default="email", description="Authentication provider")
    created_at: Optional[datetime] = Field(
        None, description="Account creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class UserInDB(User):
    """User model as stored in database (includes internal fields)."""

    id: str = Field(..., description="Document ID (same as uid)")

    @classmethod
    def from_firestore_doc(cls, doc_data: Dict[str, Any]) -> "UserInDB":
        """Create UserInDB from Firestore document data."""
        # Handle Firebase Timestamps
        if "created_at" in doc_data and hasattr(doc_data["created_at"], "timestamp"):
            doc_data["created_at"] = datetime.fromtimestamp(
                doc_data["created_at"].timestamp()
            )
        if "updated_at" in doc_data and hasattr(doc_data["updated_at"], "timestamp"):
            doc_data["updated_at"] = datetime.fromtimestamp(
                doc_data["updated_at"].timestamp()
            )
        if "last_login_at" in doc_data and hasattr(
            doc_data["last_login_at"], "timestamp"
        ):
            doc_data["last_login_at"] = datetime.fromtimestamp(
                doc_data["last_login_at"].timestamp()
            )

        # Ensure required fields have defaults
        doc_data.setdefault("profile", {})
        doc_data.setdefault("preferences", {})
        doc_data.setdefault("roles", [])
        doc_data.setdefault("custom_claims", {})

        return cls(**doc_data)


class UserPublic(BaseModel):
    """Public user model (safe for external APIs)."""

    uid: str = Field(..., description="Firebase user UID")
    display_name: Optional[str] = Field(None, description="Display name")
    photo_url: Optional[str] = Field(None, description="Profile photo URL")
    created_at: Optional[datetime] = Field(
        None, description="Account creation timestamp"
    )

    # Public profile fields
    bio: Optional[str] = Field(None, description="User biography")
    website: Optional[str] = Field(None, description="User website URL")
    location: Optional[str] = Field(None, description="User location")
    company: Optional[str] = Field(None, description="User company")
    job_title: Optional[str] = Field(None, description="User job title")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class UserList(BaseModel):
    """User list response model."""

    users: List[User] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=50, description="Items per page")
    has_next: bool = Field(default=False, description="Whether there are more pages")
    next_page_token: Optional[str] = Field(None, description="Token for next page")


class UserStats(BaseModel):
    """User statistics model."""

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    verified_users: int = Field(..., description="Number of verified users")
    new_users_today: int = Field(..., description="New users registered today")
    new_users_week: int = Field(..., description="New users registered this week")
    new_users_month: int = Field(..., description="New users registered this month")
