from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    get_current_active_user,
    get_pagination_params,
    get_search_params,
    require_admin,
    require_moderator,
    validate_resource_access,
)
from app.core.logging import get_logger, log_api_call, log_security_event
from app.models.user import UserInDB
from app.schemas.user import (
    AdminUserUpdateRequest,
    BulkUserActionRequest,
    CustomClaimsUpdateRequest,
    PreferencesUpdateRequest,
    ProfileUpdateRequest,
    RoleAssignmentRequest,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserSearchRequest,
    UserStatsResponse,
    UserUpdateRequest,
    UserActivityResponse,
)
from app.services.auth import get_auth_service
from app.services.firestore import get_firestore_service
from app.utils.helpers import generate_pagination_info

router = APIRouter()
logger = get_logger(__name__)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user's profile."""
    log_api_call("get_my_profile", "GET", user_id=current_user.uid)

    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserResponse:
    """Update current user's profile."""
    log_api_call("update_my_profile", "PUT", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Prepare update data
        update_data = {}
        profile_data = {}

        if user_update.display_name is not None:
            update_data["display_name"] = user_update.display_name
        if user_update.phone_number is not None:
            update_data["phone_number"] = user_update.phone_number
        if user_update.photo_url is not None:
            update_data["photo_url"] = user_update.photo_url

        if user_update.profile is not None:
            profile_data["profile"] = user_update.profile.dict()
        if user_update.preferences is not None:
            profile_data["preferences"] = user_update.preferences.dict()

        # Update user
        updated_user = await auth_service.update_user(
            current_user.uid, profile_data=profile_data, **update_data
        )

        logger.info(
            "User profile updated",
            uid=current_user.uid,
            fields_updated=list(update_data.keys()) + list(profile_data.keys()),
        )

        return UserResponse(**updated_user)

    except Exception as e:
        logger.error(
            "Profile update failed", uid=current_user.uid, error=str(e), exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile update failed: {str(e)}",
        )


@router.put("/me/profile", response_model=UserResponse)
async def update_my_profile_details(
    profile_update: ProfileUpdateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserResponse:
    """Update current user's profile details."""
    log_api_call("update_my_profile_details", "PUT", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Update profile data in Firestore
        profile_data = {
            "profile": {
                **current_user.profile.dict(),
                **profile_update.dict(exclude_unset=True),
            }
        }

        updated_user = await auth_service.update_user(
            current_user.uid, profile_data=profile_data
        )

        logger.info(
            "User profile details updated",
            uid=current_user.uid,
            fields_updated=list(profile_update.dict(exclude_unset=True).keys()),
        )

        return UserResponse(**updated_user)

    except Exception as e:
        logger.error(
            "Profile details update failed",
            uid=current_user.uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile update failed: {str(e)}",
        )


@router.put("/me/preferences", response_model=UserResponse)
async def update_my_preferences(
    preferences_update: PreferencesUpdateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserResponse:
    """Update current user's preferences."""
    log_api_call("update_my_preferences", "PUT", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Update preferences data in Firestore
        profile_data = {
            "preferences": {
                **current_user.preferences.dict(),
                **preferences_update.dict(exclude_unset=True),
            }
        }

        updated_user = await auth_service.update_user(
            current_user.uid, profile_data=profile_data
        )

        logger.info(
            "User preferences updated",
            uid=current_user.uid,
            fields_updated=list(preferences_update.dict(exclude_unset=True).keys()),
        )

        return UserResponse(**updated_user)

    except Exception as e:
        logger.error(
            "Preferences update failed", uid=current_user.uid, error=str(e), exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preferences update failed: {str(e)}",
        )


@router.delete("/me")
async def delete_my_account(
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Delete current user's account."""
    log_api_call("delete_my_account", "DELETE", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Delete user account
        await auth_service.delete_user(current_user.uid)

        log_security_event("user_self_deleted", user_id=current_user.uid)

        logger.info("User account deleted", uid=current_user.uid)

        return {"message": "Account deleted successfully"}

    except Exception as e:
        logger.error(
            "Account deletion failed", uid=current_user.uid, error=str(e), exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account deletion failed: {str(e)}",
        )


@router.get("/{user_uid}", response_model=UserResponse)
async def get_user_by_id(
    user_uid: str,
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserResponse:
    """Get user by UID (admins can see any user, users can only see themselves)."""
    log_api_call("get_user_by_id", "GET", user_id=current_user.uid)

    # Check access permissions
    if not validate_resource_access(
        user_uid, current_user, allow_admin=True, allow_moderator=True
    ):
        log_security_event(
            "unauthorized_user_access", user_id=current_user.uid, target_user=user_uid
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this user",
        )

    try:
        auth_service = get_auth_service()
        user = await auth_service.get_user_by_uid(user_uid)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        logger.info("User retrieved", uid=user_uid, requested_by=current_user.uid)

        return UserResponse(**user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve user", uid=user_uid, error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


# Admin endpoints
@router.get("", response_model=UserListResponse)
async def list_users(
    search: UserSearchRequest = Depends(),
    pagination=Depends(get_pagination_params),
    current_user: UserInDB = Depends(require_moderator()),
) -> UserListResponse:
    """List users (admin/moderator only)."""
    log_api_call("list_users", "GET", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Get users from Firebase Auth with pagination
        result = await auth_service.list_users(
            page_token=None,  # Implement proper pagination with tokens
            max_results=pagination["per_page"],
        )

        users = [UserResponse(**user_data) for user_data in result["users"]]

        # Apply filters if needed (implement in auth service)
        # For now, return all users

        logger.info("Users listed", count=len(users), requested_by=current_user.uid)

        return UserListResponse(
            users=users,
            total=len(users),
            page=pagination["page"],
            per_page=pagination["per_page"],
            has_next=bool(result["next_page_token"]),
        )

    except Exception as e:
        logger.error("Failed to list users", error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users",
        )


@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    current_user: UserInDB = Depends(require_admin()),
) -> UserResponse:
    """Create new user (admin only)."""
    log_api_call("create_user", "POST", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        user = await auth_service.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name,
            phone_number=user_data.phone_number,
            photo_url=user_data.photo_url,
            email_verified=user_data.email_verified,
            disabled=user_data.disabled,
            custom_claims=user_data.custom_claims,
        )

        log_security_event(
            "user_created_by_admin",
            user_id=current_user.uid,
            created_user=user["uid"],
            email=user_data.email,
        )

        logger.info(
            "User created by admin",
            created_user=user["uid"],
            admin_user=current_user.uid,
            email=user_data.email,
        )

        return UserResponse(**user)

    except Exception as e:
        logger.error(
            "Failed to create user",
            admin_user=current_user.uid,
            email=user_data.email,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}",
        )


@router.put("/{user_uid}", response_model=UserResponse)
async def update_user(
    user_uid: str,
    user_update: AdminUserUpdateRequest,
    current_user: UserInDB = Depends(require_admin()),
) -> UserResponse:
    """Update user (admin only)."""
    log_api_call("update_user", "PUT", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Prepare update data
        update_data = user_update.dict(
            exclude_unset=True, exclude={"profile", "preferences"}
        )
        profile_data = {}

        if user_update.profile is not None:
            profile_data["profile"] = user_update.profile.dict()
        if user_update.preferences is not None:
            profile_data["preferences"] = user_update.preferences.dict()

        updated_user = await auth_service.update_user(
            user_uid, profile_data=profile_data, **update_data
        )

        log_security_event(
            "user_updated_by_admin",
            user_id=current_user.uid,
            updated_user=user_uid,
            fields_updated=list(update_data.keys()) + list(profile_data.keys()),
        )

        logger.info(
            "User updated by admin",
            updated_user=user_uid,
            admin_user=current_user.uid,
            fields_updated=list(update_data.keys()) + list(profile_data.keys()),
        )

        return UserResponse(**updated_user)

    except Exception as e:
        logger.error(
            "Failed to update user",
            admin_user=current_user.uid,
            updated_user=user_uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update user: {str(e)}",
        )


@router.delete("/{user_uid}")
async def delete_user(
    user_uid: str,
    current_user: UserInDB = Depends(require_admin()),
) -> Dict[str, str]:
    """Delete user (admin only)."""
    log_api_call("delete_user", "DELETE", user_id=current_user.uid)

    # Prevent self-deletion
    if user_uid == current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    try:
        auth_service = get_auth_service()
        await auth_service.delete_user(user_uid)

        log_security_event(
            "user_deleted_by_admin", user_id=current_user.uid, deleted_user=user_uid
        )

        logger.info(
            "User deleted by admin", deleted_user=user_uid, admin_user=current_user.uid
        )

        return {"message": "User deleted successfully"}

    except Exception as e:
        logger.error(
            "Failed to delete user",
            admin_user=current_user.uid,
            deleted_user=user_uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete user: {str(e)}",
        )


@router.post("/roles/assign")
async def assign_roles(
    role_data: RoleAssignmentRequest,
    current_user: UserInDB = Depends(require_admin()),
) -> Dict[str, str]:
    """Assign roles to user (admin only)."""
    log_api_call("assign_roles", "POST", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        # Update user roles in custom claims
        custom_claims = {"roles": role_data.roles}

        await auth_service.update_user(
            role_data.user_uid,
            custom_claims=custom_claims,
            profile_data={"roles": role_data.roles},
        )

        log_security_event(
            "roles_assigned",
            user_id=current_user.uid,
            target_user=role_data.user_uid,
            assigned_roles=role_data.roles,
        )

        logger.info(
            "Roles assigned",
            target_user=role_data.user_uid,
            admin_user=current_user.uid,
            roles=role_data.roles,
        )

        return {"message": "Roles assigned successfully"}

    except Exception as e:
        logger.error(
            "Failed to assign roles",
            admin_user=current_user.uid,
            target_user=role_data.user_uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign roles: {str(e)}",
        )


@router.post("/custom-claims")
async def update_custom_claims(
    claims_data: CustomClaimsUpdateRequest,
    current_user: UserInDB = Depends(require_admin()),
) -> Dict[str, str]:
    """Update user custom claims (admin only)."""
    log_api_call("update_custom_claims", "POST", user_id=current_user.uid)

    try:
        auth_service = get_auth_service()

        await auth_service.update_user(
            claims_data.user_uid, custom_claims=claims_data.custom_claims
        )

        log_security_event(
            "custom_claims_updated",
            user_id=current_user.uid,
            target_user=claims_data.user_uid,
            claims=list(claims_data.custom_claims.keys()),
        )

        logger.info(
            "Custom claims updated",
            target_user=claims_data.user_uid,
            admin_user=current_user.uid,
            claims=list(claims_data.custom_claims.keys()),
        )

        return {"message": "Custom claims updated successfully"}

    except Exception as e:
        logger.error(
            "Failed to update custom claims",
            admin_user=current_user.uid,
            target_user=claims_data.user_uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update custom claims: {str(e)}",
        )


@router.post("/bulk-action")
async def bulk_user_action(
    action_data: BulkUserActionRequest,
    current_user: UserInDB = Depends(require_admin()),
) -> Dict[str, Any]:
    """Perform bulk action on users (admin only)."""
    log_api_call("bulk_user_action", "POST", user_id=current_user.uid)

    # Prevent actions on self
    if current_user.uid in action_data.user_uids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot perform bulk action on your own account",
        )

    try:
        auth_service = get_auth_service()

        success_count = 0
        failed_users = []

        for user_uid in action_data.user_uids:
            try:
                if action_data.action == "disable":
                    await auth_service.update_user(user_uid, disabled=True)
                elif action_data.action == "enable":
                    await auth_service.update_user(user_uid, disabled=False)
                elif action_data.action == "delete":
                    await auth_service.delete_user(user_uid)
                elif action_data.action == "verify_email":
                    await auth_service.update_user(user_uid, email_verified=True)
                else:
                    raise ValueError(f"Unknown action: {action_data.action}")

                success_count += 1

            except Exception as e:
                failed_users.append({"uid": user_uid, "error": str(e)})
                logger.error(
                    "Bulk action failed for user",
                    user_uid=user_uid,
                    action=action_data.action,
                    error=str(e),
                )

        log_security_event(
            "bulk_user_action",
            user_id=current_user.uid,
            action=action_data.action,
            total_users=len(action_data.user_uids),
            success_count=success_count,
            failed_count=len(failed_users),
        )

        logger.info(
            "Bulk user action completed",
            admin_user=current_user.uid,
            action=action_data.action,
            success_count=success_count,
            failed_count=len(failed_users),
        )

        return {
            "message": "Bulk action completed",
            "success_count": success_count,
            "failed_count": len(failed_users),
            "failed_users": failed_users,
        }

    except Exception as e:
        logger.error(
            "Bulk user action failed",
            admin_user=current_user.uid,
            action=action_data.action,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk action failed: {str(e)}",
        )


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: UserInDB = Depends(require_moderator()),
) -> UserStatsResponse:
    """Get user statistics (admin/moderator only)."""
    log_api_call("get_user_stats", "GET", user_id=current_user.uid)

    try:
        # In a real implementation, you would query the database for these stats
        # For now, return mock data

        firestore_service = get_firestore_service()

        # Get total user count
        total_users = await firestore_service.get_collection_count("users")

        # Get active users (not disabled)
        active_users = await firestore_service.get_collection_count(
            "users", filters=[{"field": "disabled", "operator": "==", "value": False}]
        )

        # Get verified users
        verified_users = await firestore_service.get_collection_count(
            "users",
            filters=[{"field": "email_verified", "operator": "==", "value": True}],
        )

        logger.info(
            "User stats retrieved", admin_user=current_user.uid, total_users=total_users
        )

        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            disabled_users=total_users - active_users,
            new_users_today=0,  # Implement date filtering
            new_users_week=0,  # Implement date filtering
            new_users_month=0,  # Implement date filtering
            users_by_provider={"email": total_users},  # Implement provider grouping
        )

    except Exception as e:
        logger.error(
            "Failed to get user stats",
            admin_user=current_user.uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics",
        )
