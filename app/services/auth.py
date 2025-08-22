from typing import Dict, List, Optional

from firebase_admin import auth as firebase_auth
from fastapi import HTTPException, status

from app.core.logging import get_logger, log_firebase_operation, log_security_event
from app.services.firestore import get_firestore_service

logger = get_logger(__name__)


class AuthService:
    """Service for Firebase Authentication operations."""

    def __init__(self):
        self.firestore = get_firestore_service()
        self.users_collection = "users"

    async def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        photo_url: Optional[str] = None,
        email_verified: bool = False,
        disabled: bool = False,
        custom_claims: Optional[Dict] = None,
    ) -> Dict:
        """Create a new user in Firebase Auth and Firestore."""
        try:
            # Prepare user data for Firebase Auth
            auth_data = {
                "email": email,
                "email_verified": email_verified,
                "disabled": disabled,
            }

            if password:
                auth_data["password"] = password
            if display_name:
                auth_data["display_name"] = display_name
            if phone_number:
                auth_data["phone_number"] = phone_number
            if photo_url:
                auth_data["photo_url"] = photo_url

            # Create user in Firebase Auth
            firebase_user = firebase_auth.create_user(**auth_data)

            # Set custom claims if provided
            if custom_claims:
                firebase_auth.set_custom_user_claims(firebase_user.uid, custom_claims)

            # Create user profile in Firestore
            user_profile = {
                "uid": firebase_user.uid,
                "email": email,
                "display_name": display_name,
                "phone_number": phone_number,
                "photo_url": photo_url,
                "email_verified": email_verified,
                "disabled": disabled,
                "custom_claims": custom_claims or {},
                "provider": "email",
            }

            await self.firestore.create_document(
                self.users_collection, firebase_user.uid, user_profile
            )

            log_firebase_operation(
                "create_user",
                uid=firebase_user.uid,
                email=email,
                has_custom_claims=bool(custom_claims),
            )

            log_security_event("user_created", user_id=firebase_user.uid, email=email)

            return {
                "uid": firebase_user.uid,
                "email": firebase_user.email,
                "display_name": firebase_user.display_name,
                "email_verified": firebase_user.email_verified,
                "disabled": firebase_user.disabled,
                "custom_claims": custom_claims or {},
            }

        except Exception as e:
            logger.error("Failed to create user", email=email, error=str(e), exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user: {str(e)}",
            )

    async def get_user_by_uid(self, uid: str) -> Optional[Dict]:
        """Get user by UID from Firebase Auth and Firestore."""
        try:
            # Get user from Firebase Auth
            firebase_user = firebase_auth.get_user(uid)

            # Get user profile from Firestore
            user_profile = await self.firestore.get_document(self.users_collection, uid)

            if not user_profile:
                # Create user profile in Firestore if it doesn't exist
                user_profile = {
                    "uid": firebase_user.uid,
                    "email": firebase_user.email,
                    "display_name": firebase_user.display_name,
                    "phone_number": firebase_user.phone_number,
                    "photo_url": firebase_user.photo_url,
                    "email_verified": firebase_user.email_verified,
                    "disabled": firebase_user.disabled,
                    "custom_claims": firebase_user.custom_claims or {},
                    "provider": "unknown",
                }

                await self.firestore.create_document(
                    self.users_collection, uid, user_profile
                )

            # Merge Firebase Auth data with Firestore profile
            user_data = {
                **user_profile,
                "uid": firebase_user.uid,
                "email": firebase_user.email,
                "display_name": firebase_user.display_name,
                "phone_number": firebase_user.phone_number,
                "photo_url": firebase_user.photo_url,
                "email_verified": firebase_user.email_verified,
                "disabled": firebase_user.disabled,
                "custom_claims": firebase_user.custom_claims or {},
            }

            log_firebase_operation("get_user_by_uid", uid=uid, found=True)

            return user_data

        except firebase_auth.UserNotFoundError:
            log_firebase_operation("get_user_by_uid", uid=uid, found=False)
            return None
        except Exception as e:
            logger.error("Failed to get user by UID", uid=uid, error=str(e), exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}",
            )

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email from Firebase Auth."""
        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            return await self.get_user_by_uid(firebase_user.uid)

        except firebase_auth.UserNotFoundError:
            log_firebase_operation("get_user_by_email", email=email, found=False)
            return None
        except Exception as e:
            logger.error(
                "Failed to get user by email", email=email, error=str(e), exc_info=e
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}",
            )

    async def update_user(
        self,
        uid: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        photo_url: Optional[str] = None,
        email_verified: Optional[bool] = None,
        disabled: Optional[bool] = None,
        custom_claims: Optional[Dict] = None,
        profile_data: Optional[Dict] = None,
    ) -> Dict:
        """Update user in Firebase Auth and Firestore."""
        try:
            # Prepare update data for Firebase Auth
            auth_update_data = {}

            if email is not None:
                auth_update_data["email"] = email
            if password is not None:
                auth_update_data["password"] = password
            if display_name is not None:
                auth_update_data["display_name"] = display_name
            if phone_number is not None:
                auth_update_data["phone_number"] = phone_number
            if photo_url is not None:
                auth_update_data["photo_url"] = photo_url
            if email_verified is not None:
                auth_update_data["email_verified"] = email_verified
            if disabled is not None:
                auth_update_data["disabled"] = disabled

            # Update user in Firebase Auth
            if auth_update_data:
                firebase_auth.update_user(uid, **auth_update_data)

            # Update custom claims if provided
            if custom_claims is not None:
                firebase_auth.set_custom_user_claims(uid, custom_claims)

            # Update user profile in Firestore
            firestore_update_data = {}

            if email is not None:
                firestore_update_data["email"] = email
            if display_name is not None:
                firestore_update_data["display_name"] = display_name
            if phone_number is not None:
                firestore_update_data["phone_number"] = phone_number
            if photo_url is not None:
                firestore_update_data["photo_url"] = photo_url
            if email_verified is not None:
                firestore_update_data["email_verified"] = email_verified
            if disabled is not None:
                firestore_update_data["disabled"] = disabled
            if custom_claims is not None:
                firestore_update_data["custom_claims"] = custom_claims

            # Add additional profile data
            if profile_data:
                firestore_update_data.update(profile_data)

            if firestore_update_data:
                await self.firestore.update_document(
                    self.users_collection, uid, firestore_update_data
                )

            log_firebase_operation(
                "update_user",
                uid=uid,
                auth_fields_updated=list(auth_update_data.keys()),
                profile_fields_updated=list(firestore_update_data.keys()),
            )

            log_security_event(
                "user_updated",
                user_id=uid,
                fields_updated=list(auth_update_data.keys())
                + list(firestore_update_data.keys()),
            )

            # Return updated user data
            return await self.get_user_by_uid(uid)

        except Exception as e:
            logger.error("Failed to update user", uid=uid, error=str(e), exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update user: {str(e)}",
            )

    async def delete_user(self, uid: str) -> bool:
        """Delete user from Firebase Auth and Firestore."""
        try:
            # Delete user from Firebase Auth
            firebase_auth.delete_user(uid)

            # Delete user profile from Firestore
            await self.firestore.delete_document(self.users_collection, uid)

            log_firebase_operation("delete_user", uid=uid)

            log_security_event("user_deleted", user_id=uid)

            return True

        except Exception as e:
            logger.error("Failed to delete user", uid=uid, error=str(e), exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete user: {str(e)}",
            )

    async def verify_id_token(self, token: str) -> Dict:
        """Verify Firebase ID token."""
        try:
            decoded_token = firebase_auth.verify_id_token(token)

            log_firebase_operation(
                "verify_id_token", uid=decoded_token["uid"], success=True
            )

            return decoded_token

        except Exception as e:
            logger.error("Failed to verify ID token", error=str(e), exc_info=e)

            log_security_event("invalid_token", error=str(e))

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def create_custom_token(
        self, uid: str, additional_claims: Optional[Dict] = None
    ) -> str:
        """Create Firebase custom token."""
        try:
            custom_token = firebase_auth.create_custom_token(uid, additional_claims)

            log_firebase_operation(
                "create_custom_token",
                uid=uid,
                has_additional_claims=bool(additional_claims),
            )

            return custom_token.decode("utf-8")

        except Exception as e:
            logger.error(
                "Failed to create custom token", uid=uid, error=str(e), exc_info=e
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create custom token: {str(e)}",
            )

    async def list_users(
        self, page_token: Optional[str] = None, max_results: int = 1000
    ) -> Dict:
        """List users from Firebase Auth."""
        try:
            page = firebase_auth.list_users(page_token, max_results)

            users = []
            for user in page.users:
                users.append(
                    {
                        "uid": user.uid,
                        "email": user.email,
                        "display_name": user.display_name,
                        "phone_number": user.phone_number,
                        "photo_url": user.photo_url,
                        "email_verified": user.email_verified,
                        "disabled": user.disabled,
                        "custom_claims": user.custom_claims or {},
                    }
                )

            log_firebase_operation(
                "list_users", count=len(users), has_next_page=bool(page.next_page_token)
            )

            return {
                "users": users,
                "next_page_token": page.next_page_token,
            }

        except Exception as e:
            logger.error("Failed to list users", error=str(e), exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list users: {str(e)}",
            )


# Global auth service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get the auth service instance."""
    return auth_service
