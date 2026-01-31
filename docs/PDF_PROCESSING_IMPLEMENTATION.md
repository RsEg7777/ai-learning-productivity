# PDF Processing Implementation

## Overview

The PDF processing service provides comprehensive text extraction and analysis capabilities for PDF documents. It integrates with the existing text processing pipeline to generate structured summaries while preserving technical terms and formatting.

## Features

### Core Capabilities

1. **Text Extraction**
   - Extracts text from all pages in a PDF document
   - Preserves formatting including bullet points, numbered lists, and code blocks
   - Handles multi-page documents efficiently
   - Supports both pypdf and PyPDF2 libraries

2. **Technical Term Preservation**
   - Identifies and preserves technical terms during processing
   - Recognizes patterns including:
     - CamelCase identifiers (e.g., `HTTPRequest`, `DatabaseConnection`)
     - ACRONYMS (e.g., `HTTP`, `JSON`, `API`)
     - Function names (e.g., `getData()`, `processRequest()`)
     - Module/package names (e.g., `module.function`)
     - Version numbers (e.g., `1.2.3`)
     - Type names with numbers (e.g., `Type1`, `Class2`)

3. **Structured Summarization**
   - Generates summaries using Amazon Bedrock
   - Supports multiple summary types (brief, detailed, hierarchical)
   - Extracts key points and concepts
   - Maintains technical accuracy

4. **Performance**
   - Completes processing within 30-second timeout
   - Efficient handling of large documents
   - Automatic chunking for very large PDFs

## Architecture

### Component Structure

```
PDFProcessor
├── Text Extraction
│   ├── PDF parsing (pypdf/PyPDF2)
│   ├── Page-by-page extraction
│   └── Formatting preservation
├── Technical Term Identification
│   ├── Pattern matching
│   ├── Frequency analysis
│   └── Common word filtering
└── Text Processing Integration
    ├── TextProcessor delegation
    ├── Summary generation
    └── Concept extraction
```

### Integration with Existing Services

The PDF processor integrates seamlessly with existing services:

1. **TextProcessor**: Delegates text analysis and summarization
2. **ContentUploadService**: Handles PDF file storage in S3
3. **BedrockClient**: Powers AI-driven summarization

## Implementation Details

### Class: PDFProcessor

Located in: `src/services/content_processing/pdf_processor.py`

#### Key Methods

##### `process_pdf()`

Main method for processing PDF documents with full analysis.

```python
def process_pdf(
    self,
    pdf_file: BytesIO,
    language: str = "en",
    summary_type: Optional[SummaryType] = None,
    preserve_formatting: bool = True,
) -> ProcessedContent
```

**Parameters:**
- `pdf_file`: PDF file as BytesIO object
- `language`: Language code (default: "en")
- `summary_type`: Type of summary to generate (auto-detected if None)
- `preserve_formatting`: Whether to preserve formatting (default: True)

**Returns:** `ProcessedContent` with summary, key points, and concepts

**Raises:**
- `ContentProcessingError`: If processing fails
- `ProcessingTimeoutError`: If processing exceeds 30 seconds
- `ValidationError`: If PDF is invalid or empty

##### `extract_text_only()`

Quick text extraction without summarization.

```python
def extract_text_only(
    self,
    pdf_file: BytesIO,
    preserve_formatting: bool = True,
) -> str
```

**Parameters:**
- `pdf_file`: PDF file as BytesIO object
- `preserve_formatting`: Whether to preserve formatting

**Returns:** Extracted text as string

##### `get_pdf_metadata()`

Extract metadata without processing content.

```python
def get_pdf_metadata(
    self,
    pdf_file: BytesIO,
) -> Dict[str, Any]
```

**Returns:** Dictionary with PDF metadata including:
- `page_count`: Number of pages
- `title`: Document title (if available)
- `author`: Document author (if available)
- `subject`: Document subject (if available)

### Technical Term Identification

The system uses regex patterns to identify technical terms:

```python
TECHNICAL_TERM_PATTERNS = [
    r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b',  # CamelCase
    r'\b[A-Z]{2,}\b',                     # ACRONYMS
    r'\b\w+\(\)',                         # function()
    r'\b[a-z_]+\.[a-z_]+\b',             # module.function
    r'\b\d+\.\d+\.\d+\b',                # version numbers
    r'\b[A-Z][a-z]+\d+\b',               # Type1, Class2
]
```

Common words are filtered out to avoid false positives.

### Formatting Preservation

The system preserves document structure:

1. **Paragraph Breaks**: Maintains empty lines between paragraphs
2. **Bullet Points**: Preserves lines starting with `-`, `•`, or `*`
3. **Numbered Lists**: Preserves lines starting with numbers and periods
4. **Code Blocks**: Preserves indented content (4+ spaces)
5. **Page Breaks**: Inserts markers between pages

## Usage Examples

### Basic PDF Processing

