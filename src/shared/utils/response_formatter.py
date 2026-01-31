"""Response formatting utilities for consistent API responses.

This module provides utilities for creating consistent, scannable API responses
with proper structure, headings, pagination, and filtering capabilities.

Validates: Requirements 5.5 - Result formatting and organization
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ResponseStatus(Enum):
    """Response status types."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class SortOrder(Enum):
    """Sort order for pagination."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class PaginationMetadata:
    """Pagination metadata for large result sets."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FilterMetadata:
    """Filter metadata for result sets."""
    applied_filters: Dict[str, Any]
    available_filters: List[str]
    filter_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ResponseSection:
    """A section in a scannable response with heading and content."""
    heading: str
    content: Union[str, List[str], Dict[str, Any]]
    subsections: Optional[List['ResponseSection']] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "heading": self.heading,
            "content": self.content,
        }
        if self.subsections:
            result["subsections"] = [s.to_dict() for s in self.subsections]
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class ResponseFormatter:
    """Formatter for creating consistent, scannable API responses."""

    @staticmethod
    def success_response(
        data: Any,
        message: Optional[str] = None,
        status_code: int = 200,
        sections: Optional[List[ResponseSection]] = None,
        pagination: Optional[PaginationMetadata] = None,
        filters: Optional[FilterMetadata] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a success API response with consistent structure.

        Args:
            data: Response data
            message: Optional success message
            status_code: HTTP status code (default: 200)
            sections: Optional list of response sections for scannable format
            pagination: Optional pagination metadata
            filters: Optional filter metadata
            metadata: Optional additional metadata

        Returns:
            Formatted API Gateway response
        """
        response_body = {
            "status": ResponseStatus.SUCCESS.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if message:
            response_body["message"] = message

        # Add data in scannable format if sections provided
        if sections:
            response_body["sections"] = [s.to_dict() for s in sections]
            # Also include raw data for programmatic access
            response_body["data"] = data
        else:
            response_body["data"] = data

        # Add pagination metadata if provided
        if pagination:
            response_body["pagination"] = pagination.to_dict()

        # Add filter metadata if provided
        if filters:
            response_body["filters"] = filters.to_dict()

        # Add additional metadata if provided
        if metadata:
            response_body["metadata"] = metadata

        return {
            "statusCode": status_code,
            "headers": ResponseFormatter._get_headers(),
            "body": json.dumps(response_body, default=str),
        }

    @staticmethod
    def error_response(
        error_code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an error API response with consistent structure.

        Args:
            error_code: Error code identifier
            message: User-friendly error message
            status_code: HTTP status code (default: 500)
            details: Optional error details
            suggestions: Optional list of suggestions to resolve the error

        Returns:
            Formatted API Gateway response
        """
        response_body = {
            "status": ResponseStatus.ERROR.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": {
                "code": error_code,
                "message": message,
            },
        }

        if details:
            response_body["error"]["details"] = details

        if suggestions:
            response_body["error"]["suggestions"] = suggestions

        return {
            "statusCode": status_code,
            "headers": ResponseFormatter._get_headers(),
            "body": json.dumps(response_body, default=str),
        }

    @staticmethod
    def paginated_response(
        items: List[Any],
        page: int,
        page_size: int,
        total_items: int,
        message: Optional[str] = None,
        sections: Optional[List[ResponseSection]] = None,
        filters: Optional[FilterMetadata] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a paginated response for large result sets.

        Args:
            items: List of items for current page
            page: Current page number (1-indexed)
            page_size: Number of items per page
            total_items: Total number of items across all pages
            message: Optional message
            sections: Optional response sections for scannable format
            filters: Optional filter metadata
            metadata: Optional additional metadata

        Returns:
            Formatted API Gateway response with pagination
        """
        total_pages = (total_items + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1

        pagination = PaginationMetadata(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            next_page=page + 1 if has_next else None,
            previous_page=page - 1 if has_previous else None,
        )

        return ResponseFormatter.success_response(
            data={"items": items},
            message=message,
            sections=sections,
            pagination=pagination,
            filters=filters,
            metadata=metadata,
        )

    @staticmethod
    def scannable_response(
        sections: List[ResponseSection],
        message: Optional[str] = None,
        status_code: int = 200,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a scannable response with organized sections and headings.

        This format is optimized for human readability with clear structure.

        Args:
            sections: List of response sections with headings
            message: Optional message
            status_code: HTTP status code
            metadata: Optional metadata

        Returns:
            Formatted API Gateway response
        """
        # Extract data from sections for programmatic access
        data = {section.heading: section.content for section in sections}

        return ResponseFormatter.success_response(
            data=data,
            message=message,
            status_code=status_code,
            sections=sections,
            metadata=metadata,
        )

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Get standard response headers."""
        return {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }


class PaginationHelper:
    """Helper for pagination operations."""

    @staticmethod
    def paginate(
        items: List[T],
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[List[T], PaginationMetadata]:
        """
        Paginate a list of items.

        Args:
            items: List of items to paginate
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (paginated items, pagination metadata)
        """
        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 10

        total_items = len(items)
        total_pages = (total_items + page_size - 1) // page_size

        # Ensure page is within bounds
        if page > total_pages and total_pages > 0:
            page = total_pages

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]

        has_next = page < total_pages
        has_previous = page > 1

        pagination = PaginationMetadata(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            next_page=page + 1 if has_next else None,
            previous_page=page - 1 if has_previous else None,
        )

        return paginated_items, pagination

    @staticmethod
    def extract_pagination_params(
        event: Dict[str, Any],
        default_page: int = 1,
        default_page_size: int = 10,
        max_page_size: int = 100,
    ) -> tuple[int, int]:
        """
        Extract pagination parameters from API Gateway event.

        Args:
            event: API Gateway event
            default_page: Default page number
            default_page_size: Default page size
            max_page_size: Maximum allowed page size

        Returns:
            Tuple of (page, page_size)
        """
        params = event.get("queryStringParameters") or {}

        try:
            page = int(params.get("page", default_page))
            page = max(1, page)  # Ensure page >= 1
        except (ValueError, TypeError):
            page = default_page

        try:
            page_size = int(params.get("page_size", default_page_size))
            page_size = max(1, min(page_size, max_page_size))  # Clamp to valid range
        except (ValueError, TypeError):
            page_size = default_page_size

        return page, page_size


class FilterHelper:
    """Helper for filtering operations."""

    @staticmethod
    def apply_filters(
        items: List[Dict[str, Any]],
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Apply filters to a list of items.

        Args:
            items: List of items to filter
            filters: Dictionary of field -> value filters

        Returns:
            Filtered list of items
        """
        if not filters:
            return items

        filtered_items = items
        for field, value in filters.items():
            if value is not None:
                filtered_items = [
                    item for item in filtered_items
                    if FilterHelper._matches_filter(item, field, value)
                ]

        return filtered_items

    @staticmethod
    def _matches_filter(item: Dict[str, Any], field: str, value: Any) -> bool:
        """
        Check if an item matches a filter.

        Args:
            item: Item to check
            field: Field name (supports nested fields with dot notation)
            value: Filter value

        Returns:
            True if item matches filter
        """
        # Support nested field access with dot notation
        field_parts = field.split(".")
        current = item

        for part in field_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False

        # Handle different comparison types
        if isinstance(value, list):
            return current in value
        elif isinstance(value, str) and value.startswith("*"):
            # Wildcard matching
            return str(current).endswith(value[1:])
        elif isinstance(value, str) and value.endswith("*"):
            return str(current).startswith(value[:-1])
        else:
            return current == value

    @staticmethod
    def extract_filters(
        event: Dict[str, Any],
        allowed_filters: List[str],
    ) -> Dict[str, Any]:
        """
        Extract filter parameters from API Gateway event.

        Args:
            event: API Gateway event
            allowed_filters: List of allowed filter field names

        Returns:
            Dictionary of filters
        """
        params = event.get("queryStringParameters") or {}
        filters = {}

        for field in allowed_filters:
            if field in params:
                value = params[field]
                # Try to parse as JSON for complex filters
                try:
                    filters[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    filters[field] = value

        return filters

    @staticmethod
    def create_filter_metadata(
        applied_filters: Dict[str, Any],
        available_filters: List[str],
    ) -> FilterMetadata:
        """
        Create filter metadata.

        Args:
            applied_filters: Dictionary of applied filters
            available_filters: List of available filter fields

        Returns:
            FilterMetadata object
        """
        return FilterMetadata(
            applied_filters=applied_filters,
            available_filters=available_filters,
            filter_count=len(applied_filters),
        )


class SortHelper:
    """Helper for sorting operations."""

    @staticmethod
    def sort_items(
        items: List[Dict[str, Any]],
        sort_by: str,
        order: SortOrder = SortOrder.ASC,
    ) -> List[Dict[str, Any]]:
        """
        Sort a list of items.

        Args:
            items: List of items to sort
            sort_by: Field name to sort by (supports nested fields with dot notation)
            order: Sort order (ASC or DESC)

        Returns:
            Sorted list of items
        """
        def get_sort_key(item: Dict[str, Any]) -> Any:
            """Extract sort key from item."""
            field_parts = sort_by.split(".")
            current = item

            for part in field_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

            return current

        reverse = order == SortOrder.DESC
        return sorted(items, key=get_sort_key, reverse=reverse)

    @staticmethod
    def extract_sort_params(
        event: Dict[str, Any],
        default_sort_by: Optional[str] = None,
        default_order: SortOrder = SortOrder.ASC,
    ) -> tuple[Optional[str], SortOrder]:
        """
        Extract sort parameters from API Gateway event.

        Args:
            event: API Gateway event
            default_sort_by: Default field to sort by
            default_order: Default sort order

        Returns:
            Tuple of (sort_by, order)
        """
        params = event.get("queryStringParameters") or {}

        sort_by = params.get("sort_by", default_sort_by)

        order_str = params.get("order", default_order.value).lower()
        order = SortOrder.DESC if order_str == "desc" else SortOrder.ASC

        return sort_by, order
