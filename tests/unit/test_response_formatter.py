"""Unit tests for response formatting utilities."""

import json
import pytest
from datetime import datetime
from typing import Dict, Any

from src.shared.utils.response_formatter import (
    ResponseFormatter,
    ResponseSection,
    PaginationHelper,
    FilterHelper,
    SortHelper,
    PaginationMetadata,
    FilterMetadata,
    ResponseStatus,
    SortOrder,
)


class TestResponseFormatter:
    """Test ResponseFormatter class."""

    def test_success_response_basic(self):
        """Test basic success response creation."""
        data = {"key": "value"}
        response = ResponseFormatter.success_response(data)

        assert response["statusCode"] == 200
        assert "headers" in response
        assert "body" in response

        body = json.loads(response["body"])
        assert body["status"] == ResponseStatus.SUCCESS.value
        assert body["data"] == data
        assert "timestamp" in body

    def test_success_response_with_message(self):
        """Test success response with message."""
        data = {"result": "success"}
        message = "Operation completed successfully"
        response = ResponseFormatter.success_response(data, message=message)

        body = json.loads(response["body"])
        assert body["message"] == message

    def test_success_response_with_sections(self):
        """Test success response with scannable sections."""
        data = {"key": "value"}
        sections = [
            ResponseSection(
                heading="Summary",
                content="This is a summary",
            ),
            ResponseSection(
                heading="Details",
                content=["Point 1", "Point 2", "Point 3"],
            ),
        ]

        response = ResponseFormatter.success_response(data, sections=sections)
        body = json.loads(response["body"])

        assert "sections" in body
        assert len(body["sections"]) == 2
        assert body["sections"][0]["heading"] == "Summary"
        assert body["sections"][1]["heading"] == "Details"
        assert body["data"] == data

    def test_success_response_with_pagination(self):
        """Test success response with pagination metadata."""
        data = {"items": [1, 2, 3]}
        pagination = PaginationMetadata(
            page=1,
            page_size=10,
            total_items=25,
            total_pages=3,
            has_next=True,
            has_previous=False,
            next_page=2,
        )

        response = ResponseFormatter.success_response(data, pagination=pagination)
        body = json.loads(response["body"])

        assert "pagination" in body
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["total_items"] == 25
        assert body["pagination"]["has_next"] is True

    def test_success_response_with_filters(self):
        """Test success response with filter metadata."""
        data = {"items": []}
        filters = FilterMetadata(
            applied_filters={"status": "active"},
            available_filters=["status", "type", "date"],
            filter_count=1,
        )

        response = ResponseFormatter.success_response(data, filters=filters)
        body = json.loads(response["body"])

        assert "filters" in body
        assert body["filters"]["filter_count"] == 1
        assert body["filters"]["applied_filters"]["status"] == "active"

    def test_error_response_basic(self):
        """Test basic error response creation."""
        response = ResponseFormatter.error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            status_code=400,
        )

        assert response["statusCode"] == 400
        body = json.loads(response["body"])

        assert body["status"] == ResponseStatus.ERROR.value
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "Invalid input"

    def test_error_response_with_details(self):
        """Test error response with details."""
        details = {"field": "email", "reason": "Invalid format"}
        response = ResponseFormatter.error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            details=details,
        )

        body = json.loads(response["body"])
        assert body["error"]["details"] == details

    def test_error_response_with_suggestions(self):
        """Test error response with suggestions."""
        suggestions = [
            "Check the file format",
            "Ensure file size is under 10MB",
        ]
        response = ResponseFormatter.error_response(
            error_code="UPLOAD_ERROR",
            message="Upload failed",
            suggestions=suggestions,
        )

        body = json.loads(response["body"])
        assert body["error"]["suggestions"] == suggestions

    def test_paginated_response(self):
        """Test paginated response creation."""
        items = [{"id": i} for i in range(1, 6)]
        response = ResponseFormatter.paginated_response(
            items=items,
            page=1,
            page_size=5,
            total_items=15,
        )

        body = json.loads(response["body"])
        assert body["data"]["items"] == items
        assert body["pagination"]["page"] == 1
        assert body["pagination"]["total_pages"] == 3
        assert body["pagination"]["has_next"] is True

    def test_scannable_response(self):
        """Test scannable response with sections."""
        sections = [
            ResponseSection(
                heading="Overview",
                content="System overview",
            ),
            ResponseSection(
                heading="Key Points",
                content=["Point 1", "Point 2"],
            ),
        ]

        response = ResponseFormatter.scannable_response(sections)
        body = json.loads(response["body"])

        assert "sections" in body
        assert len(body["sections"]) == 2
        assert "data" in body
        assert body["data"]["Overview"] == "System overview"

    def test_response_section_with_subsections(self):
        """Test response section with nested subsections."""
        subsections = [
            ResponseSection(heading="Sub 1", content="Content 1"),
            ResponseSection(heading="Sub 2", content="Content 2"),
        ]
        section = ResponseSection(
            heading="Main",
            content="Main content",
            subsections=subsections,
        )

        section_dict = section.to_dict()
        assert section_dict["heading"] == "Main"
        assert len(section_dict["subsections"]) == 2
        assert section_dict["subsections"][0]["heading"] == "Sub 1"

    def test_response_headers(self):
        """Test that responses include proper headers."""
        response = ResponseFormatter.success_response({"data": "test"})
        headers = response["headers"]

        assert headers["Content-Type"] == "application/json"
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"