```python
from io import BytesIO
from src.services.content_processing import PDFProcessor, TextProcessor
from src.shared.aws_clients.bedrock_client import BedrockClient

# Initialize services
bedrock_client = BedrockClient()
text_processor = TextProcessor(bedrock_client=bedrock_client)
pdf_processor = PDFProcessor(text_processor=text_processor)

# Process PDF
with open("document.pdf", "rb") as f:
    pdf_file = BytesIO(f.read())

result = pdf_processor.process_pdf(
    pdf_file=pdf_file,
    language="en",
)

print(f"Summary: {result.summary.text}")
print(f"Key Points: {result.key_points}")
print(f"Technical Terms: {result.metadata['technical_terms']}")
```

### Extract Text Only

```python
# Quick text extraction
with open("document.pdf", "rb") as f:
    pdf_file = BytesIO(f.read())

text = pdf_processor.extract_text_only(pdf_file=pdf_file)
print(text)
```

### Get Metadata

```python
# Extract metadata
with open("document.pdf", "rb") as f:
    pdf_file = BytesIO(f.read())

metadata = pdf_processor.get_pdf_metadata(pdf_file=pdf_file)
print(f"Pages: {metadata['page_count']}")
print(f"Title: {metadata.get('title', 'N/A')}")
```

## Testing

### Unit Tests

Comprehensive unit tests are located in `tests/unit/test_pdf_processor.py`:

- **25 test cases** covering all functionality
- **87% code coverage**
- Tests for success cases, error handling, and edge cases

Key test categories:
1. PDF processing with various configurations
2. Text extraction and formatting preservation
3. Technical term identification
4. Metadata extraction
5. Error handling (invalid PDFs, timeouts, empty content)
6. Multi-page document handling
7. Different language support

### Running Tests

```bash
# Run all PDF processor tests
pytest tests/unit/test_pdf_processor.py -v

# Run with coverage
pytest tests/unit/test_pdf_processor.py --cov=src/services/content_processing/pdf_processor

# Run specific test
pytest tests/unit/test_pdf_processor.py::TestPDFProcessor::test_process_pdf_success -v
```

## Performance Considerations

### Timeout Management

The processor enforces a 30-second timeout for PDF processing:

1. **Initial Check**: After text extraction
2. **Pre-Processing Check**: Before delegating to TextProcessor
3. **Final Check**: After complete processing

### Large Document Handling

For documents exceeding 10,000 words:
- Automatic hierarchical summarization
- Content chunking (8,000 words per chunk)
- Efficient memory management

### Optimization Tips

1. **Use `extract_text_only()`** for quick text extraction without AI processing
2. **Disable formatting preservation** if not needed to speed up extraction
3. **Specify summary type** to avoid auto-detection overhead
4. **Cache extracted text** if processing multiple times

## Error Handling

### Common Errors

1. **ValidationError**
   - Invalid PDF file format
   - Empty PDF (no extractable text)
   - Missing file extension

2. **ProcessingTimeoutError**
   - Processing exceeds 30-second limit
   - Large documents requiring more time

3. **ContentProcessingError**
   - PDF parsing failures
   - Text extraction errors
   - Summarization failures

### Error Recovery

```python
try:
    result = pdf_processor.process_pdf(pdf_file=pdf_file)
except ValidationError as e:
    print(f"Invalid PDF: {e.message}")
    # Handle invalid input
except ProcessingTimeoutError as e:
    print(f"Timeout: {e.message}")
    # Try with simpler processing or chunking
except ContentProcessingError as e:
    print(f"Processing failed: {e.message}")
    # Log error and notify user
```

## Requirements Validation

This implementation satisfies **Requirement 1.3**:

> WHEN a user uploads PDF documents, THE Content_Processor SHALL extract text and generate summaries preserving key technical terms

### Validation Checklist

- ✅ PDF text extraction using PyPDF2/pypdf
- ✅ Technical term identification and preservation
- ✅ Structured summary generation
- ✅ Integration with existing text processing pipeline
- ✅ Error handling for invalid PDFs
- ✅ 30-second processing timeout compliance
- ✅ Comprehensive unit test coverage (87%)

## Future Enhancements

Potential improvements for future iterations:

1. **OCR Support**: Extract text from scanned PDFs using Amazon Textract
2. **Table Extraction**: Preserve table structures in extracted text
3. **Image Analysis**: Extract and analyze images using Amazon Rekognition
4. **Multi-Column Layout**: Better handling of complex PDF layouts
5. **Annotation Support**: Extract PDF annotations and comments
6. **Incremental Processing**: Process large PDFs in background jobs

## Dependencies

### Required Libraries

- `pypdf>=3.17.0` or `PyPDF2>=3.0.0`: PDF parsing and text extraction
- `boto3>=1.34.0`: AWS SDK for Bedrock integration
- `pydantic>=2.5.0`: Data validation and serialization

### Development Dependencies

- `reportlab>=4.0.0`: PDF generation for testing
- `pytest>=7.4.3`: Testing framework
- `pytest-cov>=4.1.0`: Coverage reporting

## Related Documentation

- [Text Processing Implementation](./TEXT_PROCESSING_IMPLEMENTATION.md)
- [Content Upload System](./CONTENT_UPLOAD_SYSTEM.md)
- [Development Guide](./DEVELOPMENT.md)

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review error messages and logs
3. Consult the design document for architecture details
4. Refer to AWS Bedrock documentation for AI capabilities
