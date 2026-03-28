"""AWS service client utilities."""

from .s3_client import S3Client
from .dynamodb_client import DynamoDBClient
from .bedrock_client import BedrockClient
from .transcribe_client import TranscribeClient
from .polly_client import PollyClient
from .translate_client import TranslateClient
from .comprehend_client import ComprehendClient
from .cognito_client import CognitoClient

__all__ = [
    "S3Client",
    "DynamoDBClient",
    "BedrockClient",
    "TranscribeClient",
    "PollyClient",
    "TranslateClient",
    "ComprehendClient",
    "CognitoClient",
]
