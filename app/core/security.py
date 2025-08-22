from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from firebase_admin import auth as firebase_auth
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token and return decoded token."""
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def create_firebase_custom_token(
    uid: str, additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """Create a Firebase custom token."""
    try:
        custom_token = firebase_auth.create_custom_token(uid, additional_claims)
        return custom_token.decode("utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom token: {str(e)}",
        )


async def get_firebase_user(uid: str) -> firebase_auth.UserRecord:
    """Get Firebase user by UID."""
    try:
        user = firebase_auth.get_user(uid)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {str(e)}",
        )


async def create_firebase_user(
    email: str,
    password: Optional[str] = None,
    display_name: Optional[str] = None,
    **kwargs: Any,
) -> firebase_auth.UserRecord:
    """Create a new Firebase user."""
    try:
        user_data = {
            "email": email,
            "email_verified": False,
        }

        if password:
            user_data["password"] = password
        if display_name:
            user_data["display_name"] = display_name

        user_data.update(kwargs)

        user = firebase_auth.create_user(**user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}",
        )


async def update_firebase_user(
    uid: str,
    email: Optional[str] = None,
    password: Optional[str] = None,
    display_name: Optional[str] = None,
    **kwargs: Any,
) -> firebase_auth.UserRecord:
    """Update a Firebase user."""
    try:
        update_data = {}

        if email is not None:
            update_data["email"] = email
        if password is not None:
            update_data["password"] = password
        if display_name is not None:
            update_data["display_name"] = display_name

        update_data.update(kwargs)

        user = firebase_auth.update_user(uid, **update_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update user: {str(e)}",
        )


async def delete_firebase_user(uid: str) -> None:
    """Delete a Firebase user."""
    try:
        firebase_auth.delete_user(uid)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete user: {str(e)}",
        )


async def set_custom_user_claims(uid: str, custom_claims: Dict[str, Any]) -> None:
    """Set custom claims for a Firebase user."""
    try:
        firebase_auth.set_custom_user_claims(uid, custom_claims)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to set custom claims: {str(e)}",
        )
