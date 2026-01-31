"""Example demonstrating response formatting with pagination and filtering.

This example shows how to use the ResponseFormatter, PaginationHelper, and
FilterHelper to create consistent, scannable API responses.
"""

import json
from datetime import datetime
from src.shared.utils.response_formatter import (
    ResponseFormatter,
    ResponseSection,
    PaginationHelper,
    FilterHelper,
    SortHelper,
    SortOrder,
)


def example_basic_success_response():
    """Example: Basic success response."""
    print("=" * 80)
    print("Example 1: Basic Success Response")
    print("=" * 80)

    data = {
        "user_id": "user-123",
        "name": "John Doe",
        "email": "john@example.com",
    }

    response = ResponseFormatter.success_response(
        data=data,
        message="User retrieved successfully",
    )

    print(json.dumps(json.loads(response["body"]), indent=2))
    print()


def example_scannable_response():
    """Example: Scannable response with sections and headings."""
    print("=" * 80)
    print("Example 2: Scannable Response with Sections")
    print("=" * 80)

    sections = [
        ResponseSection(
            heading="Summary",
            content="Your content has been processed successfully.",
        ),
        ResponseSection(
            heading="Key Points",
            content=[
                "Content analyzed and summarized",
                "10 flashcards generated",
                "Quiz created with 15 questions",
            ],
        ),
        ResponseSection(
            heading="Processing Details",
            content={
                "processing_time": "2.5 seconds",
                "word_count": 1500,
                "language": "English",
            },
        ),
        ResponseSection(
            heading="Next Steps",
            content="You can now review the flashcards or take the quiz.",
            subsections=[
                ResponseSection(
                    heading="Flashcards",
                    content="Access your flashcards at /api/flashcards/content-123",
                ),
                ResponseSection(
                    heading="Quiz",
                    content="Start the quiz at /api/quiz/quiz-456",
                ),
            ],
        ),
    ]

    response = ResponseFormatter.scannable_response(
        sections=sections,
        message="Content processing complete",
    )

    print(json.dumps(json.loads(response["body"]), indent=2))
    print()


def example_paginated_response():
    """Example: Paginated response for large result sets."""
    print("=" * 80)
    print("Example 3: Paginated Response")
    print("=" * 80)

    # Simulate a large dataset
    all_items = [
        {
            "id": i,
            "title": f"Content {i}",
            "type": "text" if i % 2 == 0 else "video",
            "created_at": f"2024-01-{(i % 28) + 1:02d}",
        }
        for i in range(1, 51)  # 50 items total
    ]

    # Paginate the items
    page = 2
    page_size = 10
    paginated_items, pagination = PaginationHelper.paginate(
        all_items, page=page, page_size=page_size
    )

    # Create sections for scannable format
    sections = [
        ResponseSection(
            heading="Results",
            content=f"Showing {len(paginated_items)} of {pagination.total_items} items",
        ),
        ResponseSection(
            heading="Items",
            content=[item["title"] for item in paginated_items],
        ),
    ]

    response = ResponseFormatter.paginated_response(
        items=paginated_items,
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=pagination.total_items,
        message="Content list retrieved successfully",
        sections=sections,
    )

    body = json.loads(response["body"])
    print(json.dumps(body, indent=2))
    print()


def example_filtered_response():
    """Example: Filtered response with filter metadata."""
    print("=" * 80)
    print("Example 4: Filtered Response")
    print("=" * 80)

    # Simulate dataset
    all_items = [
        {"id": 1, "title": "Python Tutorial", "type": "text", "status": "active"},
        {"id": 2, "title": "JavaScript Guide", "type": "video", "status": "active"},
        {"id": 3, "title": "Java Basics", "type": "text", "status": "inactive"},
        {"id": 4, "title": "React Course", "type": "video", "status": "active"},
        {"id": 5, "title": "SQL Tutorial", "type": "text", "status": "active"},
    ]

    # Apply filters
    filters = {"type": "text", "status": "active"}
    filtered_items = FilterHelper.apply_filters(all_items, filters)

    # Create filter metadata
    filter_metadata = FilterHelper.create_filter_metadata(
        applied_filters=filters,
        available_filters=["type", "status", "title"],
    )

    # Create sections
    sections = [
        ResponseSection(
            heading="Filter Summary",
            content=f"Found {len(filtered_items)} items matching your filters",
        ),
        ResponseSection(
            heading="Applied Filters",
            content=[f"{k}: {v}" for k, v in filters.items()],
        ),
        ResponseSection(
            heading="Results",
            content=[item["title"] for item in filtered_items],
        ),
    ]

    response = ResponseFormatter.success_response(
        data={"items": filtered_items},
        message="Filtered results retrieved successfully",
        sections=sections,
        filters=filter_metadata,
    )

    print(json.dumps(json.loads(response["body"]), indent=2))
    print()


