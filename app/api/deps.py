from typing import Any, Dict, Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from app.core.logging import get_logger, log_security_event
from app.models.user import User, UserInDB
from app.services.auth import get_auth_service
from app.services.firebase import get_firebase_app
from app.services.firestore import get_firestore_service

logger = get_logger(__name__)

# Security scheme for Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInDB:
    """Get current authenticated user from Firebase token."""
    try:
        # Verify Firebase ID token
        token = credentials.credentials
        decoded_token = firebase_auth.verify_id_token(token, app=get_firebase_app())

        # Get user from auth service
        auth_service = get_auth_service()
        user_data = await auth_service.get_user_by_uid(decoded_token["uid"])

        if not user_data:
            log_security_event("user_not_found", user_id=decoded_token["uid"])
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if user_data.get("disabled", False):
            log_security_event(
                "disabled_user_access_attempt", user_id=decoded_token["uid"]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
            )

        # Update last login time
        firestore_service = get_firestore_service()
        await firestore_service.update_document(
            "users",
            decoded_token["uid"],
            {"last_login_at": firestore_service.client.SERVER_TIMESTAMP},
        )

        return UserInDB.from_firestore_doc(user_data)

    except firebase_auth.InvalidIdTokenError:
        log_security_event("invalid_token", error="Invalid ID token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth.ExpiredIdTokenError:
        log_security_event("expired_token", error="Expired ID token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth.RevokedIdTokenError:
        log_security_event("revoked_token", error="Revoked ID token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Authentication error", error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Get current active user (not disabled)."""
    if current_user.disabled:
        log_security_event("disabled_user_access_attempt", user_id=current_user.uid)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )
    return current_user


async def get_current_verified_user(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """Get current verified user (email verified)."""
    if not current_user.email_verified:
        log_security_event("unverified_user_access_attempt", user_id=current_user.uid)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required"
        )
    return current_user


def require_roles(*required_roles: str):
    """Dependency factory for role-based access control."""

    def role_checker(
        current_user: UserInDB = Depends(get_current_active_user),
    ) -> UserInDB:
        if not any(role in current_user.roles for role in required_roles):
            log_security_event(
                "insufficient_permissions",
                user_id=current_user.uid,
                required_roles=list(required_roles),
                user_roles=current_user.roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}",
            )
        return current_user

    return role_checker


def require_admin():
    """Dependency for admin access."""
    return require_roles("admin")


def require_moderator():
    """Dependency for moderator access."""
    return require_roles("admin", "moderator")


def require_custom_claim(claim_name: str, claim_value: Any = True):
    """Dependency factory for custom claim-based access control."""

    def claim_checker(
        current_user: UserInDB = Depends(get_current_active_user),
    ) -> UserInDB:
        user_claims = current_user.custom_claims or {}

        if claim_name not in user_claims:
            log_security_event(
                "missing_custom_claim",
                user_id=current_user.uid,
                required_claim=claim_name,
                required_value=claim_value,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required claim: {claim_name}",
            )

        if user_claims[claim_name] != claim_value:
            log_security_event(
                "invalid_custom_claim",
                user_id=current_user.uid,
                required_claim=claim_name,
                required_value=claim_value,
                actual_value=user_claims[claim_name],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid claim value for: {claim_name}",
            )

        return current_user

    return claim_checker


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[UserInDB]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None

    try:
        # Create a new HTTPAuthorizationCredentials to pass to get_current_user
        required_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=credentials.credentials
        )

        # Mock the dependency to avoid circular issues
        async def mock_security():
            return required_credentials

        # Get the current user
        user = await get_current_user(required_credentials)
        return user

    except HTTPException:
        # If authentication fails, return None (don't raise exception)
        return None
    except Exception as e:
        logger.warning("Optional authentication failed", error=str(e))
        return None


def get_pagination_params(page: int = 1, per_page: int = 20, max_per_page: int = 100):
    """Get pagination parameters with validation."""
    if page < 1:
        page = 1

    if per_page < 1:
        per_page = 20
    elif per_page > max_per_page:
        per_page = max_per_page

    return {"page": page, "per_page": per_page}


def get_search_params(
    query: Optional[str] = None, sort_by: str = "created_at", sort_order: str = "desc"
):
    """Get search parameters with validation."""
    if sort_order not in ["asc", "desc"]:
        sort_order = "desc"

    return {
        "query": query.strip() if query else None,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }


class DatabaseSession:
    """Database session context manager."""

    def __init__(self):
        self.firestore_service = get_firestore_service()

    def __enter__(self):
        return self.firestore_service

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass


def get_database() -> Generator[DatabaseSession, None, None]:
    """Get database session."""
    session = DatabaseSession()
    try:
        yield session
    finally:
        # Cleanup
        pass


def validate_resource_access(
    resource_owner_uid: str,
    current_user: UserInDB,
    allow_admin: bool = True,
    allow_moderator: bool = False,
) -> bool:
    """Validate if user can access a resource."""
    # Owner can always access
    if resource_owner_uid == current_user.uid:
        return True

    # Admin can access if allowed
    if allow_admin and "admin" in current_user.roles:
        return True

    # Moderator can access if allowed
    if allow_moderator and "moderator" in current_user.roles:
        return True

    return False


def require_resource_access(
    resource_owner_uid: str, allow_admin: bool = True, allow_moderator: bool = False
):
    """Dependency factory for resource access control."""

    def access_checker(current_user: UserInDB = Depends(get_current_active_user)):
        if not validate_resource_access(
            resource_owner_uid, current_user, allow_admin, allow_moderator
        ):
            log_security_event(
                "unauthorized_resource_access",
                user_id=current_user.uid,
                resource_owner=resource_owner_uid,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource",
            )
        return current_user

    return access_checker


def rate_limit_key(
    current_user: Optional[UserInDB] = Depends(get_optional_current_user),
) -> str:
    """Generate rate limit key based on user or IP."""
    if current_user:
        return f"user:{current_user.uid}"

    # In a real implementation, you would get the IP from request
    # For now, return a default key
    return "anonymous"


async def check_feature_flag(
    feature_name: str,
    current_user: Optional[UserInDB] = Depends(get_optional_current_user),
) -> bool:
    """Check if a feature flag is enabled for the user."""
    # In a real implementation, you would check against a feature flag service
    # For now, return True for all features

    # You could implement different logic based on user roles, custom claims, etc.
    if current_user and "beta_tester" in current_user.roles:
        return True

    # Check custom claims for feature flags
    if current_user and current_user.custom_claims:
        feature_flags = current_user.custom_claims.get("feature_flags", {})
        return feature_flags.get(feature_name, False)

    return False


def require_feature_flag(feature_name: str):
    """Dependency factory for feature flag-based access control."""

    async def feature_checker(
        current_user: UserInDB = Depends(get_current_active_user),
    ) -> UserInDB:
        enabled = await check_feature_flag(feature_name, current_user)

        if not enabled:
            log_security_event(
                "feature_flag_denied", user_id=current_user.uid, feature=feature_name
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_name}' is not available",
            )

        return current_user

    return feature_checker