class TestPaginationHelper:
    """Test PaginationHelper class."""

    def test_paginate_first_page(self):
        """Test pagination of first page."""
        items = list(range(1, 26))  # 25 items
        paginated, metadata = PaginationHelper.paginate(items, page=1, page_size=10)

        assert len(paginated) == 10
        assert paginated[0] == 1
        assert paginated[-1] == 10
        assert metadata.page == 1
        assert metadata.total_items == 25
        assert metadata.total_pages == 3
        assert metadata.has_next is True
        assert metadata.has_previous is False

    def test_paginate_middle_page(self):
        """Test pagination of middle page."""
        items = list(range(1, 26))
        paginated, metadata = PaginationHelper.paginate(items, page=2, page_size=10)

        assert len(paginated) == 10
        assert paginated[0] == 11
        assert paginated[-1] == 20
        assert metadata.has_next is True
        assert metadata.has_previous is True

    def test_paginate_last_page(self):
        """Test pagination of last page."""
        items = list(range(1, 26))
        paginated, metadata = PaginationHelper.paginate(items, page=3, page_size=10)

        assert len(paginated) == 5
        assert paginated[0] == 21
        assert paginated[-1] == 25
        assert metadata.has_next is False
        assert metadata.has_previous is True

    def test_paginate_empty_list(self):
        """Test pagination of empty list."""
        items = []
        paginated, metadata = PaginationHelper.paginate(items, page=1, page_size=10)

        assert len(paginated) == 0
        assert metadata.total_items == 0
        assert metadata.total_pages == 0

    def test_paginate_invalid_page(self):
        """Test pagination with invalid page number."""
        items = list(range(1, 26))
        paginated, metadata = PaginationHelper.paginate(items, page=0, page_size=10)

        # Should default to page 1
        assert metadata.page == 1

    def test_paginate_page_beyond_total(self):
        """Test pagination with page number beyond total pages."""
        items = list(range(1, 11))  # 10 items
        paginated, metadata = PaginationHelper.paginate(items, page=5, page_size=10)

        # Should return last page
        assert metadata.page == 1
        assert len(paginated) == 10

    def test_extract_pagination_params_defaults(self):
        """Test extracting pagination params with defaults."""
        event = {}
        page, page_size = PaginationHelper.extract_pagination_params(event)

        assert page == 1
        assert page_size == 10

    def test_extract_pagination_params_from_query(self):
        """Test extracting pagination params from query string."""
        event = {
            "queryStringParameters": {
                "page": "2",
                "page_size": "20",
            }
        }
        page, page_size = PaginationHelper.extract_pagination_params(event)

        assert page == 2
        assert page_size == 20

    def test_extract_pagination_params_max_page_size(self):
        """Test that page size is clamped to maximum."""
        event = {
            "queryStringParameters": {
                "page_size": "200",
            }
        }
        page, page_size = PaginationHelper.extract_pagination_params(
            event, max_page_size=100
        )

        assert page_size == 100

    def test_extract_pagination_params_invalid_values(self):
        """Test extracting pagination params with invalid values."""
        event = {
            "queryStringParameters": {
                "page": "invalid",
                "page_size": "not_a_number",
            }
        }
        page, page_size = PaginationHelper.extract_pagination_params(event)

        # Should use defaults
        assert page == 1
        assert page_size == 10


