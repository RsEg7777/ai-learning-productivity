"""Example demonstrating PDF processing with text extraction."""

import sys
from io import BytesIO
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.content_processing import PDFProcessor, TextProcessor
from src.shared.aws_clients.bedrock_client import BedrockClient


def create_sample_pdf() -> BytesIO:
    """Create a sample PDF for demonstration."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        print("Error: reportlab is required for this example")
        print("Install it with: pip install reportlab")
        sys.exit(1)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Page 1: Introduction
    c.drawString(100, 750, "AI Learning Assistant - Technical Documentation")
    c.drawString(100, 730, "Version 1.2.3")
    c.drawString(100, 700, "Introduction")
    c.drawString(100, 680, "This document describes the HTTPRequest and JSONParser modules.")
    c.drawString(100, 660, "The API uses RESTful architecture with JSON data format.")
    c.drawString(100, 640, "")
    c.drawString(100, 620, "Key Features:")
    c.drawString(120, 600, "- CamelCase naming conventions")
    c.drawString(120, 580, "- Comprehensive error handling")
    c.drawString(120, 560, "- Support for multiple programming languages")
    c.showPage()

    # Page 2: Technical Details
    c.drawString(100, 750, "Technical Implementation")
    c.drawString(100, 730, "")
    c.drawString(100, 710, "The DatabaseConnection class handles all SQL queries.")
    c.drawString(100, 690, "Functions like getData() and processRequest() are available.")
    c.drawString(100, 670, "")
    c.drawString(100, 650, "Code Example:")
    c.drawString(120, 630, "    def getData():")
    c.drawString(120, 610, "        return database.query()")
    c.drawString(100, 590, "")
    c.drawString(100, 570, "Common acronyms: HTTP, JSON, API, SQL, REST")
    c.showPage()

    # Page 3: Conclusion
    c.drawString(100, 750, "Conclusion")
    c.drawString(100, 730, "")
    c.drawString(100, 710, "This API provides a robust foundation for building")
    c.drawString(100, 690, "scalable web applications with modern best practices.")
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


def main():
    """Run PDF processing example."""
    print("=" * 80)
    print("PDF Processing Example")
    print("=" * 80)
    print()

    # Create sample PDF
    print("1. Creating sample PDF document...")
    pdf_file = create_sample_pdf()
    print("   ✓ Sample PDF created")
    print()

    # Initialize services (using mock for Bedrock in this example)
    print("2. Initializing PDF processor...")
    
    # Note: In production, you would use real AWS clients
    # For this example, we'll demonstrate the structure
    try:
        bedrock_client = BedrockClient()
        text_processor = TextProcessor(bedrock_client=bedrock_client)
        pdf_processor = PDFProcessor(text_processor=text_processor)
        print("   ✓ PDF processor initialized")
    except Exception as e:
        print(f"   ⚠ Could not initialize AWS clients: {e}")
        print("   Note: This example requires AWS credentials configured")
        print()
        print("   Demonstrating text extraction only...")
        
        # Create a minimal mock for demonstration
        from unittest.mock import Mock
        mock_bedrock = Mock()
        text_processor = TextProcessor(bedrock_client=mock_bedrock)
        pdf_processor = PDFProcessor(text_processor=text_processor)
    
    print()

    # Extract text only
    print("3. Extracting text from PDF...")
    try:
        extracted_text = pdf_processor.extract_text_only(
            pdf_file=pdf_file,
            preserve_formatting=True,
        )
        print("   ✓ Text extracted successfully")
        print()
        print("   Extracted Text Preview:")
        print("   " + "-" * 76)
        # Show first 500 characters
        preview = extracted_text[:500]
        for line in preview.split('\n'):
            print(f"   {line}")
        if len(extracted_text) > 500:
            print("   ...")
        print("   " + "-" * 76)
        print()
    except Exception as e:
        print(f"   ✗ Error extracting text: {e}")
        return

    # Get PDF metadata
    print("4. Extracting PDF metadata...")
    pdf_file.seek(0)  # Reset file pointer
    try:
        metadata = pdf_processor.get_pdf_metadata(pdf_file=pdf_file)
        print("   ✓ Metadata extracted successfully")
        print()
        print("   Metadata:")
        for key, value in metadata.items():
            print(f"   - {key}: {value}")
        print()
    except Exception as e:
        print(f"   ✗ Error extracting metadata: {e}")

    # Identify technical terms
    print("5. Identifying technical terms...")
    technical_terms = pdf_processor._identify_technical_terms(extracted_text)
    print(f"   ✓ Found {len(technical_terms)} technical terms")
    print()
    print("   Top Technical Terms:")
    for i, term in enumerate(technical_terms[:10], 1):
        print(f"   {i}. {term}")
    print()

    # Process PDF with summarization (requires AWS)
    print("6. Processing PDF with summarization...")
    print("   Note: This step requires AWS Bedrock credentials")
    print("   In production, this would:")
    print("   - Extract text from all pages")
    print("   - Preserve technical terms and formatting")
    print("   - Generate structured summaries using Amazon Bedrock")
    print("   - Extract key concepts and points")
    print("   - Complete within 30-second timeout")
    print()

    # Example of what the output would look like
    print("   Example Output Structure:")
    print("   {")
    print("     'id': 'processed-123',")
    print("     'summary': {")
    print("       'text': 'Comprehensive summary...',")
    print("       'key_points': ['Point 1', 'Point 2', ...],")
    print("       'type': 'detailed'")
    print("     },")
    print("     'concepts': [")
    print("       {'name': 'HTTPRequest', 'importance': 0.9},")
    print("       {'name': 'JSONParser', 'importance': 0.85},")
    print("       ...")
    print("     ],")
    print("     'metadata': {")
    print("       'page_count': 3,")
    print("       'word_count': 150,")
    print("       'technical_terms': ['HTTPRequest', 'JSONParser', ...]")
    print("     }")
    print("   }")
    print()

    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
