from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    get_current_active_user,
    get_optional_current_user,
    get_pagination_params,
    require_moderator,
    validate_resource_access,
)
from app.core.logging import get_logger, log_api_call
from app.models.item import ItemStatus, ItemCategory, ItemPriority
from app.models.user import UserInDB
from app.schemas.item import (
    BulkItemActionRequest,
    ItemCreateRequest,
    ItemInteractionRequest,
    ItemInteractionResponse,
    ItemListResponse,
    ItemResponse,
    ItemSearchRequest,
    ItemStatsResponse,
    ItemSummaryResponse,
    ItemUpdateRequest,
)
from app.services.firestore import get_firestore_service
from app.utils.helpers import generate_id, generate_pagination_info, get_utc_now

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=ItemListResponse)
async def list_items(
    category: Optional[ItemCategory] = None,
    status: Optional[ItemStatus] = None,
    priority: Optional[ItemPriority] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = None,
    owner_uid: Optional[str] = None,
    is_public: Optional[bool] = None,
    pagination=Depends(get_pagination_params),
    current_user: Optional[UserInDB] = Depends(get_optional_current_user),
) -> ItemListResponse:
    """List items with filtering and pagination."""
    log_api_call(
        "list_items", "GET", user_id=current_user.uid if current_user else None
    )

    try:
        firestore_service = get_firestore_service()

        # Build filters
        filters = []

        # Only show public items for non-authenticated users
        if not current_user:
            filters.append({"field": "is_public", "operator": "==", "value": True})
        else:
            # For authenticated users, show their own items + public items
            if is_public is not None:
                filters.append(
                    {"field": "is_public", "operator": "==", "value": is_public}
                )
            elif owner_uid is None:
                # If no specific owner requested, show public items + user's own items
                # This requires a compound query, for now just show public items
                filters.append({"field": "is_public", "operator": "==", "value": True})

        if category:
            filters.append(
                {"field": "category", "operator": "==", "value": category.value}
            )
        if status:
            filters.append({"field": "status", "operator": "==", "value": status.value})
        if priority:
            filters.append(
                {"field": "priority", "operator": "==", "value": priority.value}
            )
        if owner_uid:
            # Only allow viewing specific user's items if it's the current user or admin
            if current_user and validate_resource_access(
                owner_uid, current_user, allow_admin=True, allow_moderator=True
            ):
                filters.append(
                    {"field": "owner_uid", "operator": "==", "value": owner_uid}
                )
            else:
                # Add public filter for other users' items
                filters.extend(
                    [
                        {"field": "owner_uid", "operator": "==", "value": owner_uid},
                        {"field": "is_public", "operator": "==", "value": True},
                    ]
                )

        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
            if tag_list:
                # For Firestore, we need to use array-contains for each tag
                # For simplicity, just use the first tag
                filters.append(
                    {
                        "field": "tags",
                        "operator": "array-contains",
                        "value": tag_list[0],
                    }
                )

        # Query items
        items = await firestore_service.query_documents(
            collection="items",
            filters=filters,
            order_by="created_at",
            descending=True,
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )

        # Convert to response models
        item_summaries = []
        for item_data in items:
            try:
                item_summary = ItemSummaryResponse(
                    id=item_data["id"],
                    title=item_data["title"],
                    category=ItemCategory(item_data["category"]),
                    priority=ItemPriority(item_data["priority"]),
                    status=ItemStatus(item_data["status"]),
                    tags=item_data.get("tags", []),
                    is_public=item_data.get("is_public", False),
                    owner_uid=item_data["owner_uid"],
                    created_at=item_data.get("created_at"),
                    updated_at=item_data.get("updated_at"),
                    view_count=item_data.get("view_count", 0),
                    like_count=item_data.get("like_count", 0),
                )
                item_summaries.append(item_summary)
            except Exception as e:
                logger.warning(
                    "Failed to parse item", item_id=item_data.get("id"), error=str(e)
                )
                continue

        # Get total count (for pagination)
        total = await firestore_service.get_collection_count("items", filters=filters)

        pagination_info = generate_pagination_info(
            total, pagination["page"], pagination["per_page"]
        )

        logger.info(
            "Items listed",
            count=len(item_summaries),
            total=total,
            user_id=current_user.uid if current_user else None,
        )

        return ItemListResponse(
            items=item_summaries,
            total=total,
            page=pagination["page"],
            per_page=pagination["per_page"],
            has_next=pagination_info["has_next"],
        )

    except Exception as e:
        logger.error("Failed to list items", error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list items",
        )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    current_user: Optional[UserInDB] = Depends(get_optional_current_user),
) -> ItemResponse:
    """Get item by ID."""
    log_api_call("get_item", "GET", user_id=current_user.uid if current_user else None)

    try:
        firestore_service = get_firestore_service()

        # Get item
        item_data = await firestore_service.get_document("items", item_id)

        if not item_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Check if user can access this item
        is_owner = current_user and item_data["owner_uid"] == current_user.uid
        is_public = item_data.get("is_public", False)
        is_admin = current_user and "admin" in current_user.roles
        is_moderator = current_user and "moderator" in current_user.roles

        if not (is_public or is_owner or is_admin or is_moderator):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this item",
            )

        # Increment view count
        if current_user and item_data["owner_uid"] != current_user.uid:
            await firestore_service.update_document(
                "items", item_id, {"view_count": item_data.get("view_count", 0) + 1}
            )
            item_data["view_count"] = item_data.get("view_count", 0) + 1

        # Record view interaction
        if current_user:
            await record_item_interaction(item_id, current_user.uid, "view")

        logger.info(
            "Item retrieved",
            item_id=item_id,
            owner_uid=item_data["owner_uid"],
            user_id=current_user.uid if current_user else None,
        )

        return ItemResponse(
            id=item_data["id"],
            title=item_data["title"],
            description=item_data.get("description"),
            category=ItemCategory(item_data["category"]),
            priority=ItemPriority(item_data["priority"]),
            status=ItemStatus(item_data["status"]),
            tags=item_data.get("tags", []),
            metadata=item_data.get("metadata", {}),
            is_public=item_data.get("is_public", False),
            owner_uid=item_data["owner_uid"],
            created_at=item_data.get("created_at"),
            updated_at=item_data.get("updated_at"),
            view_count=item_data.get("view_count", 0),
            like_count=item_data.get("like_count", 0),
            share_count=item_data.get("share_count", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get item", item_id=item_id, error=str(e), exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get item",
        )


@router.post("", response_model=ItemResponse)
async def create_item(
    item_data: ItemCreateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
) -> ItemResponse:
    """Create new item."""
    log_api_call("create_item", "POST", user_id=current_user.uid)

    try:
        firestore_service = get_firestore_service()

        # Generate item ID
        item_id = generate_id()

        # Prepare item data
        now = get_utc_now()
        item_doc_data = {
            "title": item_data.title,
            "description": item_data.description,
            "category": item_data.category.value,
            "priority": item_data.priority.value,
            "status": item_data.status.value,
            "tags": item_data.tags,
            "metadata": item_data.metadata,
            "is_public": item_data.is_public,
            "owner_uid": current_user.uid,
            "view_count": 0,
            "like_count": 0,
            "share_count": 0,
        }

        # Create item
        await firestore_service.create_document("items", item_id, item_doc_data)

        logger.info(
            "Item created",
            item_id=item_id,
            title=item_data.title,
            owner_uid=current_user.uid,
        )

        # Return created item
        item_doc_data["id"] = item_id
        item_doc_data["created_at"] = now
        item_doc_data["updated_at"] = now

        return ItemResponse(
            id=item_id,
            title=item_data.title,
            description=item_data.description,
            category=item_data.category,
            priority=item_data.priority,
            status=item_data.status,
            tags=item_data.tags,
            metadata=item_data.metadata,
            is_public=item_data.is_public,
            owner_uid=current_user.uid,
            created_at=now,
            updated_at=now,
            view_count=0,
            like_count=0,
            share_count=0,
        )

    except Exception as e:
        logger.error(
            "Failed to create item", user_id=current_user.uid, error=str(e), exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create item: {str(e)}",
        )


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    item_update: ItemUpdateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
) -> ItemResponse:
    """Update item."""
    log_api_call("update_item", "PUT", user_id=current_user.uid)

    try:
        firestore_service = get_firestore_service()

        # Get existing item
        item_data = await firestore_service.get_document("items", item_id)

        if not item_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Check permissions
        if not validate_resource_access(
            item_data["owner_uid"], current_user, allow_admin=True, allow_moderator=True
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this item",
            )

        # Prepare update data
        update_data = {}
        for field, value in item_update.dict(exclude_unset=True).items():
            if field in ["category", "priority", "status"] and value is not None:
                update_data[field] = value.value
            elif value is not None:
                update_data[field] = value

        # Update item
        await firestore_service.update_document("items", item_id, update_data)

        # Get updated item
        updated_item_data = await firestore_service.get_document("items", item_id)

        logger.info(
            "Item updated",
            item_id=item_id,
            owner_uid=item_data["owner_uid"],
            updated_by=current_user.uid,
            fields_updated=list(update_data.keys()),
        )

        return ItemResponse(
            id=updated_item_data["id"],
            title=updated_item_data["title"],
            description=updated_item_data.get("description"),
            category=ItemCategory(updated_item_data["category"]),
            priority=ItemPriority(updated_item_data["priority"]),
            status=ItemStatus(updated_item_data["status"]),
            tags=updated_item_data.get("tags", []),
            metadata=updated_item_data.get("metadata", {}),
            is_public=updated_item_data.get("is_public", False),
            owner_uid=updated_item_data["owner_uid"],
            created_at=updated_item_data.get("created_at"),
            updated_at=updated_item_data.get("updated_at"),
            view_count=updated_item_data.get("view_count", 0),
            like_count=updated_item_data.get("like_count", 0),
            share_count=updated_item_data.get("share_count", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update item",
            item_id=item_id,
            user_id=current_user.uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update item: {str(e)}",
        )


@router.delete("/{item_id}")
async def delete_item(
    item_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Delete item."""
    log_api_call("delete_item", "DELETE", user_id=current_user.uid)

    try:
        firestore_service = get_firestore_service()

        # Get existing item
        item_data = await firestore_service.get_document("items", item_id)

        if not item_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Check permissions
        if not validate_resource_access(
            item_data["owner_uid"], current_user, allow_admin=True, allow_moderator=True
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this item",
            )

        # Delete item
        await firestore_service.delete_document("items", item_id)

        # TODO: Delete related data (interactions, etc.)

        logger.info(
            "Item deleted",
            item_id=item_id,
            owner_uid=item_data["owner_uid"],
            deleted_by=current_user.uid,
        )

        return {"message": "Item deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete item",
            item_id=item_id,
            user_id=current_user.uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete item: {str(e)}",
        )


@router.post("/{item_id}/interact", response_model=ItemInteractionResponse)
async def interact_with_item(
    item_id: str,
    interaction: ItemInteractionRequest,
    current_user: UserInDB = Depends(get_current_active_user),
) -> ItemInteractionResponse:
    """Interact with item (like, unlike, etc.)."""
    log_api_call("interact_with_item", "POST", user_id=current_user.uid)

    try:
        firestore_service = get_firestore_service()

        # Get item
        item_data = await firestore_service.get_document("items", item_id)

        if not item_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        # Check if item is accessible
        is_public = item_data.get("is_public", False)
        is_owner = item_data["owner_uid"] == current_user.uid

        if not (is_public or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to interact with this item",
            )

        # Process interaction
        success = False
        new_count = 0
        message = ""

        if interaction.interaction_type == "like":
            # Check if already liked (in a real app, you'd check interactions collection)
            new_count = item_data.get("like_count", 0) + 1
            await firestore_service.update_document(
                "items", item_id, {"like_count": new_count}
            )
            await record_item_interaction(
                item_id, current_user.uid, "like", interaction.metadata
            )
            success = True
            message = "Item liked"

        elif interaction.interaction_type == "unlike":
            new_count = max(0, item_data.get("like_count", 0) - 1)
            await firestore_service.update_document(
                "items", item_id, {"like_count": new_count}
            )
            # TODO: Remove like interaction record
            success = True
            message = "Item unliked"

        elif interaction.interaction_type == "share":
            new_count = item_data.get("share_count", 0) + 1
            await firestore_service.update_document(
                "items", item_id, {"share_count": new_count}
            )
            await record_item_interaction(
                item_id, current_user.uid, "share", interaction.metadata
            )
            success = True
            message = "Item shared"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown interaction type: {interaction.interaction_type}",
            )

        logger.info(
            "Item interaction recorded",
            item_id=item_id,
            user_id=current_user.uid,
            interaction_type=interaction.interaction_type,
            new_count=new_count,
        )

        return ItemInteractionResponse(
            item_id=item_id,
            interaction_type=interaction.interaction_type,
            success=success,
            new_count=new_count,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to record interaction",
            item_id=item_id,
            user_id=current_user.uid,
            interaction_type=interaction.interaction_type,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record interaction: {str(e)}",
        )


async def record_item_interaction(
    item_id: str,
    user_uid: str,
    interaction_type: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Record item interaction."""
    try:
        firestore_service = get_firestore_service()

        interaction_data = {
            "item_id": item_id,
            "user_uid": user_uid,
            "interaction_type": interaction_type,
            "timestamp": get_utc_now(),
            "metadata": metadata or {},
        }

        await firestore_service.create_document(
            "item_interactions", generate_id(), interaction_data
        )

    except Exception as e:
        logger.error(
            "Failed to record interaction",
            item_id=item_id,
            user_uid=user_uid,
            interaction_type=interaction_type,
            error=str(e),
        )


@router.get("/stats/overview", response_model=ItemStatsResponse)
async def get_item_stats(
    current_user: UserInDB = Depends(require_moderator()),
) -> ItemStatsResponse:
    """Get item statistics (admin/moderator only)."""
    log_api_call("get_item_stats", "GET", user_id=current_user.uid)

    try:
        firestore_service = get_firestore_service()

        # Get total count
        total_items = await firestore_service.get_collection_count("items")

        # Get counts by status
        items_by_status = {}
        for status_value in ItemStatus:
            count = await firestore_service.get_collection_count(
                "items",
                filters=[
                    {"field": "status", "operator": "==", "value": status_value.value}
                ],
            )
            items_by_status[status_value.value] = count

        # Get counts by category
        items_by_category = {}
        for category_value in ItemCategory:
            count = await firestore_service.get_collection_count(
                "items",
                filters=[
                    {
                        "field": "category",
                        "operator": "==",
                        "value": category_value.value,
                    }
                ],
            )
            items_by_category[category_value.value] = count

        # Get counts by priority
        items_by_priority = {}
        for priority_value in ItemPriority:
            count = await firestore_service.get_collection_count(
                "items",
                filters=[
                    {
                        "field": "priority",
                        "operator": "==",
                        "value": priority_value.value,
                    }
                ],
            )
            items_by_priority[priority_value.value] = count

        # Get public/private counts
        public_items = await firestore_service.get_collection_count(
            "items", filters=[{"field": "is_public", "operator": "==", "value": True}]
        )
        private_items = total_items - public_items

        logger.info(
            "Item stats retrieved", admin_user=current_user.uid, total_items=total_items
        )

        return ItemStatsResponse(
            total_items=total_items,
            items_by_status=items_by_status,
            items_by_category=items_by_category,
            items_by_priority=items_by_priority,
            public_items=public_items,
            private_items=private_items,
            items_created_today=0,  # TODO: Implement date filtering
            items_created_week=0,  # TODO: Implement date filtering
            items_created_month=0,  # TODO: Implement date filtering
            top_tags=[],  # TODO: Implement tag aggregation
            most_viewed_items=[],  # TODO: Implement top items query
            most_liked_items=[],  # TODO: Implement top items query
        )

    except Exception as e:
        logger.error(
            "Failed to get item stats",
            admin_user=current_user.uid,
            error=str(e),
            exc_info=e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get item statistics",
        )
