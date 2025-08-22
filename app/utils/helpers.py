import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from pydantic import ValidationError


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate a short unique ID."""
    return str(uuid.uuid4()).replace("-", "")[:length]


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a URL-friendly slug."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")[:max_length]


def is_valid_email(email: str) -> bool:
    """Check if email is valid."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_phone(phone: str) -> bool:
    """Check if phone number is valid (basic validation)."""
    # Remove common formatting characters
    cleaned = re.sub(r"[\s\-\(\)]+", "", phone)

    # Check if it starts with + and has appropriate length
    if cleaned.startswith("+"):
        return len(cleaned) >= 10 and cleaned[1:].isdigit()

    return False


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize a string by removing/escaping dangerous characters."""
    if not text:
        return ""

    # Remove null bytes and control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Strip whitespace
    text = text.strip()

    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def normalize_tags(tags: List[str]) -> List[str]:
    """Normalize and deduplicate tags."""
    normalized = []
    seen = set()

    for tag in tags:
        # Clean and normalize
        clean_tag = sanitize_string(tag.lower().strip())
        if clean_tag and clean_tag not in seen and len(clean_tag) >= 2:
            normalized.append(clean_tag)
            seen.add(clean_tag)

    return normalized[:20]  # Limit to 20 tags


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text."""
    if not text:
        return []

    hashtags = re.findall(r"#(\w+)", text)
    return normalize_tags(hashtags)


def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text."""
    if not text:
        return []

    mentions = re.findall(r"@(\w+)", text)
    return [mention.lower() for mention in mentions if len(mention) >= 2]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def format_duration(seconds: int) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def parse_datetime(dt_string: str) -> Optional[datetime]:
    """Parse datetime string with multiple format support."""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_string, fmt)
        except ValueError:
            continue

    return None


def format_datetime(dt: datetime, format_type: str = "iso") -> str:
    """Format datetime to string."""
    if not dt:
        return ""

    if format_type == "iso":
        return dt.isoformat()
    elif format_type == "friendly":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "date":
        return dt.strftime("%Y-%m-%d")
    elif format_type == "time":
        return dt.strftime("%H:%M:%S")
    else:
        return dt.strftime(format_type)


def calculate_age(birth_date: datetime) -> int:
    """Calculate age from birth date."""
    today = datetime.now().date()
    birth_date = birth_date.date() if isinstance(birth_date, datetime) else birth_date

    age = today.year - birth_date.year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1

    return age


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data like emails, phone numbers, etc."""
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""

    if "@" in data:  # Email
        local, domain = data.split("@", 1)
        masked_local = local[:2] + mask_char * (len(local) - 2)
        return f"{masked_local}@{domain}"
    else:  # Other sensitive data
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def validate_json_data(data: Any, schema_class) -> Dict[str, Any]:
    """Validate data against Pydantic schema."""
    try:
        validated = schema_class(**data)
        return validated.dict()
    except ValidationError as e:
        raise ValueError(f"Validation error: {e}")


def clean_dict(
    data: Dict[str, Any], remove_none: bool = True, remove_empty: bool = False
) -> Dict[str, Any]:
    """Clean dictionary by removing None/empty values."""
    cleaned = {}

    for key, value in data.items():
        if remove_none and value is None:
            continue
        if remove_empty and not value:
            continue

        if isinstance(value, dict):
            cleaned_nested = clean_dict(value, remove_none, remove_empty)
            if cleaned_nested or not remove_empty:
                cleaned[key] = cleaned_nested
        elif isinstance(value, list):
            cleaned_list = [
                clean_dict(item, remove_none, remove_empty)
                if isinstance(item, dict)
                else item
                for item in value
                if not (remove_none and item is None)
                and not (remove_empty and not item)
            ]
            if cleaned_list or not remove_empty:
                cleaned[key] = cleaned_list
        else:
            cleaned[key] = value

    return cleaned


def merge_dicts(
    dict1: Dict[str, Any], dict2: Dict[str, Any], deep: bool = True
) -> Dict[str, Any]:
    """Merge two dictionaries."""
    if not deep:
        return {**dict1, **dict2}

    merged = dict1.copy()

    for key, value in dict2.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_dicts(merged[key], value, deep=True)
        else:
            merged[key] = value

    return merged


def paginate_list(
    items: List[Any], page: int = 1, per_page: int = 20
) -> Dict[str, Any]:
    """Paginate a list of items."""
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20

    total = len(items)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    paginated_items = items[start_idx:end_idx]

    has_next = end_idx < total
    has_prev = page > 1

    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": has_next,
        "has_prev": has_prev,
        "total_pages": (total + per_page - 1) // per_page,
    }


def generate_pagination_info(
    total: int, page: int = 1, per_page: int = 20
) -> Dict[str, Any]:
    """Generate pagination information."""
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20

    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }


def extract_keywords(
    text: str, min_length: int = 3, max_keywords: int = 10
) -> List[str]:
    """Extract keywords from text."""
    if not text:
        return []

    # Simple keyword extraction
    words = re.findall(r"\b[a-zA-Z]{" + str(min_length) + r",}\b", text.lower())

    # Remove common stop words
    stop_words = {
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "was",
        "are",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "this",
        "that",
        "these",
        "those",
        "a",
        "an",
    }

    keywords = [word for word in words if word not in stop_words]

    # Count frequency and return most common
    word_count = {}
    for word in keywords:
        word_count[word] = word_count.get(word, 0) + 1

    sorted_keywords = sorted(
        word_count.keys(), key=lambda x: word_count[x], reverse=True
    )

    return sorted_keywords[:max_keywords]


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity score (0.0 to 1.0)."""
    if not text1 or not text2:
        return 0.0

    # Extract keywords from both texts
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))

    if not keywords1 and not keywords2:
        return 0.0

    # Calculate Jaccard similarity
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)

    if not union:
        return 0.0

    return len(intersection) / len(union)
