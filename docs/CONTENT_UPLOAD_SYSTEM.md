# Content Upload and Storage System

## Overview

The Content Upload and Storage System provides secure file upload capabilities with AWS S3 integration, supporting multiple file types including text, PDF, video, and audio files. The system implements AES-256 encryption for data at rest and in transit, along with drag-and-drop functionality and upload progress tracking.

## Features

### Supported File Types

- **Text Files**: `.txt`, `.md`, `.markdown`
- **PDF Documents**: `.pdf`
- **Video Files**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`
- **Audio Files**: `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`
- **Code Files**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.cs`, `.go`, `.rs`, `.php`, `.rb`

### File Size Limits

- Text: 10 MB
- PDF: 50 MB
- Video: 500 MB
- Audio: 100 MB
- Code: 1 MB

### Security Features

1. **AES-256 Encryption**: All files are encrypted at rest using AWS S3 server-side encryption
2. **Encryption in Transit**: HTTPS/TLS for all data transfers
3. **Access Control**: User-based access control with Cognito authentication
4. **Presigned URLs**: Temporary access URLs with configurable expiration
5. **Audit Logging**: All upload operations are logged for security auditing

## Architecture

### Components

1. **ContentUploadService**: Core service handling file uploads and S3 operations
2. **ContentUploadHandler**: API Gateway Lambda handler for HTTP requests
3. **S3Client**: AWS S3 client wrapper with encryption support

### Data Flow

```
Client → API Gateway → Lambda Handler → ContentUploadService → S3 Client → AWS S3
```

## Usage

### Service Layer

```python
from src.services.content_processing import ContentUploadService
from src.shared.aws_clients.s3_client import S3Client

# Initialize service
s3_client = S3Client(bucket_name="my-content-bucket")
upload_service = ContentUploadService(s3_client=s3_client)

# Upload content
with open("document.pdf", "rb") as file_obj:
    content = upload_service.upload_content(
        user_id="user123",
        file_obj=file_obj,
        filename="document.pdf",
        title="My Document",
        language="en",
    )

# Get presigned URL for download
url = upload_service.get_presigned_url(content, expiration=3600)

# Download content
with open("downloaded.pdf", "wb") as file_obj:
    upload_service.download_content(content, file_obj)

# Delete content
upload_service.delete_content(content)
```

### API Layer

#### Upload Endpoint

**POST** `/content/upload`

**Query Parameters:**
- `filename` (required): Original filename with extension
- `title` (optional): Content title
- `language` (optional): Language code (default: "en")

**Request Body:**
- Base64-encoded file content OR
- JSON with `file_content` field containing base64-encoded data

**Headers:**
- `Authorization`: Bearer token from Cognito

**Response (201 Created):**
```json
{
  "content_id": "uuid",
  "title": "My Document",
  "type": "pdf",
  "language": "en",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "s3_location": "s3://bucket/uploads/user123/2024/01/content-id.pdf",
  "presigned_url": "https://...",
  "metadata": {
    "file_size": 1024000,
    "mime_type": "application/pdf"
  },
  "message": "Content uploaded successfully"
}
```

#### Upload Progress Endpoint

**GET** `/content/upload/{content_id}/progress`

**Response (200 OK):**
```json
{
  "content_id": "uuid",
  "status": "completed",
  "progress": 100,
  "message": "Upload completed successfully"
}
```

### Client-Side Integration

#### JavaScript/TypeScript Example

```javascript
// Drag-and-drop upload
const dropZone = document.getElementById('drop-zone');

dropZone.addEventListener('drop', async (e) => {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  
  // Convert file to base64
  const reader = new FileReader();
  reader.onload = async () => {
    const base64Content = reader.result.split(',')[1];
    
    // Upload to API
    const response = await fetch(
      `/content/upload?filename=${file.name}&title=${file.name}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_content: base64Content
        })
      }
    );
    
    const result = await response.json();
    console.log('Upload successful:', result);
  };
  
  reader.readAsDataURL(file);
});

// Track upload progress (for large files)
async function trackProgress(contentId) {
  const response = await fetch(`/content/upload/${contentId}/progress`, {
    headers: {
      'Authorization': `Bearer ${authToken}`
    }
  });
  
  const progress = await response.json();
  console.log(`Upload progress: ${progress.progress}%`);
}
```

#### React Example

```jsx
import React, { useState } from 'react';

function FileUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleDrop = async (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    
    setUploading(true);
    setProgress(0);
    
    try {
      // Convert to base64
      const base64 = await fileToBase64(file);
      
      // Upload
      const response = await fetch(
        `/content/upload?filename=${file.name}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ file_content: base64 })
        }
      );
      
      const result = await response.json();
      setProgress(100);
      console.log('Upload complete:', result);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      style={{
        border: '2px dashed #ccc',
        padding: '20px',
        textAlign: 'center'
      }}
    >
      {uploading ? (
        <div>Uploading... {progress}%</div>
      ) : (
        <div>Drag and drop files here</div>
      )}
    </div>
  );
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
```

## S3 Storage Structure

Files are organized in S3 with the following structure:

```
uploads/
  {user_id}/
    {year}/
      {month}/
        {content_id}.{extension}
```

Example:
```
uploads/
  user123/
    2024/
      01/
        abc-123-def.pdf
        xyz-456-ghi.mp4
```

This structure provides:
- User isolation
- Time-based organization
- Easy cleanup and archival
- Efficient querying

## Error Handling

### Validation Errors (400)

```json
{
  "error": "VALIDATION_ERROR",
  "message": "File size (15.5 MB) exceeds limit (10.0 MB)",
  "details": {
    "field": "file_size",
    "file_size": 16252928,
    "max_size": 10485760,
    "content_type": "text"
  }
}
```

### Unsupported Format Errors (400)

```json
{
  "error": "UNSUPPORTED_FORMAT",
  "message": "Unsupported format: .xyz. Supported formats are: .txt, .pdf, .mp4, ...",
  "details": {
    "format_provided": ".xyz",
    "supported_formats": [".txt", ".pdf", ".mp4", "..."]
  }
}
```

### Processing Errors (500)

```json
{
  "error": "CONTENT_PROCESSING_ERROR",
  "message": "Failed to upload content: S3 upload failed",
  "details": {
    "content_type": "pdf"
  }
}
```

## Testing

### Unit Tests

Run unit tests for the upload service:

```bash
pytest tests/unit/test_content_upload_service.py -v
```

Run unit tests for the API handler:

```bash
pytest tests/unit/test_content_upload_handler.py -v
```

### Test Coverage

The implementation includes comprehensive test coverage:

- **ContentUploadService**: 93% coverage
  - Upload success for all file types
  - Validation errors
  - File size limits
  - S3 operations
  - Metadata handling

- **ContentUploadHandler**: 82% coverage
  - API request handling
  - Authentication
  - Error responses
  - CORS headers
  - Multiple content encodings

## Configuration

### Environment Variables

```bash
# S3 bucket for content storage
CONTENT_BUCKET_NAME=ai-learning-assistant-content

# AWS region
AWS_REGION=us-east-1

# Cognito user pool (for authentication)
COGNITO_USER_POOL_ID=us-east-1_xxxxx
```

### AWS IAM Permissions

The Lambda execution role requires the following S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:HeadObject"
      ],
      "Resource": "arn:aws:s3:::ai-learning-assistant-content/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::ai-learning-assistant-content"
    }
  ]
}
```

## Security Best Practices

1. **Always use HTTPS**: Ensure all API calls use HTTPS to encrypt data in transit
2. **Validate file types**: Server-side validation prevents malicious file uploads
3. **Limit file sizes**: Prevents denial-of-service attacks
4. **Use presigned URLs**: Temporary access URLs expire automatically
5. **Implement rate limiting**: Prevent abuse through API Gateway throttling
6. **Audit logging**: Track all upload operations for security monitoring
7. **User isolation**: Files are organized by user ID to prevent unauthorized access

## Performance Considerations

1. **Large Files**: For files > 100MB, consider implementing multipart uploads
2. **Concurrent Uploads**: API Gateway and Lambda scale automatically
3. **Presigned URLs**: Generate URLs on-demand to avoid storage overhead
4. **Caching**: Use CloudFront for frequently accessed content
5. **Compression**: Consider compressing large text files before upload

## Future Enhancements

1. **Multipart Upload**: Support for files > 500MB using S3 multipart upload
2. **Virus Scanning**: Integrate with AWS GuardDuty or third-party scanners
3. **Image Processing**: Automatic thumbnail generation for images
4. **Video Transcoding**: Convert videos to optimized formats
5. **Duplicate Detection**: Hash-based deduplication to save storage
6. **Batch Upload**: Support uploading multiple files in a single request
7. **Resume Upload**: Support resuming interrupted uploads

## Troubleshooting

### Upload Fails with 400 Error

- Check file extension is supported
- Verify file size is within limits
- Ensure filename has an extension
- Validate language code is supported

### Upload Fails with 401 Error

- Verify authentication token is valid
- Check Cognito user pool configuration
- Ensure user has necessary permissions

### Upload Fails with 500 Error

- Check S3 bucket exists and is accessible
- Verify IAM role has correct permissions
- Check CloudWatch logs for detailed error messages
- Ensure AWS credentials are configured correctly

### Presigned URL Doesn't Work

- Check URL hasn't expired (default: 1 hour)
- Verify S3 object exists
- Ensure CORS is configured on S3 bucket
- Check S3 bucket policy allows GetObject

## Related Documentation

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Cognito Authentication](https://docs.aws.amazon.com/cognito/)
