from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.item import ItemStatus, ItemCategory, ItemPriority


class ItemCreateRequest(BaseModel):
    """Item creation request model."""

    title: str = Field(..., min_length=1, max_length=200, description="Item title")
    description: Optional[str] = Field(
        None, max_length=2000, description="Item description"
    )
    category: ItemCategory = Field(
        default=ItemCategory.GENERAL, description="Item category"
    )
    priority: ItemPriority = Field(
        default=ItemPriority.MEDIUM, description="Item priority"
    )
    status: ItemStatus = Field(default=ItemStatus.DRAFT, description="Item status")
    tags: List[str] = Field(default_factory=list, description="Item tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    is_public: bool = Field(default=False, description="Whether the item is public")


class ItemUpdateRequest(BaseModel):
    """Item update request model."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Item title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Item description"
    )
    category: Optional[ItemCategory] = Field(None, description="Item category")
    priority: Optional[ItemPriority] = Field(None, description="Item priority")
    status: Optional[ItemStatus] = Field(None, description="Item status")
    tags: Optional[List[str]] = Field(None, description="Item tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    is_public: Optional[bool] = Field(None, description="Whether the item is public")


class ItemResponse(BaseModel):
    """Item response model."""

    id: str = Field(..., description="Item ID")
    title: str = Field(..., description="Item title")
    description: Optional[str] = Field(None, description="Item description")
    category: ItemCategory = Field(..., description="Item category")
    priority: ItemPriority = Field(..., description="Item priority")
    status: ItemStatus = Field(..., description="Item status")
    tags: List[str] = Field(..., description="Item tags")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    is_public: bool = Field(..., description="Whether the item is public")
    owner_uid: str = Field(..., description="Owner's Firebase UID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    view_count: int = Field(default=0, description="Number of views")
    like_count: int = Field(default=0, description="Number of likes")
    share_count: int = Field(default=0, description="Number of shares")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ItemSummaryResponse(BaseModel):
    """Item summary response model for lists."""

    id: str = Field(..., description="Item ID")
    title: str = Field(..., description="Item title")
    category: ItemCategory = Field(..., description="Item category")
    priority: ItemPriority = Field(..., description="Item priority")
    status: ItemStatus = Field(..., description="Item status")
    tags: List[str] = Field(..., description="Item tags")
    is_public: bool = Field(..., description="Whether the item is public")
    owner_uid: str = Field(..., description="Owner's Firebase UID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    view_count: int = Field(default=0, description="Number of views")
    like_count: int = Field(default=0, description="Number of likes")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ItemListResponse(BaseModel):
    """Item list response model."""

    items: List[ItemSummaryResponse] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=20, description="Items per page")
    has_next: bool = Field(default=False, description="Whether there are more pages")


class ItemSearchRequest(BaseModel):
    """Item search request model."""

    query: Optional[str] = Field(
        None, description="Search query for title and description"
    )
    category: Optional[ItemCategory] = Field(None, description="Filter by category")
    priority: Optional[ItemPriority] = Field(None, description="Filter by priority")
    status: Optional[ItemStatus] = Field(None, description="Filter by status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (OR operation)")
    is_public: Optional[bool] = Field(
        None, description="Filter by public/private status"
    )
    owner_uid: Optional[str] = Field(None, description="Filter by owner UID")
    created_after: Optional[datetime] = Field(
        None, description="Filter items created after"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter items created before"
    )
    min_views: Optional[int] = Field(None, ge=0, description="Minimum view count")
    min_likes: Optional[int] = Field(None, ge=0, description="Minimum like count")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


class ItemStatsResponse(BaseModel):
    """Item statistics response model."""

    total_items: int = Field(..., description="Total number of items")
    items_by_status: Dict[str, int] = Field(..., description="Items grouped by status")
    items_by_category: Dict[str, int] = Field(
        ..., description="Items grouped by category"
    )
    items_by_priority: Dict[str, int] = Field(
        ..., description="Items grouped by priority"
    )
    public_items: int = Field(..., description="Number of public items")
    private_items: int = Field(..., description="Number of private items")
    items_created_today: int = Field(..., description="Items created today")
    items_created_week: int = Field(..., description="Items created this week")
    items_created_month: int = Field(..., description="Items created this month")
    top_tags: List[Dict[str, Any]] = Field(..., description="Most popular tags")
    most_viewed_items: List[ItemSummaryResponse] = Field(
        ..., description="Most viewed items"
    )
    most_liked_items: List[ItemSummaryResponse] = Field(
        ..., description="Most liked items"
    )


class BulkItemActionRequest(BaseModel):
    """Bulk item action request model."""

    item_ids: List[str] = Field(..., min_items=1, description="List of item IDs")
    action: str = Field(
        ..., description="Action: delete, archive, activate, make_public, make_private"
    )

    class Config:
        schema_extra = {
            "example": {"item_ids": ["item1", "item2", "item3"], "action": "archive"}
        }


class ItemInteractionRequest(BaseModel):
    """Item interaction request model."""

    interaction_type: str = Field(..., description="Type: view, like, unlike, share")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional data"
    )


class ItemInteractionResponse(BaseModel):
    """Item interaction response model."""

    item_id: str = Field(..., description="Item ID")
    interaction_type: str = Field(..., description="Interaction type")
    success: bool = Field(..., description="Whether the interaction succeeded")
    new_count: int = Field(..., description="New count after interaction")
    message: Optional[str] = Field(None, description="Response message")


class ItemExportRequest(BaseModel):
    """Item export request model."""

    format: str = Field(default="json", description="Export format: json, csv, xml")
    filters: Optional[ItemSearchRequest] = Field(None, description="Filters to apply")
    fields: Optional[List[str]] = Field(None, description="Fields to include in export")


class ItemImportRequest(BaseModel):
    """Item import request model."""

    format: str = Field(..., description="Import format: json, csv")
    data: str = Field(..., description="Import data as string")
    merge_strategy: str = Field(
        default="create", description="Strategy: create, update, upsert"
    )
    validate_only: bool = Field(
        default=False, description="Only validate, don't import"
    )


class ItemImportResponse(BaseModel):
    """Item import response model."""

    success: bool = Field(..., description="Whether import succeeded")
    imported_count: int = Field(default=0, description="Number of items imported")
    failed_count: int = Field(default=0, description="Number of items failed")
    errors: List[str] = Field(default_factory=list, description="Import errors")
    warnings: List[str] = Field(default_factory=list, description="Import warnings")
    preview: Optional[List[Dict[str, Any]]] = Field(
        None, description="Preview of items to import"
    )


class ItemTagsResponse(BaseModel):
    """Item tags response model."""

    tags: List[str] = Field(..., description="List of all tags")
    tag_counts: Dict[str, int] = Field(..., description="Tag usage counts")
    total_tags: int = Field(..., description="Total number of unique tags")


class ItemCategoriesResponse(BaseModel):
    """Item categories response model."""

    categories: List[Dict[str, Any]] = Field(..., description="Available categories")
    category_counts: Dict[str, int] = Field(..., description="Item counts per category")


class ItemActivityResponse(BaseModel):
    """Item activity response model."""

    item_id: str = Field(..., description="Item ID")
    recent_views: int = Field(default=0, description="Views in last 7 days")
    recent_likes: int = Field(default=0, description="Likes in last 7 days")
    recent_shares: int = Field(default=0, description="Shares in last 7 days")
    activity_timeline: List[Dict[str, Any]] = Field(
        ..., description="Activity timeline"
    )
    top_viewers: List[Dict[str, Any]] = Field(..., description="Top viewers")
    engagement_rate: float = Field(default=0.0, description="Engagement rate")


class RelatedItemsResponse(BaseModel):
    """Related items response model."""

    item_id: str = Field(..., description="Source item ID")
    related_items: List[ItemSummaryResponse] = Field(..., description="Related items")
    similarity_scores: Dict[str, float] = Field(..., description="Similarity scores")
    recommendation_reason: Dict[str, str] = Field(
        ..., description="Recommendation reasons"
    )


class ItemVersionResponse(BaseModel):
    """Item version response model."""

    version_id: str = Field(..., description="Version ID")
    item_id: str = Field(..., description="Item ID")
    version_number: int = Field(..., description="Version number")
    changes: Dict[str, Any] = Field(..., description="Changes made in this version")
    created_at: datetime = Field(..., description="Version creation timestamp")
    created_by: str = Field(..., description="User who created this version")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
