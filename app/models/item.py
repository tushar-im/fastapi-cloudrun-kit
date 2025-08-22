from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ItemStatus(str, Enum):
    """Item status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ItemCategory(str, Enum):
    """Item category enumeration."""

    GENERAL = "general"
    TECH = "tech"
    BUSINESS = "business"
    PERSONAL = "personal"
    OTHER = "other"


class ItemPriority(str, Enum):
    """Item priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ItemBase(BaseModel):
    """Base item model with common fields."""

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

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        # Clean and deduplicate tags
        cleaned_tags = []
        for tag in v:
            cleaned_tag = tag.strip().lower()
            if cleaned_tag and cleaned_tag not in cleaned_tags:
                cleaned_tags.append(cleaned_tag)
        return cleaned_tags[:10]  # Limit to 10 tags


class ItemCreate(ItemBase):
    """Item creation model."""

    pass


class ItemUpdate(BaseModel):
    """Item update model."""

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

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 1:
                raise ValueError("Title cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            cleaned_tags = []
            for tag in v:
                cleaned_tag = tag.strip().lower()
                if cleaned_tag and cleaned_tag not in cleaned_tags:
                    cleaned_tags.append(cleaned_tag)
            return cleaned_tags[:10]  # Limit to 10 tags
        return v


class Item(ItemBase):
    """Full item model with all fields."""

    id: str = Field(..., description="Item ID")
    owner_uid: str = Field(..., description="Owner's Firebase UID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    view_count: int = Field(default=0, description="Number of views")
    like_count: int = Field(default=0, description="Number of likes")
    share_count: int = Field(default=0, description="Number of shares")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ItemInDB(Item):
    """Item model as stored in database."""

    @classmethod
    def from_firestore_doc(cls, doc_data: Dict[str, Any]) -> "ItemInDB":
        """Create ItemInDB from Firestore document data."""
        # Handle Firebase Timestamps
        if "created_at" in doc_data and hasattr(doc_data["created_at"], "timestamp"):
            doc_data["created_at"] = datetime.fromtimestamp(
                doc_data["created_at"].timestamp()
            )
        if "updated_at" in doc_data and hasattr(doc_data["updated_at"], "timestamp"):
            doc_data["updated_at"] = datetime.fromtimestamp(
                doc_data["updated_at"].timestamp()
            )

        # Ensure required fields have defaults
        doc_data.setdefault("tags", [])
        doc_data.setdefault("metadata", {})
        doc_data.setdefault("view_count", 0)
        doc_data.setdefault("like_count", 0)
        doc_data.setdefault("share_count", 0)

        return cls(**doc_data)


class ItemPublic(BaseModel):
    """Public item model (safe for external APIs)."""

    id: str = Field(..., description="Item ID")
    title: str = Field(..., description="Item title")
    description: Optional[str] = Field(None, description="Item description")
    category: ItemCategory = Field(..., description="Item category")
    priority: ItemPriority = Field(..., description="Item priority")
    status: ItemStatus = Field(..., description="Item status")
    tags: List[str] = Field(..., description="Item tags")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    view_count: int = Field(default=0, description="Number of views")
    like_count: int = Field(default=0, description="Number of likes")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ItemSummary(BaseModel):
    """Item summary model for lists."""

    id: str = Field(..., description="Item ID")
    title: str = Field(..., description="Item title")
    category: ItemCategory = Field(..., description="Item category")
    priority: ItemPriority = Field(..., description="Item priority")
    status: ItemStatus = Field(..., description="Item status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    view_count: int = Field(default=0, description="Number of views")
    like_count: int = Field(default=0, description="Number of likes")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ItemList(BaseModel):
    """Item list response model."""

    items: List[ItemSummary] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=20, description="Items per page")
    has_next: bool = Field(default=False, description="Whether there are more pages")


class ItemStats(BaseModel):
    """Item statistics model."""

    total_items: int = Field(..., description="Total number of items")
    items_by_status: Dict[ItemStatus, int] = Field(
        ..., description="Items grouped by status"
    )
    items_by_category: Dict[ItemCategory, int] = Field(
        ..., description="Items grouped by category"
    )
    items_by_priority: Dict[ItemPriority, int] = Field(
        ..., description="Items grouped by priority"
    )
    public_items: int = Field(..., description="Number of public items")
    private_items: int = Field(..., description="Number of private items")
    items_created_today: int = Field(..., description="Items created today")
    items_created_week: int = Field(..., description="Items created this week")
    items_created_month: int = Field(..., description="Items created this month")


class ItemFilter(BaseModel):
    """Item filtering options."""

    category: Optional[ItemCategory] = Field(None, description="Filter by category")
    priority: Optional[ItemPriority] = Field(None, description="Filter by priority")
    status: Optional[ItemStatus] = Field(None, description="Filter by status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (OR operation)")
    is_public: Optional[bool] = Field(
        None, description="Filter by public/private status"
    )
    owner_uid: Optional[str] = Field(None, description="Filter by owner UID")
    created_after: Optional[datetime] = Field(
        None, description="Filter items created after this date"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter items created before this date"
    )
    search: Optional[str] = Field(None, description="Search in title and description")


class ItemSort(BaseModel):
    """Item sorting options."""

    field: str = Field(default="created_at", description="Field to sort by")
    direction: str = Field(default="desc", description="Sort direction: asc or desc")

    @field_validator("field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        allowed_fields = [
            "created_at",
            "updated_at",
            "title",
            "priority",
            "status",
            "view_count",
            "like_count",
            "share_count",
        ]
        if v not in allowed_fields:
            raise ValueError(f"Invalid sort field. Allowed: {allowed_fields}")
        return v

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ["asc", "desc"]:
            raise ValueError("Direction must be 'asc' or 'desc'")
        return v


class ItemInteraction(BaseModel):
    """Item interaction model."""

    item_id: str = Field(..., description="Item ID")
    user_uid: str = Field(..., description="User UID")
    interaction_type: str = Field(
        ..., description="Type of interaction: view, like, share"
    )
    timestamp: datetime = Field(..., description="Interaction timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional interaction data"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
