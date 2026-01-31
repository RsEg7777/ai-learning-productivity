# Response Formatting Implementation

## Overview

This document describes the implementation of consistent API response formatting with scannable organization, pagination, and filtering capabilities for the AI Learning Assistant system.

**Validates:** Requirements 5.5 - Result formatting and organization  
**Property:** Property 15 - Result formatting consistency

## Architecture

The response formatting system consists of several key components:

1. **ResponseFormatter**: Core formatter for creating consistent API responses
2. **PaginationHelper**: Utilities for paginating large result sets
3. **FilterHelper**: Utilities for filtering data
4. **SortHelper**: Utilities for sorting data
5. **ResponseSection**: Data structure for scannable content organization

## Components

### ResponseFormatter

The `ResponseFormatter` class provides static methods for creating consistent API Gateway responses:

#### Success Response
```python
ResponseFormatter.success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200,
    sections: Optional[List[ResponseSection]] = None,
    pagination: Optional[PaginationMetadata] = None,
    filters: Optional[FilterMetadata] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]
```

Creates a success response with:
- Consistent status field ("success")
- ISO 8601 timestamp
- Optional message
- Data payload
- Optional scannable sections with headings
- Optional pagination metadata
- Optional filter metadata
- Optional additional metadata

#### Error Response
```python
ResponseFormatter.error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
) -> Dict[str, Any]
```

Creates an error response with:
- Consistent status field ("error")
- ISO 8601 timestamp
- Error code and message
- Optional error details
- Optional suggestions for resolution

#### Paginated Response
```python
ResponseFormatter.paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total_items: int,
    message: Optional[str] = None,
    sections: Optional[List[ResponseSection]] = None,
    filters: Optional[FilterMetadata] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]
```

Creates a paginated response with automatic pagination metadata calculation.

#### Scannable Response
```python
ResponseFormatter.scannable_response(
    sections: List[ResponseSection],
    message: Optional[str] = None,
    status_code: int = 200,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]
```

Creates a response optimized for human readability with organized sections and headings.

### ResponseSection

Data structure for organizing content with headings:

```python
@dataclass
class ResponseSection:
    heading: str
    content: Union[str, List[str], Dict[str, Any]]
    subsections: Optional[List['ResponseSection']] = None
    metadata: Optional[Dict[str, Any]] = None
```

Supports:
- Hierarchical organization with subsections
- Multiple content types (text, lists, objects)
- Optional metadata per section

### PaginationHelper

Utilities for pagination operations:

#### Paginate Items
```python
PaginationHelper.paginate(
    items: List[T],
    page: int = 1,
    page_size: int = 10,
) -> tuple[List[T], PaginationMetadata]
```

Paginates a list and returns items for the requested page along with metadata.

#### Extract Pagination Parameters
```python
PaginationHelper.extract_pagination_params(
    event: Dict[str, Any],
    default_page: int = 1,
    default_page_size: int = 10,
    max_page_size: int = 100,
) -> tuple[int, int]
```

Extracts pagination parameters from API Gateway event query strings.

### FilterHelper

Utilities for filtering operations:

#### Apply Filters
```python
FilterHelper.apply_filters(
    items: List[Dict[str, Any]],
    filters: Dict[str, Any],
) -> List[Dict[str, Any]]
```

Applies filters to a list of items. Supports:
- Simple field matching
- Nested field access with dot notation (e.g., "metadata.category")
- List values (item matches if field value is in list)
- Wildcard matching (prefix with `*` or suffix with `*`)

#### Extract Filters
```python
FilterHelper.extract_filters(
    event: Dict[str, Any],
    allowed_filters: List[str],
) -> Dict[str, Any]
```

Extracts filter parameters from API Gateway event query strings.

### SortHelper

Utilities for sorting operations:

#### Sort Items
```python
SortHelper.sort_items(
    items: List[Dict[str, Any]],
    sort_by: str,
    order: SortOrder = SortOrder.ASC,
) -> List[Dict[str, Any]]
```

Sorts items by a field. Supports:
- Ascending and descending order
- Nested field access with dot notation
- String and numeric sorting

#### Extract Sort Parameters
```python
SortHelper.extract_sort_params(
    event: Dict[str, Any],
    default_sort_by: Optional[str] = None,
    default_order: SortOrder = SortOrder.ASC,
) -> tuple[Optional[str], SortOrder]
```

Extracts sort parameters from API Gateway event query strings.

## Response Structure

### Success Response Structure
```json
{
  "status": "success",
  "timestamp": "2024-01-31T12:00:00.000Z",
  "message": "Optional success message",
  "data": {
    "key": "value"
  },
  "sections": [
    {
      "heading": "Section Title",
      "content": "Section content or list or object",
      "subsections": []
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 100,
    "total_pages": 10,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  },
  "filters": {
    "applied_filters": {"status": "active"},
    "available_filters": ["status", "type"],
    "filter_count": 1
  },
  "metadata": {
    "additional": "metadata"
  }
}
```

### Error Response Structure
```json
{
  "status": "error",
  "timestamp": "2024-01-31T12:00:00.000Z",
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": {
      "field": "value"
    },
    "suggestions": [
      "Suggestion 1",
      "Suggestion 2"
    ]
  }
}
```

## Usage Examples

### Basic Success Response
```python
from src.shared.utils.response_formatter import ResponseFormatter

response = ResponseFormatter.success_response(
    data={"user_id": "123", "name": "John"},
    message="User retrieved successfully"
)
```