class TestFilterHelper:
    """Test FilterHelper class."""

    def test_apply_filters_single_field(self):
        """Test applying single field filter."""
        items = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "inactive"},
            {"id": 3, "status": "active"},
        ]
        filters = {"status": "active"}
        filtered = FilterHelper.apply_filters(items, filters)

        assert len(filtered) == 2
        assert all(item["status"] == "active" for item in filtered)

    def test_apply_filters_multiple_fields(self):
        """Test applying multiple field filters."""
        items = [
            {"id": 1, "status": "active", "type": "A"},
            {"id": 2, "status": "inactive", "type": "B"},
            {"id": 3, "status": "active", "type": "B"},
        ]
        filters = {"status": "active", "type": "B"}
        filtered = FilterHelper.apply_filters(items, filters)

        assert len(filtered) == 1
        assert filtered[0]["id"] == 3

    def test_apply_filters_nested_field(self):
        """Test applying filter to nested field."""
        items = [
            {"id": 1, "metadata": {"category": "tech"}},
            {"id": 2, "metadata": {"category": "science"}},
        ]
        filters = {"metadata.category": "tech"}
        filtered = FilterHelper.apply_filters(items, filters)

        assert len(filtered) == 1
        assert filtered[0]["id"] == 1

    def test_apply_filters_list_value(self):
        """Test applying filter with list of values."""
        items = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "inactive"},
            {"id": 3, "status": "pending"},
        ]
        filters = {"status": ["active", "pending"]}
        filtered = FilterHelper.apply_filters(items, filters)

        assert len(filtered) == 2

    def test_apply_filters_wildcard_prefix(self):
        """Test applying filter with wildcard prefix."""
        items = [
            {"id": 1, "name": "test_file.txt"},
            {"id": 2, "name": "document.pdf"},
            {"id": 3, "name": "image.txt"},
        ]
        filters = {"name": "*.txt"}
        filtered = FilterHelper.apply_filters(items, filters)

        assert len(filtered) == 2

    def test_apply_filters_wildcard_suffix(self):
        """Test applying filter with wildcard suffix."""
        items = [
            {"id": 1, "name": "test_file.txt"},
            {"id": 2, "name": "test_document.pdf"},
            {"id": 3, "name": "image.txt"},
        ]
        filters = {"name": "test_*"}
        filtered = FilterHelper.apply_filters(items, filters)

        assert len(filtered) == 2

    def test_apply_filters_no_filters(self):
        """Test applying no filters returns all items."""
        items = [{"id": 1}, {"id": 2}]
        filtered = FilterHelper.apply_filters(items, {})

        assert len(filtered) == 2

    def test_extract_filters(self):
        """Test extracting filters from event."""
        event = {
            "queryStringParameters": {
                "status": "active",
                "type": "A",
                "other": "value",
            }
        }
        allowed_filters = ["status", "type"]
        filters = FilterHelper.extract_filters(event, allowed_filters)

        assert filters == {"status": "active", "type": "A"}
        assert "other" not in filters

    def test_extract_filters_json_value(self):
        """Test extracting filters with JSON values."""
        event = {
            "queryStringParameters": {
                "status": '["active", "pending"]',
            }
        }
        filters = FilterHelper.extract_filters(event, ["status"])

        assert filters["status"] == ["active", "pending"]

    def test_create_filter_metadata(self):
        """Test creating filter metadata."""
        applied = {"status": "active"}
        available = ["status", "type", "date"]
        metadata = FilterHelper.create_filter_metadata(applied, available)

        assert metadata.filter_count == 1
        assert metadata.applied_filters == applied
        assert metadata.available_filters == available


