from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr

from app.models.user import (
    UserProfile,
    UserPreferences,
)
from app.models.item import (
    ItemStatus,
    ItemCategory,
    ItemPriority,
)


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: "UserResponse" = Field(..., description="User information")


class FirebaseTokenResponse(BaseModel):
    """Firebase token response model."""

    custom_token: str = Field(..., description="Firebase custom token")
    token_type: str = Field(default="firebase", description="Token type")
    user: "UserResponse" = Field(..., description="User information")


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    remember_me: bool = Field(default=False, description="Remember user login")


class FirebaseLoginRequest(BaseModel):
    """Firebase login request model."""

    id_token: str = Field(..., description="Firebase ID token")


class RegisterRequest(BaseModel):
    """User registration request model."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    display_name: Optional[str] = Field(None, description="Display name")
    phone_number: Optional[str] = Field(None, description="Phone number")


class PasswordResetRequest(BaseModel):
    """Password reset request model."""

    email: EmailStr = Field(..., description="User email")


class PasswordUpdateRequest(BaseModel):
    """Password update request model."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class EmailUpdateRequest(BaseModel):
    """Email update request model."""

    new_email: EmailStr = Field(..., description="New email address")
    password: str = Field(..., description="Current password for verification")


class UserResponse(BaseModel):
    """User response model."""

    uid: str = Field(..., description="Firebase user UID")
    email: EmailStr = Field(..., description="User email")
    display_name: Optional[str] = Field(None, description="Display name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    photo_url: Optional[str] = Field(None, description="Profile photo URL")
    email_verified: bool = Field(..., description="Email verification status")
    disabled: bool = Field(..., description="Account disabled status")
    roles: List[str] = Field(..., description="User roles")
    profile: UserProfile = Field(..., description="User profile")
    preferences: UserPreferences = Field(..., description="User preferences")
    provider: str = Field(..., description="Authentication provider")
    created_at: Optional[datetime] = Field(
        None, description="Account creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class UserListResponse(BaseModel):
    """User list response model."""

    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=50, description="Items per page")
    has_next: bool = Field(default=False, description="Whether there are more pages")


class UserCreateRequest(BaseModel):
    """User creation request model (admin only)."""

    email: EmailStr = Field(..., description="User email")
    password: Optional[str] = Field(None, min_length=8, description="User password")
    display_name: Optional[str] = Field(None, description="Display name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    photo_url: Optional[str] = Field(None, description="Profile photo URL")
    email_verified: bool = Field(default=False, description="Email verification status")
    disabled: bool = Field(default=False, description="Account disabled status")
    roles: List[str] = Field(default_factory=list, description="User roles")
    custom_claims: Dict[str, Any] = Field(
        default_factory=dict, description="Custom claims"
    )
    profile: Optional[UserProfile] = Field(
        default_factory=UserProfile, description="User profile"
    )
    preferences: Optional[UserPreferences] = Field(
        default_factory=UserPreferences, description="User preferences"
    )


class UserUpdateRequest(BaseModel):
    """User update request model."""

    display_name: Optional[str] = Field(None, description="Display name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    photo_url: Optional[str] = Field(None, description="Profile photo URL")
    profile: Optional[UserProfile] = Field(None, description="User profile")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")


class AdminUserUpdateRequest(BaseModel):
    """Admin user update request model."""

    email: Optional[EmailStr] = Field(None, description="User email")
    display_name: Optional[str] = Field(None, description="Display name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    photo_url: Optional[str] = Field(None, description="Profile photo URL")
    email_verified: Optional[bool] = Field(
        None, description="Email verification status"
    )
    disabled: Optional[bool] = Field(None, description="Account disabled status")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    roles: Optional[List[str]] = Field(None, description="User roles")
    custom_claims: Optional[Dict[str, Any]] = Field(None, description="Custom claims")
    profile: Optional[UserProfile] = Field(None, description="User profile")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences")


class UserStatsResponse(BaseModel):
    """User statistics response model."""

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    verified_users: int = Field(..., description="Number of verified users")
    disabled_users: int = Field(..., description="Number of disabled users")
    new_users_today: int = Field(..., description="New users registered today")
    new_users_week: int = Field(..., description="New users registered this week")
    new_users_month: int = Field(..., description="New users registered this month")
    users_by_provider: Dict[str, int] = Field(
        ..., description="Users grouped by provider"
    )


class UserSearchRequest(BaseModel):
    """User search request model."""

    query: Optional[str] = Field(None, description="Search query")
    email: Optional[str] = Field(None, description="Filter by email")
    display_name: Optional[str] = Field(None, description="Filter by display name")
    roles: Optional[List[str]] = Field(None, description="Filter by roles")
    email_verified: Optional[bool] = Field(
        None, description="Filter by email verification"
    )
    disabled: Optional[bool] = Field(None, description="Filter by disabled status")
    provider: Optional[str] = Field(None, description="Filter by auth provider")
    created_after: Optional[datetime] = Field(
        None, description="Filter users created after"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter users created before"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


class RoleAssignmentRequest(BaseModel):
    """Role assignment request model."""

    user_uid: str = Field(..., description="User UID")
    roles: List[str] = Field(..., description="Roles to assign")


class CustomClaimsUpdateRequest(BaseModel):
    """Custom claims update request model."""

    user_uid: str = Field(..., description="User UID")
    custom_claims: Dict[str, Any] = Field(..., description="Custom claims to set")


class BulkUserActionRequest(BaseModel):
    """Bulk user action request model."""

    user_uids: List[str] = Field(..., min_items=1, description="List of user UIDs")
    action: str = Field(
        ..., description="Action to perform: enable, disable, delete, verify_email"
    )

    class Config:
        schema_extra = {
            "example": {"user_uids": ["uid1", "uid2", "uid3"], "action": "disable"}
        }


class ProfileUpdateRequest(BaseModel):
    """Profile update request model."""

    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    website: Optional[str] = Field(None, description="User website URL")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    company: Optional[str] = Field(None, max_length=100, description="User company")
    job_title: Optional[str] = Field(None, max_length=100, description="User job title")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, description="Preferred language")
    theme: Optional[str] = Field(None, description="UI theme preference")


class PreferencesUpdateRequest(BaseModel):
    """Preferences update request model."""

    notifications_email: Optional[bool] = Field(None, description="Email notifications")
    notifications_push: Optional[bool] = Field(None, description="Push notifications")
    marketing_emails: Optional[bool] = Field(None, description="Marketing emails")
    data_sharing: Optional[bool] = Field(None, description="Data sharing consent")
    analytics: Optional[bool] = Field(None, description="Analytics tracking consent")


class UserActivityResponse(BaseModel):
    """User activity response model."""

    uid: str = Field(..., description="User UID")
    total_items: int = Field(..., description="Total items created")
    items_by_status: Dict[str, int] = Field(..., description="Items by status")
    items_by_category: Dict[str, int] = Field(..., description="Items by category")
    recent_activity: List[Dict[str, Any]] = Field(..., description="Recent activity")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


# Update forward references
TokenResponse.model_rebuild()
FirebaseTokenResponse.model_rebuild()