### Scannable Response with Sections
```python
from src.shared.utils.response_formatter import ResponseFormatter, ResponseSection

sections = [
    ResponseSection(
        heading="Summary",
        content="Content processed successfully"
    ),
    ResponseSection(
        heading="Key Points",
        content=["Point 1", "Point 2", "Point 3"]
    )
]

response = ResponseFormatter.scannable_response(
    sections=sections,
    message="Processing complete"
)
```

### Paginated Response
```python
from src.shared.utils.response_formatter import (
    ResponseFormatter,
    PaginationHelper
)

# Paginate items
items = [...]  # Your data
paginated_items, pagination = PaginationHelper.paginate(
    items, page=1, page_size=10
)

# Create response
response = ResponseFormatter.paginated_response(
    items=paginated_items,
    page=pagination.page,
    page_size=pagination.page_size,
    total_items=pagination.total_items
)
```

### Filtered and Sorted Response
```python
from src.shared.utils.response_formatter import (
    ResponseFormatter,
    FilterHelper,
    SortHelper,
    SortOrder
)

# Apply filters
filters = {"status": "active"}
filtered_items = FilterHelper.apply_filters(items, filters)

# Sort items
sorted_items = SortHelper.sort_items(
    filtered_items,
    sort_by="created_at",
    order=SortOrder.DESC
)

# Create filter metadata
filter_metadata = FilterHelper.create_filter_metadata(
    applied_filters=filters,
    available_filters=["status", "type", "date"]
)

# Create response
response = ResponseFormatter.success_response(
    data={"items": sorted_items},
    filters=filter_metadata
)
```

### Parsing API Gateway Event
```python
from src.shared.utils.response_formatter import (
    PaginationHelper,
    FilterHelper,
    SortHelper
)

def handler(event, context):
    # Extract parameters from query string
    page, page_size = PaginationHelper.extract_pagination_params(event)
    filters = FilterHelper.extract_filters(
        event,
        allowed_filters=["status", "type"]
    )
    sort_by, order = SortHelper.extract_sort_params(event)
    
    # Use parameters to query and format data
    # ...
```

### Error Response with Suggestions
```python
from src.shared.utils.response_formatter import ResponseFormatter

response = ResponseFormatter.error_response(
    error_code="UNSUPPORTED_FORMAT",
    message="File format not supported",
    status_code=400,
    details={"filename": "doc.xyz"},
    suggestions=[
        "Supported formats: PDF, TXT, DOCX",
        "Convert your file to a supported format"
    ]
)
```

## Integration with API Handlers

The response formatter is designed to integrate seamlessly with Lambda handlers:

```python
from src.shared.utils.response_formatter import (
    ResponseFormatter,
    ResponseSection,
    PaginationHelper
)

class MyHandler:
    def handle_request(self, event, context):
        try:
            # Extract parameters
            page, page_size = PaginationHelper.extract_pagination_params(event)
            
            # Process request
            items = self.get_items()
            
            # Paginate
            paginated_items, pagination = PaginationHelper.paginate(
                items, page, page_size
            )
            
            # Create scannable sections
            sections = [
                ResponseSection(
                    heading="Results",
                    content=f"Found {pagination.total_items} items"
                ),
                ResponseSection(
                    heading="Items",
                    content=[item["title"] for item in paginated_items]
                )
            ]
            
            # Return formatted response
            return ResponseFormatter.paginated_response(
                items=paginated_items,
                page=pagination.page,
                page_size=pagination.page_size,
                total_items=pagination.total_items,
                sections=sections
            )
            
        except Exception as e:
            return ResponseFormatter.error_response(
                error_code="INTERNAL_ERROR",
                message="An error occurred",
                status_code=500
            )
```

## Benefits

### Consistency
- All API responses follow the same structure
- Predictable error handling
- Standard pagination and filtering patterns

### Scannability
- Organized sections with clear headings
- Hierarchical content organization
- Both human-readable and machine-parsable formats

### Developer Experience
- Simple, intuitive API
- Type hints for better IDE support
- Comprehensive examples and documentation

### User Experience
- Clear error messages with suggestions
- Consistent response structure across all endpoints
- Easy navigation of large result sets

## Testing

The response formatter includes comprehensive unit tests covering:
- Basic success and error responses
- Scannable responses with sections
- Pagination with various edge cases
- Filtering with different filter types
- Sorting in ascending and descending order
- Integration scenarios combining multiple features

Run tests with:
```bash
pytest tests/unit/test_response_formatter.py -v
```

## Security Considerations

The response formatter includes security headers:
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking attacks
- CORS headers for cross-origin requests

## Performance Considerations

- Pagination reduces response size for large datasets
- Filtering happens in-memory (consider database-level filtering for large datasets)
- Sorting is efficient for moderate-sized result sets
- Response sections add minimal overhead

## Future Enhancements

Potential improvements:
1. Database-level pagination and filtering
2. Cursor-based pagination for very large datasets
3. Response caching
4. Compression for large responses
5. GraphQL-style field selection
6. Response schema validation

## Related Documentation

- [API Gateway Implementation](./API_GATEWAY_IMPLEMENTATION.md)
- [Error Handling Implementation](./ERROR_HANDLING_IMPLEMENTATION.md)
- [Development Guide](./DEVELOPMENT.md)

## References

- Requirements 5.5: User Interface and Interaction
- Property 15: Result formatting consistency
- Design Document: Interface Properties section
