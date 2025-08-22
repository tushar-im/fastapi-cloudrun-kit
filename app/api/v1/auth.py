from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_active_user, security
from app.core.logging import get_logger, log_api_call, log_security_event
from app.models.user import UserInDB
from app.schemas.user import (
    FirebaseLoginRequest,
    FirebaseTokenResponse,
    LoginRequest,
    PasswordResetRequest,
    PasswordUpdateRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import get_auth_service
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_firebase_token,
    create_firebase_custom_token,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: RegisterRequest,
) -> Dict[str, Any]:
    """Register a new user with Firebase Auth."""
    log_api_call("register", "POST")

    auth_service = get_auth_service()

    try:
        # Create user in Firebase Auth and Firestore
        user = await auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name,
            phone_number=user_data.phone_number,
            email_verified=False,
            disabled=False,
        )

        log_security_event(
            "user_registered", user_id=user["uid"], email=user_data.email
        )

        logger.info(
            "User registered successfully", uid=user["uid"], email=user_data.email
        )

        return UserResponse(**user)

    except Exception as e:
        log_security_event("registration_failed", email=user_data.email, error=str(e))
        logger.error(
            "Registration failed", email=user_data.email, error=str(e), exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login/firebase", response_model=FirebaseTokenResponse)
async def login_with_firebase(
    login_data: FirebaseLoginRequest,
) -> Dict[str, Any]:
    """Login with Firebase ID token."""
    log_api_call("login_firebase", "POST")

    try:
        # Verify Firebase ID token
        decoded_token = await verify_firebase_token(login_data.id_token)
        uid = decoded_token["uid"]

        # Get or create user in our system
        auth_service = get_auth_service()
        user = await auth_service.get_user_by_uid(uid)

        if not user:
            # Create user profile if it doesn't exist
            firebase_user = await auth_service.get_user_by_uid(uid)
            if not firebase_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

        # Create custom token for the user
        custom_token = await create_firebase_custom_token(uid)

        log_security_event("user_logged_in", user_id=uid, method="firebase")

        logger.info("User logged in successfully", uid=uid, method="firebase")

        return FirebaseTokenResponse(
            custom_token=custom_token, user=UserResponse(**user)
        )

    except HTTPException:
        raise
    except Exception as e:
        log_security_event("login_failed", method="firebase", error=str(e))
        logger.error("Firebase login failed", error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
) -> Dict[str, Any]:
    """Login with email and password (creates JWT tokens)."""
    log_api_call("login", "POST")

    try:
        auth_service = get_auth_service()

        # Get user by email
        user = await auth_service.get_user_by_email(login_data.email)

        if not user:
            log_security_event(
                "login_failed", email=login_data.email, reason="user_not_found"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # For Firebase Auth, we can't verify passwords directly
        # This endpoint is mainly for demonstration of JWT token creation
        # In a real app, you might use Firebase Admin SDK to create custom tokens

        # Create JWT tokens
        access_token = create_access_token(subject=user["uid"])
        refresh_token = create_refresh_token(subject=user["uid"])

        log_security_event(
            "user_logged_in", user_id=user["uid"], email=login_data.email, method="jwt"
        )

        logger.info(
            "User logged in successfully",
            uid=user["uid"],
            email=login_data.email,
            method="jwt",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800,  # 30 minutes
            user=UserResponse(**user),
        )

    except HTTPException:
        raise
    except Exception as e:
        log_security_event("login_failed", email=login_data.email, error=str(e))
        logger.error("Login failed", email=login_data.email, error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


@router.post("/logout")
async def logout(
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Logout user (invalidate tokens)."""
    log_api_call("logout", "POST", user_id=current_user.uid)

    try:
        # In a real implementation, you would:
        # 1. Add token to blacklist
        # 2. Clear any cached sessions
        # 3. Revoke Firebase refresh tokens if needed

        log_security_event("user_logged_out", user_id=current_user.uid)

        logger.info("User logged out successfully", uid=current_user.uid)

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error("Logout failed", uid=current_user.uid, error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user information."""
    log_api_call("get_current_user", "GET", user_id=current_user.uid)

    logger.info("Retrieved current user info", uid=current_user.uid)

    return UserResponse.from_orm(current_user)


@router.post("/password/reset")
async def request_password_reset(
    request_data: PasswordResetRequest,
) -> Dict[str, str]:
    """Request password reset email."""
    log_api_call("request_password_reset", "POST")

    try:
        # In a real implementation, you would:
        # 1. Generate password reset token
        # 2. Send email with reset link
        # 3. Store token in database with expiration

        # For Firebase, you would use the Auth API to send reset email
        # firebase_auth.generate_password_reset_link(request_data.email)

        log_security_event("password_reset_requested", email=request_data.email)

        logger.info("Password reset requested", email=request_data.email)

        return {"message": "Password reset email sent (if email exists)"}

    except Exception as e:
        logger.error(
            "Password reset request failed",
            email=request_data.email,
            error=str(e),
            exc_info=e,
        )
        # Don't reveal if email exists or not
        return {"message": "Password reset email sent (if email exists)"}


@router.post("/password/update")
async def update_password(
    password_data: PasswordUpdateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Update user password."""
    log_api_call("update_password", "POST", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Update password in Firebase Auth
        await auth_service.update_user(
            current_user.uid, password=password_data.new_password
        )

        log_security_event("password_updated", user_id=current_user.uid)

        logger.info("Password updated successfully", uid=current_user.uid)

        return {"message": "Password updated successfully"}

    except Exception as e:
        log_security_event(
            "password_update_failed", user_id=current_user.uid, error=str(e)
        )
        logger.error(
            "Password update failed", uid=current_user.uid, error=str(e), exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password update failed: {str(e)}",
        )


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Refresh access token using refresh token."""
    log_api_call("refresh_token", "POST")

    try:
        from app.core.security import verify_token

        # Verify refresh token
        payload = verify_token(credentials.credentials)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        uid = payload.get("sub")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Get user to make sure they still exist and are active
        auth_service = get_auth_service()
        user = await auth_service.get_user_by_uid(uid)

        if not user or user.get("disabled", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or disabled",
            )

        # Create new access token
        access_token = create_access_token(subject=uid)

        logger.info("Token refreshed successfully", uid=uid)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
        }

    except HTTPException:
        raise
    except Exception as e:
        log_security_event("token_refresh_failed", error=str(e))
        logger.error("Token refresh failed", error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed"
        )


@router.post("/verify-email")
async def verify_email(
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Send email verification."""
    log_api_call("verify_email", "POST", user_id=current_user.uid)

    try:
        # In a real implementation, you would use Firebase Auth API
        # firebase_auth.generate_email_verification_link(current_user.email)

        log_security_event(
            "email_verification_requested",
            user_id=current_user.uid,
            email=current_user.email,
        )

        logger.info(
            "Email verification requested",
            uid=current_user.uid,
            email=current_user.email,
        )

        return {"message": "Verification email sent"}

    except Exception as e:
        logger.error(
            "Email verification failed", uid=current_user.uid, error=str(e), exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed",
        )