def example_sorted_paginated_filtered():
    """Example: Combined sorting, pagination, and filtering."""
    print("=" * 80)
    print("Example 5: Combined Sorting, Pagination, and Filtering")
    print("=" * 80)

    # Simulate dataset
    all_items = [
        {
            "id": i,
            "title": f"Content {i}",
            "type": "text" if i % 2 == 0 else "video",
            "status": "active" if i % 3 != 0 else "inactive",
            "priority": i % 5,
            "created_at": f"2024-01-{(i % 28) + 1:02d}",
        }
        for i in range(1, 31)  # 30 items
    ]

    # Step 1: Apply filters
    filters = {"status": "active", "type": "text"}
    filtered_items = FilterHelper.apply_filters(all_items, filters)

    # Step 2: Sort items
    sorted_items = SortHelper.sort_items(
        filtered_items, sort_by="priority", order=SortOrder.DESC
    )

    # Step 3: Paginate
    page = 1
    page_size = 5
    paginated_items, pagination = PaginationHelper.paginate(
        sorted_items, page=page, page_size=page_size
    )

    # Create metadata
    filter_metadata = FilterHelper.create_filter_metadata(
        applied_filters=filters,
        available_filters=["status", "type", "priority"],
    )

    # Create sections
    sections = [
        ResponseSection(
            heading="Query Summary",
            content=f"Found {pagination.total_items} items (showing page {page} of {pagination.total_pages})",
        ),
        ResponseSection(
            heading="Applied Filters",
            content=[f"{k}: {v}" for k, v in filters.items()],
        ),
        ResponseSection(
            heading="Sort Order",
            content="Sorted by priority (descending)",
        ),
        ResponseSection(
            heading="Results",
            content=[
                f"{item['title']} (priority: {item['priority']})"
                for item in paginated_items
            ],
        ),
    ]

    response = ResponseFormatter.paginated_response(
        items=paginated_items,
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=pagination.total_items,
        message="Query results retrieved successfully",
        sections=sections,
        filters=filter_metadata,
        metadata={"sort_by": "priority", "sort_order": "desc"},
    )

    print(json.dumps(json.loads(response["body"]), indent=2))
    print()


def example_error_response():
    """Example: Error response with suggestions."""
    print("=" * 80)
    print("Example 6: Error Response with Suggestions")
    print("=" * 80)

    response = ResponseFormatter.error_response(
        error_code="UNSUPPORTED_FORMAT",
        message="The uploaded file format is not supported",
        status_code=400,
        details={
            "filename": "document.xyz",
            "detected_format": "xyz",
        },
        suggestions=[
            "Supported formats: PDF, TXT, DOCX",
            "Convert your file to a supported format",
            "Check the file extension",
        ],
    )

    print(json.dumps(json.loads(response["body"]), indent=2))
    print()


def example_api_gateway_event_parsing():
    """Example: Parsing pagination and filter params from API Gateway event."""
    print("=" * 80)
    print("Example 7: Parsing API Gateway Event Parameters")
    print("=" * 80)

    # Simulate API Gateway event
    event = {
        "queryStringParameters": {
            "page": "2",
            "page_size": "15",
            "status": "active",
            "type": "text",
            "sort_by": "created_at",
            "order": "desc",
        }
    }

    # Extract parameters
    page, page_size = PaginationHelper.extract_pagination_params(event)
    filters = FilterHelper.extract_filters(event, ["status", "type"])
    sort_by, order = SortHelper.extract_sort_params(event)

    print(f"Pagination: page={page}, page_size={page_size}")
    print(f"Filters: {filters}")
    print(f"Sort: sort_by={sort_by}, order={order.value}")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("=" * 80)
    print("RESPONSE FORMATTING EXAMPLES")
    print("=" * 80)
    print("\n")

    example_basic_success_response()
    example_scannable_response()
    example_paginated_response()
    example_filtered_response()
    example_sorted_paginated_filtered()
    example_error_response()
    example_api_gateway_event_parsing()

    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