class TestSortHelper:
    """Test SortHelper class."""

    def test_sort_items_ascending(self):
        """Test sorting items in ascending order."""
        items = [
            {"id": 3, "name": "C"},
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
        ]
        sorted_items = SortHelper.sort_items(items, "id", SortOrder.ASC)

        assert sorted_items[0]["id"] == 1
        assert sorted_items[1]["id"] == 2
        assert sorted_items[2]["id"] == 3

    def test_sort_items_descending(self):
        """Test sorting items in descending order."""
        items = [
            {"id": 1, "name": "A"},
            {"id": 3, "name": "C"},
            {"id": 2, "name": "B"},
        ]
        sorted_items = SortHelper.sort_items(items, "id", SortOrder.DESC)

        assert sorted_items[0]["id"] == 3
        assert sorted_items[1]["id"] == 2
        assert sorted_items[2]["id"] == 1

    def test_sort_items_nested_field(self):
        """Test sorting items by nested field."""
        items = [
            {"id": 1, "metadata": {"priority": 3}},
            {"id": 2, "metadata": {"priority": 1}},
            {"id": 3, "metadata": {"priority": 2}},
        ]
        sorted_items = SortHelper.sort_items(items, "metadata.priority", SortOrder.ASC)

        assert sorted_items[0]["metadata"]["priority"] == 1
        assert sorted_items[1]["metadata"]["priority"] == 2
        assert sorted_items[2]["metadata"]["priority"] == 3

    def test_sort_items_string_field(self):
        """Test sorting items by string field."""
        items = [
            {"name": "Charlie"},
            {"name": "Alice"},
            {"name": "Bob"},
        ]
        sorted_items = SortHelper.sort_items(items, "name", SortOrder.ASC)

        assert sorted_items[0]["name"] == "Alice"
        assert sorted_items[1]["name"] == "Bob"
        assert sorted_items[2]["name"] == "Charlie"

    def test_extract_sort_params_defaults(self):
        """Test extracting sort params with defaults."""
        event = {}
        sort_by, order = SortHelper.extract_sort_params(event, default_sort_by="id")

        assert sort_by == "id"
        assert order == SortOrder.ASC

    def test_extract_sort_params_from_query(self):
        """Test extracting sort params from query string."""
        event = {
            "queryStringParameters": {
                "sort_by": "name",
                "order": "desc",
            }
        }
        sort_by, order = SortHelper.extract_sort_params(event)

        assert sort_by == "name"
        assert order == SortOrder.DESC

    def test_extract_sort_params_invalid_order(self):
        """Test extracting sort params with invalid order."""
        event = {
            "queryStringParameters": {
                "order": "invalid",
            }
        }
        sort_by, order = SortHelper.extract_sort_params(event)

        # Should default to ASC
        assert order == SortOrder.ASC


class TestIntegration:
    """Integration tests for response formatting."""

    def test_paginated_filtered_sorted_response(self):
        """Test combining pagination, filtering, and sorting."""
        # Create sample data
        items = [
            {"id": i, "status": "active" if i % 2 == 0 else "inactive", "priority": i}
            for i in range(1, 21)
        ]

        # Apply filters
        filters = {"status": "active"}
        filtered_items = FilterHelper.apply_filters(items, filters)

        # Apply sorting
        sorted_items = SortHelper.sort_items(filtered_items, "priority", SortOrder.DESC)

        # Apply pagination
        paginated_items, pagination = PaginationHelper.paginate(
            sorted_items, page=1, page_size=5
        )

        # Create response
        filter_metadata = FilterHelper.create_filter_metadata(
            filters, ["status", "priority"]
        )
        response = ResponseFormatter.paginated_response(
            items=paginated_items,
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=pagination.total_items,
            filters=filter_metadata,
        )

        body = json.loads(response["body"])

        # Verify response structure
        assert body["status"] == "success"
        assert "data" in body
        assert "pagination" in body
        assert "filters" in body

        # Verify pagination
        assert body["pagination"]["total_items"] == 10  # 10 active items
        assert len(body["data"]["items"]) == 5

        # Verify sorting (descending priority)
        assert body["data"]["items"][0]["priority"] > body["data"]["items"][1]["priority"]

    def test_scannable_response_with_nested_sections(self):
        """Test creating scannable response with nested sections."""
        subsections = [
            ResponseSection(heading="Technical Details", content="Details here"),
            ResponseSection(heading="Examples", content=["Example 1", "Example 2"]),
        ]

        sections = [
            ResponseSection(heading="Overview", content="System overview"),
            ResponseSection(
                heading="Documentation",
                content="Main documentation",
                subsections=subsections,
            ),
        ]

        response = ResponseFormatter.scannable_response(sections)
        body = json.loads(response["body"])

        # Verify structure
        assert len(body["sections"]) == 2
        assert body["sections"][1]["heading"] == "Documentation"
        assert len(body["sections"][1]["subsections"]) == 2
        assert body["sections"][1]["subsections"][0]["heading"] == "Technical Details"
